from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class KnowledgeChunk:
    source: str
    title: str
    text: str


class KnowledgeRetriever:
    def __init__(self, knowledge_dir: str) -> None:
        self.knowledge_dir = Path(knowledge_dir)
        self.chunks = self._load_chunks()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in self.chunks]) if self.chunks else None

    def _load_chunks(self) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        for path in sorted(self.knowledge_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            sections = [section.strip() for section in text.split("\n## ") if section.strip()]
            if not sections:
                chunks.append(KnowledgeChunk(source=path.name, title=path.stem.replace("_", " ").title(), text=text.strip()))
                continue
            for index, section in enumerate(sections):
                if index == 0 and section.startswith("# "):
                    title_line, _, body = section.partition("\n")
                    title = title_line.replace("# ", "").strip()
                    chunks.append(KnowledgeChunk(source=path.name, title=title, text=body.strip()))
                    continue
                title_line, _, body = section.partition("\n")
                chunks.append(KnowledgeChunk(source=path.name, title=title_line.strip(), text=body.strip()))
        return [chunk for chunk in chunks if chunk.text]

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not query.strip() or not self.chunks or self.matrix is None:
            return []
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).flatten()
        ranked = scores.argsort()[::-1][:top_k]
        results = []
        for index in ranked:
            score = float(scores[index])
            if score <= 0:
                continue
            chunk = self.chunks[index]
            results.append(
                {
                    "source": chunk.source,
                    "title": chunk.title,
                    "text": chunk.text,
                    "score": round(score, 4),
                }
            )
        return results
