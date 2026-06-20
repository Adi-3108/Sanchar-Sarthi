import os
import httpx
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("MAPMYINDIA_REST_KEY")

endpoints = [
    f"https://search.mappls.com/search/address/geocode?access_token={key}&address=bengaluru"
]

with httpx.Client(timeout=8.0) as client:
    for url in endpoints:
        print(f"\n--- Testing: {url} ---")
        try:
            resp = client.get(url)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")
