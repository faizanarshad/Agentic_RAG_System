"""Agentic legal document intelligence: batch analysis, question answering and corpus synthesis."""

import json
import os
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, StateGraph
from openai import OpenAI
from typing_extensions import TypedDict

from core.config import settings
from utils.logger import logger
from .embeddings_service import EmbeddingsService
from .legal_document_loader import SUPPORTED_EXTENSIONS, LegalDocumentLoader
from .legal_prompts import (
    CLASSIFY_SYSTEM, DOC_TYPES, EXTRACT_SYSTEM, FIELD_GUIDE, MAP_SYSTEM, PLAN_SYSTEM, QA_SYSTEM,
    REDUCE_SYSTEM, RISK_SYSTEM, SUMMARY_SYSTEM,
)
from .legal_store import LegalStore
from .prompt_guard import UNTRUSTED_NOTICE, detect_injection, fence, injection_risk
from .file_safety import UnsafeFileError, validate_upload
from .usage_tracker import record_usage
from .vectordb_service import VectorDBService


# Longest document text sent to the LLM in one analysis call (~40k tokens)
MAX_ANALYSIS_CHARS = 150_000
LEGAL_DOMAIN = "legal"
# Legal vectors live in their own namespace so the general Chat tab never retrieves them
LEGAL_NAMESPACE = "legal"


class DocumentState(TypedDict):
    """State for the per-document analysis graph."""
    doc_id: str
    filename: str
    file_path: str
    text: str
    classification: Dict[str, Any]
    extraction: Dict[str, Any]
    risks: Dict[str, Any]
    summary: Dict[str, Any]
    chunks_indexed: int
    owner_id: Optional[str]


class QAState(TypedDict):
    """State for the question-answering graph."""
    question: str
    file_id: Optional[str]
    owner_id: Optional[str]
    strategy: str
    sources: List[Dict[str, Any]]
    answer: Dict[str, Any]


class SynthesisState(TypedDict):
    """State for the cross-document synthesis graph."""
    question: str
    doc_type: Optional[str]
    overall_risk: Optional[str]
    max_documents: int
    owner_id: Optional[str]
    plan: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    report: Dict[str, Any]


