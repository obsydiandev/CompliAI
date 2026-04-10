"""RAG (Retrieval-Augmented Generation) engine for Q&A over Technical Files.

Embeds section content using OpenAI text-embedding-3-small, stores
vectors in PostgreSQL via pgvector, and answers questions using
retrieved context + GPT.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models.embedding import SectionEmbedding
from app.models.technical_file import Section
from app.modules.ai_assistant import cache as _cache
from app.modules.ai_assistant.prompt_templates import QA_SYSTEM_PROMPT, QA_USER_PROMPT
from app.modules.ai_assistant.usage_logger import log_usage
from app.modules.annex_iv_core.schemas import SECTION_NAMES

logger = logging.getLogger(__name__)

_EMBED_MODEL = "text-embedding-3-small"
_EMBED_DIM = 1536
_PROMPT_VERSION = "v1.0"


# ── Embedding helpers ─────────────────────────────────────────────────────────

def _get_embedding(client: OpenAI, text: str) -> list[float]:
    """Return embedding vector, using Redis cache when available."""
    cached = _cache.get_embedding_cache(text, _EMBED_MODEL)
    if cached:
        return cached
    response = client.embeddings.create(model=_EMBED_MODEL, input=text)
    vector = response.data[0].embedding
    _cache.set_embedding_cache(text, _EMBED_MODEL, vector)
    return vector


def _section_text(section: Section) -> str:
    """Convert section content dict to a flat text representation for embedding."""
    section_name = SECTION_NAMES.get(section.section_number, "")
    content = section.content or {}
    parts = [f"Section {section.section_number}: {section_name}"]
    for key, value in content.items():
        if value:
            if isinstance(value, list):
                parts.append(f"{key}: {', '.join(str(v) for v in value)}")
            else:
                parts.append(f"{key}: {value}")
    return "\n".join(parts)


def _content_hash(content: dict) -> str:
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:32]


# ── Indexing ──────────────────────────────────────────────────────────────────

def index_revision_sections(
    db: Session,
    *,
    revision_id: str,
    ai_system_id: str,
    org_id: str | None = None,
) -> int:
    """Embed and store vectors for all sections of a revision.

    Returns the number of sections indexed.
    """
    sections = db.query(Section).filter(Section.revision_id == revision_id).all()
    if not sections:
        return 0

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    indexed = 0
    total_tokens = 0

    for section in sections:
        text = _section_text(section)
        c_hash = _content_hash(section.content or {})

        existing = (
            db.query(SectionEmbedding)
            .filter(SectionEmbedding.section_id == section.id)
            .first()
        )
        if existing and existing.content_hash == c_hash:
            continue  # Already up to date

        try:
            vector = _get_embedding(client, text)
            total_tokens += len(text.split())  # rough estimate

            if existing:
                existing.embedding = vector
                existing.content_hash = c_hash
                existing.updated_at = datetime.now(UTC)
            else:
                emb = SectionEmbedding(
                    id=uuid.uuid4(),
                    section_id=section.id,
                    revision_id=uuid.UUID(revision_id),
                    ai_system_id=uuid.UUID(ai_system_id),
                    section_number=section.section_number,
                    model=_EMBED_MODEL,
                    content_hash=c_hash,
                    embedding=vector,
                )
                db.add(emb)

            indexed += 1
        except Exception as exc:
            logger.warning("Failed to embed section %d: %s", section.section_number, exc)

    try:
        db.commit()
        # Log approximate embedding cost
        log_usage(
            db,
            feature="index_revision",
            model=_EMBED_MODEL,
            prompt_tokens=total_tokens,
            completion_tokens=0,
            org_id=org_id,
            ai_system_id=ai_system_id,
            prompt_version=_PROMPT_VERSION,
            success=True,
        )
    except Exception as exc:
        logger.warning("Failed to commit embeddings: %s", exc)
        db.rollback()

    return indexed


# ── Q&A ───────────────────────────────────────────────────────────────────────

def _cosine_search(
    db: Session, revision_id: str, query_vector: list[float], top_k: int = 5
) -> list[tuple[SectionEmbedding, float]]:
    """Return top-k most similar sections using pgvector cosine distance."""
    try:

        results = (
            db.query(SectionEmbedding)
            .filter(SectionEmbedding.revision_id == revision_id)
            .order_by(SectionEmbedding.embedding.cosine_distance(query_vector))
            .limit(top_k)
            .all()
        )
        return [(r, 0.0) for r in results]
    except Exception as exc:
        logger.warning("Vector search failed, falling back to full scan: %s", exc)
        return _fallback_search(db, revision_id, query_vector, top_k)


def _fallback_search(
    db: Session, revision_id: str, query_vector: list[float], top_k: int
) -> list[tuple[SectionEmbedding, float]]:
    """Fallback: return all sections for the revision (no vector ranking)."""
    results = (
        db.query(SectionEmbedding)
        .filter(SectionEmbedding.revision_id == revision_id)
        .limit(top_k)
        .all()
    )
    return [(r, 0.0) for r in results]


def answer_question(
    db: Session,
    *,
    question: str,
    revision_id: str,
    ai_system_id: str,
    org_id: str | None = None,
    user_id: str | None = None,
    top_k: int = 4,
) -> dict:
    """Answer a natural-language question about the Technical File.

    Returns:
        {answer: str, citations: [{section_number, section_name, excerpt}]}
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt_tokens = 0
    completion_tokens = 0
    success = True
    error_msg = None

    try:
        # Embed query
        query_vector = _get_embedding(client, question)

        # Retrieve similar sections
        matches = _cosine_search(db, revision_id, query_vector, top_k)

        # Build context from matched sections
        context_parts = []
        citations = []
        for emb, _score in matches:
            section = db.query(Section).filter(Section.id == emb.section_id).first()
            if not section:
                continue
            section_name = SECTION_NAMES.get(section.section_number, "")
            content_preview = json.dumps(section.content or {}, ensure_ascii=False)[:500]
            context_parts.append(
                f"[Section {section.section_number}: {section_name}]\n{content_preview}"
            )
            citations.append({
                "section_number": section.section_number,
                "section_name": section_name,
                "excerpt": content_preview[:200],
            })

        context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant content found."

        user_prompt = QA_USER_PROMPT.format(context=context, question=question)

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": QA_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1000,
        )
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        answer = response.choices[0].message.content or ""

        return {"answer": answer, "citations": citations}

    except Exception as exc:
        logger.error("Q&A failed: %s", exc)
        success = False
        error_msg = str(exc)
        raise
    finally:
        try:
            log_usage(
                db,
                feature="qa",
                model=settings.OPENAI_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                org_id=org_id,
                user_id=user_id,
                ai_system_id=ai_system_id,
                prompt_version=_PROMPT_VERSION,
                success=success,
                error_message=error_msg,
            )
        except Exception:
            pass
