"""Tests for chat module."""
import os
from unittest.mock import patch
from src.dashboard.chat import ask_groq


def test_ask_groq_no_api_key():
    with patch.dict(os.environ, {}, clear=True):
        result = ask_groq("test question")
        assert result["sql"] == ""
        assert "GROQ_API_KEY" in result["answer"]
