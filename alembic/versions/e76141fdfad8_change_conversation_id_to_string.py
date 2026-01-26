"""change_conversation_id_to_string

Revision ID: e76141fdfad8
Revises: 5c6758e838d3
Create Date: 2026-01-26 19:30:28.639370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e76141fdfad8'
down_revision: Union[str, Sequence[str], None] = '5c6758e838d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Change conversation.id from INTEGER to VARCHAR(255) to support UUIDs."""
    # Get the database connection to check dialect
    conn = op.get_bind()
    
    # Skip for SQLite (local development) - SQLite doesn't support ALTER CONSTRAINT
    # For SQLite, the model changes will take effect on next table creation
    if conn.dialect.name == 'sqlite':
        print("Skipping migration for SQLite - model changes will apply on next table creation")
        return
    
    # PostgreSQL-specific migration
    # Step 1: Drop foreign key constraint from messages table
    op.drop_constraint('messages_conversation_id_fkey', 'messages', type_='foreignkey')
    
    # Step 2: Change conversation_id in messages table to VARCHAR
    op.alter_column('messages', 'conversation_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(255),
                    existing_nullable=False,
                    postgresql_using='conversation_id::varchar')
    
    # Step 3: Change id in conversations table to VARCHAR
    op.alter_column('conversations', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.String(255),
                    existing_nullable=False,
                    autoincrement=False,
                    postgresql_using='id::varchar')
    
    # Step 4: Recreate foreign key constraint
    op.create_foreign_key('messages_conversation_id_fkey', 'messages', 'conversations',
                          ['conversation_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema: Change conversation.id back from VARCHAR to INTEGER."""
    # Step 1: Drop foreign key constraint
    op.drop_constraint('messages_conversation_id_fkey', 'messages', type_='foreignkey')
    
    # Step 2: Change conversation_id in messages back to INTEGER
    op.alter_column('messages', 'conversation_id',
                    existing_type=sa.String(255),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='conversation_id::integer')
    
    # Step 3: Change id in conversations back to INTEGER
    op.alter_column('conversations', 'id',
                    existing_type=sa.String(255),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    autoincrement=True,
                    postgresql_using='id::integer')
    
    # Step 4: Recreate foreign key constraint
    op.create_foreign_key('messages_conversation_id_fkey', 'messages', 'conversations',
                          ['conversation_id'], ['id'])
