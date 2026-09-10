"""add price_cut to products

Revision ID: 20260903_01
Revises: 20260831_01
Create Date: 2026-09-03 22:42:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260903_01'
down_revision = '20260831_01'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('products', sa.Column('article_internal', sa.String(length=255), nullable=True, index=True))

def downgrade():
    op.drop_column('products', 'article_internal')