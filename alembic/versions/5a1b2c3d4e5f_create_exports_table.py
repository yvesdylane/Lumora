"""create exports table

Revision ID: 5a1b2c3d4e5f
Revises: 3c91014b04a1
Create Date: 2026-07-30 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '3c91014b04a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('exports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('timeline_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('output_format', sa.String(length=10), nullable=False, server_default='mp4'),
        sa.Column('b2_key', sa.String(length=1023), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['timeline_id'], ['timelines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_exports_project_id'), 'exports', ['project_id'], unique=False)
    op.create_index(op.f('ix_exports_timeline_id'), 'exports', ['timeline_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_exports_timeline_id'), table_name='exports')
    op.drop_index(op.f('ix_exports_project_id'), table_name='exports')
    op.drop_table('exports')
