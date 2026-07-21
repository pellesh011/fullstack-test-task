import pytest
import pytest_asyncio

from src.infrastructure.storage.local_file_storage import LocalFileStorage


@pytest_asyncio.fixture
async def storage(tmp_path) -> LocalFileStorage:
    return LocalFileStorage(tmp_path)


class TestSaveStream:
    async def test_save_stream_writes_all_chunks(self, storage: LocalFileStorage):
        async def chunk_generator():
            yield b"hello "
            yield b"world"
            yield b"!"

        path = await storage.save_stream("test.txt", chunk_generator())
        assert path.exists()
        content = await storage.read_bytes("test.txt")
        assert content == b"hello world!"

    async def test_save_stream_single_chunk(self, storage: LocalFileStorage):
        async def chunk_generator():
            yield b"single chunk"

        await storage.save_stream("single.txt", chunk_generator())
        content = await storage.read_bytes("single.txt")
        assert content == b"single chunk"

    async def test_save_stream_empty_generator(self, storage: LocalFileStorage):
        async def empty_generator():
            return
            yield  # make it an async generator

        await storage.save_stream("empty.txt", empty_generator())
        content = await storage.read_bytes("empty.txt")
        assert content == b""

    async def test_save_stream_large_chunks(self, storage: LocalFileStorage):
        chunk_a = b"A" * 10000
        chunk_b = b"B" * 10000

        async def large_generator():
            yield chunk_a
            yield chunk_b

        await storage.save_stream("large.txt", large_generator())
        content = await storage.read_bytes("large.txt")
        assert len(content) == 20000
        assert content == chunk_a + chunk_b


class TestReadBytesStream:
    async def test_read_bytes_stream_full_content(self, storage: LocalFileStorage):
        await storage.save("test.txt", b"hello world")
        chunks = []
        async for chunk in storage.read_bytes_stream("test.txt"):
            chunks.append(chunk)
        assert b"".join(chunks) == b"hello world"

    async def test_read_bytes_stream_chunked(self, storage: LocalFileStorage):
        content = b"A" * 100
        await storage.save("chunked.txt", content)

        chunks = []
        async for chunk in storage.read_bytes_stream("chunked.txt", chunk_size=30):
            chunks.append(chunk)

        # Should have 4 chunks: 30+30+30+10
        assert len(chunks) == 4
        assert b"".join(chunks) == content

    async def test_read_bytes_stream_empty_file(self, storage: LocalFileStorage):
        await storage.save("empty.txt", b"")
        chunks = []
        async for chunk in storage.read_bytes_stream("empty.txt"):
            chunks.append(chunk)
        assert chunks == []

    async def test_read_bytes_stream_single_byte_chunks(
        self, storage: LocalFileStorage
    ):
        await storage.save("abc.txt", b"abc")
        chunks = []
        async for chunk in storage.read_bytes_stream("abc.txt", chunk_size=1):
            chunks.append(chunk)
        assert chunks == [b"a", b"b", b"c"]

    async def test_read_bytes_stream_file_not_found(self, storage: LocalFileStorage):
        with pytest.raises(FileNotFoundError):
            async for _ in storage.read_bytes_stream("nonexistent.txt"):
                pass


class TestReadTextStream:
    async def test_read_text_stream_full_content(self, storage: LocalFileStorage):
        await storage.save("text.txt", b"hello world")
        chunks = []
        async for chunk in storage.read_text_stream("text.txt"):
            chunks.append(chunk)
        assert "".join(chunks) == "hello world"

    async def test_read_text_stream_chunked(self, storage: LocalFileStorage):
        content = "A" * 100
        await storage.save("chunked.txt", content.encode())

        chunks = []
        async for chunk in storage.read_text_stream("chunked.txt", chunk_size=30):
            chunks.append(chunk)

        assert len(chunks) == 4
        assert "".join(chunks) == content

    async def test_read_text_stream_multiline(self, storage: LocalFileStorage):
        content = "line1\nline2\nline3"
        await storage.save("multi.txt", content.encode())

        chunks = []
        async for chunk in storage.read_text_stream("multi.txt"):
            chunks.append(chunk)

        assert "".join(chunks) == content

    async def test_read_text_stream_empty_file(self, storage: LocalFileStorage):
        await storage.save("empty.txt", b"")
        chunks = []
        async for chunk in storage.read_text_stream("empty.txt"):
            chunks.append(chunk)
        assert chunks == []

    async def test_read_text_stream_file_not_found(self, storage: LocalFileStorage):
        with pytest.raises(FileNotFoundError):
            async for _ in storage.read_text_stream("nonexistent.txt"):
                pass


class TestSaveThenReadStream:
    async def test_save_stream_then_read_stream(self, storage: LocalFileStorage):
        original = b"round trip test content"

        async def write_chunks():
            yield original[:10]
            yield original[10:]

        await storage.save_stream("roundtrip.txt", write_chunks())

        read_chunks = []
        async for chunk in storage.read_bytes_stream("roundtrip.txt"):
            read_chunks.append(chunk)

        assert b"".join(read_chunks) == original

    async def test_save_stream_text_then_read_text(self, storage: LocalFileStorage):
        original = "text round trip content"

        async def write_chunks():
            yield original[:10].encode()
            yield original[10:].encode()

        await storage.save_stream("text_roundtrip.txt", write_chunks())

        read_chunks = []
        async for chunk in storage.read_text_stream("text_roundtrip.txt"):
            read_chunks.append(chunk)

        assert "".join(read_chunks) == original
