from app.rag.ingestion import ingest_document


def _parse_sse(raw_text: str) -> list[dict]:
    events = []
    normalized = raw_text.replace("\r\n", "\n")
    for block in normalized.strip().split("\n\n"):
        if not block.strip():
            continue
        event_type, data_line = None, None
        for line in block.splitlines():
            if line.startswith("event:"):
                event_type = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_line = line.removeprefix("data:").strip()
        if data_line:
            import json

            events.append(json.loads(data_line))
    return events


def test_chat_without_any_documents_short_circuits(client, fake_llm):
    resp = client.post("/api/chat", json={"message": "What is this about?"})
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types = [e["type"] for e in events]
    assert "sources" in types
    sources_event = next(e for e in events if e["type"] == "sources")
    assert sources_event["sources"] == []
    full_answer = "".join(e["text"] for e in events if e["type"] == "delta")
    assert "upload" in full_answer.lower()
    assert types[-1] == "done"


def test_chat_grounded_answer_streams_and_cites_sources(client, session, fake_llm):
    ingest_document(
        session,
        "watering.txt",
        "text/plain",
        b"Water tomato plants deeply twice a week rather than lightly every day.",
    )

    resp = client.post("/api/chat", json={"message": "How often should I water tomatoes?"})
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    sources_event = next(e for e in events if e["type"] == "sources")
    assert len(sources_event["sources"]) > 0

    full_answer = "".join(e["text"] for e in events if e["type"] == "delta")
    assert "grounded answer" in full_answer  # from the FakeAnthropicClient fixture

    done_event = next(e for e in events if e["type"] == "done")
    assert done_event["conversation_id"]
    assert done_event["trace_id"]

    trace = client.get(f"/api/traces/{done_event['trace_id']}").json()
    assert trace["answer"] == full_answer
    assert trace["model"]
    assert trace["latency_ms"]["total_ms"] > 0


def test_chat_rejects_empty_message(client, fake_llm):
    resp = client.post("/api/chat", json={"message": "   "})
    events = _parse_sse(resp.text)
    assert events[0]["type"] == "error"


def test_chat_persists_conversation_history(client, session, fake_llm):
    ingest_document(session, "notes.txt", "text/plain", b"The warehouse closes at 6pm on weekdays.")

    first = client.post("/api/chat", json={"message": "When does the warehouse close?"})
    conv_id = next(e for e in _parse_sse(first.text) if e["type"] == "meta")["conversation_id"]

    second = client.post("/api/chat", json={"message": "And on weekends?", "conversation_id": conv_id})
    assert second.status_code == 200

    messages = client.get(f"/api/conversations/{conv_id}/messages").json()
    assert len(messages) == 4  # 2 user + 2 assistant
    assert messages[0]["role"] == "user"
