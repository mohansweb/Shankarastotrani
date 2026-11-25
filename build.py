#!/usr/bin/env python3
"""
Static site generator for Shankarastotrani (Philosophical Hymns of Adi Shankara).
Reads Blogger Takeout feed.atom + local images/audio and outputs a clean,
responsive, accessible, SEO-ready static site for GitHub Pages.
"""

import html
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "_raw_import"
ASSETS_IMG_DIR = BASE_DIR / "assets" / "images"
ASSETS_AUD_DIR = BASE_DIR / "assets" / "audio"
HYMNS_DIR = BASE_DIR / "hymns"

SITE_URL = "https://mohansweb.github.io/Shankarastotrani"
SITE_TITLE = "Shankarastotrani"
SITE_SUBTITLE = "Philosophical Hymns of Adi Shankara"
GA_ID = "G-BNQN7Q0P3D"

# Explicit mapping from Blogger title prefix -> metadata
POST_META = [
    {
        "match": "About Adi Shankara's Philosophical Hymns",
        "slug": "about-adi-shankaras-philosophical-hymns",
        "title": "About Adi Shankara's Philosophical Hymns",
        "subtitle": "An introduction to the hymns, their structure, Devanagari text, IAST transliteration, anvaya, and metre",
        "category": "Introduction",
        "image": "Adi Shankara.jpeg",
        "audio": None,
        "order": 0,
    },
    {
        "match": "Nirvana Shatkam",
        "slug": "nirvana-shatkam",
        "title": "Nirvana Shatkam",
        "subtitle": "Six Verses on Liberation (Atma Shatkam)",
        "category": "Panchakams & Ashtakams",
        "image": "Nirvana Shatkam.jpg",
        "audio": "Nirvana Shatkam.mp3",
        "order": 1,
    },
    {
        "match": "Advaita Pancharatnam",
        "slug": "advaita-pancharatnam",
        "title": "Advaita Pancharatnam",
        "subtitle": "Five Gems of Non-Duality (Atma Panchakam)",
        "category": "Panchakams & Ashtakams",
        "image": "Advaita Pancharatnam.jpg",
        "audio": "Advaita Pancharathan Chanting.mp3",
        "order": 2,
    },
    {
        "match": "Upadesha Panchakam",
        "slug": "upadesha-panchakam",
        "title": "Upadesha Panchakam",
        "subtitle": "Counsel in Five Verses (Sadhana Panchakam)",
        "category": "Panchakams & Ashtakams",
        "image": "Upadesha Panchakam.jpg",
        "audio": "Upadeshapanchakam.mp3",
        "order": 3,
    },
    {
        "match": "Manisha Panchakam",
        "slug": "manisha-panchakam",
        "title": "Manisha Panchakam",
        "subtitle": "Five Verses of Considered Opinion",
        "category": "Panchakams & Ashtakams",
        "image": "Manisha Panchakam.jpg",
        "audio": None,
        "order": 4,
    },
    {
        "match": "Maya Panchakam",
        "slug": "maya-panchakam",
        "title": "Maya Panchakam",
        "subtitle": "Five Verses on Apparitional Power",
        "category": "Panchakams & Ashtakams",
        "image": "Maya Panchakam.jpg",
        "audio": None,
        "order": 5,
    },
    {
        "match": "Yati Panchakam",
        "slug": "yati-panchakam",
        "title": "Yati Panchakam",
        "subtitle": "Five Verses on Ascetics (Kaupina Panchakam)",
        "category": "Panchakams & Ashtakams",
        "image": "Yati Panchakam.jpg",
        "audio": None,
        "order": 6,
    },
    {
        "match": "Dhanyashtakam",
        "slug": "dhanyashtakam",
        "title": "Dhanyashtakam",
        "subtitle": "Eight Verses on the Fortunate",
        "category": "Panchakams & Ashtakams",
        "image": "Dhanytashtakam.jpg",
        "audio": "Dhanyashtakam.mp3",
        "order": 7,
    },
    {
        "match": "Eka Sloka Prakaranam",
        "slug": "eka-shloka-prakaranam",
        "title": "Eka Shloka Prakaranam",
        "subtitle": "A Treatise in One Verse",
        "category": "Prakarana Granthas",
        "image": "Eka Shloka Prakaranam.jpg",
        "audio": "Eka Shloka Prakaranam.mp3",
        "order": 8,
    },
    {
        "match": "Dasha Shloki",
        "slug": "dasha-shloki",
        "title": "Dasha Shloki",
        "subtitle": "A Hymn of Ten Verses",
        "category": "Prakarana Granthas",
        "image": "Dasha Shloki.jpg",
        "audio": "Dasha Shloki.mp3",
        "order": 9,
    },
    {
        "match": "Advaita Anubhuti",
        "slug": "advaita-anubhuti",
        "title": "Advaita Anubhuti",
        "subtitle": "Experience of Non-Duality",
        "category": "Prakarana Granthas",
        "image": "Advaita Anubhuti.jpg",
        "audio": "Advaita Anubhitih.mp3",
        "order": 10,
    },
    {
        "match": "Praudha Anubhuti",
        "slug": "praudha-anubhuti",
        "title": "Praudha Anubhuti",
        "subtitle": "The Profound Experience",
        "category": "Prakarana Granthas",
        "image": "Praudha Anubhuti.jpg",
        "audio": "Praudha Anubhuti.mp3",
        "order": 11,
    },
    {
        "match": "Anatma Shri Vigarhanam",
        "slug": "anatma-shri-vigarhanam",
        "title": "Anatma Shri Vigarhanam",
        "subtitle": "The Condemnation of False Glory",
        "category": "Prakarana Granthas",
        "image": "Anatma Shri Vigarhanam.jpg",
        "audio": "Anatmashrivigarhanam.mp3",
        "order": 12,
    },
    {
        "match": "Brahma Jnanavali Mala",
        "slug": "brahma-jnanavali-mala",
        "title": "Brahma Jnanavali Mala",
        "subtitle": "Garland of Self-Knowledge",
        "category": "Prakarana Granthas",
        "image": "Brahma Jnanavali Mala.jpg",
        "audio": "Brahma Jnanavali Mala.mp3",
        "order": 13,
    },
    {
        "match": "Brahmanuchintanam",
        "slug": "brahmanuchintanam",
        "title": "Brahmanuchintanam",
        "subtitle": "Meditation on Brahman",
        "category": "Prakarana Granthas",
        "image": "Brahmanuchintanam.jpg",
        "audio": None,
        "order": 14,
    },
    {
        "match": "Tattvopadesha",
        "slug": "tattvopadesha",
        "title": "Tattvopadesha",
        "subtitle": "Pointers Towards Truth",
        "category": "Prakarana Granthas",
        "image": "Tattvopadesha.jpg",
        "audio": "Tattva Upadesha.mp3",
        "order": 15,
    },
    {
        "match": "Nirvana Manjari",
        "slug": "nirvana-manjari",
        "title": "Nirvana Manjari",
        "subtitle": "Blossom of Liberation",
        "category": "Prakarana Granthas",
        "image": "Nirvana Manjari.jpg",
        "audio": "Nirvana Manjari.mp3",
        "order": 16,
    },
    {
        "match": "Jivanmukta Ananda Lahari",
        "slug": "jivanmukta-ananda-lahari",
        "title": "Jivanmukta Ananda Lahari",
        "subtitle": "The Bliss-Waves of the Living-Liberated",
        "category": "Prakarana Granthas",
        "image": "Jeevanmuktha Ananda Lahari.jpg",
        "audio": "Jivan Muktananda Lahari .mp3",
        "order": 17,
    },
    {
        "match": "Prashnottara Ratna Malika",
        "slug": "prashnottara-ratna-malika",
        "title": "Prashnottara Ratna Malika",
        "subtitle": "Necklace of Questions and Answers",
        "category": "Prakarana Granthas",
        "image": "Prashnottara Ratna Malika.jpg",
        "audio": "Prashnottara Ratna Malika.mp3",
        "order": 18,
    },
    {
        "match": "Laghu Vakya Vritti",
        "slug": "laghu-vakya-vritti",
        "title": "Laghu Vakya Vritti",
        "subtitle": "A Brief Exposition of the Great Statement",
        "category": "Prakarana Granthas",
        "image": "Laghu Vakya Vritti.jpg",
        "audio": None,
        "order": 19,
    },
    {
        "match": "Yoga Taravali",
        "slug": "yoga-taravali",
        "title": "Yoga Taravali",
        "subtitle": "An Array of the Stars of Yoga",
        "category": "Prakarana Granthas",
        "image": "Yoga Taravali.jpg",
        "audio": None,
        "order": 20,
    },
]

