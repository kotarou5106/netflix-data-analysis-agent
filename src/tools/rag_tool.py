import re
from dataclasses import dataclass
from pathlib import Path

from src.config import DOCS_DIR


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    content: str


def search_knowledge(query: str, top_k: int = 3) -> list[dict[str, object]]:
    if not query or top_k <= 0:
        return []

    chunks = _load_chunks()
    if not chunks:
        return []

    expanded_query = _expand_query(query)
    query_tokens = _tokenize(expanded_query)
    query_terms = _query_terms(expanded_query)
    if not query_tokens and not query_terms:
        return []

    best_result_by_source = {}
    for chunk in chunks:
        score = _score_chunk(query_tokens, query_terms, chunk.content)
        if score > 0:
            current_result = best_result_by_source.get(chunk.source)
            if current_result is None or score > current_result["score"]:
                best_result_by_source[chunk.source] = {
                    "source": chunk.source,
                    "content": chunk.content,
                    "score": score,
                }

    scored_results = list(best_result_by_source.values())
    scored_results.sort(key=lambda item: item["score"], reverse=True)
    return scored_results[:top_k]


def _load_chunks() -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        for chunk in _split_markdown(content):
            chunks.append(KnowledgeChunk(source=path.name, content=chunk))
    return chunks


def _split_markdown(content: str) -> list[str]:
    blocks = re.split(r"\n(?=#{1,6}\s)|\n\s*\n", content)
    return [block.strip() for block in blocks if block.strip()]


def _score_chunk(query_tokens: set[str], query_terms: list[str], content: str) -> float:
    content_lower = content.lower()
    content_tokens = _tokenize(content)
    score = 0.0

    for term in query_terms:
        if term and term in content:
            score += 3.0
        elif term and term.lower() in content_lower:
            score += 2.0

    for token in query_tokens:
        if token in content_tokens:
            score += 1.0

    if query_tokens:
        overlap = query_tokens & content_tokens
        score += len(overlap) / len(query_tokens)

    return score


def _query_terms(text: str) -> list[str]:
    terms = [text.strip()]
    terms.extend(re.findall(r"[\u4e00-\u9fff]{2,}", text))
    terms.extend(re.findall(r"[A-Za-z][A-Za-z\s-]{2,}", text))
    return list(dict.fromkeys(term.strip() for term in terms if term.strip()))


def _expand_query(query: str) -> str:
    expansions = []
    if "流失" in query:
        expansions.extend(["churn", "churn rate", "流失率"])
    if "订阅" in query:
        expansions.extend(["subscription", "subscription type", "订阅类型"])
    if "分层" in query:
        expansions.extend(["segmentation", "用户分层"])
    if "完播" in query:
        expansions.extend(["completion rate", "完播率"])

    if not expansions:
        return query
    return " ".join([query, *expansions])


def _tokenize(text: str) -> set[str]:
    english_tokens = re.findall(r"[a-zA-Z][a-zA-Z-]+", text.lower())
    chinese_tokens = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    return set(english_tokens + chinese_tokens)
