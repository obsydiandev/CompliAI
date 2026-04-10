"""Pydantic schemas for Policy Engine (Epic 5)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


# ── PolicyRule ────────────────────────────────────────────────────────────────


class PolicyRuleCreate(BaseModel):
    name: str
    description: str | None = None
    ai_system_id: UUID | None = None
    rule_type: str = "custom"
    condition: dict[str, Any]
    severity: str = "warning"
    is_active: bool = True


class PolicyRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    condition: dict[str, Any] | None = None
    severity: str | None = None
    is_active: bool | None = None


class PolicyRuleRead(BaseModel):
    id: UUID
    org_id: UUID
    ai_system_id: UUID | None
    name: str
    description: str | None
    rule_type: str
    condition: dict[str, Any]
    severity: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── ComplianceEvent ───────────────────────────────────────────────────────────


class ComplianceEventRead(BaseModel):
    id: UUID
    rule_id: UUID
    ai_system_id: UUID
    status: str
    details: dict[str, Any] | None
    triggered_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


# ── Compliance Health Dashboard ───────────────────────────────────────────────


class SectionDebt(BaseModel):
    section_number: int
    section_name: str
    completeness: float
    missing_fields: list[str]
    days_since_update: int | None


class ComplianceHealthReport(BaseModel):
    ai_system_id: UUID
    system_name: str
    days_since_last_revision: int | None
    overall_completeness: float
    open_violations: int
    unlinked_deployments: int
    missing_evidence_count: int
    section_debt: list[SectionDebt]
    open_events: list[ComplianceEventRead]


# ── Shadow Validation ─────────────────────────────────────────────────────────


class ShadowValidationRequest(BaseModel):
    new_metrics: dict[str, float]
    threshold_pct: float = 5.0


class ShadowValidationResponse(BaseModel):
    ok: bool
    summary: str
    sections_requiring_update: list[int]
    details: list[dict[str, Any]]


# ── Bias Audit ────────────────────────────────────────────────────────────────


class BiasAuditRequest(BaseModel):
    current_metrics: dict[str, float]
    previous_metrics: dict[str, float] | None = None
    custom_thresholds: dict[str, Any] | None = None


class BiasAuditResponse(BaseModel):
    ok: bool
    summary: str
    metrics: list[dict[str, Any]]
    section5_evidence: dict[str, Any]


# ── Run checks ────────────────────────────────────────────────────────────────


class RunChecksResponse(BaseModel):
    evaluated: int
    violations: int
    events_created: int
    results: list[dict[str, Any]]
