"""Add ai_categorization_feedback table

Revision ID: 90df7a8434df
Revises: 54d9aaacdc6b
Create Date: 2025-05-09 14:49:22.926013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90df7a8434df'
down_revision: Union[str, None] = '54d9aaacdc6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ai_categorization_feedback',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('note_id', sa.Uuid(), nullable=False),
        sa.Column('note_content_snippet', sa.Text(), nullable=True),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        # Temporarily create as TEXT
        sa.Column('ai_suggested_type', sa.Text(), nullable=True),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        # Temporarily create as TEXT
        sa.Column('user_chosen_type', sa.Text(), nullable=False),
        sa.Column('was_suggestion_correct', sa.Boolean(), nullable=True),
        sa.Column('feedback_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_comment', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['note_id'], ['notes.id'], name=op.f('fk_ai_categorization_feedback_note_id_notes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_categorization_feedback'))
    )
    # Now, alter the columns to use the existing ENUM type with raw SQL
    op.execute("ALTER TABLE ai_categorization_feedback ALTER COLUMN ai_suggested_type TYPE memory_type_enum USING ai_suggested_type::memory_type_enum")
    op.execute("ALTER TABLE ai_categorization_feedback ALTER COLUMN user_chosen_type TYPE memory_type_enum USING user_chosen_type::memory_type_enum")

    # Add indexes (autogenerate should have these)
    op.create_index(op.f('ix_ai_categorization_feedback_ai_suggested_type'), 'ai_categorization_feedback', ['ai_suggested_type'], unique=False)
    # ... other indexes ...
    op.create_index(op.f('ix_ai_categorization_feedback_user_chosen_type'), 'ai_categorization_feedback', ['user_chosen_type'], unique=False)
    op.create_index(op.f('ix_ai_categorization_feedback_note_id'), 'ai_categorization_feedback', ['note_id'], unique=False)
    op.create_index(op.f('ix_ai_categorization_feedback_was_suggestion_correct'), 'ai_categorization_feedback', ['was_suggestion_correct'], unique=False)


def downgrade() -> None:
    # Note: Downgrading type alterations can be complex.
    # For simplicity, just drop the table. A more robust downgrade
    # would alter columns back to TEXT before dropping.
    op.drop_table('ai_categorization_feedback')
