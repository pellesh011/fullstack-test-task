from httpx import AsyncClient


class TestListFiles:
    async def test_empty(self, client: AsyncClient):
        response = await client.get("/files")
        assert response.status_code == 200
        assert response.json() == []

    async def test_with_files(self, client: AsyncClient, upload_file: dict):
        response = await client.get("/files")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["title"] == "test file"


class TestCreateFile:
    async def test_create(self, client: AsyncClient):
        content = b"hello world"
        response = await client.post(
            "/files",
            data={"title": "new file"},
            files={"file": ("test.txt", content, "text/plain")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "new file"
        assert data["original_name"] == "test.txt"
        assert data["mime_type"] == "text/plain"
        assert data["size"] == 11
        assert data["status"] == "new"
        assert data["id"] is not None
        assert "created_at" in data
        assert "updated_at" in data

    async def test_mime_type_from_content_not_header(self, client: AsyncClient):
        png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        response = await client.post(
            "/files",
            data={"title": "mime test"},
            files={"file": ("fake.txt", png_header, "text/plain")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["mime_type"] == "image/png"
        assert data["original_mime_type"] == "text/plain"

    async def test_pdf_detected_from_magic_bytes(self, client: AsyncClient):
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
        response = await client.post(
            "/files",
            data={"title": "pdf test"},
            files={"file": ("doc.bin", pdf_content, "application/octet-stream")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["mime_type"] == "application/pdf"

    async def test_empty_file(self, client: AsyncClient):
        response = await client.post(
            "/files",
            data={"title": "empty"},
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    async def test_missing_title(self, client: AsyncClient):
        response = await client.post(
            "/files",
            files={"file": ("f.txt", b"content", "text/plain")},
        )
        assert response.status_code == 422

    async def test_missing_file(self, client: AsyncClient):
        response = await client.post(
            "/files",
            data={"title": "no file"},
        )
        assert response.status_code == 422


class TestGetFile:
    async def test_existing(self, client: AsyncClient, upload_file: dict):
        file_id = upload_file["id"]
        response = await client.get(f"/files/{file_id}")
        assert response.status_code == 200
        assert response.json()["id"] == file_id
        assert response.json()["title"] == "test file"

    async def test_not_found(self, client: AsyncClient):
        response = await client.get("/files/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateFile:
    async def test_update(self, client: AsyncClient, upload_file: dict):
        file_id = upload_file["id"]
        response = await client.patch(
            f"/files/{file_id}", json={"title": "updated title"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "updated title"

    async def test_not_found(self, client: AsyncClient):
        response = await client.patch("/files/nonexistent", json={"title": "new title"})
        assert response.status_code == 404


class TestDownloadFile:
    async def test_download(self, client: AsyncClient, upload_file: dict):
        file_id = upload_file["id"]
        response = await client.get(f"/files/{file_id}/download")
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("text/plain")
        assert response.headers.get("content-disposition") is not None
        assert response.content == b"hello world\nthis is a test file\nline three"

    async def test_not_found(self, client: AsyncClient):
        response = await client.get("/files/nonexistent/download")
        assert response.status_code == 404


class TestDeleteFile:
    async def test_delete(self, client: AsyncClient, upload_file: dict):
        file_id = upload_file["id"]
        response = await client.delete(f"/files/{file_id}")
        assert response.status_code == 204

        response = await client.get(f"/files/{file_id}")
        assert response.status_code == 404

    async def test_not_found(self, client: AsyncClient):
        response = await client.delete("/files/nonexistent")
        assert response.status_code == 404


class TestCORS:
    async def test_cors_allowed_origin(self, client: AsyncClient):
        response = await client.options(
            "/files",
            headers={
                "origin": "http://localhost:3000",
                "access-control-request-method": "GET",
            },
        )
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:3000"
        )

    async def test_cors_blocked_origin(self, client: AsyncClient):
        response = await client.options(
            "/files",
            headers={
                "origin": "http://evil.com",
                "access-control-request-method": "GET",
            },
        )
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert "evil.com" not in allow_origin
