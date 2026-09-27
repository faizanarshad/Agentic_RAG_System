import engineeringReview from '@/assets/engineering-review.png';
import engineeringCompare from '@/assets/engineering-compare.png';
import legalSynthesis from '@/assets/legal-synthesis.png';
import medicalChat from '@/assets/medical-chat.png';

// Marketing content. Figures in `benchmarks` come from internal evaluations on synthetic test data
// (see scripts/generate_engineering_samples.py and scripts/generate_legal_corpus.py) and are labelled as such.

export const workflow = [
  {
    step: '01',
    title: 'Ingest',
    body: 'PDFs, scanned pages, Word files, images and DXF CAD files are rendered and read. Scanned pages go through OCR; vector files keep their exact text.',
  },
  {
    step: '02',
    title: 'Extract',
    body: 'Specialised agents pull out the structure that matters: title blocks and tolerances, parties and obligations, findings and deadlines.',
  },
  {
    step: '03',
    title: 'Verify',
    body: 'Deterministic rule checks, cross-checks between views and documents, and zoomed re-verification catch what a single model pass misses.',
  },
  {
    step: '04',
    title: 'Deliver',
    body: 'Findings with locations and fixes, cited answers, comparison reports and filled documentation templates you can edit and export.',
  },
];

export const guardrails = [
  {
    title: 'Cited, not asserted',
    body: 'Answers and synthesis reports reference the exact documents and passages they rely on, so every claim can be traced.',
  },
  {
    title: 'Rules before judgement',
    body: 'Deterministic checks run alongside the models: revision mismatches, unit mixing, undefined datums, overridden CAD dimensions.',
  },
  {
    title: 'Claims are re-checked',
    body: 'When a model reports a detail, a second, narrower pass verifies it on a zoomed crop. Unconfirmed claims are dropped.',
  },
  {
    title: 'Gaps are flagged',
    body: 'Missing facts stay empty and are listed for review. Drafted text is marked, and numbers not found in the sources are flagged.',
  },
];

export const benchmarks = [
  { value: '7/7', label: 'Planted drawing errors detected', detail: 'Across a PDF part drawing and a DXF flange' },
  { value: '2/2', label: 'Unrecorded revision changes caught', detail: 'Changes missing from the revision table' },
  { value: '96%', label: 'Legal documents classified as intended', detail: '96 of 100 synthetic documents' },
  { value: '100', label: 'Documents synthesised in one corpus', detail: 'Including 5 scanned PDFs read by OCR' },
];

// Real findings from the agents' runs on the synthetic test datasets (see scripts/evaluate_agents.py)
export const findings = [
  {
    workspace: 'Engineering', tone: 'critical', tag: 'Critical',
    title: 'Overall length 120 mm in the front view, 125 mm in the top view',
    detail: 'Cross-view consistency check on a bracket drawing, with the location and the fix.',
    source: 'bracket_EP-1001_revA.pdf',
  },
  {
    workspace: 'Engineering', tone: 'critical', tag: 'Critical',
    title: 'Dimension text overridden to Ø50, but the CAD geometry measures 48.0 mm',
    detail: 'Read directly from DXF entities: a mismatch a visual check would miss.',
    source: 'flange_FL-2040.dxf',
  },
  {
    workspace: 'Engineering', tone: 'major', tag: 'Unrecorded',
    title: 'Hole Ø8.5 → Ø9.0 and thickness 10 → 12 changed, not in the revision table',
    detail: 'Every change between revisions is audited against the new revision-table entries.',
    source: 'rev A → rev B comparison',
  },
  {
    workspace: 'Engineering', tone: 'verify', tag: 'Verified',
    title: 'Claimed “datum C” rejected after a zoomed re-check of the drawing',
    detail: 'A second, targeted look stops the model reporting details that are not there.',
    source: 'datum verification step',
  },
  {
    workspace: 'Legal', tone: 'critical', tag: 'High risk',
    title: 'Uncapped liability for one party, found in all 3 planted contracts',
    detail: 'Cross-document synthesis across 100 documents, with every claim cited to its source.',
    source: 'legal corpus · synthesis report',
  },
  {
    workspace: 'Legal', tone: 'major', tag: 'Flagged',
    title: 'Text addressed to the AI reviewer detected inside a document',
    detail: 'Hidden instructions are treated as a red flag, never followed, and shown to the reviewer.',
    source: 'prompt-injection guard',
  },
  {
    workspace: 'Medical', tone: 'verify', tag: 'Sourced',
    title: 'Answer drawn from 5 retrieved passages of the uploaded documents',
    detail: 'When the documents do not contain the answer, the assistant says so.',
    source: 'medical workspace',
  },
];

