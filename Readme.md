# 🧠 Job Scraper

A modular job scraping system that collects job postings from multiple company career pages and exports them into structured CSV files.

---

## 🚀 Features

- Scrapes jobs from multiple companies:
  - Deloitte
  - Pocketful
  - Vahn (Wellfound)
  - Valtech
  - Zapier
- Supports:
  - Static scraping (Requests + BeautifulSoup)
  - Dynamic scraping (Playwright for JS-heavy sites)
- Extracts:
  - Job Title
  - Description
  - Posting Date
  - Experience
  - Location
  - Job Type (Remote/Hybrid/Onsite)
  - Application Link
- Filters jobs (e.g., last 2 days for supported sites)
- Outputs clean CSV files
- Handles encoding + Excel-safe formatting

---

## 📁 Project Structure
```
JOB-SCRAPER/
│
├── scrapers/
│ ├── output/
│ │ ├── deloitte.csv
│ │ ├── pocketful.csv
│ │ ├── vahn.csv
│ │ ├── valtech.csv
│ │ ├── zapier.csv
│ │
│ ├── deloitte.py
│ ├── pocketful.py
│ ├── vahn.py
│ ├── valtech.py
│ ├── zapier.py
│ └── scraper.py
│
├── main.py
├── requirements.txt
└── venv/
```
---

## ⚙️ Tech Stack

- Python
- BeautifulSoup (HTML parsing)
- Requests (API calls)
- Playwright (dynamic scraping)
- Pandas (data processing)

---

## 🛠️ Installation

1. Clone the repository

```bash
git clone <your-repo-link>
cd job-scraper
```
2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate   # Windows
```
3. Install dependencies
```bash
pip install -r requirements.txt
```
4. Install Playwright browsers
```bash
playwright install
```

▶️ Usage
Run individual scrapers
```bash
python scrapers/deloitte.py
python scrapers/pocketful.py
python scrapers/vahn.py
python scrapers/valtech.py
python scrapers/zapier.py
```
Output
All scraped data is saved in:
```bash
scrapers/output/
```
