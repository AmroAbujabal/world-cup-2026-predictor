# tests/test_cors.py
"""The CORS allowlist is a trust boundary — every deployed origin in, nothing else."""
import pytest

from backend.main import ALLOWED_ORIGINS


@pytest.mark.parametrize("origin", [
    "http://localhost:5200",
    "https://frontend-nine-alpha-56.vercel.app",
    "https://frontend-git-main-amrabujabal35-2594s-projects.vercel.app",
    "https://worldcup.amrabujabal.com",
])
def test_allowed(origin):
    assert ALLOWED_ORIGINS.match(origin)


@pytest.mark.parametrize("origin", [
    "https://worldcup.amrabujabal.com.evil.test",   # suffix attack
    "https://evil-worldcup.amrabujabal.com",        # sibling subdomain
    "http://worldcup.amrabujabal.com",              # plaintext
    "https://amrabujabal.com",                      # apex is a different site
    "",
])
def test_rejected(origin):
    assert not ALLOWED_ORIGINS.match(origin)
