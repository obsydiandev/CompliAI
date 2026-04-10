import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DeploymentEvent(Base):
    __tablename__ = "deployment_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ai_system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_systems.id", ondelete="CASCADE"),
        nullable=False,
    )
    integration_id = Column(
        UUID(as_uuid=True),
        ForeignKey("integration_configs.id", ondelete="SET NULL"),
        nullable=True,
    )
    source = Column(
        Enum("github", "gitlab", "mlflow", "wandb", "ci_cd", "manual", name="deploy_source_enum"),
        nullable=False,
        default="manual",
    )
    event_type = Column(
        Enum(
            "deploy",
            "model_update",
            "test_run",
            "tag",
            "commit",
            name="deploy_event_type_enum",
        ),
        nullable=False,
        default="deploy",
    )
    version = Column(String(100), nullable=True)
    commit_sha = Column(String(40), nullable=True)
    model_version = Column(String(100), nullable=True)
    is_significant = Column(Boolean, default=False, nullable=False)
    significance_reason = Column(String(500), nullable=True)
    payload = Column(JSON, nullable=True)
    tf_revision_id = Column(
        UUID(as_uuid=True),
        ForeignKey("technical_file_revisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    triggered_at = Column(DateTime, default=func.now(), nullable=False)

    ai_system = relationship("AISystem")
    integration = relationship("IntegrationConfig")
    tf_revision = relationship("TechnicalFileRevision")
