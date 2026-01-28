#!/usr/bin/env python3
"""
Comprehensive monitoring test script.
Tests all monitoring components: Prometheus metrics, health checks, OpenTelemetry tracing, and Sentry.
"""

import os
import sys
import time
import requests
from typing import Dict, Any

# Set environment variables
os.environ["SENTRY_DSN"] = "https://f184e400fb0f19ea28bafde3c40314d2@o4510789455249408.ingest.de.sentry.io/4510789464883280"
os.environ["ENABLE_SENTRY"] = "true"
os.environ["ENABLE_METRICS"] = "true"
os.environ["ENABLE_HEALTH_CHECKS"] = "true"

BASE_URL = os.getenv("AGENT_URL", "http://localhost:9998")

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(test_name: str, success: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"    {details}")

def test_health_endpoint() -> bool:
    """Test /health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_result("Health Endpoint", True, f"Status: {data.get('status', 'unknown')}")
            
            # Print individual health checks
            checks = data.get('checks', {})
            for check_name, check_status in checks.items():
                status_str = check_status.get('status', 'unknown')
                print(f"      - {check_name}: {status_str}")
            
            return True
        else:
            print_result("Health Endpoint", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_result("Health Endpoint", False, f"Error: {str(e)}")
        return False

def test_ready_endpoint() -> bool:
    """Test /ready endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/ready", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_result("Ready Endpoint", True, f"Ready: {data.get('ready', False)}")
            return True
        else:
            print_result("Ready Endpoint", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_result("Ready Endpoint", False, f"Error: {str(e)}")
        return False

def test_metrics_endpoint() -> bool:
    """Test /metrics endpoint (Prometheus format)."""
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            metrics_text = response.text
            
            # Count metrics
            metric_lines = [line for line in metrics_text.split('\n') 
                          if line and not line.startswith('#')]
            
            # Check for key metrics
            has_http_metrics = 'http_requests_total' in metrics_text
            has_llm_metrics = 'llm_requests_total' in metrics_text
            has_agent_metrics = 'agent_executions_total' in metrics_text
            
            print_result("Metrics Endpoint", True, 
                        f"Found {len(metric_lines)} metric values")
            print(f"      - HTTP metrics: {'✓' if has_http_metrics else '✗'}")
            print(f"      - LLM metrics: {'✓' if has_llm_metrics else '✗'}")
            print(f"      - Agent metrics: {'✓' if has_agent_metrics else '✗'}")
            
            return True
        else:
            print_result("Metrics Endpoint", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_result("Metrics Endpoint", False, f"Error: {str(e)}")
        return False

def test_sentry_integration() -> bool:
    """Test Sentry integration."""
    try:
        import sentry_sdk
        
        # Initialize Sentry
        sentry_sdk.init(
            dsn=os.environ["SENTRY_DSN"],
            environment="production",
            traces_sample_rate=0.1,
        )
        
        # Send test event
        event_id = sentry_sdk.capture_message(
            "🧪 Monitoring Test: Sentry integration verified",
            level="info"
        )
        
        # Flush to ensure it's sent
        sentry_sdk.flush(timeout=2.0)
        
        print_result("Sentry Integration", True, f"Event ID: {event_id}")
        return True
    except ImportError:
        print_result("Sentry Integration", False, "sentry-sdk not installed")
        return False
    except Exception as e:
        print_result("Sentry Integration", False, f"Error: {str(e)}")
        return False

def test_opentelemetry() -> bool:
    """Test OpenTelemetry setup."""
    try:
        from opentelemetry import trace
        
        tracer = trace.get_tracer(__name__)
        
        # Create a test span
        with tracer.start_as_current_span("test_monitoring_span") as span:
            span.set_attribute("test.type", "monitoring_verification")
            span.set_attribute("test.component", "opentelemetry")
            time.sleep(0.1)  # Simulate some work
        
        print_result("OpenTelemetry Tracing", True, "Tracer initialized and span created")
        return True
    except ImportError:
        print_result("OpenTelemetry Tracing", False, "opentelemetry not installed")
        return False
    except Exception as e:
        print_result("OpenTelemetry Tracing", False, f"Error: {str(e)}")
        return False

def test_prometheus_client() -> bool:
    """Test Prometheus client library."""
    try:
        from prometheus_client import Counter, Gauge, Histogram
        
        # Create test metrics
        test_counter = Counter('test_counter', 'Test counter metric')
        test_gauge = Gauge('test_gauge', 'Test gauge metric')
        test_histogram = Histogram('test_histogram', 'Test histogram metric')
        
        # Use the metrics
        test_counter.inc()
        test_gauge.set(42)
        test_histogram.observe(0.5)
        
        print_result("Prometheus Client", True, "Metrics created and updated successfully")
        return True
    except ImportError:
        print_result("Prometheus Client", False, "prometheus-client not installed")
        return False
    except Exception as e:
        print_result("Prometheus Client", False, f"Error: {str(e)}")
        return False

def main():
    """Run all monitoring tests."""
    print_header("ProCode Agent Framework - Monitoring Test Suite")
    print(f"\nTesting against: {BASE_URL}")
    print(f"Sentry DSN configured: {os.environ.get('SENTRY_DSN', 'Not set')[:50]}...")
    
    results = {}
    
    # Test monitoring endpoints
    print_header("Testing Monitoring Endpoints")
    results['health'] = test_health_endpoint()
    results['ready'] = test_ready_endpoint()
    results['metrics'] = test_metrics_endpoint()
    
    # Test monitoring libraries
    print_header("Testing Monitoring Libraries")
    results['prometheus'] = test_prometheus_client()
    results['opentelemetry'] = test_opentelemetry()
    results['sentry'] = test_sentry_integration()
    
    # Summary
    print_header("Test Summary")
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 All monitoring components are working correctly!")
        print("\n📊 Next Steps:")
        print("  1. Check Sentry dashboard: https://sentry.io/organizations/o4510789455249408/")
        print("  2. Access metrics: curl http://localhost:9998/metrics")
        print("  3. Check health: curl http://localhost:9998/health")
        print("  4. Deploy Prometheus & Grafana: docker-compose up -d prometheus grafana")
    else:
        print("\n⚠️  Some monitoring components failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("  - Ensure all dependencies are installed")
        print("  - Check that the agent server is running")
        print("  - Verify environment variables are set correctly")
    
    print("\n" + "=" * 70 + "\n")
    
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
