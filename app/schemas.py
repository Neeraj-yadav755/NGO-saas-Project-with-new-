"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum


class RoleEnum(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    COORDINATOR = "coordinator"
    MEMBER = "member"
    DONOR = "donor"
    VOLUNTEER = "volunteer"


class StatusEnum(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    DEACTIVATED = "deactivated"
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Base schemas
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# User schemas
class UserBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    role: RoleEnum = RoleEnum.MEMBER
    status: StatusEnum = StatusEnum.ACTIVE


class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[RoleEnum] = None
    status: Optional[StatusEnum] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Member schemas
class MemberBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    role: RoleEnum = RoleEnum.MEMBER
    status: StatusEnum = StatusEnum.ACTIVE
    address: Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[RoleEnum] = None
    status: Optional[StatusEnum] = None
    address: Optional[str] = None


class MemberResponse(MemberBase):
    id: int
    joined_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Donation schemas
class DonationBase(BaseSchema):
    amount: float = Field(..., gt=0)
    currency: str = Field("USD", max_length=10)
    donation_type: str = Field("one-time", max_length=50)
    payment_method: Optional[str] = Field(None, max_length=50)
    status: StatusEnum = StatusEnum.PENDING
    notes: Optional[str] = None


class DonationCreate(DonationBase):
    member_id: Optional[int] = None
    user_id: Optional[int] = None
    project_id: Optional[int] = None


class DonationUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    status: Optional[StatusEnum] = None
    notes: Optional[str] = None


class DonationResponse(DonationBase):
    id: int
    member_id: Optional[int] = None
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Event schemas
class EventBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    event_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_participants: Optional[int] = None
    status: StatusEnum = StatusEnum.PENDING


class EventCreate(EventBase):
    organizer_id: Optional[int] = None
    project_id: Optional[int] = None


class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_participants: Optional[int] = None
    status: Optional[StatusEnum] = None


class EventResponse(EventBase):
    id: int
    organizer_id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Project schemas
class ProjectBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    goal_amount: Optional[float] = None
    current_amount: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: StatusEnum = StatusEnum.PENDING


class ProjectCreate(ProjectBase):
    manager_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    goal_amount: Optional[float] = None
    current_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[StatusEnum] = None


class ProjectResponse(ProjectBase):
    id: int
    manager_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# AuditReport schemas
class AuditReportBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: Optional[str] = Field(None, max_length=50)
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    status: StatusEnum = StatusEnum.PENDING


class AuditReportCreate(AuditReportBase):
    auditor_id: Optional[int] = None
    project_id: Optional[int] = None


class AuditReportUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    status: Optional[StatusEnum] = None


class AuditReportResponse(AuditReportBase):
    id: int
    auditor_id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Manager schemas
class ManagerBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    status: StatusEnum = StatusEnum.ACTIVE


class ManagerCreate(ManagerBase):
    pass


class ManagerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = None
    status: Optional[StatusEnum] = None


class ManagerResponse(ManagerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Coordinator schemas
class CoordinatorBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    region: Optional[str] = Field(None, max_length=100)
    status: StatusEnum = StatusEnum.ACTIVE


class CoordinatorCreate(CoordinatorBase):
    manager_id: Optional[int] = None


class CoordinatorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    region: Optional[str] = None
    status: Optional[StatusEnum] = None


class CoordinatorResponse(CoordinatorBase):
    id: int
    manager_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Issue schemas
class IssueBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    issue_type: Optional[str] = Field(None, max_length=50)
    priority: str = Field("medium", max_length=20)
    status: StatusEnum = StatusEnum.PENDING
    resolution_notes: Optional[str] = None


class IssueCreate(IssueBase):
    reporter_id: Optional[int] = None
    project_id: Optional[int] = None
    assigned_to_id: Optional[int] = None


class IssueUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, max_length=20)
    status: Optional[StatusEnum] = None
    resolution_notes: Optional[str] = None
    assigned_to_id: Optional[int] = None


class IssueResponse(IssueBase):
    id: int
    reporter_id: Optional[int] = None
    project_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Referral schemas
class ReferralBase(BaseSchema):
    referral_code: str = Field(..., min_length=1, max_length=50)
    status: StatusEnum = StatusEnum.PENDING
    reward_amount: float = 0.0
    notes: Optional[str] = None


class ReferralCreate(ReferralBase):
    referrer_id: Optional[int] = None
    referred_member_id: Optional[int] = None


class ReferralUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    reward_amount: Optional[float] = None
    notes: Optional[str] = None


class ReferralResponse(ReferralBase):
    id: int
    referrer_id: Optional[int] = None
    referred_member_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# NGO schemas
class NGOBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    website: Optional[str] = Field(None, max_length=255)
    status: StatusEnum = StatusEnum.ACTIVE
    subscription_plan: str = Field("basic", max_length=50)


class NGOCreate(NGOBase):
    pass


class NGOUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    website: Optional[str] = None
    status: Optional[StatusEnum] = None
    subscription_plan: Optional[str] = None


class NGOResponse(NGOBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Generic response schema for lists
class ListResponse(BaseModel):
    items: List
    total: int
    page: int = 1
    page_size: int = 10
