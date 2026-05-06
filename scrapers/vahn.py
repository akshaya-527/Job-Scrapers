import re
import time
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://wellfound.com"
LIST_URL = "https://wellfound.com/company/vahn-1/jobs"

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


from playwright.sync_api import sync_playwright
import re
from bs4 import BeautifulSoup

def get_job_links():
    links = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto("https://wellfound.com/company/vahn-1/jobs", timeout=60000)

            page.wait_for_load_state("networkidle")

            for _ in range(8):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_load_state("networkidle")

            html = page.content()

        except Exception as e:
            print("Playwright Error:", e)
            browser.close()
            return []

        browser.close()

    soup = BeautifulSoup(html, "lxml")

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if re.match(r"^/jobs/\d+", href):
            links.add("https://wellfound.com" + href)

    print(f"Found {len(links)} job links")
    return list(links)

def scrape_job(url):
    res = requests.get(url, headers=headers)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title_tag = soup.find("h1")
    job_name = clean_text(title_tag.get_text()) if title_tag else ""

    desc_container = soup.find("div", class_=re.compile("job-description"))

    job_description = ""
    if desc_container:
        parts = []

        for tag in desc_container.find_all(["h2", "h3", "p", "li"]):
            text = tag.get_text(" ", strip=True)

            if not text:
                continue

            if tag.name in ["h2", "h3"]:
                parts.append(f"\n{text.upper()}\n")
            elif tag.name == "li":
                parts.append(f"- {text}")
            else:
                parts.append(text)

        job_description = "\n".join(parts)

    if not job_description:
        job_description = clean_text(soup.get_text())

    location = "Not Available"

    loc_tag = soup.find(string=re.compile("Location", re.I))
    if loc_tag:
        parent = loc_tag.find_parent()
        if parent:
            location = clean_text(parent.get_text())

    posting_date = "Not Available"

    experience = extract_experience(job_description)

    job_type = infer_work_type(job_description + " " + location)

    return {
        "job_name": safe_for_excel(job_name),
        "job_description": safe_for_excel(job_description),
        "posting_date": posting_date,
        "experience": experience,
        "location": location,
        "company_name": "Vahn (Wellfound)",
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
            print("Error:", link, e)

        time.sleep(1)

    df = pd.DataFrame(all_jobs)
    df = df.map(safe_for_excel)

    df.to_csv("output/vahn.csv", index=False, encoding="utf-8")

    print(f"\nSaved {len(all_jobs)} jobs to output/vahn.csv")


if __name__ == "__main__":
    main()