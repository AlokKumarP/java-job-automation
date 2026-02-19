import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

SHEET_WEBHOOK_URL = os.getenv("SHEET_WEBHOOK_URL")

def get_existing_links():
    response = requests.get(SHEET_WEBHOOK_URL)
    try:
        return set(response.json())
    except:
        return set()


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


import xml.etree.ElementTree as ET

def fetch_indeed():
    jobs = []
    url = "https://in.indeed.com/rss?q=java+developer+0-2+years&l=India"

    response = requests.get(url)
    root = ET.fromstring(response.content)

    for item in root.findall(".//item"):

        title = item.find("title").text if item.find("title") is not None else ""
        link = item.find("link").text if item.find("link") is not None else ""
        description = item.find("description").text if item.find("description") is not None else ""

        if not title or not link:
            continue

        if "java" not in title.lower():
            continue

        # Basic location detection from description
        location = "India"
        if "bangalore" in description.lower() or "bengaluru" in description.lower():
            location = "Bangalore"
        elif "remote" in description.lower():
            location = "Remote"

        company = "Unknown"

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "experience": "0-2 years",
            "type": "Unknown",
            "link": link,
            "source": "Indeed RSS"
        })

        if len(jobs) >= MAX_JOBS * 2:
            break

    print("Indeed RSS jobs:", len(jobs))
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


def rank_job(job):
    location = job["location"].lower()
    score = 0

    if "bangalore" in location or "bengaluru" in location:
        score -= 2
    elif "remote" in location:
        score -= 1

    if job["type"] == "Target MNC":
        score -= 3

    return score




def main():
    all_jobs = []

    indeed_jobs = fetch_indeed()
    remotive_jobs = fetch_remotive()

    print("Indeed jobs found:", len(indeed_jobs))
    print("Remotive jobs found:", len(remotive_jobs))


    all_jobs.extend(indeed_jobs)
    all_jobs.extend(remotive_jobs)

    # Remove duplicates
    unique = {}
    for job in all_jobs:
        unique[job["link"]] = job

    jobs_list = list(unique.values())

    # Sort: Target MNC first
    jobs_list.sort(key=rank_job)

    final_jobs = jobs_list[:MAX_JOBS]


    existing_links = get_existing_links()

    for job in final_jobs:
        if job["link"] not in existing_links:
            send_to_sheet(job)

    print("Success")



if __name__ == "__main__":
    main()
