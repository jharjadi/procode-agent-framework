"""
Database Integration Demo
Demonstrates all database features working together.
"""

from database.connection import init_db, get_db
from database.repositories.conversation_repository import ConversationRepository
from database.repositories.audit_repository import AuditRepository
from core.conversation_memory import ConversationMemory
from security.audit_logger import AuditLogger

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def demo_repositories():
    """Demo: Direct repository usage."""
    print_section("1. Testing Repositories Directly")
    
    # Initialize database
    init_db()
    db = next(get_db())
    
    # Create repositories
    conv_repo = ConversationRepository(db)
    audit_repo = AuditRepository(db)
    
    # Create a test user first (needed for foreign key)
    from database.models import User
    print("\n👤 Creating a test user...")
    test_user = User(
        email="demo@example.com",
        username="demo_user",
        hashed_password="hashed_password_here",  # In Step 11, this will be properly hashed
        role="user"
    )
    db.add(test_user)
    db.commit()
    print(f"✓ Created user: {test_user.id} ({test_user.username})")
    
    print("\n📝 Creating a conversation...")
    conversation = conv_repo.create_conversation(
        user_id=1,
        title="Demo Conversation",
        intent="demo"
    )
    print(f"✓ Created conversation: {conversation.id}")
    print(f"  - Title: {conversation.title}")
    print(f"  - Intent: {conversation.intent}")
    print(f"  - Status: {conversation.status}")
    
    print("\n💬 Adding messages to conversation...")
    msg1 = conv_repo.add_message(
        conversation_id=conversation.id,
        role="user",
        content="Hello! Can you help me?",
        intent="greeting",
        model_used="gpt-4",
        cost=0.001
    )
    print(f"✓ Added user message: {msg1.id}")
    
    msg2 = conv_repo.add_message(
        conversation_id=conversation.id,
        role="assistant",
        content="Of course! I'm here to help. What do you need?",
        intent="greeting",
        model_used="gpt-4",
        cost=0.002
    )
    print(f"✓ Added assistant message: {msg2.id}")
    
    msg3 = conv_repo.add_message(
        conversation_id=conversation.id,
        role="user",
        content="I need to create a support ticket",
        intent="support",
        model_used="gemini-flash",
        cost=0.0001
    )
    print(f"✓ Added user message: {msg3.id}")
    
    print("\n📊 Retrieving conversation messages...")
    messages = conv_repo.get_conversation_messages(conversation.id)
    print(f"✓ Retrieved {len(messages)} messages:")
    for msg in messages:
        print(f"  - [{msg.role}] {msg.content[:50]}... (cost: ${msg.cost})")
    
    print("\n💰 Calculating conversation cost...")
    total_cost = conv_repo.get_conversation_cost(conversation.id)
    print(f"✓ Total conversation cost: ${total_cost}")
    
    print("\n📋 Creating audit logs...")
    audit1 = audit_repo.create_audit_log(
        user_id=1,
        event_type="conversation_started",
        event_category="system",
        severity="info",
        description="User started a new conversation",
        extra_metadata={"conversation_id": conversation.id}
    )
    print(f"✓ Created audit log: {audit1.id}")
    
    audit2 = audit_repo.create_audit_log(
        user_id=1,
        event_type="blocked_content",
        event_category="security",
        severity="warning",
        description="PII detected in user input",
        extra_metadata={"pii_types": ["email", "phone"]}
    )
    print(f"✓ Created audit log: {audit2.id}")
    
    print("\n🔍 Querying audit logs...")
    user_logs = audit_repo.get_user_audit_logs(user_id=1, limit=10)
    print(f"✓ Retrieved {len(user_logs)} audit logs for user 1:")
    for log in user_logs:
        print(f"  - [{log.severity}] {log.event_type}: {log.description[:50]}...")
    
    security_logs = audit_repo.get_logs_by_type("blocked_content")
    print(f"\n✓ Retrieved {len(security_logs)} security logs:")
    for log in security_logs:
        print(f"  - [{log.severity}] {log.event_category}: {log.description}")
    
    db.close()
    print("\n✓ Database session closed")

