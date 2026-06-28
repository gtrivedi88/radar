"""Project the blog repo's `_posts/` into catalog.md so the eval grades shipped
predictions without anyone hand-tagging catalog.md.

The contract: a post opts a theme in by adding `radar_theme: <theme_id>` to its
Jekyll front matter. That tag travels with the post (single source of truth);
catalog.md becomes a generated projection, and `radar_memory eval` matches the
emitted `(theme: <theme_id>)` token. No fuzzy title matching, so no false-positive
grades: an untagged post is still listed, just not auto-graded.

stdlib-only, like the rest of the package.
"""

import re
from dataclasses import dataclass
from pathlib import Path

# Jekyll filename convention: YYYY-MM-DD-slug.md
_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
# A top-level "key: value" line in a front-matter block (indented/nested lines skipped).
_FM_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
_BLOG_SECTION_RE = re.compile(r"^## Blog Posts.*?(?=^## |\Z)", re.S | re.M)
_HEADER = "## Blog Posts (sorted by date, most recent first)"


@dataclass
class Post:
    date: str
    title: str
    permalink: str
    theme_id: str  # "" when the post hasn't opted into a Radar theme


def parse_front_matter(text: str) -> dict:
    """Extract top-level scalar keys from a Jekyll `---` front-matter block.

    Block keys (e.g. `faqs:` followed by a nested list) have an empty value and are
    skipped, as are their indented child lines. Good enough for the handful of
    scalars we need (title, permalink, radar_theme) without a YAML dependency.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm: dict = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = _FM_KEY_RE.match(line)  # anchored: indented child lines never match
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
        if val:  # skip block-scalar keys whose value is on following lines
            fm[key] = val
    return fm


def load_post(path: Path) -> Post | None:
    """Build a Post from a markdown file, or None if it has no title."""
    fm = parse_front_matter(path.read_text(encoding="utf-8"))
    title = fm.get("title", "").strip()
    if not title:
        return None
    m = _DATE_RE.search(path.name)
    date = m.group(1) if m else fm.get("date", "")
    return Post(date, title, fm.get("permalink", ""), fm.get("radar_theme", ""))


def collect_posts(blog_dir: Path) -> list[Post]:
    """Load every `*.md` post under blog_dir (recursively), newest first."""
    posts = [p for p in (load_post(f) for f in sorted(blog_dir.rglob("*.md"))) if p]
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def render_blog_section(posts: list[Post]) -> str:
    lines = [_HEADER]
    if not posts:
        lines.append("- (none yet — paste entries here as YYYY-MM-DD | title | url)")
    for p in posts:
        entry = f"- {p.date} | {p.title} | {p.permalink}".rstrip()
        if p.theme_id:
            entry += f" (theme: {p.theme_id})"
        lines.append(entry)
    return "\n".join(lines)


def sync_catalog(catalog_text: str, posts: list[Post]) -> str:
    """Replace the `## Blog Posts` section with one regenerated from posts.

    Every other section of catalog.md is left untouched. If no Blog Posts section
    exists, one is appended.
    """
    new_section = render_blog_section(posts)
    if _BLOG_SECTION_RE.search(catalog_text):
        return _BLOG_SECTION_RE.sub(new_section + "\n\n", catalog_text)
    return catalog_text.rstrip() + "\n\n" + new_section + "\n"
