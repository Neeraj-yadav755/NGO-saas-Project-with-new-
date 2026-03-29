"""SQLAlchemy models for NGO SaaS platform."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Text, ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship
import enum

from .database import Base


class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    COORDINATOR = "coordinator"
    MEMBER = "member"
    DONOR = "donor"
    VOLUNTEER = "volunteer"


class StatusEnum(str, enum.Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    DEACTIVATED = "deactivated"
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    role = Column(Enum(RoleEnum), default=RoleEnum.MEMBER)
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE)
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    donations = relationship("Donation", back_populates="user")
    organized_events = relationship("Event", back_populates="organizer")
    issues_reported = relationship("Issue", back_populates="reporter")
    audit_reports = relationship("AuditReport", back_populates="auditor")


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    role = Column(Enum(RoleEnum), default=RoleEnum.MEMBER)
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE)
    address = Column(Text)
    joined_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    donations = relationship("Donation", back_populates="member")
    events = relationship("EventMember", back_populates="member")
    referrals_made = relationship("Referral", back_populates="referrer", foreign_keys="Referral.referrer_id")
    referrals_received = relationship("Referral", back_populates="referred_member", foreign_keys="Referral.referred_member_id")


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    donation_type = Column(String(50), default="one-time")  # one-time, recurring
    payment_method = Column(String(50))  # card, bank_transfer, cash, etc.
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Relationships
    member = relationship("Member", back_populates="donations")
    user = relationship("User", back_populates="donations")
    project = relationship("Project", back_populates="donations")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(String(50))  # fundraiser, volunteer, awareness, etc.
    location = Column(String(255))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    max_participants = Column(Integer)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Relationships
    organizer = relationship("User", foreign_keys=[organizer_id])
    project = relationship("Project", backref="events")
    members = relationship("EventMember", back_populates="event")


class EventMember(Base):
    """Association table for many-to-many relationship between Events and Members."""
    __tablename__ = "event_members"

    id = Column(Integer, primary_key=True, index=True)
    registration_date = Column(DateTime, default=datetime.utcnow)
    attendance_status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)

    # Foreign keys
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)

    # Relationships
    event = relationship("Event", back_populates="members")
    member = relationship("Member", back_populates="events")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    goal_amount = Column(Float)
    current_amount = Column(Float, default=0.0)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=True)

    # Relationships
    manager = relationship("Manager", backref="managed_projects")
    donations = relationship("Donation", back_populates="project")
    issues = relationship("Issue", back_populates="project")


class AuditReport(Base):
    __tablename__ = "audit_reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    report_type = Column(String(50))  # financial, compliance, performance, etc.
    findings = Column(Text)
    recommendations = Column(Text)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    auditor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Relationships
    auditor = relationship("User", back_populates="audit_reports")
    project = relationship("Project", backref="audit_reports")


class Manager(Base):
    __tablename__ = "managers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    department = Column(String(100))
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    coordinators = relationship("Coordinator", back_populates="manager")


class Coordinator(Base):
    __tablename__ = "coordinators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    region = Column(String(100))
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=True)

    # Relationships
    manager = relationship("Manager", back_populates="coordinators")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    issue_type = Column(String(50))  # bug, complaint, suggestion, etc.
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("coordinators.id"), nullable=True)

    # Relationships
    reporter = relationship("User", back_populates="issues_reported")
    project = relationship("Project", back_populates="issues")
    assigned_to = relationship("Coordinator", backref="assigned_issues")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referral_code = Column(String(50), unique=True, index=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    reward_amount = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    referrer_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    referred_member_id = Column(Integer, ForeignKey("members.id"), nullable=True)

    # Relationships
    referrer = relationship("Member", back_populates="referrals_made", foreign_keys=[referrer_id])
    referred_member = relationship("Member", back_populates="referrals_received", foreign_keys=[referred_member_id])
