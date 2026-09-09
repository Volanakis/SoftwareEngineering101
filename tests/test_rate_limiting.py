"""ΜΛΑ-3.3: rate limiting on the search and submission endpoints.

The limiter is active in the testing config; conftest's autouse
`_reset_rate_limiter` fixture clears its storage before each test.
"""

import pytest


def _exhaust(client, method, path, allowed, **kwargs):
    """Call `path` `allowed` times (all accepted), then once more; return the
    status code of that final, over-limit call."""
    call = getattr(client, method)
    for _ in range(allowed):
        response = call(path, **kwargs)
        assert response.status_code != 429
    return call(path, **kwargs).status_code


@pytest.mark.usefixtures("db")
def test_program_search_is_rate_limited(client):
    assert _exhaust(client, "get", "/programs", allowed=30) == 429


@pytest.mark.usefixtures("db")
def test_screening_search_is_rate_limited(client):
    path = "/programs/does-not-matter/screenings"
    assert _exhaust(client, "get", path, allowed=30) == 429


@pytest.mark.usefixtures("db")
def test_screening_submit_is_rate_limited(client):
    path = "/programs/p/screenings/s/submit"
    assert _exhaust(client, "post", path, allowed=10) == 429


@pytest.mark.usefixtures("db")
def test_screening_final_submit_is_rate_limited(client):
    path = "/programs/p/screenings/s/final-submit"
    assert _exhaust(client, "post", path, allowed=10) == 429


@pytest.mark.usefixtures("db")
def test_non_throttled_endpoint_is_not_rate_limited(client):
    # program creation has no @limiter.limit — 40 unauthenticated calls, all 401,
    # none throttled.
    for _ in range(40):
        assert client.post("/programs", json={}).status_code == 401
