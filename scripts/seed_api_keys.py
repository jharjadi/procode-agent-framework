#!/usr/bin/env python3
"""
Seed script for API key authentication system.
Creates default organization and test API key.
"""
import sys
import os
import secrets
import hashlib
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.connection import get_database_url


def generate_api_key(environment='test'):
    """Generate a secure API key."""
    # Generate cryptographically secure random token
    token = secrets.token_urlsafe(32)  # 32 bytes = 43 chars base64
    
    # Create key with prefix
    prefix = f"pk_{environment}_"
    full_key = f"{prefix}{token}"
    
    # Hash for storage (never store plaintext)
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    # Get hint (last 4 chars)
    key_hint = token[-4:]
    
    return {
        'full_key': full_key,
        'key_hash': key_hash,
        'key_hint': key_hint,
        'key_prefix': prefix
    }


def seed_api_keys():
    """Seed default organization and API key."""
    print("🌱 Seeding API key authentication data...")
    
    # Get database connection
    database_url = get_database_url()
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if default organization already exists
        result = session.execute(
            text("SELECT id FROM organizations WHERE slug = 'default'")
        ).fetchone()
        
        if result:
            print("⚠️  Default organization already exists. Skipping seed.")
            org_id = result[0]
        else:
            # Create default organization (PostgreSQL will generate UUID)
            print("📦 Creating default organization...")
            result = session.execute(
                text("""
                    INSERT INTO organizations (name, slug, email, plan, monthly_request_limit, rate_limit_per_minute, max_api_keys)
                    VALUES (:name, :slug, :email, :plan, :monthly_limit, :rate_limit, :max_keys)
                    RETURNING id
                """),
                {
                    'name': 'Default Organization',
                    'slug': 'default',
                    'email': 'admin@procode.local',
                    'plan': 'free',
                    'monthly_limit': 10000,
                    'rate_limit': 60,
                    'max_keys': 10
                }
            )
            org_id = result.fetchone()[0]
            session.commit()
            print(f"✅ Created organization: default (ID: {org_id})")
        
        # Generate test API key
        print("🔑 Generating test API key...")
        key_data = generate_api_key(environment='test')
        
        # Check if test key already exists
        result = session.execute(
            text("SELECT id FROM api_keys WHERE organization_id = :org_id AND environment = 'test'"),
            {'org_id': org_id}
        ).fetchone()
        
        if result:
            print("⚠️  Test API key already exists. Skipping key generation.")
            # Get existing key hint
            result = session.execute(
                text("SELECT key_hint FROM api_keys WHERE organization_id = :org_id AND environment = 'test'"),
                {'org_id': org_id}
            ).fetchone()
            key_hint = result[0]
            print(f"\n{'='*60}")
            print(f"ℹ️  Existing Test API Key (last 4 chars): ...{key_hint}")
            print(f"{'='*60}\n")
        else:
            # Insert API key (PostgreSQL will generate UUID)
            session.execute(
                text("""
                    INSERT INTO api_keys (
                        organization_id, key_prefix, key_hash, key_hint,
                        name, environment, scopes
                    )
                    VALUES (
                        :org_id, :key_prefix, :key_hash, :key_hint,
                        :name, :environment, :scopes::jsonb
                    )
                """),
                {
                    'org_id': org_id,
                    'key_prefix': key_data['key_prefix'],
                    'key_hash': key_data['key_hash'],
                    'key_hint': key_data['key_hint'],
                    'name': 'Default Test Key',
                    'environment': 'test',
                    'scopes': '["*"]'
                }
            )
            session.commit()
            
            print(f"✅ Created test API key")
            print(f"\n{'='*60}")
            print(f"🔑 TEST API KEY (save this, it won't be shown again):")
            print(f"\n{key_data['full_key']}\n")
            print(f"{'='*60}")
            print(f"\n📝 Usage example:")
            print(f"curl -H 'Authorization: Bearer {key_data['full_key']}' \\")
            print(f"     http://localhost:8000/chat")
            print(f"\n{'='*60}\n")
        
        # Display summary
        print("\n📊 Summary:")
        org_count = session.execute(text("SELECT COUNT(*) FROM organizations")).scalar()
        key_count = session.execute(text("SELECT COUNT(*) FROM api_keys")).scalar()
        print(f"  Organizations: {org_count}")
        print(f"  API Keys: {key_count}")
        
        print("\n✅ Seed completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error seeding data: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    seed_api_keys()
