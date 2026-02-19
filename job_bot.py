import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

SHEET_WEBHOOK_URL = os.getenv("SHEET_WEBHOOK_URL")

KEYWORDS = ["java"]
LOCATION = "bangalore"
MAX_JOBS = 15

def send_to_sheet(job):
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
    requests.post(SHEET_WEBHOOK_URL, json=data)

def fetch_indeed_jobs():
    jobs = []
    url = "https://in.indeed.com/jobs?q=java+developer&l=Bengaluru"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    for card in soup.select("a.tapItem"):
        title = card.select_one("h2 span")
        company = card.select_one(".companyName")
        location = card.select_one(".companyLocation")

        if title and company and location:
            title_text = title.text.strip()
            company_text = company.text.strip()
            location_text = location.text.strip()

            if "java" in title_text.lower() and "bengaluru" in location_text.lower():
                job_link = "https://in.indeed.com" + card.get("href")

                jobs.append({
                    "title": title_text,
                    "company": company_text,
                    "location": location_text,
                    "experience": "1-2 years",
                    "type": "Unknown",
                    "link": job_link,
                    "source": "Indeed"
                })

        if len(jobs) >= MAX_JOBS:
            break

    return jobs

def fetch_remotive_jobs():
    jobs = []
    url = "https://remotive.com/api/remote-jobs?search=java"
    response = requests.get(url)
    data = response.json()

    for job in data.get("jobs", []):
        if "java" in job["title"].lower():
            jobs.append({
                "title": job["title"],
                "company": job["company_name"],
                "location": "Remote",
                "experience": "1-2 years",
                "type": "Remote",
                "link": job["url"],
                "source": "Remotive"
            })

        if len(jobs) >= MAX_JOBS:
            break

    return jobs

def main():
    all_jobs = []
    all_jobs.extend(fetch_indeed_jobs())
    all_jobs.extend(fetch_remotive_jobs())

    for job in all_jobs:
        send_to_sheet(job)

    print("Success")

if __name__ == "__main__":
    main()
