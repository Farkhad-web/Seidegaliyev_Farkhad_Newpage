def test_list_documents_empty(client):
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_upload_txt_document(client):
    content = b"Tomatoes need at least six hours of direct sunlight per day to fruit well."
    resp = client.post(
        "/api/documents",
        files={"file": ("tomato_care.txt", content, "text/plain")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "tomato_care.txt"
    assert body["status"] == "ready"
    assert body["num_chunks"] >= 1

    listed = client.get("/api/documents").json()
    assert len(listed) == 1
    assert listed[0]["id"] == body["id"]


def test_upload_rejects_unsupported_extension(client):
    resp = client.post(
        "/api/documents",
        files={"file": ("report.docx", b"binary-ish content", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "Unsupported" in resp.json()["detail"]


def test_upload_rejects_empty_file(client):
    resp = client.post(
        "/api/documents",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert resp.status_code == 400


def test_delete_document(client):
    content = b"Some content about soil pH management for row crops."
    upload = client.post(
        "/api/documents",
        files={"file": ("soil.txt", content, "text/plain")},
    ).json()

    resp = client.delete(f"/api/documents/{upload['id']}")
    assert resp.status_code == 204
    assert client.get("/api/documents").json() == []


def test_delete_missing_document_404s(client):
    resp = client.delete("/api/documents/does-not-exist")
    assert resp.status_code == 404


def test_get_document_file_returns_original_bytes(client):
    content = b"Raw bytes served back verbatim for the preview panel."
    upload = client.post(
        "/api/documents",
        files={"file": ("verbatim.txt", content, "text/plain")},
    ).json()

    resp = client.get(f"/api/documents/{upload['id']}/file")
    assert resp.status_code == 200
    assert resp.content == content
    assert resp.headers["content-type"].startswith("text/plain")


def test_get_file_missing_document_404s(client):
    resp = client.get("/api/documents/does-not-exist/file")
    assert resp.status_code == 404


def test_reindex_recomputes_chunks(client):
    content = b"Paragraph one about drainage.\n\nParagraph two about mulching techniques."
    upload = client.post(
        "/api/documents",
        files={"file": ("garden.txt", content, "text/plain")},
    ).json()

    resp = client.post(f"/api/documents/{upload['id']}/reindex")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["num_chunks"] == upload["num_chunks"]


def test_reindex_missing_document_404s(client):
    resp = client.post("/api/documents/does-not-exist/reindex")
    assert resp.status_code == 404
