"""Initial tables

Revision ID: e11b22cc33dd
Revises: 
Create Date: 2026-07-16 19:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e11b22cc33dd'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('telegram_chat_id', sa.String(), nullable=True),
        sa.Column('telegram_pairing_token', sa.String(), nullable=True),
        sa.Column('pairing_token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('subscription_tier', sa.String(50), server_default='free', nullable=False),
        sa.Column('subscription_status', sa.String(50), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # 2. Create job_opportunities table
    op.create_table(
        'job_opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('job_title', sa.String(), nullable=True),
        sa.Column('required_skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('preferred_skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('recruiter_email', sa.String(), nullable=True),
        sa.Column('application_deadline', sa.Date(), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=False),
        sa.Column('original_source_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create application_drafts table
    op.create_table(
        'application_drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_opportunity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_subject', sa.String(), nullable=True),
        sa.Column('email_body', sa.Text(), nullable=True),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('recommended_resume_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recommended_certificate_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('ats_compatibility_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skill_match_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('experience_match_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(), nullable=False, server_default='Draft'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_opportunity_id'], ['job_opportunities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Create application_records table
    op.create_table(
        'application_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('position', sa.String(), nullable=False),
        sa.Column('date_applied', sa.DateTime(), nullable=False),
        sa.Column('email_sent_body', sa.Text(), nullable=False),
        sa.Column('email_subject', sa.String(), nullable=False),
        sa.Column('sent_resume_url', sa.String(), nullable=False),
        sa.Column('sent_certificate_urls', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Create resumes table
    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_url', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('role_tag', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Create certificates table
    op.create_table(
        'certificates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_url', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('certificates')
    op.drop_table('resumes')
    op.drop_table('application_records')
    op.drop_table('application_drafts')
    op.drop_table('job_opportunities')
    op.drop_table('users')