export const techStack = ['OpenAI GPT-4.1', 'LangGraph', 'Pinecone', 'FastAPI', 'PyMuPDF', 'ezdxf', 'Next.js'];

export const faqs = [
  {
    question: 'What kinds of documents can AIDocumentAgent read?',
    answer:
      'PDF files (including scanned pages, which are read by OCR), Word documents, plain text, PNG, JPG and TIFF images, CSV data and DXF CAD drawings.',
  },
  {
    question: 'How does it check an engineering drawing?',
    answer:
      'It renders each sheet, reads the exact text layer or CAD entities, extracts the title block, dimensions, tolerances, GD&T and notes, re-verifies datum symbols on zoomed crops, runs automated rule checks and a cross-view consistency check, then reviews the drawing against an ISO or ASME checklist. Every finding includes a severity, a location and a recommended fix.',
  },
  {
    question: 'Does the AI invent missing information?',
    answer:
      'It is designed not to. When filling documentation templates, facts must come from the source documents; anything missing is left empty and flagged. Drafted analysis is marked as a draft, and any number that does not appear in the sources is flagged for verification.',
  },
  {
    question: 'Can it replace a drawing checker or a lawyer?',
    answer:
      'No. AIDocumentAgent speeds up review and documentation and surfaces issues for a qualified person to confirm. Final approval, legal advice and clinical decisions remain with qualified professionals.',
  },
  {
    question: 'Where is my data stored?',
    answer:
      'Uploaded files and analyses are stored by the application back end you run, and text passages are indexed in your own vector database for search. Documents are sent to the configured AI model provider for analysis.',
  },
];

