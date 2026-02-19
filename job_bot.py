import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

SHEET_WEBHOOK_URL = os.getenv("SHEET_WEBHOOK_URL")

LOCATION_KEYWORDS = ["bengaluru", "bangalore", "remote"]
EXPERIENCE_KEYWORDS = ["0 year", "1 year", "2 year", "0-2", "1-2"]
TARGET_COMPANIES = [
    "accenture", "deloitte", "jp morgan", "infosys",
    "cognizant", "pwc", "ey", "genpact", "kpmg", "opentext", "capgemini"
]

MAX_JOBS = 10


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


def is_relevant(title, company, location):
    text = f"{title} {company} {location}".lower()

    if "java" not in text:
        return False

    if not any(loc in text for loc in LOCATION_KEYWORDS):
        return False

    return True


def detect_company_type(company):
    name = company.lower()
    if any(mnc in name for mnc in TARGET_COMPANIES):
        return "Target MNC"
    return "Other"


def fetch_indeed():
    jobs = []
    url = "https://in.indeed.com/jobs?q=java+developer+0-2+years&l=Bengaluru"
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

            if is_relevant(title_text, company_text, location_text):
                job_link = "https://in.indeed.com" + card.get("href")

                jobs.append({
                    "title": title_text,
                    "company": company_text,
                    "location": location_text,
                    "experience": "0-2 years",
                    "type": detect_company_type(company_text),
                    "link": job_link,
                    "source": "Indeed"
                })

        if len(jobs) >= MAX_JOBS:
            break

    return jobs


def fetch_remotive():
    jobs = []
    url = "https://remotive.com/api/remote-jobs?search=java"
    response = requests.get(url)
    data = response.json()

    for job in data.get("jobs", []):
        title = job["title"]
        company = job["company_name"]

        if "java" in title.lower():
            jobs.append({
                "title": title,
                "company": company,
                "location": "Remote",
                "experience": "0-2 years",
                "type": detect_company_type(company),
                "link": job["url"],
                "source": "Remotive"
            })

        if len(jobs) >= MAX_JOBS:
            break

    return jobs


def main():
    all_jobs = []

    indeed_jobs = fetch_indeed()
    remotive_jobs = fetch_remotive()

    all_jobs.extend(indeed_jobs)
    all_jobs.extend(remotive_jobs)

    # Remove duplicates
    unique = {}
    for job in all_jobs:
        unique[job["link"]] = job

    final_jobs = list(unique.values())[:MAX_JOBS]

    for job in final_jobs:
        send_to_sheet(job)

    print("Success")


if __name__ == "__main__":
    main()
