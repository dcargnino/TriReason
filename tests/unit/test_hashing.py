"""Tests for utility functions."""

from trireason.utils.hashing import hash_text


class TestHashText:
    def test_deterministic(self):
        assert hash_text("hello") == hash_text("hello")

    def test_different_inputs(self):
        assert hash_text("a") != hash_text("b")

    def test_sha256_length(self):
        result = hash_text("test")
        assert len(result) == 64  # SHA-256 hex digest is 64 chars

    def test_empty_string(self):
        result = hash_text("")
        assert len(result) == 64