VOID_TAGS = {"br", "hr", "img", "input", "meta", "link", "source"}
SKIP_TAGS = {"script", "style", "head", "title", "meta", "link", "audio", "source", "img", "object", "embed"}
ALLOWED_TAGS = {
    "p", "br", "hr", "b", "strong", "i", "em", "u", "sup", "sub",
    "h1", "h2", "h3", "h4", "ul", "ol", "li", "table", "thead", "tbody",
    "tr", "th", "td", "a", "span", "blockquote"
}

DEVA_RE = re.compile(r"([\u0900-\u097F\u1CD0-\u1CFF\uA8E0-\uA8FF]+(?:[\s।॥०-९\-–—]*[\u0900-\u097F\u1CD0-\u1CFF\uA8E0-\uA8FF।॥०-९]+)*)")


class WordHTMLCleaner(HTMLParser):
    """Cleans MS Word-exported Blogger HTML into semantic, accessible HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self.in_body = False
        self.has_body_tag = False
        self.tag_stack = []
        self.in_deva_span = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attr_dict = dict(attrs)

        if tag == "body":
            self.has_body_tag = True
            self.in_body = True
            return

        if self.has_body_tag and not self.in_body:
            return

        if tag in SKIP_TAGS:
            if tag not in VOID_TAGS:
                self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        # Drop MS Word Symbol bullet spans
        style = attr_dict.get("style", "")
        if tag == "span" and "font-family:Symbol" in style.replace(" ", "").replace("'", "").replace('"', ""):
            self.skip_depth += 1
            return

        if tag not in ALLOWED_TAGS:
            self.tag_stack.append((tag, False))
            return

        # Handle <a name="SectionX"> -> semantic <h2 id="section-x">
        if tag == "a":
            name = attr_dict.get("name", "") or attr_dict.get("id", "")
            href = attr_dict.get("href", "")
            if name and re.match(r"^Section\d+$", name, re.I):
                sec_id = name.lower().replace("section", "section-")
                self.out.append(f'<h2 id="{sec_id}">')
                self.tag_stack.append(("h2_from_a", True))
                return
            if href:
                safe_href = html.escape(href, quote=True)
                self.out.append(f'<a href="{safe_href}">')
                self.tag_stack.append(("a", True))
                return
            self.tag_stack.append(("a", False))
            return

        if tag == "table":
            self.out.append('<div class="table-wrap"><table>')
            self.tag_stack.append(("table", True))
            return

        if tag == "span":
            # Preserve IAST / Sanskrit term red highlight with high-contrast class
            if "#C00000" in style.upper() or "MAROON" in style.upper():
                if "background" not in style.lower():
                    self.out.append('<span class="sa-iast" lang="sa-Latn">')
                    self.tag_stack.append(("span", True))
                    return
            self.tag_stack.append(("span", False))
            return

        if tag in ("td", "th"):
            attrs_out = []
            for k in ("colspan", "rowspan"):
                if k in attr_dict and attr_dict[k].isdigit():
                    attrs_out.append(f'{k}="{attr_dict[k]}"')
            attr_str = (" " + " ".join(attrs_out)) if attrs_out else ""
            self.out.append(f"<{tag}{attr_str}>")
            self.tag_stack.append((tag, True))
            return

        if tag in VOID_TAGS:
            self.out.append(f"<{tag}>")
            return

        self.out.append(f"<{tag}>")
        self.tag_stack.append((tag, True))

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "body":
            self.in_body = False
            return
        if self.has_body_tag and not self.in_body:
            return
        if tag in SKIP_TAGS:
            if tag not in VOID_TAGS and self.skip_depth > 0:
                self.skip_depth -= 1
            return
        if self.skip_depth > 0:
            if tag == "span":
                self.skip_depth -= 1
            return

        if not self.tag_stack:
            return

        orig_tag, emitted = self.tag_stack.pop()
        if not emitted:
            return
        if orig_tag == "h2_from_a":
            self.out.append("</h2>")
        elif orig_tag == "table":
            self.out.append("</table></div>")
        else:
            self.out.append(f"</{orig_tag}>")

    def handle_data(self, data):
        if self.has_body_tag and not self.in_body:
            return
        if self.skip_depth > 0:
            return
        # Normalize non-breaking spaces and excessive whitespace
        text = data.replace("\xa0", " ")
        escaped = html.escape(text, quote=False)
        # Wrap Devanagari runs in <span lang="sa" class="sa-deva">
        escaped = DEVA_RE.sub(r'<span lang="sa" class="sa-deva">\1</span>', escaped)
        self.out.append(escaped)


def clean_post_html(raw_html: str, has_audio: bool) -> tuple[str, list[tuple[str, str]], str]:
    """Clean raw Blogger/Word HTML and return (cleaned_html, sections, plain_text)."""
    cleaner = WordHTMLCleaner()
    cleaner.feed(raw_html)
    cleaner.close()
    cleaned = "".join(cleaner.out)

    # Remove old Word jump-menu paragraphs at top
    cleaned = re.sub(
        r"<p[^>]*>\s*(?:<b>)?\s*Click below to jump to.*?</p>",
        "",
        cleaned,
        flags=re.I | re.S,
    )
    cleaned = re.sub(
        r'<p[^>]*>\s*(?:<a href="#Section\d+"[^>]*>.*?</a>\s*[|]?\s*)+</p>',
        "",
        cleaned,
        flags=re.I | re.S,
    )

    # Remove empty paragraphs and redundant <br> spacers
    cleaned = re.sub(r"<p>\s*(?:&nbsp;|\s|<br>)*\s*</p>", "", cleaned, flags=re.I)
    cleaned = re.sub(r"<h[1-6][^>]*>\s*</h[1-6]>", "", cleaned, flags=re.I)

    # Unwrap <p><h2 ...>...</h2></p> -> <h2 ...>...</h2>
    cleaned = re.sub(r"<p>\s*(<h2 id=\"section-\d+\">.*?</h2>)\s*</p>", r"\1", cleaned, flags=re.I | re.S)

    # Strip redundant <b> inside <h2>
    cleaned = re.sub(r"(<h2[^>]*>)\s*<b>(.*?)</b>\s*(</h2>)", r"\1\2\3", cleaned, flags=re.I | re.S)

    # If post has no audio, remove any orphaned Section 4 ("Chanting") heading
    if not has_audio:
        cleaned = re.sub(r'<h2 id="section-4">.*?</h2>', "", cleaned, flags=re.I | re.S)

    # Extract actual headings for jump nav
    sections = []
    for sec_id, sec_title in re.findall(r'<h2 id="(section-\d+)">(.*?)</h2>', cleaned, flags=re.I | re.S):
        clean_title = re.sub(r"<[^>]+>", "", sec_title).strip()
        if clean_title:
            sections.append((sec_id, clean_title))

    # Plain text for search index & reading time
    plain = re.sub(r"<[^>]+>", " ", cleaned)
    plain = html.unescape(plain)
    plain = re.sub(r"\s+", " ", plain).strip()

    return cleaned, sections, plain


def slugify_filename(name: str) -> str:
    stem, ext = os.path.splitext(name)
    safe = re.sub(r"[^a-zA-Z0-9]+", "-", stem).strip("-").lower()
    return f"{safe}{ext.lower()}"


def head_html(title: str, description: str, canonical_path: str, prefix: str = "", og_image: str = "") -> str:
    full_title = f"{title} | {SITE_TITLE}" if title != SITE_TITLE else f"{SITE_TITLE} — {SITE_SUBTITLE}"
    canonical = f"{SITE_URL}/{canonical_path}".rstrip("/") + ("/" if canonical_path == "" else "")
    og_img_tag = f'<meta property="og:image" content="{SITE_URL}/{og_image}">' if og_image else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(full_title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{html.escape(full_title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:url" content="{canonical}">
  {og_img_tag}
  <link rel="icon" href="{prefix}favicon.ico" type="image/x-icon">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+Devanagari:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}assets/css/style.css">
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{GA_ID}');
  </script>
</head>"""


