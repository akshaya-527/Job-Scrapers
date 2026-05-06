import re
import time
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://www.pocketful.in"
LIST_URL = "https://www.pocketful.in/careers/open-roles"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def safe_for_excel(text):
    if isinstance(text, str) and text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def infer_work_type(text):
    text = text.lower()
    if "remote" in text:
        return "remote"
    elif "hybrid" in text:
        return "hybrid"
    else:
        return "onsite"


def extract_experience(text):
    match = re.search(
        r"(\d+\s*(?:to|-)?\s*\d*\s*years?)",
        text,
        re.IGNORECASE
    )
    return match.group(0) if match else ""



def get_job_links():
    res = requests.get(LIST_URL, headers=headers)
    soup = BeautifulSoup(res.text, "lxml")

    links = soup.find_all("a", href=re.compile(r"^/careers/open-roles/[^/]+$"))

    seen = set()
    job_links = []

    for a in links:
        href = a["href"]
        if href not in seen and href != "/careers/open-roles":
            seen.add(href)
            job_links.append(BASE_URL + href)

    print(f"Found {len(job_links)} job links")
    return job_links



def scrape_job(url):
    res = requests.get(url, headers=headers)
    res.encoding = "utf-8"  
    soup = BeautifulSoup(res.text, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title_tag = soup.find("h1")
    job_name = clean_text(title_tag.get_text()) if title_tag else ""

    desc_container = soup.find("div", class_=re.compile("rolesDetailContentDiv"))

    job_description = ""

    if desc_container:
        parts = []

        for tag in desc_container.find_all(["h2", "p", "li"]):

            text = tag.get_text(" ", strip=True)

            if not text:
                continue

            if tag.name == "h2":
                parts.append(f"\n{text.upper()}\n")   

            elif tag.name == "li":
                parts.append(f"- {text}")           

            else:
                parts.append(text)

        job_description = "\n".join(parts)
        job_description = job_description.replace("â€™", "'").replace("â€“", "-")
    experience = extract_experience(job_description)

    location = "Not Available"

    loc_label = soup.find("p", string=re.compile("^Location$", re.I))
    if loc_label:
        loc_value = loc_label.find_next("p")
        if loc_value:
            location = clean_text(loc_value.get_text())

    posting_date = "Not Available"

    job_type = infer_work_type(job_description + " " + location)

    return {
        "job_name": safe_for_excel(job_name),
        "job_description": safe_for_excel(job_description),
        "posting_date": posting_date,
        "experience": experience,
        "location": location,
        "company_name": "Pocketful",
        "jobapplication_link": url,
        "type": job_type
    }



def main():
    os.makedirs("output", exist_ok=True)

    job_links = get_job_links()
    all_jobs = []

    for link in job_links:
        try:
            job = scrape_job(link)
            all_jobs.append(job)
            print("Scraped:", job["job_name"])
        except Exception as e:
            print("Error:", e)

        time.sleep(1)

    df = pd.DataFrame(all_jobs)

    df = df.applymap(safe_for_excel)

    df.to_csv("output/pocketful.csv", index=False, encoding="utf-8")



if __name__ == "__main__":
    main()
