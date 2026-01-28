"""
Test script to send a test error to Sentry.

This script initializes Sentry and sends a test error to verify the integration is working.
"""

import os

# Set Sentry DSN directly if not in environment
if not os.getenv("SENTRY_DSN"):
    os.environ["SENTRY_DSN"] = "https://f184e400fb0f19ea28bafde3c40314d2@o4510789455249408.ingest.de.sentry.io/4510789464883280"
    os.environ["ENABLE_SENTRY"] = "true"
    os.environ["SENTRY_ENVIRONMENT"] = "production"

# Import Sentry integration
from observability.sentry_integration import (
    init_sentry,
    capture_exception,
    capture_message,
    set_user_context,
    add_breadcrumb,
    flush
)

def test_sentry_integration():
    """Test Sentry integration by sending test events."""
    
    print("=" * 60)
    print("Testing Sentry Integration")
    print("=" * 60)
    
    # Initialize Sentry
    print("\n1. Initializing Sentry...")
    if init_sentry():
        print("✅ Sentry initialized successfully!")
    else:
        print("❌ Sentry initialization failed. Check your SENTRY_DSN.")
        return
    
    # Set user context
    print("\n2. Setting user context...")
    set_user_context(
        user_id="test_user_123",
        email="test@example.com",
        username="test_user",
        organization="ProCode Test Org"
    )
    print("✅ User context set")
    
    # Add breadcrumbs
    print("\n3. Adding breadcrumbs...")
    add_breadcrumb("User navigated to dashboard", category="navigation", level="info")
    add_breadcrumb("User clicked test button", category="ui", level="info")
    add_breadcrumb("About to trigger test error", category="test", level="warning")
    print("✅ Breadcrumbs added")
    
    # Send a test message
    print("\n4. Sending test message...")
    message_id = capture_message(
        "🧪 Test message from ProCode Agent Framework - Sentry integration working!",
        level="info",
        context={
            "test_type": "integration_test",
            "framework": "procode-agent-framework",
            "step": "step_12_monitoring"
        }
    )
    if message_id:
        print(f"✅ Test message sent! Event ID: {message_id}")
    else:
        print("⚠️  Message not sent (Sentry might be disabled)")
    
    # Trigger a test exception
    print("\n5. Triggering test exception...")
    try:
        # This will create a test error
        raise ValueError(
            "🧪 Test Error: This is a test exception to verify Sentry error tracking is working! "
            "If you see this in your Sentry dashboard, the integration is successful!"
        )
    except Exception as e:
        error_id = capture_exception(
            e,
            context={
                "test_type": "error_test",
                "framework": "procode-agent-framework",
                "step": "step_12_monitoring",
                "expected": True,
                "severity": "test"
            },
            level="error"
        )
        if error_id:
            print(f"✅ Test exception captured! Event ID: {error_id}")
        else:
            print("⚠️  Exception not captured (Sentry might be disabled)")
    
    # Flush events to Sentry
    print("\n6. Flushing events to Sentry...")
    if flush(timeout=5.0):
        print("✅ All events sent to Sentry successfully!")
    else:
        print("⚠️  Some events may not have been sent")
    
    print("\n" + "=" * 60)
    print("✅ Sentry Test Complete!")
    print("=" * 60)
    print("\n📊 Check your Sentry dashboard at:")
    print("   https://sentry.io/organizations/o4510789455249408/")
    print("\nYou should see:")
    print("  1. A test message (info level)")
    print("  2. A test error (ValueError)")
    print("  3. User context (test_user_123)")
    print("  4. Breadcrumbs showing the test flow")
    print("  5. Additional context data")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_sentry_integration()