class LegalAgentService:
    """Orchestrates the legal agents with LangGraph and runs batch ingestion in the background."""

    def __init__(self):
        """Initialize services, compile the agent graphs and resume unfinished work."""
        # Short timeout so a stalled connection is retried quickly instead of hanging for the 10-minute default
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL or None, max_retries=5, timeout=90)
        self.model = settings.LEGAL_MODEL
        self.loader = LegalDocumentLoader()
        self.store = LegalStore()
        self.embeddings = EmbeddingsService()
        self.vectordb = VectorDBService()
        self.upload_dir = os.path.join(settings.LEGAL_DATA_DIR, "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=200,
            separators=["\nARTICLE ", "\nArticle ", "\nSECTION ", "\nSection ", "\n\n", "\n", ". ", " ", ""],
        )
        self.document_graph = self._build_document_graph()
        self.qa_graph = self._build_qa_graph()
        self.synthesis_graph = self._build_synthesis_graph()
        self.executor = ThreadPoolExecutor(max_workers=settings.LEGAL_WORKERS, thread_name_prefix="legal")

        unfinished = self.store.requeue_unfinished()
        if unfinished:
            logger.info(f"Resuming {len(unfinished)} unfinished legal documents")
            for doc_id in unfinished:
                self.executor.submit(self.process_document, doc_id)

    # ------------------------------------------------------------------ LLM helper

    def _chat_json(self, system: str, user: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """Call the LLM in JSON mode and parse the result."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system + UNTRUSTED_NOTICE}, {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=max_tokens,
        )
        record_usage(self.model, response.usage, "legal")
        return json.loads(response.choices[0].message.content or "{}")

    # ------------------------------------------------------------------ ingestion

    def ingest_files(self, files: List[Tuple[str, bytes]], owner_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Save uploaded files and queue them for background analysis as one batch.

        Args:
            files: (filename, content) pairs
            owner_id: ID of the uploading user; members only ever see their own documents

        Returns:
            The batch record plus any files that were rejected
        """
        accepted, rejected = [], []
        max_bytes = settings.LEGAL_MAX_FILE_MB * 1024 * 1024
        for filename, content in files:
            extension = os.path.splitext(filename)[1].lower()
            if extension not in SUPPORTED_EXTENSIONS:
                rejected.append({"filename": filename, "reason": f"Unsupported file type '{extension}'"})
            elif not content:
                rejected.append({"filename": filename, "reason": "File is empty"})
            elif len(content) > max_bytes:
                rejected.append({"filename": filename, "reason": f"Larger than {settings.LEGAL_MAX_FILE_MB} MB"})
            else:
                try:
                    validate_upload(filename, content, SUPPORTED_EXTENSIONS)
                except UnsafeFileError as e:
                    rejected.append({"filename": filename, "reason": str(e)})
                    continue
                accepted.append((filename, extension, content))

        if not accepted:
            return {"batch": None, "rejected": rejected}

        batch_id = str(uuid.uuid4())
        self.store.create_batch(batch_id, len(accepted), owner_id)
        for filename, extension, content in accepted:
            doc_id = str(uuid.uuid4())
            # Stored under a generated name so user-supplied filenames never touch the filesystem path
            file_path = os.path.join(self.upload_dir, f"{doc_id}{extension}")
            with open(file_path, "wb") as f:
                f.write(content)
            self.store.create_document(doc_id, os.path.basename(filename), file_path, batch_id, owner_id)
            self.executor.submit(self.process_document, doc_id)

        logger.info(f"Queued legal batch {batch_id} with {len(accepted)} documents")
        return {"batch": self.store.get_batch(batch_id), "rejected": rejected}

    def process_document(self, doc_id: str) -> None:
        """Run the analysis graph for one document, recording failure instead of raising."""
        if not self.store.claim_document(doc_id):
            return
        record = self.store.get_document(doc_id)
        file_path = self.store.get_file_path(doc_id)
        if record is None or not file_path:
            return
        try:
            self.document_graph.invoke({
                "doc_id": doc_id,
                "filename": record["filename"],
                "file_path": file_path,
                "text": "",
                "classification": {},
                "extraction": {},
                "risks": {},
                "summary": {},
                "chunks_indexed": 0,
                "owner_id": record.get("owner_id"),
            })
            self.store.update_document(doc_id, status="completed")
            logger.info(f"Completed legal analysis for {record['filename']}")
        except Exception as e:
            logger.error(f"Legal analysis failed for {record['filename']}: {str(e)}")
            self.store.update_document(doc_id, status="failed", error=str(e)[:500])

    def retry_document(self, doc_id: str) -> bool:
        """Re-queue a document for analysis. Returns False if it does not exist."""
        if self.store.get_document(doc_id) is None:
            return False
        self.store.update_document(doc_id, status="queued", error=None)
        self.executor.submit(self.process_document, doc_id)
        return True

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document, its vectors and its stored file. Returns False if it does not exist."""
        if self.store.get_document(doc_id) is None:
            return False
        self._delete_vectors(doc_id)
        file_path = self.store.get_file_path(doc_id)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        self.store.delete_document(doc_id)
        return True

    def _delete_vectors(self, doc_id: str) -> None:
        """Delete every vector whose ID starts with the document ID."""
        for id_page in self.vectordb.index.list(prefix=f"{doc_id}_", namespace=LEGAL_NAMESPACE):
            if id_page:
                self.vectordb.index.delete(ids=list(id_page), namespace=LEGAL_NAMESPACE)

    # ------------------------------------------------------------------ per-document graph

    def _build_document_graph(self):
        """load -> classify -> (extract -> assess_risk ->) summarize -> index."""

        def load(state: DocumentState) -> DocumentState:
            loaded = self.loader.load(state["file_path"], state["filename"])
            self.store.update_document(
                state["doc_id"],
                text=loaded["text"],
                page_count=loaded["page_count"],
                ocr_pages=loaded["ocr_pages"],
            )
            state["text"] = loaded["text"]
            return state

        def classify(state: DocumentState) -> DocumentState:
            result = self._chat_json(
                CLASSIFY_SYSTEM,
                f"Filename: {state['filename']}\n\nDocument (beginning):\n{fence(state['text'][:12000])}",
                max_tokens=400,
            )
            if result.get("doc_type") not in DOC_TYPES:
                result["doc_type"] = "other_legal"
            state["classification"] = result
            self.store.update_document(
                state["doc_id"],
                classification=result,
                doc_type=result["doc_type"],
                subtype=result.get("subtype"),
                title=result.get("title") or state["filename"],
            )
            return state

        def route_after_classify(state: DocumentState) -> str:
            return "summarize" if state["classification"]["doc_type"] == "non_legal" else "extract"

        def extract(state: DocumentState) -> DocumentState:
            doc_type = state["classification"]["doc_type"]
            result = self._chat_json(
                EXTRACT_SYSTEM,
                f"Document type: {doc_type} ({state['classification'].get('subtype')})\n"
                f"Fields to extract into \"fields\": {FIELD_GUIDE.get(doc_type, FIELD_GUIDE['other_legal'])}\n\n"
                f"Document:\n{fence(state['text'][:MAX_ANALYSIS_CHARS])}",
                max_tokens=4000,
            )
            state["extraction"] = result
            governing_law = (result.get("fields") or {}).get("governing_law") or state["classification"].get(
                "jurisdiction"
            )
            self.store.update_document(state["doc_id"], extraction=result, governing_law=governing_law)
            return state

        def assess_risk(state: DocumentState) -> DocumentState:
            result = self._chat_json(
                RISK_SYSTEM,
                f"Document type: {state['classification'].get('subtype') or state['classification']['doc_type']}\n"
                f"Extracted data:\n{json.dumps(state['extraction'])[:20000]}\n\n"
                f"Document:\n{fence(state['text'][:MAX_ANALYSIS_CHARS])}",
                max_tokens=3000,
            )
            # Derive the level from the score so the two can never disagree
            risk_score = max(0, min(100, int(result.get("risk_score") or 0)))
            result["risk_score"] = risk_score
            result["overall_risk"] = "low" if risk_score < 35 else "medium" if risk_score < 65 else "high"
            # Text trying to steer the AI is itself a red flag: surface it and never let the document look low-risk
            excerpts = detect_injection(state["text"])
            if excerpts:
                result["risks"] = [injection_risk(excerpts)] + [r for r in result.get("risks") or [] if isinstance(r, dict)]
                result["injection_warnings"] = excerpts
                if result["overall_risk"] == "low":
                    result["risk_score"] = risk_score = max(risk_score, 35)
                    result["overall_risk"] = "medium"
            state["risks"] = result
            self.store.update_document(
                state["doc_id"],
                risks=result,
                overall_risk=result["overall_risk"],
                risk_score=risk_score,
            )
            return state

        def summarize(state: DocumentState) -> DocumentState:
            result = self._chat_json(
                SUMMARY_SYSTEM,
                f"Document:\n{fence(state['text'][:MAX_ANALYSIS_CHARS])}",
                max_tokens=800,
            )
            state["summary"] = result
            self.store.update_document(state["doc_id"], summary=result)
            return state

        def index(state: DocumentState) -> DocumentState:
            doc_id = state["doc_id"]
            classification = state["classification"]
            title = classification.get("title") or state["filename"]
            # Contextual header on each chunk improves retrieval of passages that never name the document
            header = f"Document: {title} ({classification.get('subtype') or classification['doc_type']})\n"
            metadata = {
                "file_id": doc_id,
                "source": "legal",
                "domain": LEGAL_DOMAIN,
                "doc_type": classification["doc_type"],
                "subtype": classification.get("subtype"),
                "filename": state["filename"],
                "title": title,
                "overall_risk": state["risks"].get("overall_risk"),
            }
            if state.get("owner_id"):
                metadata["owner_id"] = state["owner_id"]
            chunks = self.splitter.split_text(state["text"])
            documents = [
                Document(
                    page_content=header + chunk,
                    metadata={**metadata, "chunk_index": i, "total_chunks": len(chunks)},
                )
                for i, chunk in enumerate(chunks)
            ]
            # Remove vectors from any earlier run so a re-analysis leaves no stale chunks
            self._delete_vectors(doc_id)
            for start in range(0, len(documents), 100):
                processed = self.embeddings.process_documents(documents[start:start + 100])
                for offset, item in enumerate(processed):
                    item["id"] = f"{doc_id}_{start + offset}"
                self.vectordb.upsert_documents(processed, namespace=LEGAL_NAMESPACE)
            state["chunks_indexed"] = len(documents)
            return state

        workflow = StateGraph(DocumentState)
        workflow.add_node("load", load)
        workflow.add_node("classify", classify)
        workflow.add_node("extract", extract)
        workflow.add_node("assess_risk", assess_risk)
        workflow.add_node("summarize", summarize)
        workflow.add_node("index", index)
        workflow.set_entry_point("load")
        workflow.add_edge("load", "classify")
        workflow.add_conditional_edges(
            "classify", route_after_classify, {"extract": "extract", "summarize": "summarize"}
        )
        workflow.add_edge("extract", "assess_risk")
        workflow.add_edge("assess_risk", "summarize")
        workflow.add_edge("summarize", "index")
        workflow.add_edge("index", END)
        return workflow.compile()

    # ------------------------------------------------------------------ question answering

    def _build_qa_graph(self):
        """route -> (read full document | retrieve passages) -> generate_answer."""

        def route(state: QAState) -> str:
            if state["file_id"]:
                document = self.store.get_document(state["file_id"], include_text=True)
                if document and len(document.get("text") or "") <= settings.LEGAL_FULL_TEXT_QA_CHARS:
                    return "full_document"
            return "retrieve"

        def full_document(state: QAState) -> QAState:
            document = self.store.get_document(state["file_id"], include_text=True)
            state["strategy"] = "full_document"
            state["sources"] = [{
                "label": "S1",
                "file_id": document["id"],
                "filename": document["filename"],
                "title": document.get("title"),
                "text": document["text"],
                "score": None,
            }]
            return state

        def retrieve(state: QAState) -> QAState:
            metadata_filter = self._corpus_filter(None, None, state["owner_id"])
            if state["file_id"]:
                metadata_filter["file_id"] = {"$eq": state["file_id"]}
            matches = self.vectordb.search_similar(
                self.embeddings.generate_embedding(state["question"]),
                top_k=8,
                metadata_filter=metadata_filter,
                namespace=LEGAL_NAMESPACE,
            )
            state["strategy"] = "retrieval"
            state["sources"] = [
                {
                    "label": f"S{i}",
                    "file_id": match["metadata"].get("file_id"),
                    "filename": match["metadata"].get("filename"),
                    "title": match["metadata"].get("title"),
                    "text": match["text"],
                    "score": round(match["score"], 3),
                }
                for i, match in enumerate(matches, start=1)
            ]
            return state

        def answer(state: QAState) -> QAState:
            if not state["sources"]:
                state["answer"] = {
                    "answer": "No legal documents matched this question. Upload and analyze documents first.",
                    "citations": [],
                    "confidence": "low",
                }
                return state
            sources_text = "\n\n".join(
                f"[{source['label']}] {source.get('title') or source['filename']}\n{source['text']}"
                for source in state["sources"]
            )
            state["answer"] = self._chat_json(
                QA_SYSTEM, f"Sources:\n{fence(sources_text, 'SOURCES')}\n\nQuestion: {state['question']}", max_tokens=1500
            )
            return state

        workflow = StateGraph(QAState)
        workflow.add_node("full_document", full_document)
        workflow.add_node("retrieve", retrieve)
        workflow.add_node("generate_answer", answer)
        workflow.set_conditional_entry_point(route, {"full_document": "full_document", "retrieve": "retrieve"})
        workflow.add_edge("full_document", "generate_answer")
        workflow.add_edge("retrieve", "generate_answer")
        workflow.add_edge("generate_answer", END)
        return workflow.compile()

    def ask(self, question: str, file_id: Optional[str] = None, owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Answer a question about one document or the corpus (owner_id limits it to one user's documents)."""
        result = self.qa_graph.invoke({
            "question": question, "file_id": file_id, "owner_id": owner_id,
            "strategy": "", "sources": [], "answer": {},
        })
        return {
            "question": question,
            "answer": result["answer"].get("answer", ""),
            "confidence": result["answer"].get("confidence"),
            "citations": result["answer"].get("citations", []),
            "strategy": result["strategy"],
            "sources": [
                {**{k: v for k, v in source.items() if k != "text"}, "excerpt": source["text"][:500]}
                for source in result["sources"]
            ],
        }

    def search(
        self, query: str, doc_type: Optional[str] = None, overall_risk: Optional[str] = None, top_k: int = 10,
        owner_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search over legal document passages."""
        matches = self.vectordb.search_similar(
            self.embeddings.generate_embedding(query),
            top_k=top_k,
            metadata_filter=self._corpus_filter(doc_type, overall_risk, owner_id),
            namespace=LEGAL_NAMESPACE,
        )
        return [
            {
                "file_id": match["metadata"].get("file_id"),
                "filename": match["metadata"].get("filename"),
                "title": match["metadata"].get("title"),
                "doc_type": match["metadata"].get("doc_type"),
                "score": round(match["score"], 3),
                "text": match["text"],
            }
            for match in matches
        ]

    @staticmethod
    def _corpus_filter(
        doc_type: Optional[str], overall_risk: Optional[str], owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        metadata_filter: Dict[str, Any] = {"domain": {"$eq": LEGAL_DOMAIN}}
        if owner_id:
            metadata_filter["owner_id"] = {"$eq": owner_id}
        if doc_type:
            metadata_filter["doc_type"] = {"$eq": doc_type}
        if overall_risk:
            metadata_filter["overall_risk"] = {"$eq": overall_risk}
        return metadata_filter

    # ------------------------------------------------------------------ corpus synthesis

    def _build_synthesis_graph(self):
        """plan_queries -> retrieve -> map (per document, in parallel) -> reduce."""

        def plan(state: SynthesisState) -> SynthesisState:
            result = self._chat_json(PLAN_SYSTEM, f"Research question: {state['question']}", max_tokens=400)
            queries = [q for q in result.get("search_queries", []) if isinstance(q, str) and q.strip()][:4]
            result["search_queries"] = [state["question"]] + queries
            state["plan"] = result
            return state

        def retrieve(state: SynthesisState) -> SynthesisState:
            metadata_filter = self._corpus_filter(state["doc_type"], state["overall_risk"], state["owner_id"])
            by_document: Dict[str, Dict[str, Any]] = {}
            for query in state["plan"]["search_queries"]:
                matches = self.vectordb.search_similar(
                    self.embeddings.generate_embedding(query),
                    top_k=30,
                    metadata_filter=metadata_filter,
                    namespace=LEGAL_NAMESPACE,
                )
                for match in matches:
                    file_id = match["metadata"].get("file_id")
                    entry = by_document.setdefault(file_id, {"file_id": file_id, "score": 0.0, "passages": {}})
                    entry["score"] = max(entry["score"], match["score"])
                    entry["passages"][match["id"]] = (match["score"], match["text"])
            ranked = sorted(by_document.values(), key=lambda entry: entry["score"], reverse=True)
            candidates = []
            for entry in ranked[:state["max_documents"]]:
                passages = sorted(entry["passages"].values(), key=lambda item: item[0], reverse=True)[:4]
                candidates.append({
                    "file_id": entry["file_id"],
                    "score": round(entry["score"], 3),
                    "passages": [text for _, text in passages],
                })
            state["candidates"] = candidates
            return state

        def map_documents(state: SynthesisState) -> SynthesisState:
            records = {r["id"]: r for r in self.store.get_documents([c["file_id"] for c in state["candidates"]])}

            def analyze(candidate: Dict[str, Any]) -> Dict[str, Any]:
                record = records.get(candidate["file_id"])
                if record is None:
                    return {**candidate, "relevant": False, "findings": [], "evidence": []}
                context = {
                    "title": record.get("title"),
                    "type": record.get("subtype") or record.get("doc_type"),
                    "summary": (record.get("summary") or {}).get("summary"),
                    "key_fields": (record.get("extraction") or {}).get("fields"),
                    "overall_risk": record.get("overall_risk"),
                    "top_risks": [
                        {"title": r.get("title"), "severity": r.get("severity")}
                        for r in ((record.get("risks") or {}).get("risks") or [])[:4]
                    ],
                }
                try:
                    result = self._chat_json(
                        MAP_SYSTEM,
                        f"Research question: {state['question']}\n"
                        f"Analysis focus: {state['plan'].get('analysis_focus', '')}\n\n"
                        f"Document profile:\n{json.dumps(context)}\n\n"
                        "Passages:\n" + fence("\n---\n".join(candidate["passages"]), "PASSAGES"),
                        max_tokens=900,
                    )
                except Exception as e:
                    logger.error(f"Synthesis map step failed for {candidate['file_id']}: {str(e)}")
                    result = {"relevant": False, "findings": [], "evidence": []}
                return {
                    **candidate,
                    "filename": record["filename"],
                    "title": record.get("title"),
                    "doc_type": record.get("doc_type"),
                    "subtype": record.get("subtype"),
                    "overall_risk": record.get("overall_risk"),
                    "relevant": bool(result.get("relevant")),
                    "findings": result.get("findings") or [],
                    "evidence": result.get("evidence") or [],
                }

            with ThreadPoolExecutor(max_workers=8) as pool:
                findings = list(pool.map(analyze, state["candidates"]))
            for i, finding in enumerate(findings, start=1):
                finding["label"] = f"D{i}"
            state["findings"] = findings
            return state

        def reduce(state: SynthesisState) -> SynthesisState:
            relevant = [f for f in state["findings"] if f["relevant"]]
            if not relevant:
                state["report"] = {
                    "executive_summary": "None of the retrieved documents contained information relevant to "
                                         "this question.",
                    "themes": [], "comparisons": [], "outliers": [], "risks": [], "recommendations": [],
                    "limitations": f"{len(state['findings'])} candidate documents were reviewed.",
                }
                return state
            findings_text = "\n\n".join(
                f"{f['label']}: {f.get('title') or f['filename']} "
                f"[{f.get('subtype') or f.get('doc_type')}, risk: {f.get('overall_risk')}]\n"
                + "\n".join(f"- {finding}" for finding in f["findings"])
                for f in relevant
            )
            stats = self.corpus_stats()
            stats_text = json.dumps({
                "documents_analyzed": stats["completed"],
                "by_doc_type": stats["by_doc_type"],
                "by_risk": stats["by_risk"],
            })
            state["report"] = self._chat_json(
                REDUCE_SYSTEM,
                f"Research question: {state['question']}\n\nCorpus statistics: {stats_text}\n\n"
                f"Per-document findings ({len(relevant)} relevant of {len(state['findings'])} reviewed):\n"
                f"{findings_text}",
                max_tokens=3500,
            )
            return state

        workflow = StateGraph(SynthesisState)
        workflow.add_node("plan_queries", plan)
        workflow.add_node("retrieve", retrieve)
        workflow.add_node("map", map_documents)
        workflow.add_node("reduce", reduce)
        workflow.set_entry_point("plan_queries")
        workflow.add_edge("plan_queries", "retrieve")
        workflow.add_edge("retrieve", "map")
        workflow.add_edge("map", "reduce")
        workflow.add_edge("reduce", END)
        return workflow.compile()

    def synthesize(
        self,
        question: str,
        doc_type: Optional[str] = None,
        overall_risk: Optional[str] = None,
        max_documents: int = 15,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answer a research question by synthesizing findings across many documents."""
        result = self.synthesis_graph.invoke({
            "question": question,
            "doc_type": doc_type,
            "overall_risk": overall_risk,
            "max_documents": max_documents,
            "owner_id": owner_id,
            "plan": {},
            "candidates": [],
            "findings": [],
            "report": {},
        })
        return {
            "question": question,
            "plan": result["plan"],
            "report": result["report"],
            "documents": [
                {k: v for k, v in finding.items() if k != "passages"} for finding in result["findings"]
            ],
            "documents_reviewed": len(result["findings"]),
            "documents_relevant": sum(1 for finding in result["findings"] if finding["relevant"]),
        }

    # ------------------------------------------------------------------ corpus statistics

    def corpus_stats(self, owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate the structured analyses of every completed document (optionally one user's)."""
        documents = self.store.all_analyzed(owner_id)
        by_type = Counter(d["doc_type"] or "unknown" for d in documents)
        by_risk = Counter(d["overall_risk"] for d in documents if d["overall_risk"])
        governing_law = Counter(
            " ".join(d["governing_law"].split()) for d in documents if isinstance(d["governing_law"], str)
        )
        parties: Counter = Counter()
        risk_categories: Counter = Counter()
        deadlines = []
        today = date.today()

        for d in documents:
            extraction = d.get("extraction") or {}
            label = d.get("title") or d["filename"]
            for party in {p.get("name", "").strip() for p in extraction.get("parties") or [] if p.get("name")}:
                parties[party] += 1
            for risk in (d.get("risks") or {}).get("risks") or []:
                risk_categories[risk.get("category") or "other"] += 1
            dated_items = [(item.get("date"), item.get("label")) for item in extraction.get("key_dates") or []]
            dated_items += [
                (item.get("deadline"), f"{item.get('party')}: {item.get('obligation')}")
                for item in extraction.get("obligations") or []
            ]
            seen_dates = set()
            for raw_date, description in dated_items:
                parsed = _parse_iso_date(raw_date)
                # The same date often appears as both a key date and an obligation deadline
                if parsed and parsed >= today and parsed not in seen_dates:
                    seen_dates.add(parsed)
                    deadlines.append({
                        "date": parsed.isoformat(), "description": description, "document": label, "file_id": d["id"]
                    })

        scores = [d["risk_score"] for d in documents if d.get("risk_score") is not None]
        high_risk = sorted(
            (d for d in documents if d["overall_risk"] == "high"),
            key=lambda d: d.get("risk_score") or 0,
            reverse=True,
        )
        status_counts = self.store.status_counts(owner_id)
        return {
            "total": sum(status_counts.values()),
            "completed": status_counts.get("completed", 0),
            "by_status": status_counts,
            "by_doc_type": dict(by_type.most_common()),
            "by_risk": {level: by_risk.get(level, 0) for level in ("high", "medium", "low")},
            "average_risk_score": round(sum(scores) / len(scores), 1) if scores else None,
            "governing_law": governing_law.most_common(8),
            "top_parties": parties.most_common(10),
            "risk_categories": risk_categories.most_common(10),
            "upcoming_deadlines": sorted(deadlines, key=lambda item: item["date"])[:15],
            "high_risk_documents": [
                {"file_id": d["id"], "title": d.get("title") or d["filename"], "risk_score": d.get("risk_score"),
                 "doc_type": d["doc_type"]}
                for d in high_risk[:10]
            ],
            "total_pages": sum(d.get("page_count") or 0 for d in documents),
            "ocr_pages": sum(len(d.get("ocr_pages") or []) for d in documents),
        }


def _parse_iso_date(value: Any) -> Optional[date]:
    """Parse a YYYY-MM-DD prefix; return None for free-text dates."""
    if not isinstance(value, str) or len(value) < 10:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None
