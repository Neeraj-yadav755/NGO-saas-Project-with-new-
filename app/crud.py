"""CRUD operations for all models."""

from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas


# Generic CRUD functions
def get_db_obj(db: Session, model: Any, obj_id: int) -> Optional[Any]:
    """Get a single object by ID."""
    return db.query(model).filter(model.id == obj_id).first()


def get_db_objs(
    db: Session, 
    model: Any, 
    skip: int = 0, 
    limit: int = 100
) -> List[Any]:
    """Get a list of objects with pagination."""
    return db.query(model).offset(skip).limit(limit).all()


def get_db_objs_count(db: Session, model: Any) -> int:
    """Get total count of objects."""
    return db.query(func.count(model.id)).scalar()


def create_db_obj(db: Session, model: Any, obj_create: Any) -> Any:
    """Create a new object."""
    if hasattr(obj_create, 'model_dump'):
        # Pydantic v2
        obj_data = obj_create.model_dump(exclude_unset=True)
    else:
        # Pydantic v1
        obj_data = obj_create.dict(exclude_unset=True)
    
    db_obj = model(**obj_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_db_obj(
    db: Session, 
    model: Any, 
    obj_id: int, 
    obj_update: Any
) -> Optional[Any]:
    """Update an existing object."""
    db_obj = get_db_obj(db, model, obj_id)
    if not db_obj:
        return None
    
    if hasattr(obj_update, 'model_dump'):
        # Pydantic v2
        update_data = obj_update.model_dump(exclude_unset=True)
    else:
        # Pydantic v1
        update_data = obj_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_db_obj(db: Session, model: Any, obj_id: int) -> bool:
    """Delete an object."""
    db_obj = get_db_obj(db, model, obj_id)
    if not db_obj:
        return False
    
    db.delete(db_obj)
    db.commit()
    return True


# User CRUD
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return get_db_obj(db, models.User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return get_db_objs(db, models.User, skip, limit)


def get_users_count(db: Session) -> int:
    return get_db_objs_count(db, models.User)


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    user_data = user.model_dump() if hasattr(user, 'model_dump') else user.dict()
    password = user_data.pop('password', None)
    
    db_user = models.User(**user_data)
    if password:
        # In production, hash the password here
        db_user.password_hash = password  # Replace with proper hashing
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(
    db: Session, user_id: int, user_update: schemas.UserUpdate
) -> Optional[models.User]:
    return update_db_obj(db, models.User, user_id, user_update)


def delete_user(db: Session, user_id: int) -> bool:
    return delete_db_obj(db, models.User, user_id)


# Member CRUD
def get_member(db: Session, member_id: int) -> Optional[models.Member]:
    return get_db_obj(db, models.Member, member_id)


def get_member_by_email(db: Session, email: str) -> Optional[models.Member]:
    return db.query(models.Member).filter(models.Member.email == email).first()


def get_members(db: Session, skip: int = 0, limit: int = 100) -> List[models.Member]:
    return get_db_objs(db, models.Member, skip, limit)


def get_members_count(db: Session) -> int:
    return get_db_objs_count(db, models.Member)


def create_member(db: Session, member: schemas.MemberCreate) -> models.Member:
    return create_db_obj(db, models.Member, member)


def update_member(
    db: Session, member_id: int, member_update: schemas.MemberUpdate
) -> Optional[models.Member]:
    return update_db_obj(db, models.Member, member_id, member_update)


def delete_member(db: Session, member_id: int) -> bool:
    return delete_db_obj(db, models.Member, member_id)


# Donation CRUD
def get_donation(db: Session, donation_id: int) -> Optional[models.Donation]:
    return get_db_obj(db, models.Donation, donation_id)


def get_donations(db: Session, skip: int = 0, limit: int = 100) -> List[models.Donation]:
    return get_db_objs(db, models.Donation, skip, limit)


def get_donations_count(db: Session) -> int:
    return get_db_objs_count(db, models.Donation)


def get_donations_by_member(
    db: Session, member_id: int, skip: int = 0, limit: int = 100
) -> List[models.Donation]:
    return db.query(models.Donation).filter(
        models.Donation.member_id == member_id
    ).offset(skip).limit(limit).all()


def create_donation(db: Session, donation: schemas.DonationCreate) -> models.Donation:
    return create_db_obj(db, models.Donation, donation)


def update_donation(
    db: Session, donation_id: int, donation_update: schemas.DonationUpdate
) -> Optional[models.Donation]:
    return update_db_obj(db, models.Donation, donation_id, donation_update)


def delete_donation(db: Session, donation_id: int) -> bool:
    return delete_db_obj(db, models.Donation, donation_id)


# Event CRUD
def get_event(db: Session, event_id: int) -> Optional[models.Event]:
    return get_db_obj(db, models.Event, event_id)


def get_events(db: Session, skip: int = 0, limit: int = 100) -> List[models.Event]:
    return get_db_objs(db, models.Event, skip, limit)


def get_events_count(db: Session) -> int:
    return get_db_objs_count(db, models.Event)


def create_event(db: Session, event: schemas.EventCreate) -> models.Event:
    return create_db_obj(db, models.Event, event)


def update_event(
    db: Session, event_id: int, event_update: schemas.EventUpdate
) -> Optional[models.Event]:
    return update_db_obj(db, models.Event, event_id, event_update)


def delete_event(db: Session, event_id: int) -> bool:
    return delete_db_obj(db, models.Event, event_id)


# Project CRUD
def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    return get_db_obj(db, models.Project, project_id)


def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[models.Project]:
    return get_db_objs(db, models.Project, skip, limit)


def get_projects_count(db: Session) -> int:
    return get_db_objs_count(db, models.Project)


def create_project(db: Session, project: schemas.ProjectCreate) -> models.Project:
    return create_db_obj(db, models.Project, project)


def update_project(
    db: Session, project_id: int, project_update: schemas.ProjectUpdate
) -> Optional[models.Project]:
    return update_db_obj(db, models.Project, project_id, project_update)


def delete_project(db: Session, project_id: int) -> bool:
    return delete_db_obj(db, models.Project, project_id)


# AuditReport CRUD
def get_audit_report(db: Session, report_id: int) -> Optional[models.AuditReport]:
    return get_db_obj(db, models.AuditReport, report_id)


def get_audit_reports(db: Session, skip: int = 0, limit: int = 100) -> List[models.AuditReport]:
    return get_db_objs(db, models.AuditReport, skip, limit)


def create_audit_report(
    db: Session, report: schemas.AuditReportCreate
) -> models.AuditReport:
    return create_db_obj(db, models.AuditReport, report)


def update_audit_report(
    db: Session, report_id: int, report_update: schemas.AuditReportUpdate
) -> Optional[models.AuditReport]:
    return update_db_obj(db, models.AuditReport, report_id, report_update)


def delete_audit_report(db: Session, report_id: int) -> bool:
    return delete_db_obj(db, models.AuditReport, report_id)


# Manager CRUD
def get_manager(db: Session, manager_id: int) -> Optional[models.Manager]:
    return get_db_obj(db, models.Manager, manager_id)


def get_manager_by_email(db: Session, email: str) -> Optional[models.Manager]:
    return db.query(models.Manager).filter(models.Manager.email == email).first()


def get_managers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Manager]:
    return get_db_objs(db, models.Manager, skip, limit)


def create_manager(db: Session, manager: schemas.ManagerCreate) -> models.Manager:
    return create_db_obj(db, models.Manager, manager)


def update_manager(
    db: Session, manager_id: int, manager_update: schemas.ManagerUpdate
) -> Optional[models.Manager]:
    return update_db_obj(db, models.Manager, manager_id, manager_update)


def delete_manager(db: Session, manager_id: int) -> bool:
    return delete_db_obj(db, models.Manager, manager_id)


# Coordinator CRUD
def get_coordinator(db: Session, coordinator_id: int) -> Optional[models.Coordinator]:
    return get_db_obj(db, models.Coordinator, coordinator_id)


def get_coordinators(db: Session, skip: int = 0, limit: int = 100) -> List[models.Coordinator]:
    return get_db_objs(db, models.Coordinator, skip, limit)


def create_coordinator(
    db: Session, coordinator: schemas.CoordinatorCreate
) -> models.Coordinator:
    return create_db_obj(db, models.Coordinator, coordinator)


def update_coordinator(
    db: Session, coordinator_id: int, coordinator_update: schemas.CoordinatorUpdate
) -> Optional[models.Coordinator]:
    return update_db_obj(db, models.Coordinator, coordinator_id, coordinator_update)


def delete_coordinator(db: Session, coordinator_id: int) -> bool:
    return delete_db_obj(db, models.Coordinator, coordinator_id)


# Issue CRUD
def get_issue(db: Session, issue_id: int) -> Optional[models.Issue]:
    return get_db_obj(db, models.Issue, issue_id)


def get_issues(db: Session, skip: int = 0, limit: int = 100) -> List[models.Issue]:
    return get_db_objs(db, models.Issue, skip, limit)


def create_issue(db: Session, issue: schemas.IssueCreate) -> models.Issue:
    return create_db_obj(db, models.Issue, issue)


def update_issue(
    db: Session, issue_id: int, issue_update: schemas.IssueUpdate
) -> Optional[models.Issue]:
    return update_db_obj(db, models.Issue, issue_id, issue_update)


def delete_issue(db: Session, issue_id: int) -> bool:
    return delete_db_obj(db, models.Issue, issue_id)


# Referral CRUD
def get_referral(db: Session, referral_id: int) -> Optional[models.Referral]:
    return get_db_obj(db, models.Referral, referral_id)


def get_referrals(db: Session, skip: int = 0, limit: int = 100) -> List[models.Referral]:
    return get_db_objs(db, models.Referral, skip, limit)


def create_referral(db: Session, referral: schemas.ReferralCreate) -> models.Referral:
    return create_db_obj(db, models.Referral, referral)


def update_referral(
    db: Session, referral_id: int, referral_update: schemas.ReferralUpdate
) -> Optional[models.Referral]:
    return update_db_obj(db, models.Referral, referral_id, referral_update)


def delete_referral(db: Session, referral_id: int) -> bool:
    return delete_db_obj(db, models.Referral, referral_id)


# ============== NGO CRUD Operations ==============

def get_ngos(db: Session, skip: int = 0, limit: int = 100) -> List[models.NGO]:
    return get_db_objs(db, models.NGO, skip, limit)


def get_ngo(db: Session, ngo_id: int) -> Optional[models.NGO]:
    return get_db_obj(db, models.NGO, ngo_id)


def get_ngo_by_email(db: Session, email: str) -> Optional[models.NGO]:
    return db.query(models.NGO).filter(models.NGO.email == email).first()


def create_ngo(db: Session, ngo: schemas.NGOCreate) -> models.NGO:
    return create_db_obj(db, models.NGO, ngo)


def update_ngo(
    db: Session, ngo_id: int, ngo_update: schemas.NGOUpdate
) -> Optional[models.NGO]:
    return update_db_obj(db, models.NGO, ngo_id, ngo_update)


def delete_ngo(db: Session, ngo_id: int) -> bool:
    return delete_db_obj(db, models.NGO, ngo_id)
