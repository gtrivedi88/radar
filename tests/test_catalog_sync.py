# tests/test_catalog_sync.py
from radar_memory.catalog_sync import (
    Post,
    collect_posts,
    load_post,
    parse_front_matter,
    render_blog_section,
    sync_catalog,
)

POST = """---
title: "The Trust Layer Nobody Built"
subtitle: "A line with: a colon in it"
permalink: /trust-layer-nobody-built/
radar_theme: agent_trust_authorization
faqs:
  - question: "nested keys must be ignored"
    answer: "so the parser does not grab them"
description: "scalar after a block key still parses"
---

Body text here, not front matter: radar_theme should not be read from here.
"""

CATALOG = """# Published Work

> Auto-generated from `_posts/`.

## Blog Posts (sorted by date, most recent first)
- (none yet — paste entries here as YYYY-MM-DD | title | url)

## Courses
- (empty — no courses launched yet)

## Talks & Presentations
- (empty)
"""


def test_parse_front_matter_scalars_and_skips_blocks():
    fm = parse_front_matter(POST)
    assert fm["title"] == "The Trust Layer Nobody Built"
    assert fm["permalink"] == "/trust-layer-nobody-built/"
    assert fm["radar_theme"] == "agent_trust_authorization"
    # block key with nested list has no inline value -> not captured
    assert "faqs" not in fm
    # nested child lines never leak in as top-level keys
    assert "question" not in fm and "answer" not in fm
    # a scalar appearing after the block key still parses
    assert fm["description"] == "scalar after a block key still parses"


def test_parse_front_matter_value_with_colon():
    assert parse_front_matter(POST)["subtitle"] == "A line with: a colon in it"


def test_parse_front_matter_no_block_returns_empty():
    assert parse_front_matter("no front matter here\n") == {}


def test_load_post_date_from_filename_and_theme(tmp_path):
    f = tmp_path / "2026-06-27-the-trust-layer-nobody-built.md"
    f.write_text(POST, encoding="utf-8")
    post = load_post(f)
    assert post.date == "2026-06-27"
    assert post.title == "The Trust Layer Nobody Built"
    assert post.permalink == "/trust-layer-nobody-built/"
    assert post.theme_id == "agent_trust_authorization"


def test_load_post_without_title_is_skipped(tmp_path):
    f = tmp_path / "2026-06-27-draft.md"
    f.write_text("---\npermalink: /x/\n---\nbody\n", encoding="utf-8")
    assert load_post(f) is None


def test_collect_posts_recursive_and_newest_first(tmp_path):
    (tmp_path / "2026" / "6").mkdir(parents=True)
    (tmp_path / "2026" / "5").mkdir(parents=True)
    (tmp_path / "2026" / "6" / "2026-06-27-newer.md").write_text(
        '---\ntitle: "Newer"\npermalink: /newer/\n---\n', encoding="utf-8")
    (tmp_path / "2026" / "5" / "2026-05-01-older.md").write_text(
        '---\ntitle: "Older"\npermalink: /older/\n---\n', encoding="utf-8")
    posts = collect_posts(tmp_path)
    assert [p.title for p in posts] == ["Newer", "Older"]


def test_render_tagged_and_untagged():
    section = render_blog_section([
        Post("2026-06-27", "Tagged", "/tagged/", "agent_trust_authorization"),
        Post("2026-05-01", "Untagged", "/untagged/", ""),
    ])
    assert "- 2026-06-27 | Tagged | /tagged/ (theme: agent_trust_authorization)" in section
    assert "- 2026-05-01 | Untagged | /untagged/" in section
    assert "(theme:" not in section.split("Untagged")[1]  # untagged line carries no token


def test_render_empty_has_placeholder():
    assert "none yet" in render_blog_section([])


def test_sync_replaces_only_blog_section_and_preserves_others():
    posts = [Post("2026-06-27", "The Trust Layer Nobody Built",
                  "/trust-layer-nobody-built/", "agent_trust_authorization")]
    out = sync_catalog(CATALOG, posts)
    # new entry projected, theme token present (so eval can match)
    assert "agent_trust_authorization" in out
    assert "/trust-layer-nobody-built/" in out
    # stale placeholder gone
    assert "none yet" not in out
    # untouched sections survive intact
    assert "## Courses" in out
    assert "## Talks & Presentations" in out
    # header preserved exactly once
    assert out.count("## Blog Posts") == 1


def test_sync_is_idempotent():
    posts = [Post("2026-06-27", "X", "/x/", "t_x")]
    once = sync_catalog(CATALOG, posts)
    assert sync_catalog(once, posts) == once


def test_sync_appends_when_no_section():
    text = "# Published Work\n\nsome notes\n"
    out = sync_catalog(text, [Post("2026-06-27", "X", "/x/", "t_x")])
    assert "## Blog Posts" in out
    assert "some notes" in out
