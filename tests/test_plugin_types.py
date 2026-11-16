import dataclasses

from create_static_html_files import PluginPageData, get_plugin_types


def plugin(**contributions) -> PluginPageData:
    """A plugin with no contributions except the ones given."""
    fields = {
        field.name: [] if field.type == "list[str]" else ""
        for field in dataclasses.fields(PluginPageData)
        if field.default is dataclasses.MISSING
        and field.default_factory is dataclasses.MISSING
    }
    return PluginPageData(**{**fields, **contributions})


def test_themes_are_a_plugin_type():
    assert get_plugin_types(plugin(contributions_themes=["Nord", "Nord Light"])) == [
        "theme"
    ]


def test_plugin_types_in_order():
    both = plugin(contributions_widgets=["Viewer"], contributions_themes=["Dark"])
    assert get_plugin_types(both) == ["widget", "theme"]


def test_data_fetched_before_themes_still_loads():
    assert plugin().contributions_themes == []
