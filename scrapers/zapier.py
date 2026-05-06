import requests
import pandas as pd
import re
import os
from datetime import datetime

API_URL = "https://api.ashbyhq.com/posting-api/job-board/zapier"


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip() if text else ""


def safe_for_excel(text):
    if isinstance(text, str) and text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text if text else "Not Available"


def extract_experience(text):
    match = re.search(
        r"(\d+[\+]?\s*(?:to\s*\d+)?\s*years?)",
        text,
        re.IGNORECASE
    )
    return match.group(0) if match else "Not Available"


def infer_work_type(is_remote, location):
    if is_remote:
        return "remote"
    if location and "remote" in location.lower():
        return "remote"
    return "onsite"



def scrape_zapier_jobs():
    try:
        res = requests.get(API_URL, params={"includeCompensation": "true"})
        data = res.json()
    except Exception as e:
        print("API Error:", e)
        return []

    jobs = []

    for item in data.get("jobs", []):

        if not item.get("isListed", True):
            continue


        job_name = clean_text(item.get("title", ""))

        description = item.get("descriptionPlain", "")
        if not description:
            html_desc = item.get("descriptionHtml", "")
            description = re.sub(r"<[^>]+>", " ", html_desc)

        def clean_description(text):
            if not text:
                return ""

            text = text.replace("â€™", "'").replace("â€“", "-")
            text = re.sub(r"http\S+", "", text)
            text = re.sub(r"\s+", " ", text)

            return text.strip()

        job_description = clean_description(description)
        job_description = " | ".join(job_description.split(".")[:3])


        slug = item.get("slug") or item.get("id")
        url = item.get("externalLink") or item.get("jobPostingLink")

        if not url and slug:
            url = f"https://jobs.ashbyhq.com/zapier/{slug}"
        raw_date = item.get("publishedDate", "")
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            posting_date = dt.strftime("%Y-%m-%d")
        except:
            posting_date = "Not Available"

        loc_obj = item.get("location") or {}
        location = loc_obj.get("locationStr", "") if isinstance(loc_obj, dict) else ""
        if not location:
            location = item.get("locationName", "") or "Remote"

        location = clean_text(location)

        experience = extract_experience(job_description)

        job_type = infer_work_type(item.get("isRemote", False), location)

        jobs.append({
            "job_name": safe_for_excel(job_name),
            "job_description": safe_for_excel(job_description[:300]),  # limit size
            "posting_date": posting_date,
            "experience": experience,
            "location": location,
            "company_name": "Zapier",
            "jobapplication_link": url,
            "type": job_type
        })

    return jobs


def main():
    os.makedirs("output", exist_ok=True)

    jobs = scrape_zapier_jobs()

    df = pd.DataFrame(jobs)
    df.to_csv("output/zapier.csv", index=False, encoding="utf-8")

    print(f"Saved {len(jobs)} jobs to output/zapier_jobs.csv")


if __name__ == "__main__":
    main()