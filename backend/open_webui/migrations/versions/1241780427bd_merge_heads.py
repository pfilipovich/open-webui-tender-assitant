"""merge heads

Revision ID: 1241780427bd
Revises: add_checklists_001, add_structured_output_to_prompts
Create Date: 2025-07-28 18:31:48.204380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '1241780427bd'
down_revision: Union[str, None] = ('add_checklists_001', 'add_structured_output_to_prompts')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