def header_html(prefix: str = "", active: str = "") -> str:
    home_cur = ' aria-current="page"' if active == "home" else ""
    toc_cur = ' aria-current="page"' if active == "toc" else ""
    about_cur = ' aria-current="page"' if active == "about" else ""
    return f"""  <a class="skip-link" href="#main-content">Skip to main content</a>
  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="{prefix}index.html">
        <img class="brand-mark" src="{prefix}assets/images/adi-shankara.jpeg" alt="Adi Shankaracharya portrait">
        <span class="brand-text">
          <span class="brand-title">{SITE_TITLE}</span>
          <span class="brand-sub">{SITE_SUBTITLE}</span>
        </span>
      </a>
      <div class="nav-wrap">
        <nav class="main-nav" id="main-nav" aria-label="Main navigation">
          <a href="{prefix}index.html"{home_cur}>Hymns</a>
          <a href="{prefix}toc.html"{toc_cur}>Complete Index</a>
          <a href="{prefix}hymns/about-adi-shankaras-philosophical-hymns.html"{about_cur}>About</a>
        </nav>
        <button type="button" class="icon-btn" id="theme-toggle" aria-pressed="false" aria-label="Toggle color theme">Dark Mode</button>
        <button type="button" class="icon-btn menu-toggle" id="menu-toggle" aria-expanded="false" aria-controls="main-nav" aria-label="Toggle navigation menu">Menu</button>
      </div>
    </div>
  </header>"""


