"""upload_history

Revision ID: 20260915_01
Revises: 20260910_01
Create Date: 2026-09-15 20:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '20260915_01'
down_revision = '20260910_01'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'upload_history',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('rows_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('removed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('removed_articles_json', sa.Text(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('upload_history')