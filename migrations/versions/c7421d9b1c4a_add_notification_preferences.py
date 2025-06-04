"""add notification preferences

Revision ID: c7421d9b1c4a
Revises: ba4305683d06
Create Date: 2025-06-04 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = 'c7421d9b1c4a'
down_revision = 'ba4305683d06'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notify_invites', sa.Boolean(), nullable=True, server_default=sa.text('true')))
        batch_op.add_column(sa.Column('notify_residents', sa.Boolean(), nullable=True, server_default=sa.text('true')))
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('viewed', sa.Boolean(), nullable=True, server_default=sa.text('false')))


def downgrade():
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_column('viewed')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('notify_residents')
        batch_op.drop_column('notify_invites')