def demo_conversation_memory():
    """Demo: ConversationMemory with database persistence."""
    print_section("2. Testing ConversationMemory with Database")
    
    print("\n🧠 Creating ConversationMemory with database enabled...")
    memory = ConversationMemory(use_database=True)
    print(f"✓ Database persistence: {memory.use_database}")
    
    conv_id = "demo_conv_123"
    
    print(f"\n💬 Adding messages to conversation '{conv_id}'...")
    memory.add_message(
        conversation_id=conv_id,
        role="user",
        content="What's the weather like?",
        user_id=1,
        intent="weather",
        model_used="gemini-flash",
        cost=0.0001
    )
    print("✓ Added user message (persisted to DB)")
    
    memory.add_message(
        conversation_id=conv_id,
        role="assistant",
        content="I don't have access to real-time weather data, but I can help you with other tasks!",
        user_id=1,
        intent="weather",
        model_used="gpt-4",
        cost=0.003
    )
    print("✓ Added assistant message (persisted to DB)")
    
    print("\n📖 Retrieving conversation history from memory...")
    history = memory.get_history(conv_id)
    print(f"✓ Retrieved {len(history)} messages from cache:")
    for msg in history:
        print(f"  - [{msg['role']}] {msg['content'][:50]}...")
    
    print("\n🔄 Loading conversation from database...")
    db_history = memory.get_history(conv_id, from_database=True)
    print(f"✓ Retrieved {len(db_history)} messages from database:")
    for msg in db_history:
        print(f"  - [{msg['role']}] {msg['content'][:50]}... (model: {msg['model_used']}, cost: ${msg['cost']})")
    
    print("\n📊 Getting conversation summary...")
    summary = memory.get_context_summary(conv_id)
    print(f"✓ Summary:\n{summary}")

def demo_audit_logger():
    """Demo: AuditLogger with database persistence."""
    print_section("3. Testing AuditLogger with Database")
    
    print("\n📝 Creating AuditLogger with database enabled...")
    logger = AuditLogger(use_database=True)
    print(f"✓ Database persistence: {logger.use_database}")
    
    print("\n🔒 Logging security events...")
    logger.log_blocked_content(
        content="My email is user@example.com and phone is 555-1234",
        user_id="1"
    )
    print("✓ Logged blocked content (file + database)")
    
    logger.log_pii_detection(
        pii_types=["email", "phone"],
        user_id="1"
    )
    print("✓ Logged PII detection (file + database)")
    
    logger.log_tool_execution(
        tool_name="create_ticket",
        parameters={"title": "Demo ticket", "priority": "high"},
        result="Ticket created successfully",
        user_id="1",
        success=True
    )
    print("✓ Logged tool execution (file + database)")
    
    logger.log_authentication(
        user_id="1",
        success=True,
        method="api_key"
    )
    print("✓ Logged authentication (file + database)")
    
    print("\n📊 Getting audit log statistics...")
    stats = logger.get_stats()
    print(f"✓ Audit log stats:")
    print(f"  - Total events: {stats['total_events']}")
    print(f"  - Log file: {stats['log_file']}")
    if 'severity_counts' in stats:
        print(f"  - Severity breakdown: {stats['severity_counts']}")

def demo_database_queries():
    """Demo: Advanced database queries."""
    print_section("4. Advanced Database Queries")
    
    init_db()
    db = next(get_db())
    
    conv_repo = ConversationRepository(db)
    
    print("\n🔍 Searching conversations...")
    conversations = conv_repo.get_user_conversations(user_id=1, limit=10)
    print(f"✓ Found {len(conversations)} conversations for user 1:")
    for conv in conversations:
        print(f"  - {conv.title} (intent: {conv.intent}, status: {conv.status})")
        print(f"    Created: {conv.created_at}, Updated: {conv.updated_at}")
    
    if conversations:
        print(f"\n💰 Calculating costs for each conversation...")
        for conv in conversations:
            cost = conv_repo.get_conversation_cost(conv.id)
            print(f"  - {conv.title}: ${cost}")
    
    db.close()
    print("\n✓ Database session closed")

def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("  DATABASE INTEGRATION DEMO")
    print("  Demonstrating Step 10 Features")
    print("="*60)
    
    try:
        # Run all demos
        demo_repositories()
        demo_conversation_memory()
        demo_audit_logger()
        demo_database_queries()
        
        print("\n" + "="*60)
        print("  ✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nDatabase features demonstrated:")
        print("  ✓ SQLite database creation")
        print("  ✓ Repository pattern (Conversation, Audit)")
        print("  ✓ CRUD operations (Create, Read, Update)")
        print("  ✓ ConversationMemory with database persistence")
        print("  ✓ AuditLogger with dual logging (file + database)")
        print("  ✓ Cost tracking per message")
        print("  ✓ Advanced queries and filtering")
        print("\nNext: Step 11 - Authentication & Authorization")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
