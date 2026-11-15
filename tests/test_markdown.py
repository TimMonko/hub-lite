"""README rendering on plugin pages."""

import pytest

from create_static_html_files import md

CODE = 'print("hi") & <b>'


@pytest.mark.parametrize(
    "markdown",
    [
        f"Text\n\n    {CODE}\n",  # indented code block (hub-lite#107)
        f"```python\n{CODE}\n```\n",  # fenced code block
    ],
)
def test_code_is_escaped_once(markdown):
    html = md.render(markdown)
    assert "&amp;quot;" not in html
    assert "&amp;lt;" not in html
    assert "&amp;amp;" not in html
    # The text still reads the same once the browser unescapes it.
    assert '"hi"' in html or "&quot;hi&quot;" in html
