"""Fetch Telugu and Tamil Wikipedia article text and write sample sentence files.

Usage (from repo root):  python scripts/fetch_samples.py

Writes data/samples/{te,ta}_sample.txt (one sentence per line) and
data/samples/SOURCES.md. Text is from Wikipedia and is CC BY-SA 4.0.
"""

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "ocrrag-pilot/0.1 (academic research script)"
REQUEST_GAP_S = 5
MAX_RETRIES = 5
SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"

# Encyclopedic articles on science, geography, history and language.
ARTICLES = {
    "te": {
        "script": (0x0C00, 0x0C7F),
        "titles": [
            "భారతదేశం", "సూర్యుడు", "భూమి", "గణితం", "తెలుగు భాష",
            "హైదరాబాద్", "జీవశాస్త్రం", "రసాయన శాస్త్రం", "భౌతిక శాస్త్రం",
            "ఆంధ్ర ప్రదేశ్", "కృష్ణా నది", "నీరు",
        ],
    },
    "ta": {
        "script": (0x0B80, 0x0BFF),
        "titles": [
            "இந்தியா", "சூரியன்", "பூமி", "கணிதம்", "தமிழ் மொழி",
            "சென்னை", "உயிரியல்", "வேதியியல்", "இயற்பியல்",
            "தமிழ்நாடு", "வங்காள விரிகுடா", "நீர்",
        ],
    },
}

SENTENCE_SPLIT = re.compile(r"(?<=[.?!।])\s+")


def api_url(lang, title):
    query = urllib.parse.urlencode({
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": 1,
        "redirects": 1,
        "titles": title,
    })
    return f"https://{lang}.wikipedia.org/w/api.php?{query}"


def fetch_extract(lang, title):
    """Return (page_title, extract_text) for one article, honouring 429 Retry-After."""
    request = urllib.request.Request(api_url(lang, title), headers={"User-Agent": USER_AGENT})
    for _ in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.load(response)
            page = next(iter(data["query"]["pages"].values()))
            if "missing" in page:
                raise ValueError(f"{lang}.wikipedia.org has no article titled {title!r}")
            return page["title"], page.get("extract", "")
        except urllib.error.HTTPError as error:
            if error.code != 429:
                raise
            wait = int(error.headers.get("Retry-After", "30"))
            print(f"429 from {lang}.wikipedia.org, sleeping {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"gave up on {lang} {title!r} after {MAX_RETRIES} rate-limited attempts")


def is_target_sentence(sentence, script_range):
    """Keep 6-40 word sentences written mainly in the target script."""
    words = sentence.split()
    if not 6 <= len(words) <= 40:
        return False
    letters = [c for c in sentence if c.isalpha()]
    if not letters:
        return False
    in_script = sum(script_range[0] <= ord(c) <= script_range[1] for c in letters)
    return in_script / len(letters) >= 0.9


def extract_sentences(extract, script_range):
    sentences = []
    for line in extract.splitlines():
        if "==" in line or not line.strip():
            continue  # headings and blank lines
        for sentence in SENTENCE_SPLIT.split(line.strip()):
            if is_target_sentence(sentence, script_range):
                sentences.append(sentence)
    return sentences


def main():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    source_lines = ["# Sample text sources", "",
                    "Text is taken from Wikipedia articles and is licensed under CC BY-SA 4.0.", ""]
    first_request = True
    for lang, config in ARTICLES.items():
        sentences = []
        source_lines += [f"## {lang} ({lang}.wikipedia.org)", ""]
        for title in config["titles"]:
            if not first_request:
                time.sleep(REQUEST_GAP_S)
            first_request = False
            page_title, extract = fetch_extract(lang, title)
            found = extract_sentences(extract, config["script"])
            sentences.extend(found)
            url = f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(page_title.replace(' ', '_'))}"
            source_lines.append(f"- [{page_title}]({url}): {len(found)} sentences")
            print(f"{lang}: {page_title!r} -> {len(found)} sentences")
        unique = list(dict.fromkeys(sentences))
        (SAMPLES_DIR / f"{lang}_sample.txt").write_text("\n".join(unique) + "\n", encoding="utf-8")
        print(f"{lang}: wrote {len(unique)} sentences")
        source_lines.append("")
    (SAMPLES_DIR / "SOURCES.md").write_text("\n".join(source_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
