"""Test LLM connection and diagnose issues."""
import httpx
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings


def test_api_key():
    settings = get_settings()
    print(f"Provider: {settings.llm_provider}")
    print(f"Model: {settings.llm_model}")
    print(f"Base URL: {settings.openrouter_base_url}")
    print(f"API Key: {settings.openrouter_api_key[:12]}...{settings.openrouter_api_key[-4:]}")
    print()

    if not settings.openrouter_api_key:
        print("ERROR: No API key configured in .env")
        return False
    return True


def test_connection():
    settings = get_settings()
    url = f"{settings.openrouter_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": "Say 'hello' in one word."}],
        "max_tokens": 10,
        "temperature": 0,
    }

    print("Sending test request...")
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"Response: {content}")
            return True
        elif response.status_code == 429:
            retry_after = response.headers.get("retry-after", "unknown")
            print(f"RATE LIMITED - Retry after: {retry_after}s")
            print("Response:", response.text[:300])
            return False
        elif response.status_code == 401:
            print("AUTH FAILED - Invalid API key")
            print("Response:", response.text[:300])
            return False
        elif response.status_code == 402:
            print("PAYMENT REQUIRED - Insufficient credits")
            print("Response:", response.text[:300])
            return False
        elif response.status_code == 404:
            print(f"MODEL NOT FOUND - '{settings.llm_model}' may not exist")
            print("Response:", response.text[:300])
            return False
        else:
            print(f"UNEXPECTED ERROR: {response.status_code}")
            print("Response:", response.text[:300])
            return False

    except httpx.TimeoutException:
        print("TIMEOUT - Request took too long")
        return False
    except httpx.ConnectError as e:
        print(f"CONNECTION ERROR: {e}")
        return False
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False


def test_rate_limit_recovery():
    settings = get_settings()
    url = f"{settings.openrouter_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5,
        "temperature": 0,
    }

    print("Testing rate limit recovery (3 attempts, 5s apart)...")
    for i in range(3):
        print(f"\nAttempt {i+1}/3...")
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        print(f"  Status: {response.status_code}")
        if response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            wait = int(retry_after) if retry_after and retry_after.isdigit() else 5
            print(f"  Rate limited, waiting {wait}s...")
            time.sleep(wait)
        elif response.status_code == 200:
            print(f"  Success: {response.json()['choices'][0]['message']['content']}")
            return True
        else:
            print(f"  Error: {response.text[:200]}")
            return False
    print("Still rate limited after retries")
    return False


def list_models():
    settings = get_settings()
    url = f"{settings.openrouter_base_url}/models"
    headers = {"Authorization": f"Bearer {settings.openrouter_api_key}"}
    try:
        resp = httpx.get(url, headers=headers, timeout=15.0)
        if resp.status_code == 200:
            models = resp.json().get("data", [])
            free = [m["id"] for m in models if ":free" in m["id"]]
            print(f"\nFree models available ({len(free)}):")
            for m in sorted(free)[:20]:
                print(f"  {m}")
            if len(free) > 20:
                print(f"  ... and {len(free)-20} more")
            return free
        else:
            print(f"Could not list models: {resp.status_code}")
            return []
    except Exception as e:
        print(f"Error listing models: {e}")
        return []


if __name__ == "__main__":
    print("=" * 50)
    print("ParcelPilot LLM Connection Test")
    print("=" * 50)
    print()

    ok = test_api_key()
    if ok:
        ok = test_connection()

    if not ok:
        print("\n" + "=" * 50)
        print("Troubleshooting:")
        print("  1. Wait 30-60s if rate limited, then retry")
        print("  2. Check your API key at https://openrouter.ai/keys")
        print("  3. Try a different free model:")
        list_models()
        print("  4. Update LLM_MODEL in .env with a working model")
        sys.exit(1)
    else:
        print("\nLLM is working!")
        sys.exit(0)
