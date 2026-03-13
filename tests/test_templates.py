"""Tests for src/deckslots/templates.py"""

from pathlib import Path

from deckslots.templates import (
    Template,
    _format_template,
    _get_user_template_dir,
    _load_builtin_templates,
    _parse_template_content,
    find_template,
    load_all_templates,
    save_user_template,
    user_template_exists,
)


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


class TestLoadBuiltinTemplates:
    def test_returns_at_least_one_template(self):
        templates = _load_builtin_templates()
        assert len(templates) >= 1

    def test_templates_are_marked_builtin(self):
        templates = _load_builtin_templates()
        assert all(t.builtin for t in templates)

    def test_templates_have_non_empty_name(self):
        templates = _load_builtin_templates()
        assert all(t.name for t in templates)

    def test_goldfish_fundamentals_is_present(self):
        templates = _load_builtin_templates()
        names = [t.name for t in templates]
        assert "Goldfish Fundamentals" in names

    def test_goldfish_fundamentals_has_categories(self):
        templates = _load_builtin_templates()
        gf = next(t for t in templates if t.name == "Goldfish Fundamentals")
        assert len(gf.categories) >= 1


class TestLoadAllTemplates:
    def test_includes_builtins(self):
        templates = load_all_templates()
        assert any(t.builtin for t in templates)

    def test_user_templates_are_included(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        user_dir = tmp_path / "deckslots" / "templates"
        user_dir.mkdir(parents=True)
        (user_dir / "my-template.tmpl").write_text(
            "# My Template\nRamp [10 slots]\n"
        )
        templates = load_all_templates()
        names = [t.name for t in templates]
        assert "My Template" in names

    def test_user_templates_are_not_builtin(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        user_dir = tmp_path / "deckslots" / "templates"
        user_dir.mkdir(parents=True)
        (user_dir / "custom.tmpl").write_text("# Custom\nRamp [5 slots]\n")
        templates = load_all_templates()
        custom = next((t for t in templates if t.name == "Custom"), None)
        assert custom is not None
        assert custom.builtin is False

    def test_returns_sorted_by_name(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "empty"))
        templates = load_all_templates()
        names = [t.name for t in templates]
        assert names == sorted(names)


class TestFindTemplate:
    def test_finds_builtin_by_name(self):
        t = find_template("Goldfish Fundamentals")
        assert t is not None
        assert t.name == "Goldfish Fundamentals"

    def test_returns_none_for_unknown_name(self):
        t = find_template("Nonexistent Template XYZ")
        assert t is None

    def test_finds_user_template(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        user_dir = tmp_path / "deckslots" / "templates"
        user_dir.mkdir(parents=True)
        (user_dir / "custom.tmpl").write_text("# Custom\nRamp [5 slots]\n")
        t = find_template("Custom")
        assert t is not None
        assert t.name == "Custom"


class TestSaveUserTemplate:
    def test_creates_file_in_user_dir(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        t = Template(name="My Template", categories=[("Ramp", 10)])
        save_user_template(t)
        user_dir = tmp_path / "deckslots" / "templates"
        assert (user_dir / "my-template.tmpl").exists()

    def test_file_content_round_trips(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        t = Template(name="Round Trip", categories=[("Ramp", 10), ("Draw", 8)])
        save_user_template(t)
        user_dir = tmp_path / "deckslots" / "templates"
        content = (user_dir / "round-trip.tmpl").read_text()
        parsed = _parse_template_content(content)
        assert parsed.name == "Round Trip"
        assert parsed.categories == [("Ramp", 10), ("Draw", 8)]

    def test_creates_directory_if_missing(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "missing"))
        t = Template(name="New", categories=[("Ramp", 5)])
        save_user_template(t)  # should not raise


class TestUserTemplateExists:
    def test_returns_false_when_absent(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        assert user_template_exists("Nonexistent") is False

    def test_returns_true_after_save(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        t = Template(name="Exists Now", categories=[("Ramp", 5)])
        save_user_template(t)
        assert user_template_exists("Exists Now") is True
