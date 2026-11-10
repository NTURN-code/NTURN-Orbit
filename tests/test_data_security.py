import pytest

from core.data_sources import validate_public_url


def test_rejects_localhost():
    with pytest.raises(ValueError, match="Local/private"):
        validate_public_url("http://localhost:8501/data")


def test_rejects_private_ip_literal():
    with pytest.raises(ValueError, match="public IP"):
        validate_public_url("http://192.168.1.10/data")


def test_rejects_non_http_scheme():
    with pytest.raises(ValueError, match="http://"):
        validate_public_url("file:///etc/passwd")


def test_rejects_url_userinfo():
    with pytest.raises(ValueError, match="usernames or passwords"):
        validate_public_url("https://user:pass@example.com/data")


def test_rejects_hostname_resolving_to_private_ip(monkeypatch):
    import socket

    def fake_getaddrinfo(*args, **kwargs):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("10.0.0.5", 443),
            )
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(ValueError, match="public IP"):
        validate_public_url("https://example.test/data")
