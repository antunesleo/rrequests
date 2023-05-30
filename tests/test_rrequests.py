import httpretty
from rrequests import get_rrequests
import pytest


@pytest.fixture
def mock_api():
    return "http://mockapi.rrequests"


@pytest.fixture
def mock_success_text():
    return "Success response"


@pytest.fixture
def httppretty_fixture():
    httpretty.enable()
    yield
    httpretty.disable()
    httpretty.reset()


class TestRRequests:
    @pytest.mark.parametrize(
        "http_method", ("GET", "POST", "PUT", "DELETE")
    )
    def test_requests_succeed_for_http_methods(self, http_method, mock_api, mock_success_text, httppretty_fixture):
        httpretty.register_uri(
            http_method,
            mock_api,
            body=mock_success_text,
            content_type="text/plain",
            status=200,
        )

        requests = get_rrequests()
        response = getattr(requests, http_method.lower())(mock_api)
        assert response.text == mock_success_text
        assert response.ok
