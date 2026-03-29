"""Initial migration - Create all tables for NGO SaaS platform.

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', sa.Enum('ADMIN', 'MANAGER', 'COORDINATOR', 'MEMBER', 'DONOR', 'VOLUNTEER', name='roleenum'), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Members table
    op.create_table('members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', sa.Enum('ADMIN', 'MANAGER', 'COORDINATOR', 'MEMBER', 'DONOR', 'VOLUNTEER', name='roleenum'), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('joined_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_members_email'), 'members', ['email'], unique=True)
    op.create_index(op.f('ix_members_id'), 'members', ['id'], unique=False)

    # Managers table
    op.create_table('managers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_managers_email'), 'managers', ['email'], unique=True)
    op.create_index(op.f('ix_managers_id'), 'managers', ['id'], unique=False)

    # Coordinators table
    op.create_table('coordinators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['manager_id'], ['managers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coordinators_email'), 'coordinators', ['email'], unique=True)
    op.create_index(op.f('ix_coordinators_id'), 'coordinators', ['id'], unique=False)

    # Projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal_amount', sa.Float(), nullable=True),
        sa.Column('current_amount', sa.Float(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['manager_id'], ['managers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)

    # Donations table
    op.create_table('donations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('donation_type', sa.String(length=50), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('member_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_donations_id'), 'donations', ['id'], unique=False)

    # Events table
    op.create_table('events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('organizer_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['organizer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)

    # Event Members (association table)
    op.create_table('event_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('registration_date', sa.DateTime(), nullable=True),
        sa.Column('attendance_status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_members_id'), 'event_members', ['id'], unique=False)

    # Audit Reports table
    op.create_table('audit_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', sa.String(length=50), nullable=True),
        sa.Column('findings', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('auditor_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['auditor_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_reports_id'), 'audit_reports', ['id'], unique=False)

    # Issues table
    op.create_table('issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('issue_type', sa.String(length=50), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('reporter_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['coordinators.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_issues_id'), 'issues', ['id'], unique=False)

    # Referrals table
    op.create_table('referrals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('referral_code', sa.String(length=50), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'DEACTIVATED', 'PENDING', 'COMPLETED', 'CANCELLED', name='statusenum'), nullable=True),
        sa.Column('reward_amount', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('referrer_id', sa.Integer(), nullable=True),
        sa.Column('referred_member_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['referrer_id'], ['members.id'], ),
        sa.ForeignKeyConstraint(['referred_member_id'], ['members.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referrals_id'), 'referrals', ['id'], unique=False)
    op.create_index(op.f('ix_referrals_referral_code'), 'referrals', ['referral_code'], unique=True)


def downgrade() -> None:
    op.drop_table('referrals')
    op.drop_table('issues')
    op.drop_table('audit_reports')
    op.drop_table('event_members')
    op.drop_table('events')
    op.drop_table('donations')
    op.drop_table('projects')
    op.drop_table('coordinators')
    op.drop_table('managers')
    op.drop_table('members')
    op.drop_table('users')
