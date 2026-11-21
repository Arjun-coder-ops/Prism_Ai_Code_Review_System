from app.services.diff import parse_unified_diff


def test_tracks_added_new_side_lines() -> None:
    lines = parse_unified_diff("@@ -1,2 +1,3 @@\n a\n+b\n c", "x.py")
    assert [(line.kind, line.line) for line in lines] == [("context", 1), ("added", 2), ("context", 3)]
