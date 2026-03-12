"""Tests for src/deckslots/templates.py"""

from deckslots.templates import Template


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
