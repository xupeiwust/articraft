from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_FRONTMATTER_RE = re.compile(r"\A---\n(?P<frontmatter>.*?)\n---\n?(?P<body>.*)\Z", re.DOTALL)
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_NON_DISTINCTIVE_TAG_TOKENS = frozenset({"cadquery", "example", "examples"})


@dataclass(slots=True, frozen=True)
class ExampleDocument:
    path: Path
    title: str
    description: str
    tags: tuple[str, ...]
    body: str
    content: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def examples_root() -> Path:
    return _repo_root() / "sdk" / "_examples"


def examples_dir_for_sdk(sdk_package: str) -> Path:
    if sdk_package == "sdk_hybrid":
        return examples_root() / "hybrid"
    if sdk_package == "sdk":
        return examples_root() / "base"
    raise ValueError(f"Unsupported SDK package for examples: {sdk_package!r}")


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()


def _tokenize(value: str) -> list[str]:
    return _TOKEN_PATTERN.findall(_normalize_text(value))


def _parse_frontmatter_value(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        inner = value[1:-1]
        if value[0] == "'":
            return inner.replace("''", "'")
        return inner.replace('\\"', '"')
    return value


def _parse_frontmatter(text: str, *, source: Path) -> dict[str, object]:
    values: dict[str, object] = {}
    current_key: str | None = None
    list_values: list[str] = []

    def _flush_list() -> None:
        nonlocal current_key, list_values
        if current_key is not None:
            values[current_key] = list(list_values)
        current_key = None
        list_values = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if line.startswith("  - ") or line.startswith("- "):
            item = line.split("-", 1)[1].strip()
            if current_key is None:
                raise ValueError(f"{source}: list item found before list key")
            list_values.append(_parse_frontmatter_value(item))
            continue

        _flush_list()
        if ":" not in line:
            raise ValueError(f"{source}: invalid frontmatter line: {raw_line!r}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            raise ValueError(f"{source}: missing frontmatter key")
        if not value:
            current_key = key
            list_values = []
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                values[key] = []
            else:
                values[key] = [_parse_frontmatter_value(part) for part in inner.split(",")]
            continue
        values[key] = _parse_frontmatter_value(value)

    _flush_list()
    return values


def parse_example_document(path: Path) -> ExampleDocument:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path}: expected YAML frontmatter delimited by ---")

    frontmatter = _parse_frontmatter(match.group("frontmatter"), source=path)
    title = str(frontmatter.get("title") or "").strip()
    description = str(frontmatter.get("description") or "").strip()
    raw_tags = frontmatter.get("tags")
    if not title:
        raise ValueError(f"{path}: missing required frontmatter field 'title'")
    if not description:
        raise ValueError(f"{path}: missing required frontmatter field 'description'")
    if not isinstance(raw_tags, list) or not raw_tags:
        raise ValueError(f"{path}: missing required frontmatter field 'tags'")

    tags = tuple(str(tag).strip() for tag in raw_tags if str(tag).strip())
    if not tags:
        raise ValueError(f"{path}: tags must contain at least one non-empty value")

    return ExampleDocument(
        path=path,
        title=title,
        description=description,
        tags=tags,
        body=match.group("body"),
        content=text,
    )


@lru_cache(maxsize=8)
def load_example_documents(sdk_package: str) -> tuple[ExampleDocument, ...]:
    root = examples_dir_for_sdk(sdk_package)
    if not root.exists():
        return ()
    docs = [parse_example_document(path) for path in sorted(root.glob("*.md"))]
    return tuple(docs)


def search_example_documents(
    query: str,
    *,
    sdk_package: str,
    limit: int = 3,
) -> list[ExampleDocument]:
    query_tokens = [token for token in _tokenize(query) if token not in _NON_DISTINCTIVE_TAG_TOKENS]
    if not query_tokens:
        return []

    ranked: list[tuple[float, ExampleDocument]] = []
    phrase_query = " ".join(query_tokens)
    for doc in load_example_documents(sdk_package):
        title_tokens = _tokenize(doc.title)
        description_tokens = _tokenize(doc.description)
        tag_tokens = [
            token
            for token in _tokenize(" ".join(doc.tags))
            if token not in _NON_DISTINCTIVE_TAG_TOKENS
        ]
        body_tokens = _tokenize(doc.body)
        score = 0.0
        structured_hits = 0
        body_exact_hits: set[str] = set()
        body_prefix_hits: set[str] = set()
        for token in query_tokens:
            if token in title_tokens:
                score += 150.0
                structured_hits += 1
            elif any(candidate.startswith(token) for candidate in title_tokens):
                score += 110.0
                structured_hits += 1

            if token in description_tokens:
                score += 110.0
                structured_hits += 1
            elif any(candidate.startswith(token) for candidate in description_tokens):
                score += 75.0
                structured_hits += 1

            if token in tag_tokens:
                score += 120.0
                structured_hits += 1
            elif any(candidate.startswith(token) for candidate in tag_tokens):
                score += 90.0
                structured_hits += 1

            if token in body_tokens:
                score += 25.0
                body_exact_hits.add(token)
            elif any(candidate.startswith(token) for candidate in body_tokens):
                score += 10.0
                body_prefix_hits.add(token)

        title_phrase = _normalize_text(doc.title)
        description_phrase = _normalize_text(doc.description)
        tags_phrase = _normalize_text(" ".join(doc.tags))
        body_phrase = _normalize_text(doc.body)
        title_phrase_hit = False
        description_phrase_hit = False
        tags_phrase_hit = False
        body_phrase_hit = False
        if phrase_query and phrase_query in title_phrase:
            score += 80.0
            title_phrase_hit = True
        if phrase_query and phrase_query in description_phrase:
            score += 60.0
            description_phrase_hit = True
        if phrase_query and phrase_query in tags_phrase:
            score += 70.0
            tags_phrase_hit = True
        if phrase_query and phrase_query in body_phrase:
            score += 20.0
            body_phrase_hit = True

        has_distinctive_structured_signal = (
            structured_hits > 0 or title_phrase_hit or description_phrase_hit or tags_phrase_hit
        )
        has_sufficient_body_signal = (
            body_phrase_hit
            or len(body_exact_hits) >= 2
            or any(len(token) >= 6 for token in body_exact_hits)
            or any(len(token) >= 8 for token in body_prefix_hits)
        )

        if score > 0 and (has_distinctive_structured_signal or has_sufficient_body_signal):
            ranked.append((score, doc))

    ranked.sort(key=lambda item: (-item[0], item[1].title, item[1].path.as_posix()))
    return [doc for _, doc in ranked[:limit]]
