"""add price_cut to products

Revision ID: 20260831_01
Revises: 20260830_01
Create Date: 2026-08-31 22:42:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260831_01'
down_revision = '20260830_01'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('products', sa.Column('price_cut', sa.Numeric(10, 2), nullable=True))

def downgrade():
    op.drop_column('products', 'price_cut')