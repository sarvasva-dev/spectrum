import requests
import json

base_url = "http://127.0.0.1:8000"

def test_endpoint(method, path, **kwargs):
    url = f"{base_url}{path}"
    try:
        resp = requests.request(method, url, **kwargs)
        print(f"[{method}] {path} -> {resp.status_code}")
        try:
            print(json.dumps(resp.json(), indent=2)[:300] + "...")
        except:
            print(resp.text[:300])
    except Exception as e:
        print(f"[{method}] {path} -> FAILED: {str(e)}")

if __name__ == "__main__":
    # Test Health API
    test_endpoint("GET", "/api/health/")
    
    # Test GET Complaints
    test_endpoint("GET", "/api/complaints/")
