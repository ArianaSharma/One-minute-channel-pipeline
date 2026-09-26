import pytest


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload


class FakeSession:
    """Stands in for requests.Session; `handler(method, url, kwargs)` returns the payload."""

    def __init__(self, handler):
        self.handler = handler
        self.calls = []

    def request(self, method, url, timeout=None, **kwargs):
        self.calls.append((method, url, kwargs))
        result = self.handler(method, url, kwargs)
        return result if isinstance(result, FakeResponse) else FakeResponse(result)


@pytest.fixture
def fake_session():
    return FakeSession
