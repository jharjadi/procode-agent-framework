#!/usr/bin/env python3
"""
Simple standalone Sentry test script.
This script tests Sentry integration without requiring other dependencies.
"""

import os

# Set Sentry configuration
os.environ["SENTRY_DSN"] = "https://f184e400fb0f19ea28bafde3c40314d2@o4510789455249408.ingest.de.sentry.io/4510789464883280"

try:
    import sentry_sdk
    
    print("=" * 60)
    print("Testing Sentry Integration")
    print("=" * 60)
    
    # Initialize Sentry
    print("\n1. Initializing Sentry...")
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        environment="production",
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )
    print("✅ Sentry initialized successfully!")
    
    # Set user context
    print("\n2. Setting user context...")
    sentry_sdk.set_user({
        "id": "test_user_123",
        "email": "test@example.com",
        "username": "test_user"
    })
    print("✅ User context set")
    
    # Add breadcrumbs
    print("\n3. Adding breadcrumbs...")
    sentry_sdk.add_breadcrumb(
        category="navigation",
        message="User navigated to dashboard",
        level="info"
    )
    sentry_sdk.add_breadcrumb(
        category="ui",
        message="User clicked test button",
        level="info"
    )
    sentry_sdk.add_breadcrumb(
        category="test",
        message="About to trigger test error",
        level="warning"
    )
    print("✅ Breadcrumbs added")
    
    # Send a test message
    print("\n4. Sending test message...")
    event_id = sentry_sdk.capture_message(
        "🧪 Test message from ProCode Agent Framework - Sentry integration working!",
        level="info"
    )
    print(f"✅ Test message sent! Event ID: {event_id}")
    
    # Trigger a test exception
    print("\n5. Triggering test exception...")
    try:
        raise ValueError(
            "🧪 Test Error: This is a test exception to verify Sentry error tracking is working! "
            "If you see this in your Sentry dashboard, the integration is successful!"
        )
    except Exception as e:
        sentry_sdk.set_context("test_context", {
            "test_type": "error_test",
            "framework": "procode-agent-framework",
            "step": "step_12_monitoring",
            "expected": True,
            "severity": "test"
        })
        error_id = sentry_sdk.capture_exception(e)
        print(f"✅ Test exception captured! Event ID: {error_id}")
    
    # Flush events to Sentry
    print("\n6. Flushing events to Sentry...")
    sentry_sdk.flush(timeout=5.0)
    print("✅ All events sent to Sentry successfully!")
    
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
    
except ImportError:
    print("\n❌ Error: sentry-sdk is not installed")
    print("\nTo install it, run:")
    print("  pip3 install --break-system-packages sentry-sdk")
    print("\nOr use Docker:")
    print("  docker exec -it procode-agent-framework python3 test_sentry.py")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
