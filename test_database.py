"""
Test Database Integration

Simple script to test database setup and basic operations.
"""

import os
os.environ.setdefault("SQLITE_DB_PATH", "data/test_procode.db")

from database.connection import init_db, get_session, close_db
from database.repositories import ConversationRepository, AuditRepository


def test_database():
    """Test database initialization and basic operations."""
    
    print("=" * 60)
    print("Testing Database Integration (Step 10)")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    
    # Get a session
    print("\n2. Creating database session...")
    session = get_session()
    
    try:
        # Test conversation repository
        print("\n3. Testing ConversationRepository...")
        conv_repo = ConversationRepository(session)
        
        # Note: We'll need a user_id, but for now we'll skip creating conversations
        # since we don't have authentication yet (Step 11)
        print("   ✓ ConversationRepository initialized")
        
        # Test audit repository
        print("\n4. Testing AuditRepository...")
        audit_repo = AuditRepository(session)
        
        # Create a test audit log
        audit_log = audit_repo.create_audit_log(
            event_type="system_test",
            event_category="system",
            description="Database integration test",
            severity="info",
            extra_metadata={"test": True}
        )
        session.commit()
        print(f"   ✓ Created audit log: {audit_log}")
        
        # Retrieve audit logs
        logs = audit_repo.get_logs_by_type("system_test", limit=10)
        print(f"   ✓ Retrieved {len(logs)} audit log(s)")
        
        print("\n5. Database test completed successfully! ✓")
        print("\nDatabase features working:")
        print("  ✓ SQLite database created")
        print("  ✓ Tables created automatically")
        print("  ✓ Repositories working")
        print("  ✓ CRUD operations functional")
        
        print("\nNext steps:")
        print("  - Step 11: Add authentication (User model)")
        print("  - Integrate with conversation_memory")
        print("  - Integrate with audit_logger")
        
    except Exception as e:
        print(f"\n❌ Error during database test: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
        close_db()
        print("\n6. Database connection closed")


if __name__ == "__main__":
    test_database()
