"""Pydantic schemas for Templates, ISO 42001 Crosswalk and AI Impact Assessment (Epic 6)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel


# ── Template ──────────────────────────────────────────────────────────────────


class TemplateSummary(BaseModel):
    id: str
    name: str
    description: str
    system_type: str
    tags: list[str]
    sections_count: int


class TemplateDetail(BaseModel):
    id: str
    name: str
    description: str
    system_type: str
    tags: list[str]
    sections: dict[int, dict[str, Any]]


class ApplyTemplateRequest(BaseModel):
    template_id: str
    revision_id: UUID
    overwrite: bool = False


class ApplyTemplateResponse(BaseModel):
    applied_sections: list[int]
    skipped_sections: list[int]


# ── ISO 42001 Crosswalk ───────────────────────────────────────────────────────


class CrosswalkEntry(BaseModel):
    iso_clause: str
    iso_title: str
    annex_iv_sections: list[int]
    coverage: str
    notes: str


class EvidencePackage(BaseModel):
    total_controls: int
    fully_covered: int
    partially_covered: int
    not_covered: int
    covered_clauses: list[str]
    partial_clauses: list[str]
    not_covered_clauses: list[str]
    coverage_pct: float


# ── AI Impact Assessment ──────────────────────────────────────────────────────


class AIIARequest(BaseModel):
    system_id: UUID
    use_llm: bool = True


class AIIAResponse(BaseModel):
    report: dict[str, Any]
