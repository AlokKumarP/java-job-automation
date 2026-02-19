import requests
from datetime import datetime
import os

SHEET_WEBHOOK_URL = os.getenv("SHEET_WEBHOOK_URL")

jobs = [
    {
        "title": "Java Developer",
        "company": "Test Company",
        "location": "Bangalore",
        "experience": "1-2 years",
        "type": "Startup",
        "link": "https://example.com",
        "source": "Test Run"
    }
]

for job in jobs:
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "title": job["title"],
        "company": job["company"],
        "location": job["location"],
        "experience": job["experience"],
        "type": job["type"],
        "link": job["link"],
        "source": job["source"]
    }

    response = requests.post(SHEET_WEBHOOK_URL, json=data)
    print(response.text)
