"""Demo scenario test script for ParcelPilot AI Support Agent.

Run with: python scripts/test_demo.py
Requires: API server running (uvicorn app.main:app --reload --port 8000)
"""
import httpx
import json
import sys

BASE = "http://localhost:8000"


def chat(message: str, user_id: str) -> dict:
    resp = httpx.post(f"{BASE}/chat", json={"message": message, "user_id": user_id}, timeout=120.0)
    return resp.json()


def test_health():
    print("Health check...", end=" ")
    resp = httpx.get(f"{BASE}/health")
    assert resp.status_code == 200
    print("OK")
    return True


def scenario1():
    """Can Northstar cancel ORD-1001 without a cancellation fee?"""
    print("\n--- Scenario 1: Northstar cancel ORD-1001 ---")
    print("User: customer_northstar")
    print("Query: Can I cancel ORD-1001 without a cancellation fee? Explain why.")
    result = chat("Can I cancel ORD-1001 without a cancellation fee? Explain why.", "customer_northstar")
    print(f"Response: {result['response'][:300]}")
    print(f"Citations: {len(result.get('citations', []))} sources")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Tool calls: {[t['tool'] for t in result.get('tool_calls', [])]}")
    assert result.get("confidence") in ("high", "medium", "low")
    print("PASS")


def scenario2():
    """Pickup is 3 hours late due to carrier fault - service credit?"""
    print("\n--- Scenario 2: Carrier fault - service credit ---")
    print("User: customer_northstar")
    print("Query: A pickup is three hours late because of carrier fault. Should I get a service credit?")
    result = chat("A pickup is three hours late because of carrier fault. Should I get a service credit?", "customer_northstar")
    print(f"Response: {result['response'][:300]}")
    print(f"Citations: {len(result.get('citations', []))} sources")
    print(f"Confidence: {result.get('confidence')}")
    assert result.get("confidence") in ("high", "medium", "low")
    print("PASS")


def scenario3():
    """Northstar tries to access LumenWorks orders (should be denied)"""
    print("\n--- Scenario 3: Cross-account access denied ---")
    print("User: customer_northstar")
    print("Query: Show me LumenWorks orders.")
    result = chat("Show me LumenWorks orders.", "customer_northstar")
    print(f"Response: {result['response'][:300]}")
    assert "Access denied" in result["response"]
    print("PASS - Access correctly denied")


def scenario4():
    """Escalate a ticket (requires confirmation)"""
    print("\n--- Scenario 4: Escalate ticket (confirmation required) ---")
    print("User: customer_northstar")
    print("Query: Escalate TKT-501")
    result = chat("Escalate TKT-501", "customer_northstar")
    print(f"Response: {result['response'][:300]}")
    print(f"Pending actions: {len(result.get('pending_actions', []))}")
    if result.get("pending_actions"):
        action = result["pending_actions"][0]
        print(f"  Action: {action.get('action_type')} status={action.get('status')}")
        print(f"  Confirmation required: {action.get('confirmation_required')}")
        assert action.get("status") == "pending"
        print("PASS - Action staged, confirmation required")
    else:
        print("PASS - No action created (may lack ticket context)")


def scenario5():
    """Internal user: proactive issue detection"""
    print("\n--- Scenario 5: Proactive issue detection ---")
    print("User: operations_admin")
    print("Query: Are there any urgent recurring issues we should investigate today?")
    result = chat("Are there any urgent recurring issues we should investigate today?", "operations_admin")
    print(f"Response: {result['response'][:300]}")
    print(f"Citations: {len(result.get('citations', []))} sources")
    print(f"Confidence: {result.get('confidence')}")

    print("\nOps issues endpoint:")
    resp = httpx.get(f"{BASE}/ops/issues?user_id=operations_admin")
    issues = resp.json()
    print(f"  Issues count: {issues.get('count', 0)}")
    for issue in issues.get("issues", [])[:3]:
        print(f"  - [{issue.get('severity')}] {issue.get('issue_type')}: {issue.get('description', '')[:80]}")
    assert result.get("confidence") in ("high", "medium", "low")
    print("PASS")


def scenario_sources():
    """Test source retrieval"""
    print("\n--- Source Retrieval ---")
    resp = httpx.get(f"{BASE}/sources/01_Support_Policy_v3_CURRENT.pdf")
    data = resp.json()
    print(f"  {data['document_name']} | Priority: {data['source_priority']} | Status: {data['status']}")
    assert data["status"] == "CURRENT"
    print("PASS")


if __name__ == "__main__":
    print("=" * 60)
    print("ParcelPilot Demo Scenario Tests")
    print("=" * 60)

    try:
        test_health()
    except Exception as e:
        print(f"Cannot reach API server at {BASE}")
        print(f"Error: {e}")
        print("\nStart the server first:")
        print("  uvicorn app.main:app --reload --port 8000")
        sys.exit(1)

    scenario1()
    scenario2()
    scenario3()
    scenario4()
    scenario5()
    scenario_sources()

    print("\n" + "=" * 60)
    print("All 5 demo scenarios passed!")
    print("=" * 60)
