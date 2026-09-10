"""initial

Revision ID: 20260830_01
Revises: 
Create Date: 2026-08-30 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260830_01'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
    )

    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('article', sa.String(length=255), nullable=False, index=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.UniqueConstraint('company_id', 'article', name='uq_company_article'),
    )

def downgrade():
    op.drop_table('products')
    op.drop_table('companies')
    