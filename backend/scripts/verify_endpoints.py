import json
import urllib.request

ENDPOINTS = [
    "http://127.0.0.1:8000/health",
    "http://127.0.0.1:8000/api/v1/health/database",
    "http://127.0.0.1:8000/api/v1/drivers",
    "http://127.0.0.1:8000/api/v1/vehicles",
    "http://127.0.0.1:8000/api/v1/devices",
    "http://127.0.0.1:8000/api/v1/device-assignments",
    "http://127.0.0.1:8000/api/v1/trips/start-options",
]


def verify_all():
    print("Verifying EvolveX REST endpoints...")
    for url in ENDPOINTS:
        try:
            with urllib.request.urlopen(url) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                success = data.get("success", "N/A")
                print(f"URL: {url} -> Status: {resp.status} (Success: {success})")
        except Exception as exc:
            print(f"URL: {url} -> FAILED: {exc}")


if __name__ == "__main__":
    verify_all()
