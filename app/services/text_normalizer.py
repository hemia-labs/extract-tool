import re


INVISIBLE_CHARS = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def normalize_text(text: str) -> str:
    text = INVISIBLE_CHARS.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def join_pages(pages: list[dict]) -> str:
    return normalize_text("\n\n".join(page["text"] for page in pages if page.get("text")))
