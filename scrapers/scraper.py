from playwright.sync_api import sync_playwright
import pandas as pd
import time


def is_recent(text):
    if "day" in text:
        try:
            days = int(text.split()[0])
            return days <= 2
        except:
            return False
    return False

def detect_type(text):
    text = text.lower()
    if "remote" in text:
        return "remote"
    elif "hybrid" in text:
        return "hybrid"
    else:
        return "onsite"


all_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    for page_num in range(1, 4): 
        url = f"https://www.naukri.com/prahari-technologies-jobs-{page_num}"
        print(f"\nScraping page {page_num}...")

        page.goto(url)
        page.wait_for_selector("div.cust-job-tuple")

        jobs = page.query_selector_all("div.cust-job-tuple")
        print(f"Found {len(jobs)} jobs")

        for job in jobs:
            title = job.query_selector("a.title")
            company = job.query_selector(".comp-name")
            location = job.query_selector(".locWdth")
            experience = job.query_selector(".expwdth")
            posted = job.query_selector(".job-post-day")

            job_name = title.inner_text() if title else ""
            company_name = company.inner_text() if company else ""
            loc = location.inner_text() if location else ""
            exp = experience.inner_text() if experience else ""
            post_text = posted.inner_text() if posted else ""
            link = title.get_attribute("href") if title else ""

            if not is_recent(post_text):
                continue

            job_description = ""
            job_type = "unknown"

            try:
                detail_page = browser.new_page()
                detail_page.goto(link)
                detail_page.wait_for_load_state("domcontentloaded")
                job_description = ""

                try:
                    detail_page.wait_for_selector("[class*='dang-inner-html']", timeout=5000)
                    desc = detail_page.query_selector("[class*='dang-inner-html']")
                    
                    if desc:
                        job_description = desc.inner_text()

                except:
                    print("Description not found for:", link)

                job_type = detect_type(job_description)

                detail_page.close()

            except Exception as e:
                print("Error opening detail page:", e)

            all_data.append({
                "job_name": job_name,
                "job_description": job_description,
                "posting_date": post_text,
                "experience": exp,
                "location": loc,
                "company_name": company_name,
                "jobapplication_link": link,
                "type": job_type
            })

            time.sleep(1)  

        time.sleep(2)  

    browser.close()


df = pd.DataFrame(all_data)
df.to_csv("jobs.csv", index=False)

print(f"\nSaved {len(all_data)} jobs to jobs.csv")