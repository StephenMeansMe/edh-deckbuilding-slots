"""Tests for src/deckslots/templates.py"""

import os
from pathlib import Path

from deckslots.templates import Template, _format_template, _get_user_template_dir, _parse_template_content


class TestTemplateDataclass:
    def test_template_can_be_created_with_name_and_categories(self):
        t = Template(name="My Template", categories=[("Ramp", 10), ("Draw", 8)])
        assert t.name == "My Template"
        assert t.categories == [("Ramp", 10), ("Draw", 8)]

    def test_template_builtin_defaults_to_false(self):
        t = Template(name="Foo", categories=[])
        assert t.builtin is False

    def test_template_builtin_can_be_set_true(self):
        t = Template(name="Foo", categories=[], builtin=True)
        assert t.builtin is True


class TestFormatTemplate:
    def test_format_produces_name_header(self):
        t = Template(name="My Template", categories=[("Ramp", 10)])
        text = _format_template(t)
        assert text.startswith("# My Template\n")

    def test_format_includes_category_lines(self):
        t = Template(name="T", categories=[("Ramp", 10), ("Card Draw", 8)])
        text = _format_template(t)
        assert "Ramp [10 slots]\n" in text
        assert "Card Draw [8 slots]\n" in text

    def test_format_empty_categories(self):
        t = Template(name="Empty", categories=[])
        text = _format_template(t)
        assert text.strip() == "# Empty"


class TestParseTemplateContent:
    def test_parse_reads_name_from_header(self):
        text = "# My Template\nRamp [10 slots]\n"
        t = _parse_template_content(text)
        assert t.name == "My Template"

    def test_parse_reads_category_tuples(self):
        text = "# T\nRamp [10 slots]\nCard Draw [8 slots]\n"
        t = _parse_template_content(text)
        assert t.categories == [("Ramp", 10), ("Card Draw", 8)]

    def test_parse_round_trips(self):
        original = Template(
            name="Goodstuff",
            categories=[("Ramp", 10), ("Card Advantage", 12)],
        )
        t = _parse_template_content(_format_template(original))
        assert t.name == original.name
        assert t.categories == original.categories

    def test_parse_raises_on_missing_header(self):
        import pytest

        with pytest.raises(Exception):
            _parse_template_content("Ramp [10 slots]\n")

    def test_parse_ignores_builtin_flag(self):
        text = "# T\nRamp [5 slots]\n"
        t = _parse_template_content(text)
        assert t.builtin is False


class TestGetUserTemplateDir:
    def test_default_path_is_xdg_local_share(self, monkeypatch):
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        result = _get_user_template_dir()
        assert result == Path.home() / ".local" / "share" / "deckslots" / "templates"

    def test_respects_xdg_data_home(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        result = _get_user_template_dir()
        assert result == tmp_path / "deckslots" / "templates"
