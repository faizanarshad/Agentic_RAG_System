"""Per-user data isolation: members only see and change their own records; administrators see everything."""

import types
import uuid

import pytest

from api import routes_legal
from api.routes_engineering import get_engineering_service
from conftest import ORIGIN, login, make_user
from services.legal_store import LegalStore
from services.platform_store import get_platform_store


@pytest.fixture
def legal_store(monkeypatch):
    """A real legal store behind a stub service, so no OpenAI or Pinecone client is created."""
    store = LegalStore()
    monkeypatch.setattr(routes_legal, "get_legal_service", lambda: types.SimpleNamespace(store=store))
    return store


@pytest.fixture
def two_members():
    alice, bob = make_user("alice-iso@example.com"), make_user("bob-iso@example.com")
    return alice, bob, login("alice-iso@example.com"), login("bob-iso@example.com")


def test_legal_documents_are_private_to_their_owner(legal_store, two_members, admin_client):
    alice, bob, alice_client, bob_client = two_members
    doc_id = str(uuid.uuid4())
    legal_store.create_document(doc_id, "nda.pdf", "/nonexistent", None, owner_id=alice["id"])

    assert alice_client.get(f"/legal/documents/{doc_id}").status_code == 200
    assert bob_client.get(f"/legal/documents/{doc_id}").status_code == 404
    assert bob_client.delete(f"/legal/documents/{doc_id}", headers=ORIGIN).status_code == 404
    assert bob_client.post(f"/legal/documents/{doc_id}/retry", headers=ORIGIN).status_code == 404
    assert bob_client.post("/legal/ask", json={"question": "x", "file_id": doc_id}, headers=ORIGIN).status_code == 404

    alice_ids = [d["id"] for d in alice_client.get("/legal/documents").json()["documents"]]
    bob_ids = [d["id"] for d in bob_client.get("/legal/documents").json()["documents"]]
    assert doc_id in alice_ids and doc_id not in bob_ids
    assert admin_client.get(f"/legal/documents/{doc_id}").status_code == 200


def test_legal_batches_are_private(legal_store, two_members):
    alice, bob, alice_client, bob_client = two_members
    batch_id = str(uuid.uuid4())
    legal_store.create_batch(batch_id, 1, owner_id=alice["id"])
    assert alice_client.get(f"/legal/batches/{batch_id}").status_code == 200
    assert bob_client.get(f"/legal/batches/{batch_id}").status_code == 404
    latest = bob_client.get("/legal/batches/latest").json()["batch"]
    assert latest is None or latest["id"] != batch_id


def test_legal_vector_filter_includes_owner():
    from services.legal_agent_service import LegalAgentService
    assert LegalAgentService._corpus_filter(None, None, "u1")["owner_id"] == {"$eq": "u1"}
    assert "owner_id" not in LegalAgentService._corpus_filter(None, None, None)


def test_engineering_records_are_private(two_members, admin_client):
    alice, bob, alice_client, bob_client = two_members
    store = get_engineering_service().store
    drawing_id = str(uuid.uuid4())
    store.create_drawing(drawing_id, "part.pdf", "/nonexistent", "ISO", owner_id=alice["id"])
    document_id = store.create_document({"title": "Report", "sections": []}, owner_id=alice["id"])

    assert bob_client.get(f"/engineering/drawings/{drawing_id}").status_code == 404
    assert bob_client.get(f"/engineering/drawings/{drawing_id}/pages/1").status_code == 404
    assert bob_client.delete(f"/engineering/drawings/{drawing_id}", headers=ORIGIN).status_code == 404
    assert bob_client.get(f"/engineering/documents/{document_id}").status_code == 404
    assert bob_client.get(f"/engineering/documents/{document_id}/export").status_code == 404
    compare = {"a_id": drawing_id, "b_id": str(uuid.uuid4())}
    assert bob_client.post("/engineering/compare", json=compare, headers=ORIGIN).status_code == 404
    generate = {"template_id": "x", "drawing_ids": [drawing_id]}
    assert bob_client.post("/engineering/documents/generate", json=generate, headers=ORIGIN).status_code == 404

    assert drawing_id not in [d["id"] for d in bob_client.get("/engineering/drawings").json()["drawings"]]
    assert drawing_id in [d["id"] for d in alice_client.get("/engineering/drawings").json()["drawings"]]
    assert admin_client.get(f"/engineering/documents/{document_id}").status_code == 200


def test_templates_are_shared_but_only_their_creator_can_change_them(two_members):
    alice, bob, alice_client, bob_client = two_members
    template = {"name": f"Alice template {uuid.uuid4().hex[:6]}", "sections": [{"title": "Scope", "fields": []}]}
    created = alice_client.post("/engineering/templates", json=template, headers=ORIGIN).json()

    assert created["id"] in [t["id"] for t in bob_client.get("/engineering/templates").json()["templates"]]
    assert bob_client.delete(f"/engineering/templates/{created['id']}", headers=ORIGIN).status_code == 403
    edited = bob_client.put(f"/engineering/templates/{created['id']}", json=template, headers=ORIGIN).json()
    assert edited["id"] != created["id"]  # Bob's edit became his own copy
    assert alice_client.delete(f"/engineering/templates/{created['id']}", headers=ORIGIN).status_code == 200


def test_medical_files_can_only_be_changed_by_their_owner(two_members):
    alice, bob, alice_client, bob_client = two_members
    file_id = str(uuid.uuid4())
    get_platform_store().record_medical_file(file_id, alice["id"], "notes.pdf")
    assert bob_client.delete(f"/files/delete_file/{file_id}", headers=ORIGIN).status_code == 404
    assert bob_client.delete(f"/files/delete_file/{uuid.uuid4()}", headers=ORIGIN).status_code == 404


def test_medical_chat_retrieval_is_filtered_by_owner():
    from services.rag_service import RAGService
    captured = {}
    service = RAGService.__new__(RAGService)
    service.embeddings = types.SimpleNamespace(generate_embedding=lambda q: [0.0])
    service.vectordb = types.SimpleNamespace(
        search_similar=lambda embedding, metadata_filter=None: captured.setdefault("filter", metadata_filter) and []
    )
    service.llm = None
    service.graph = service._build_graph()
    service.process_query("question", owner_id="u1")
    assert captured["filter"] == {"owner_id": {"$eq": "u1"}}
