"""add resident blocking

Revision ID: d10f1eacb4d2
Revises: c7421d9b1c4a
Create Date: 2025-06-05 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'd10f1eacb4d2'
down_revision = 'c7421d9b1c4a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user_addresses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_blocked', sa.Boolean(), nullable=True, server_default=sa.text('false')))


def downgrade():
    with op.batch_alter_table('user_addresses', schema=None) as batch_op:
        batch_op.drop_column('is_blocked')
