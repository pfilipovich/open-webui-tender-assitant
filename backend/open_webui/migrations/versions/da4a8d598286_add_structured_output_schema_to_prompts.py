"""add structured_output_schema to prompts

Revision ID: da4a8d598286
Revises: 1241780427bd
Create Date: 2025-07-28 18:36:42.631046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = 'da4a8d598286'
down_revision: Union[str, None] = '1241780427bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add structured_output_schema column to prompt table
    op.add_column(
        'prompt',
        sa.Column('structured_output_schema', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    # Remove structured_output_schema column from prompt table
    op.drop_column('prompt', 'structured_output_schema')
