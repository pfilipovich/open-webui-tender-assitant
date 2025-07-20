"""Add checklists tables

Revision ID: add_checklists_001
Revises: ca81bd47c050
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_checklists_001'
down_revision = '9f0c9cd09105'
branch_labels = None
depends_on = None

def upgrade():
    # Create checklist table
    op.create_table('checklist',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('command', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('access_control', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('command')
    )
    
    # Create checklist_item table
    op.create_table('checklist_item',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('checklist_id', sa.String(), nullable=False),
        sa.Column('prompt_command', sa.String(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['checklist_id'], ['checklist.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_checklist_user_id', 'checklist', ['user_id'])
    op.create_index('idx_checklist_command', 'checklist', ['command'])
    op.create_index('idx_checklist_item_checklist_id', 'checklist_item', ['checklist_id'])
    op.create_index('idx_checklist_item_order', 'checklist_item', ['checklist_id', 'order_index'])

def downgrade():
    op.drop_index('idx_checklist_item_order', table_name='checklist_item')
    op.drop_index('idx_checklist_item_checklist_id', table_name='checklist_item')
    op.drop_index('idx_checklist_command', table_name='checklist')
    op.drop_index('idx_checklist_user_id', table_name='checklist')
    op.drop_table('checklist_item')
    op.drop_table('checklist')