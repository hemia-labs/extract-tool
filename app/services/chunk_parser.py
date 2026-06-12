"""Parse Q&A markdown into structured chunks with separated quick actions.

Expected per-section shape (one section per level-1 heading):

    # Titulo

    Pregunta: ...

    Respuesta: ...

    Acciones:

    ```json
    { "quickActions": [ ... ] }
    ```
"""

import json
import re
import unicodedata
from typing import Any, Optional

# Level-1 heading. Each heading starts a new chunk.
_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

# Labels tolerate optional bold (**Pregunta**) and trailing colon.
_PREGUNTA_RE = re.compile(
    r"(?:^|\n)\s*(?:\*\*)?Pregunta(?:\*\*)?\s*:\s*"
    r"(.+?)(?=\n\s*(?:\*\*)?(?:Respuesta|Acciones)(?:\*\*)?\s*:|\Z)",
    re.DOTALL,
)
_RESPUESTA_RE = re.compile(
    r"(?:^|\n)\s*(?:\*\*)?Respuesta(?:\*\*)?\s*:\s*"
    r"(.+?)(?=\n\s*(?:\*\*)?Acciones(?:\*\*)?\s*:|\Z)",
    re.DOTALL,
)
_ACCIONES_RE = re.compile(
    r"(?:^|\n)\s*(?:\*\*)?Acciones(?:\*\*)?\s*:\s*(.*)", re.DOTALL
)
_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
# Trailing horizontal rule that separates sections.
_TRAILING_RULE_RE = re.compile(r"\n\s*-{3,}\s*$")


def parse_chunks(text: str, source: Optional[str] = None) -> list[dict[str, Any]]:
    """Split markdown into chunks by level-1 heading.

    ``source`` (e.g. the file stem) prefixes each chunk ``id`` so the same
    title in different documents stays unique and stable for upserts.

    Returns an empty list when no heading is present, so non-matching
    documents simply yield no chunks instead of failing.
    """
    headings = list(_HEADING_RE.finditer(text))
    if not headings:
        return []

    source_slug = slugify(source) if source else ""
    chunks: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for index, heading in enumerate(headings):
        body_start = heading.end()
        body_end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[body_start:body_end]

        title = heading.group(1).strip()
        slug = slugify(title) or f"chunk-{index + 1}"
        # Disambiguate repeated titles within the same document.
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        if count:
            slug = f"{slug}-{count + 1}"

        chunks.append(
            {
                "id": f"{source_slug}-{slug}" if source_slug else slug,
                "slug": slug,
                "title": title,
                "question": _capture(_PREGUNTA_RE, body),
                "answer": _capture(_RESPUESTA_RE, body) or "",
                "actions": _extract_actions(body),
            }
        )
    return chunks


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def _capture(pattern: re.Pattern[str], body: str) -> Optional[str]:
    match = pattern.search(body)
    if not match:
        return None
    value = _TRAILING_RULE_RE.sub("", match.group(1)).strip()
    return value or None


def _extract_actions(body: str) -> list[dict[str, Any]]:
    acciones = _ACCIONES_RE.search(body)
    if not acciones:
        return []
    block = _JSON_BLOCK_RE.search(acciones.group(1))
    if not block:
        return []
    try:
        data = json.loads(block.group(1))
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        actions = data.get("quickActions", [])
        return actions if isinstance(actions, list) else []
    return []
