import urllib.request
import json

data = json.dumps({
    "origin": [77.5855, 12.9569], # Lalbagh approximate
    "destination": [77.6155, 12.9269],
    "purpose": "diversion_plan",
    "mode": "driving"
}).encode('utf-8')

req = urllib.request.Request("http://localhost:8000/api/map/route", data=data, headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req)
    res = json.loads(response.read())
    print("Polyline length:", len(res.get('polyline', [])))
    print("Provider:", res.get('provider'))
except Exception as e:
    print("Error:", e)
