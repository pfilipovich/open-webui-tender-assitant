"""Add structured_output to prompts

Revision ID: add_structured_output_to_prompts
Revises: ca81bd47c050
Create Date: 2025-01-21 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "add_structured_output_to_prompts"
down_revision = "ca81bd47c050"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'structured_output' column to 'prompt' table
    op.add_column(
        "prompt",
        sa.Column(
            "structured_output",
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.expression.false(),
        ),
    )


def downgrade():
    # Drop 'structured_output' column from 'prompt' table
    op.drop_column("prompt", "structured_output")