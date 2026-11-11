from datetime import datetime, timezone

from web.deps import format_date, render_markdown


def test_format_date_shows_turkey_time() -> None:
    assert format_date(datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)) == "11 Kasım 2026, 15:00"
    assert format_date(datetime(2026, 12, 31, 22, 30, tzinfo=timezone.utc)) == "1 Ocak 2027, 01:30"


def test_render_markdown_escapes_html() -> None:
    html = str(render_markdown("**kalın** <script>x</script>\n\nikinci"))

    assert html == "<p><strong>kalın</strong> &lt;script&gt;x&lt;/script&gt;</p><p>ikinci</p>"
