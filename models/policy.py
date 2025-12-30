import enum

class JurisdictionLevel(enum.Enum):
    federal = "federal"
    state = "state"


class ApprovalStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

from sqlalchemy import Column, Integer, String, Boolean
from db import Base

class PolicyStatus(Base):
    __tablename__ = "policy_statuses"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    label = Column(String, nullable=False)
    description = Column(String)
    sort_order = Column(Integer, default=0)
    is_terminal = Column(Boolean, default=False)

from sqlalchemy import (
    Column, Integer, String, Text,
    Date, DateTime, Boolean, Enum, ForeignKey
)
from sqlalchemy.sql import func
from db import Base

class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True)

    title = Column(String, nullable=False)
    summary = Column(Text)

    jurisdiction_level = Column(
        Enum(JurisdictionLevel),
        nullable=False
    )

    state_code = Column(String(2), nullable=True)
    governing_body = Column(String, nullable=True)

    current_status_id = Column(
        Integer,
        ForeignKey("policy_statuses.id"),
        nullable=True
    )

    introduced_date = Column(Date, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )


class PolicyStatusHistory(Base):
    __tablename__ = "policy_status_history"

    id = Column(Integer, primary_key=True)

    policy_id = Column(
        Integer,
        ForeignKey("policies.id"),
        nullable=False
    )

    status_id = Column(
        Integer,
        ForeignKey("policy_statuses.id"),
        nullable=False
    )

    changed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    change_source = Column(String, nullable=True)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())


class PolicyStatusChangeRequest(Base):
    __tablename__ = "policy_status_change_requests"

    id = Column(Integer, primary_key=True)

    policy_id = Column(
        Integer,
        ForeignKey("policies.id"),
        nullable=False
    )

    requested_status_id = Column(
        Integer,
        ForeignKey("policy_statuses.id"),
        nullable=False
    )

    requested_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    source_link = Column(String, nullable=True)
    note = Column(Text, nullable=True)

    approval_status = Column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.pending,
        nullable=False
    )

    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
