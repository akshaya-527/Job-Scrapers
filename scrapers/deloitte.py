import requests
from bs4 import BeautifulSoup
import re
import os
import time
import pandas as pd
from datetime import datetime

BASE_URL = "https://southasiacareers.deloitte.com"
LIST_URL = "https://southasiacareers.deloitte.com/go/Deloitte-India/718244/"

headers = {"User-Agent": "Mozilla/5.0"}

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip() if text else ""


from datetime import datetime, timedelta

def is_within_last_2_days(date_str):
    try:
        job_date = datetime.strptime(date_str.strip(), "%b %d, %Y")

        now = datetime.now()
        cutoff = now - timedelta(days=2)

        return job_date >= cutoff

    except Exception as e:
        print("Date parse error:", date_str)
        return False

def get_job_links():
    links = set()

    for page in range(8):  
        start = page * 25
        url = f"{LIST_URL}{start}/?q=&sortColumn=referencedate&sortDirection=desc"

        print(f"Fetching page {page+1}")

        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "lxml")

        count = 0

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "/job/" in href:
                if not href.startswith("http"):
                    href = BASE_URL + href

                if href not in links:
                    links.add(href)
                    count += 1

        print(f"  Found {count} links")

        if count == 0:
            break

    return list(links)


def main():
    os.makedirs("output", exist_ok=True)

    job_links = get_job_links()
    print(f"Total links: {len(job_links)}")

    name = []
    description = []
    posting_date = []
    experience = []
    location = []
    company = []
    link = []
    job_type = []

    for url in job_links:
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, "lxml")

            title_tag = soup.find("span", {"data-careersite-propertyid": "title"})
            job_name = clean_text(title_tag.text) if title_tag else ""

            date_tag = soup.find("span", {"data-careersite-propertyid": "date"})
            date = clean_text(date_tag.text) if date_tag else ""

            print("Checking:", job_name, "|", date)

            if not is_within_last_2_days(date):
                continue

            location_val = ""
            labels = soup.find_all("span", class_="joblayouttoken-label")

            for label in labels:
                if "Location" in label.text:
                    val = label.find_next("span")
                    if val:
                        location_val = clean_text(val.text)

            desc_container = soup.find("span", class_="jobdescription")

            job_desc = ""
            exp = ""

            if desc_container:
                text = clean_text(desc_container.get_text())

                job_desc = " | ".join(text.split(".")[:3])

                match = re.search(r'(\d+\+?\s*years?)', text, re.I)
                if match:
                    exp = match.group(1)

            name.append(job_name)
            description.append(job_desc)
            posting_date.append(date)
            experience.append(exp)
            location.append(location_val)
            company.append("Deloitte")
            link.append(url)
            job_type.append("Not Available")

            print("Saved:", job_name)

        except Exception as e:
            print("Error:", url, e)

        time.sleep(1)

    df = pd.DataFrame({
        "job_name": name,
        "job_description": description,
        "posting_date": posting_date,
        "experience": experience,
        "location": location,
        "company_name": company,
        "jobapplication_link": link,
        "type": job_type
    })

    df.to_csv("output/deloitte.csv", index=False, encoding="utf-8")

    print(f"\nSaved {len(df)} jobs")


if __name__ == "__main__":
    main()