import requests

# Test which servers are UP (Able, charlie, baker)
urls_to_test = [
    ("ABLE", "https://war-service-live.foxholeservices.com/api/worldconquest/war"),
    ("BAKER", "https://war-service-live-2.foxholeservices.com/api/worldconquest/war"),
    ("CHARLIE", "https://war-service-live-3.foxholeservices.com/api/worldconquest/war"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Starting Diagnostic.")

for name, url in urls_to_test:
    print(f"Testing {name}...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   Succes, this one is responding.")
            print(f"   Answer (extract): {str(response.json())}...")
        else:
            print("   Failed to get an answer.")
    except Exception as e:
        print(f"   Failed to connect : {e}")
    print("-" * 30)