from pathlib import Path

from src.data import acquire_patten_dryad as a


class Response:
    def __init__(self, payload=None, body=b""):
        self._payload = payload
        self.body = body
    def raise_for_status(self):
        return None
    def json(self):
        return self._payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def iter_content(self, chunk_size):
        yield self.body


class Session:
    def __init__(self):
        self.headers = {}
    def get(self, url, **kwargs):
        if url == a.META_URL:
            return Response({
                "_links": {
                    "stash:version": {"href": "/api/v2/versions/123"}
                }
            })
        if url.endswith("/versions/123"):
            return Response({
                "_links": {
                    "stash:files": {"href": "/api/v2/versions/123/files"}
                }
            })
        if url.endswith("/versions/123/files"):
            return Response({
                "_embedded": {
                    "stash:files": [
                        {
                            "path": "point_data.csv",
                            "size": 4,
                            "_links": {
                                "stash:download": {
                                    "href": "/stash/downloads/file_stream/456"
                                }
                            }
                        }
                    ]
                }
            })
        if "file_stream/456" in url:
            return Response(body=b"a,b\n")
        raise AssertionError(url)


def test_resolve_dryad_api():
    _, files = a.resolve(Session())
    assert files == [{
        "name": "point_data.csv",
        "bytes_reported": 4,
        "download_url": "https://datadryad.org/stash/downloads/file_stream/456",
    }]


def test_download(tmp_path, monkeypatch):
    monkeypatch.setattr(a, "RAW", tmp_path)
    monkeypatch.setattr(a, "ROOT", tmp_path.parent)
    item = {
        "name": "point_data.csv",
        "bytes_reported": 4,
        "download_url": "https://datadryad.org/stash/downloads/file_stream/456",
    }
    result = a.download(Session(), item)
    assert (tmp_path / "point_data.csv").read_bytes() == b"a,b\n"
    assert result["bytes"] == 4
    assert len(result["sha256"]) == 64
