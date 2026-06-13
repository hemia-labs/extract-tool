"""Parse Q&A markdown into structured chunks.

Each chunk is a level-1 heading optionally preceded by, or followed by, a
YAML frontmatter block that carries routing metadata and quick actions:

    ---
    agent: support
    intent: problema_acceso
    actions:
      - support.reset_steps          # string = referencia al catalogo
      - support.start_ticket
      - id: support.promo_q3         # objeto = definicion inline
        type: route
        label: Ver promocion
        value: /promos/q3
    ---
    # No puedo iniciar sesion
    Pregunta: Olvide mi contrasena / no puedo entrar.
    Respuesta: Primero intenta restablecer el acceso...

    ---
    agent: support
    intent: problema_acceso
    actions:
      - support.reset_steps
      - support.start_ticket
    ---

``actions`` items stay as-is: a bare string is kept as a catalog reference,
a mapping is emitted as an inline action object.

For backward compatibility, when the frontmatter has no ``actions`` the body
is still scanned for a legacy ``Acciones:`` JSON block.
"""

import json
import re
import unicodedata
from typing import Any, Optional, Union

import yaml

# Level-1 heading. Each heading starts a new chunk.
_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

# YAML frontmatter delimited by --- on their own lines.
_FRONTMATTER_RE = re.compile(
    r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL | re.MULTILINE
)

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

    frontmatters = list(_FRONTMATTER_RE.finditer(text))
    leading_frontmatter_style = bool(
        frontmatters
        and frontmatters[0].end() <= headings[0].start()
        and not text[frontmatters[0].end():headings[0].start()].strip()
    )

    source_slug = slugify(source) if source else ""
    chunks: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for index, heading in enumerate(headings):
        # A frontmatter block belongs to this heading when it sits right
        # before it (only whitespace in between).
        front = _frontmatter_for(heading, frontmatters, text) if leading_frontmatter_style else None
        meta = _parse_frontmatter(front.group(1)) if front else {}

        body_start = heading.end()
        body_end = _body_end(index, headings, frontmatters, text, leading_frontmatter_style)
        body, trailing_meta = _split_trailing_frontmatter(text[body_start:body_end])
        meta.update(trailing_meta)

        title = heading.group(1).strip()
        slug = slugify(title) or f"chunk-{index + 1}"
        # Disambiguate repeated titles within the same document.
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        if count:
            slug = f"{slug}-{count + 1}"

        actions = _coerce_actions(meta.get("actions"))
        if not actions:
            actions = _extract_actions(body)

        chunk: dict[str, Any] = {
            "id": f"{source_slug}-{slug}" if source_slug else slug,
            "slug": slug,
            "title": title,
            "question": _capture(_PREGUNTA_RE, body),
            "answer": _capture(_RESPUESTA_RE, body) or "",
            "actions": actions,
        }
        if meta.get("agent") is not None:
            chunk["agent"] = meta["agent"]
        if meta.get("intent") is not None:
            chunk["intent"] = meta["intent"]
        chunks.append(chunk)
    return chunks


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def _frontmatter_for(
    heading: re.Match[str],
    frontmatters: list[re.Match[str]],
    text: str,
) -> Optional[re.Match[str]]:
    """Return the frontmatter block immediately preceding ``heading``."""
    for front in frontmatters:
        if front.end() <= heading.start() and not text[front.end():heading.start()].strip():
            return front
    return None


def _body_end(
    index: int,
    headings: list[re.Match[str]],
    frontmatters: list[re.Match[str]],
    text: str,
    leading_frontmatter_style: bool,
) -> int:
    """Where the current chunk body ends.

    Stops before the next heading, or before that heading's frontmatter so the
    metadata block is not swallowed into the previous answer.
    """
    if index + 1 >= len(headings):
        return len(text)
    next_heading = headings[index + 1]
    end = next_heading.start()
    if not leading_frontmatter_style:
        return end
    front = _frontmatter_for(next_heading, frontmatters, text)
    if front is not None:
        end = front.start()
    return end


def _parse_frontmatter(raw: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _split_trailing_frontmatter(body: str) -> tuple[str, dict[str, Any]]:
    """Remove and parse a YAML metadata block at the end of a chunk body."""
    matches = list(_FRONTMATTER_RE.finditer(body))
    if not matches:
        return body, {}

    front = matches[-1]
    if body[front.end():].strip():
        return body, {}

    return body[: front.start()].rstrip(), _parse_frontmatter(front.group(1))


def _coerce_actions(value: Any) -> list[Union[str, dict[str, Any]]]:
    """Normalize frontmatter actions, keeping references and inline objects."""
    if not isinstance(value, list):
        return []
    actions: list[Union[str, dict[str, Any]]] = []
    for item in value:
        if isinstance(item, str):
            actions.append(item)
        elif isinstance(item, dict):
            actions.append(item)
    return actions


def _capture(pattern: re.Pattern[str], body: str) -> Optional[str]:
    match = pattern.search(body)
    if not match:
        return None
    value = _TRAILING_RULE_RE.sub("", match.group(1)).strip()
    return value or None


def _extract_actions(body: str) -> list[Union[str, dict[str, Any]]]:
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
