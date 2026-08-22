import ast
import os

os.chdir(os.path.join(os.path.dirname(__file__), ".."))

P, F = 0, 0

def ok(name, condition):
    global P, F
    if condition:
        P += 1
        print("  PASS  " + name)
    else:
        F += 1
        print("  FAIL  " + name)

print("=" * 60)
print("DASHBOARD + OBSERVABILITY VALIDATION")
print("=" * 60)

print("\n--- Dashboard (Streamlit) ---")
with open("frontend/app.py") as f:
    content = f.read()

tree = ast.parse(content)
st_features = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Attribute):
        if node.attr in ("set_page_config", "chat_input", "chat_message", "selectbox",
                         "session_state", "spinner", "expander", "button", "sidebar",
                         "markdown", "caption", "warning", "error", "success", "info", "rerun"):
            st_features.add(node.attr)

ok("set_page_config", "set_page_config" in st_features)
ok("chat_input", "chat_input" in st_features)
ok("chat_message", "chat_message" in st_features)
ok("selectbox", "selectbox" in st_features)
ok("session_state", "session_state" in st_features)
ok("spinner", "spinner" in st_features)
ok("expander", "expander" in st_features)
ok("button", "button" in st_features)
ok("rerun", "rerun" in st_features)

ok("User selector (4 users)", "customer_northstar" in content and "customer_lumenworks" in content)
ok("Clear Chat button", "Clear Chat" in content)
ok("Check Health button", "Check Health" in content)
ok("View Open Issues", "View Open Issues" in content)
ok("Citations display", "citations" in content)
ok("Tool calls display", "tool_calls" in content)
ok("Conflicts display", "conflicts" in content)
ok("Confidence display", "confidence" in content)
ok("Pending actions display", "pending_actions" in content)
ok("Confirm action button", "Confirm" in content and "confirm_" in content)
ok("Error handling", "except" in content)
ok("API connection", "requests.post" in content and "requests.get" in content)
ok("API URL configured", "API_URL" in content)
ok("Internal-only check", "internal" in content.lower())

print("\n--- Observability (Logging) ---")
with open("app/main.py") as f:
    main = f.read()
with open("app/api/routes.py") as f:
    routes = f.read()
with open("app/agent/graph.py") as f:
    graph = f.read()

ok("main: logging.basicConfig", "logging.basicConfig" in main)
ok("main: logger name parcelpilot", 'logging.getLogger("parcelpilot")' in main)
ok("main: startup log", "Starting ParcelPilot" in main)
ok("main: shutdown log", "shutting down" in main)
ok("main: model logged", "model=" in main)
ok("routes: request_id tracking", "request_id" in routes)
ok("routes: latency logged", "latency=" in routes)
ok("routes: audit log written", "AuditLog" in routes)
ok("routes: error logged", "logger.error" in routes)
ok("routes: confidence logged", "confidence=" in routes)
ok("routes: tools count logged", "tools=" in routes)
ok("agent: logger exists", "logger" in graph)
ok("agent: latency tracked", "latency" in graph)
ok("agent: query logged", "agent query" in graph)
ok("agent: LLM latency logged", "LLM call ok" in graph)

print("\n" + "=" * 60)
print("RESULTS: %d passed, %d failed, %d total" % (P, F, P + F))
print("=" * 60)