def footer_html(prefix: str = "") -> str:
    return f"""  <footer class="site-footer">
    <div class="container footer-inner">
      <div>
        <strong>{SITE_TITLE}</strong> &mdash; {SITE_SUBTITLE}. Freely available for genuine seekers of Advaita Vedanta.
      </div>
      <div>
        <a href="{prefix}toc.html">Complete Index</a> &middot;
        <a href="{prefix}sitemap.xml">Sitemap</a>
      </div>
    </div>
  </footer>
  <button type="button" class="back-to-top" id="back-to-top" aria-label="Back to top">&#8593;</button>
  <script src="{prefix}assets/js/main.js"></script>
</body>
</html>"""


def main():
    ASSETS_IMG_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_AUD_DIR.mkdir(parents=True, exist_ok=True)
    HYMNS_DIR.mkdir(parents=True, exist_ok=True)

    # Copy favicon
    fav_src = RAW_DIR / "favicon.ico"
    if fav_src.exists():
        shutil.copy2(fav_src, BASE_DIR / "favicon.ico")

    # Copy all images with clean filenames
    img_map = {}
    for src in (RAW_DIR / "images").iterdir():
        if src.is_file():
            clean_name = slugify_filename(src.name)
            shutil.copy2(src, ASSETS_IMG_DIR / clean_name)
            img_map[src.name] = clean_name

    # Copy all audio files with clean filenames
    aud_map = {}
    for src in (RAW_DIR / "audio").iterdir():
        if src.is_file():
            clean_name = slugify_filename(src.name)
            shutil.copy2(src, ASSETS_AUD_DIR / clean_name)
            aud_map[src.name] = clean_name

    # Parse Blogger feed.atom
    tree = ET.parse(RAW_DIR / "feed.atom")
    root = tree.getroot()
    ns = {"atom": "http://www.w3.org/2005/Atom", "blogger": "http://schemas.google.com/blogger/2018"}

    articles = []
    for entry in root.findall("atom:entry", ns):
        etype = entry.find("blogger:type", ns)
        estatus = entry.find("blogger:status", ns)
        if etype is not None and etype.text != "POST":
            continue
        if estatus is not None and estatus.text != "LIVE":
            continue

        raw_title = (entry.find("atom:title", ns).text or "").strip()
        raw_content = entry.find("atom:content", ns).text or ""
        updated = (entry.find("atom:updated", ns).text or "")[:10]

        meta = None
        for m in POST_META:
            if m["match"].lower() in raw_title.lower():
                meta = m
                break
        if not meta:
            print(f"WARNING: Unmatched post title: {raw_title}")
            continue

        has_audio = meta["audio"] is not None
        cleaned_html, sections, plain_text = clean_post_html(raw_content, has_audio)
        word_count = len(plain_text.split())
        read_mins = max(1, round(word_count / 200))

        img_file = img_map.get(meta["image"], "blog-header.jpeg")
        aud_file = aud_map.get(meta["audio"]) if meta["audio"] else None

        desc = (
            f"{meta['title']} ({meta['subtitle']}) by Adi Shankaracharya — "
            f"Sanskrit Devanagari text, IAST transliteration, word-for-word meaning, commentary"
            f"{', and MP3 chanting' if aud_file else ''}."
        )

        articles.append({
            **meta,
            "img_file": img_file,
            "aud_file": aud_file,
            "cleaned_html": cleaned_html,
            "sections": sections,
            "plain_text": plain_text,
            "read_mins": read_mins,
            "updated": updated or datetime.now().strftime("%Y-%m-%d"),
            "description": desc[:160],
        })

    articles.sort(key=lambda x: x["order"])

    # 1. Generate individual hymn pages
    for idx, art in enumerate(articles):
        prev_art = articles[idx - 1] if idx > 0 else None
        next_art = articles[idx + 1] if idx < len(articles) - 1 else None

        audio_block = ""
        if art["aud_file"]:
            audio_block = f"""
      <section class="audio-card" aria-label="Chanting audio player">
        <div class="audio-card-head">
          <span class="audio-card-title">Chanting Audio (MP3)</span>
          <a class="audio-download" href="../assets/audio/{art['aud_file']}" download>Download MP3</a>
        </div>
        <audio controls preload="metadata">
          <source src="../assets/audio/{art['aud_file']}" type="audio/mpeg">
          Your browser does not support the audio element.
        </audio>
      </section>"""

        jump_block = ""
        if art["sections"]:
            links = "".join(f'<li><a href="#{sid}">{html.escape(stitle)}</a></li>' for sid, stitle in art["sections"])
            jump_block = f"""
      <nav class="jump-nav" aria-label="Article sections">
        <p class="jump-nav-title">In This Article</p>
        <ul>{links}</ul>
      </nav>"""

        audio_badge = '<span class="badge badge--audio">MP3 Audio</span>' if art["aud_file"] else ""

        prev_html = (
            f'<a href="{prev_art["slug"]}.html"><span class="post-nav-label">&larr; Previous</span><span class="post-nav-title">{html.escape(prev_art["title"])}</span></a>'
            if prev_art else "<span></span>"
        )
        next_html = (
            f'<a class="post-nav-next" href="{next_art["slug"]}.html"><span class="post-nav-label">Next &rarr;</span><span class="post-nav-title">{html.escape(next_art["title"])}</span></a>'
            if next_art else "<span></span>"
        )

        # Append an accessible chanting section at #section-4 if audio exists and cleaned_html has #section-4
        body_html = art["cleaned_html"]
        if art["aud_file"] and 'id="section-4"' in body_html:
            body_html = re.sub(
                r'(<h2 id="section-4">.*?</h2>)',
                rf'\1\n<p>Listen to the traditional chanting below or <a href="../assets/audio/{art["aud_file"]}" download>download the MP3</a>.</p>'
                rf'\n<p><audio controls preload="metadata" style="width:100%"><source src="../assets/audio/{art["aud_file"]}" type="audio/mpeg"></audio></p>',
                body_html,
                count=1,
                flags=re.I | re.S,
            )

        page_html = f"""{head_html(art["title"], art["description"], f"hymns/{art['slug']}.html", prefix="../", og_image=f"assets/images/{art['img_file']}")}
<body>
{header_html(prefix="../", active="about" if art["slug"] == "about-adi-shankaras-philosophical-hymns" else "")}
  <main id="main-content" class="container container--narrow">
    <article>
      <header class="article-header">
        <nav class="breadcrumb" aria-label="Breadcrumb">
          <a href="../index.html">Home</a> / <a href="../toc.html">Index</a> / <span>{html.escape(art["title"])}</span>
        </nav>
        <div class="card-meta">
          <span class="badge">{html.escape(art["category"])}</span>
          {audio_badge}
          <span class="badge">{art["read_mins"]} min read</span>
        </div>
        <h1 class="article-title">{html.escape(art["title"])}</h1>
        <p class="article-subtitle">{html.escape(art["subtitle"])}</p>
        <div class="reader-controls">
          <div class="font-controls" role="group" aria-label="Reading text size">
            <button type="button" class="icon-btn" id="font-dec" aria-label="Decrease text size">A-</button>
            <button type="button" class="icon-btn" id="font-reset" aria-label="Reset text size">A</button>
            <button type="button" class="icon-btn" id="font-inc" aria-label="Increase text size">A+</button>
          </div>
        </div>
      </header>

      <figure class="article-hero">
        <img src="../assets/images/{art['img_file']}" alt="{html.escape(art['title'])} — {html.escape(art['subtitle'])}">
      </figure>
      {audio_block}
      {jump_block}

      <div class="article-content">
        {body_html}
      </div>

      <nav class="post-nav" aria-label="Adjacent hymns">
        {prev_html}
        {next_html}
      </nav>
    </article>
  </main>
{footer_html(prefix="../")}"""

        (HYMNS_DIR / f"{art['slug']}.html").write_text(page_html, encoding="utf-8")

    # 2. Generate index.html
    cards_html = []
    for art in articles:
        cats = [art["category"]]
        if art["aud_file"]:
            cats.append("With Audio")
        cats_attr = html.escape("|".join(cats))
        search_attr = html.escape(f"{art['title']} {art['subtitle']} {art['category']}")
        audio_badge = '<span class="badge badge--audio">MP3 Audio</span>' if art["aud_file"] else ""
        cards_html.append(f"""      <article class="card" data-slug="{art['slug']}" data-categories="{cats_attr}" data-search="{search_attr}">
        <a href="hymns/{art['slug']}.html" tabindex="-1" aria-hidden="true">
          <img class="card-img" src="assets/images/{art['img_file']}" alt="{html.escape(art['title'])}" loading="lazy">
        </a>
        <div class="card-body">
          <div class="card-meta">
            <span class="badge">{html.escape(art['category'])}</span>
            {audio_badge}
          </div>
          <h2 class="card-title"><a href="hymns/{art['slug']}.html">{html.escape(art['title'])}</a></h2>
          <p class="card-subtitle">{html.escape(art['subtitle'])}</p>
          <a class="card-link" href="hymns/{art['slug']}.html">Read hymn &rarr;</a>
        </div>
      </article>""")

    index_desc = "Philosophical hymns (stotras and prakarana granthas) of Adi Shankaracharya with Sanskrit Devanagari text, IAST transliteration, word-for-word meaning, commentary, and MP3 chanting."
    index_html = f"""{head_html(SITE_TITLE, index_desc, "", prefix="", og_image="assets/images/blog-header.jpeg")}
<body>
{header_html(prefix="", active="home")}
  <section class="hero">
    <div class="container hero-grid">
      <div>
        <h1>Philosophical Hymns of Adi Shankara</h1>
        <p>Explore 20 timeless Advaita Vedanta hymns and treatises—complete with Sanskrit Devanagari text, IAST transliteration, split-sandhi prose order, word-for-word meanings, commentary, and MP3 chanting.</p>
        <div class="hero-actions">
          <a class="btn-primary" href="hymns/about-adi-shankaras-philosophical-hymns.html">Start with the Introduction</a>
          <a class="btn-ghost" href="toc.html">Browse Complete Index</a>
        </div>
      </div>
      <div class="hero-image-wrap">
        <img src="assets/images/blog-header.jpeg" alt="Adi Shankaracharya philosophical hymns banner">
      </div>
    </div>
  </section>

  <main id="main-content" class="container">
    <section class="toolbar" aria-label="Search and filter hymns">
      <div class="search-box">
        <span class="search-icon" aria-hidden="true">&#128269;</span>
        <label for="hymn-search" class="skip-link">Search hymns by title, Sanskrit, or commentary</label>
        <input type="search" id="hymn-search" placeholder="Search by hymn name, Sanskrit verse, IAST, or topic (e.g. Nirvana, Maya, Advaita)..." autocomplete="off">
      </div>
      <div class="filter-pills" role="group" aria-label="Filter by category">
        <button type="button" class="pill is-active" data-filter="all" aria-pressed="true">All ({len(articles)})</button>
        <button type="button" class="pill" data-filter="Panchakams &amp; Ashtakams" aria-pressed="false">Panchakams &amp; Ashtakams</button>
        <button type="button" class="pill" data-filter="Prakarana Granthas" aria-pressed="false">Prakarana Granthas</button>
        <button type="button" class="pill" data-filter="With Audio" aria-pressed="false">With Audio (MP3)</button>
        <button type="button" class="pill" data-filter="Introduction" aria-pressed="false">Introduction</button>
        <span class="results-count" id="results-count">Showing {len(articles)} of {len(articles)} articles</span>
      </div>
    </section>

    <section class="cards-grid" id="hymns-grid" aria-label="Hymns list">
{"".join(cards_html)}
    </section>
    <div class="empty-state" id="empty-state">
      No hymns matched your search. Try another term or clear the filter.
    </div>
  </main>
{footer_html(prefix="")}"""

    (BASE_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # 3. Generate toc.html (Complete Index)
    toc_rows = []
    for i, art in enumerate(articles, start=1):
        aud_cell = f'<a href="assets/audio/{art["aud_file"]}" download>MP3</a>' if art["aud_file"] else "&mdash;"
        toc_rows.append(f"""          <tr>
            <td>{i}</td>
            <td><a href="hymns/{art['slug']}.html"><strong>{html.escape(art['title'])}</strong></a></td>
            <td>{html.escape(art['subtitle'])}</td>
            <td>{html.escape(art['category'])}</td>
            <td>{aud_cell}</td>
          </tr>""")

    toc_html = f"""{head_html("Complete Index", "Complete table of contents for all 21 philosophical hymns and articles on Shankarastotrani.", "toc.html", prefix="", og_image="assets/images/blog-header.jpeg")}
<body>
{header_html(prefix="", active="toc")}
  <main id="main-content" class="container">
    <header class="article-header">
      <h1 class="article-title">Complete Index of Hymns &amp; Treatises</h1>
      <p class="article-subtitle">All {len(articles)} works on {SITE_TITLE}, organized for easy study and reference.</p>
    </header>
    <div class="table-wrap">
      <table class="toc-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Work</th>
            <th>Description</th>
            <th>Category</th>
            <th>Audio</th>
          </tr>
        </thead>
        <tbody>
{"".join(toc_rows)}
        </tbody>
      </table>
    </div>
  </main>
{footer_html(prefix="")}"""

    (BASE_DIR / "toc.html").write_text(toc_html, encoding="utf-8")

    # 4. Generate search-index.json
    search_data = [
        {"slug": art["slug"], "title": art["title"], "text": f"{art['title']} {art['subtitle']} {art['plain_text']}"}
        for art in articles
    ]
    (BASE_DIR / "search-index.json").write_text(json.dumps(search_data, ensure_ascii=False), encoding="utf-8")

    # 5. Generate sitemap.xml and robots.txt
    urls = [
        f"  <url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>",
        f"  <url><loc>{SITE_URL}/toc.html</loc><priority>0.8</priority></url>",
    ]
    for art in articles:
        urls.append(f"  <url><loc>{SITE_URL}/hymns/{art['slug']}.html</loc><lastmod>{art['updated']}</lastmod><priority>0.9</priority></url>")

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    (BASE_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    robots = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"
    (BASE_DIR / "robots.txt").write_text(robots, encoding="utf-8")

    # 6. .nojekyll and .gitignore
    (BASE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    (BASE_DIR / ".gitignore").write_text("_raw_import/\n.DS_Store\n", encoding="utf-8")

    print(f"Built {len(articles)} pages successfully in {BASE_DIR}")


if __name__ == "__main__":
    main()
