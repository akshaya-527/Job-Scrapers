import re
import time
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.valtech.com"
LIST_URL = "https://www.valtech.com/en-in/career/jobs/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


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
    return "onsite"


def extract_experience(text):
    match = re.search(r"(\d+\s*(?:to|-)?\s*\d*\s*years?)", text, re.I)
    return match.group(0) if match else ""

def is_recent(posting_date):
    if posting_date == "Not Available":
        return False   

    formats = [
        "%B %d, %Y",   
        "%Y-%m-%d"     
    ]

    for fmt in formats:
        try:
            job_date = datetime.strptime(posting_date.strip(), fmt)
            return (datetime.now() - job_date).days <= 2
        except:
            continue

    return False


def get_job_links():
    links = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(LIST_URL, timeout=60000)
        page.wait_for_timeout(5000)

        for _ in range(6):
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(2000)

        anchors = page.query_selector_all("a")

        for a in anchors:
            href = a.get_attribute("href")
            if href and re.search(r"/career/jobs/\d{7,}/$", href):
                if not href.startswith("http"):
                    href = BASE_URL + href
                links.add(href)

        browser.close()

    print(f"Found {len(links)} valid job links")
    return list(links)


def scrape_job(url):
    res = requests.get(url, headers=headers)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title_tag = soup.find("h1")
    job_name = clean_text(title_tag.get_text()) if title_tag else ""

    desc_container = soup.find("div", class_=re.compile("rte-block__container"))

    job_description = ""

    if desc_container:
        parts = []

        capture = False   

        for tag in desc_container.find_all(["h3", "h4", "p", "li"]):
            text = tag.get_text(" ", strip=True)

            if not text:
                continue

            if "The role" in text:
                capture = True
                continue

            if not capture:
                continue

            if tag.name in ["h3", "h4"]:
                parts.append(f"\n{text.upper()}\n")
            elif tag.name == "li":
                parts.append(f"- {text}")
            else:
                parts.append(text)

        job_description = "\n".join(parts)

    experience = extract_experience(job_description)

    location = "Not Available"

    loc_tag = soup.find(string=re.compile("Location", re.I))
    if loc_tag:
        parent = loc_tag.find_parent()
        if parent:
            next_tag = parent.find_next()
            if next_tag:
                location = clean_text(next_tag.get_text())

    if location == "Not Available":
        loc_alt = soup.find("span", class_=re.compile("location", re.I))
        if loc_alt:
            location = clean_text(loc_alt.get_text())

    posting_date = "Not Available"

    date_tag = soup.find(string=re.compile("Posted", re.I))
    if date_tag:
        text = date_tag.strip()

        match = re.search(r"(\w+\s\d{1,2},\s\d{4})", text)
        if match:
            posting_date = match.group(1)

    if posting_date == "Not Available":
        meta = soup.find("meta", {"property": "article:published_time"})
        if meta and meta.get("content"):
            posting_date = meta["content"][:10]

    if not is_recent(posting_date):
        return None

    job_type = infer_work_type(job_description + " " + location)

    return {
        "job_name": safe_for_excel(job_name),
        "job_description": safe_for_excel(job_description),
        "posting_date": posting_date,
        "experience": experience,
        "location": location,
        "company_name": "Valtech",
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

            if job:   
                all_jobs.append(job)

        except Exception as e:
            print("Error scraping:", link)
            print(e)

        time.sleep(1)


    if not all_jobs:
        return

    df = pd.DataFrame(all_jobs)
    df = df.applymap(safe_for_excel)

    df.to_csv("output/valtech_jobs.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    main()