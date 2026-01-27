"""add_api_key_authentication

Revision ID: 083cef45dd3e
Revises: e76141fdfad8
Create Date: 2026-01-27 14:44:14.183842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '083cef45dd3e'
down_revision: Union[str, Sequence[str], None] = 'e76141fdfad8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('plan', sa.String(50), nullable=False, server_default='free'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('monthly_request_limit', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('max_api_keys', sa.Integer(), nullable=False, server_default='5'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index('idx_organizations_slug', 'organizations', ['slug'])
    op.create_index('idx_organizations_email', 'organizations', ['email'])
    
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False),
        sa.Column('key_hint', sa.String(10), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('environment', sa.String(20), nullable=False, server_default='production'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_used_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('revoked_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('revoked_by', sa.UUID(), nullable=True),
        sa.Column('revoked_reason', sa.Text(), nullable=True),
        sa.Column('scopes', sa.JSON(), nullable=False, server_default='["*"]'),
        sa.Column('custom_rate_limit', sa.Integer(), nullable=True),
        sa.Column('total_requests', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('last_request_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index('idx_api_keys_org', 'api_keys', ['organization_id'])
    op.create_index('idx_api_keys_hash', 'api_keys', ['key_hash'])
    op.create_index('idx_api_keys_prefix', 'api_keys', ['key_prefix'])
    op.create_index('idx_api_keys_active', 'api_keys', ['is_active'], postgresql_where=sa.text('is_active = true'))
    
    # Create api_key_usage table
    op.create_table(
        'api_key_usage',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('api_key_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Numeric(10, 6), nullable=False, server_default='0'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE')
    )
    op.create_index('idx_usage_api_key', 'api_key_usage', ['api_key_id', 'timestamp'])
    op.create_index('idx_usage_org', 'api_key_usage', ['organization_id', 'timestamp'])
    op.create_index('idx_usage_timestamp', 'api_key_usage', ['timestamp'])
    
    # Create rate_limit_tracking table (for development, use Redis in production)
    op.create_table(
        'rate_limit_tracking',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('api_key_id', sa.UUID(), nullable=False),
        sa.Column('window_start', sa.TIMESTAMP(), nullable=False),
        sa.Column('window_end', sa.TIMESTAMP(), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE')
    )
    op.create_index('idx_rate_limit_key_window', 'rate_limit_tracking', ['api_key_id', 'window_start'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('rate_limit_tracking')
    op.drop_table('api_key_usage')
    op.drop_table('api_keys')
    op.drop_table('organizations')