export const solutions = {
  engineering: {
    slug: 'engineering',
    name: 'Engineering',
    title: 'Engineering drawing review and technical documentation',
    metaTitle: 'Engineering Drawing Review Agent',
    metaDescription:
      'AI agent that checks engineering drawings against ISO and ASME, compares revisions, audits revision control and drafts ECNs, FAI reports and specifications.',
    kicker: 'Drawings · CAD · Change control',
    lede: 'Check drawings before release, compare revisions and produce the documentation that goes with them, with every finding located and every gap flagged.',
    serviceType: 'Engineering drawing review',
    image: { file: engineeringReview, alt: 'Engineering drawing review showing the drawing sheet beside critical and major findings' },
    capabilities: [
      { title: 'Standards-based review', body: 'Checks against ISO 128, 129-1, 1101, 7200 and 2768 or ASME Y14.5, Y14.100 and Y14.35, with a pass/fail checklist.' },
      { title: 'Automated rule checks', body: 'Title-block completeness, revision consistency, unit mixing, tolerance coverage, undefined datums and conflicting dimensions.' },
      { title: 'CAD-aware', body: 'Reads DXF entities directly and flags dimensions whose displayed text has been overridden to hide a geometry mismatch.' },
      { title: 'Cross-view consistency', body: 'A specialist agent compares every extent across views, dimension chains and callouts.' },
      { title: 'Revision comparison', body: 'Lists every change between revisions and audits each one against the new revision-table entries.' },
      { title: 'Documentation templates', body: 'ECN, first article inspection, drawing review record, release note and technical specification. Edit them, review them with AI or import your own.' },
    ],
    outputs: ['Verdict with severity-ranked findings', 'Location and fix for every finding', 'Revision-control audit', 'Filled templates exported to Word or Markdown'],
    limits: 'Model readings can vary between runs, which is why rule checks and targeted re-verification are part of every review. A qualified engineer approves release.',
  },
  legal: {
    slug: 'legal',
    name: 'Legal',
    title: 'Legal document intelligence and cross-document synthesis',
    metaTitle: 'Legal Document Synthesis Agent',
    metaDescription:
      'Classify, extract and risk-assess contracts, court filings, case files and compliance records, then synthesise insights across the whole collection with citations.',
    kicker: 'Contracts · Filings · Compliance',
    lede: 'Turn a folder of contracts, filings and compliance records into structured data, a risk overview and cited answers across the entire collection.',
    serviceType: 'Legal document analysis',
    image: { file: legalSynthesis, alt: 'Legal corpus dashboard with document types, risk categories and upcoming deadlines' },
    capabilities: [
      { title: 'Batch processing', body: 'Upload up to 100 documents per batch. Scanned pages are read by OCR and processing resumes after a restart.' },
      { title: 'Classification', body: 'Contracts, court filings, case files, compliance records and other legal instruments, with subtype and jurisdiction.' },
      { title: 'Structured extraction', body: 'Parties, key dates, obligations, monetary amounts, clauses and type-specific fields such as liability caps and case numbers.' },
      { title: 'Risk analysis', body: 'Categorised risks with section references, recommendations and missing protections for each document.' },
      { title: 'Cross-document synthesis', body: 'A planning agent, parallel document review and a synthesis agent produce a cited report across the collection.' },
      { title: 'Cited Q&A and search', body: 'Ask about one document or the whole corpus, or run semantic search over every passage.' },
    ],
    outputs: ['Corpus dashboard and deadline list', 'Per-document summaries and risk profiles', 'Cited synthesis reports', 'Filterable document register'],
    limits: 'AI-generated analysis supports legal research and review. It is not legal advice.',
  },
  medical: {
    slug: 'medical',
    name: 'Medical',
    title: 'Clinical question answering over your own documents',
    metaTitle: 'Clinical Document Q&A Agent',
    metaDescription:
      'Upload clinical guidelines, literature and CSV datasets and ask questions answered from those documents, with the number of supporting sources shown for every answer.',
    kicker: 'Guidelines · Literature · Datasets',
    lede: 'Ask clinical questions and get answers grounded in the guidelines, papers and datasets you upload, not in the model’s memory.',
    serviceType: 'Clinical document question answering',
    image: { file: medicalChat, alt: 'Medical workspace answering a question with the number of supporting sources' },
    capabilities: [
      { title: 'Grounded answers', body: 'Answers are generated from retrieved passages of your documents, and the assistant says when the context is insufficient.' },
      { title: 'PDF and CSV ingestion', body: 'PDFs are chunked and indexed; CSV rows are converted into searchable records with size estimates before upload.' },
      { title: 'Identifier removal', body: 'Identifier columns are dropped, and emails, phone numbers, record numbers and full dates inside the text are redacted before indexing.' },
      { title: 'Document management', body: 'Replace or delete indexed documents at any time from the documents view.' },
    ],
    outputs: ['Answers with source counts', 'Searchable clinical knowledge base', 'Upload and replacement history'],
    limits: 'Pattern-based identifier removal is not a substitute for a formal de-identification process. Answers support, and do not replace, clinical judgement.',
  },
};

export const solutionList = [solutions.engineering, solutions.legal, solutions.medical];

export const images = {
  engineeringReview: {
    file: engineeringReview,
    alt: 'Drawing review of a mounting bracket: the sheet beside a rejected verdict with critical findings for a 120 vs 125 mm mismatch and an undefined datum',
  },
  engineeringCompare: {
    file: engineeringCompare,
    alt: 'Revision comparison showing the revision was incremented but two changes are missing from the revision table',
  },
  legalSynthesis: { file: legalSynthesis, alt: 'Legal corpus dashboard for 100 documents with document types, risk categories and governing law' },
  medicalChat: { file: medicalChat, alt: 'Medical workspace answering a question about RAG system components from five sources' },
};
