# Coventry University Course Scraper

A production-quality Python scraper designed to extract structured course data from Coventry University's official website (https://www.coventry.ac.uk/).

## Features

- **Domain Whitelisting**: Strictly fetches data from `coventry.ac.uk` only.
- **Robust Extraction**: Extracts 27 specific fields with comprehensive error handling (returns "NA" for missing fields).
- **Production-Ready**: Uses `requests.Session()`, custom User-Agents, and randomized rate limiting.
- **Detailed Logging**: All activities, successes, warnings, and errors are logged to `scraper.log`.
- **Configurable**: Managed via `.env` file for easy deployment and adjustments.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Setup Instructions

1. **Clone or Download the Repository**
   Ensure all files (`scraper.py`, `requirements.txt`, `.env.example`, etc.) are in your project directory.

2. **Install Dependencies**
   Run the following command to install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```
   *Note: On Windows, you can manually copy `.env.example` to `.env`.*

4. **Review Configuration**
   The default `.env` is pre-configured to:
   - `BASE_URL`: The Coventry University Undergraduate Course Finder.
   - `OUTPUT_FILE`: `coventry_courses.json`
   - `DELAY_MIN/MAX`: 1.5 to 3.5 seconds randomized delay.

## Running the Scraper

Execute the scraper using Python:

```bash
python scraper.py
```

## Expected Output

### JSON Data
The results are saved to `coventry_courses.json`. It contains an array of exactly 5 course objects. 

**Sample Snippet:**
```json
[
    {
        "program_course_name": "Accountancy BSc (Hons)",
        "university_name": "Coventry University",
        "course_website_url": "https://www.coventry.ac.uk/course-structure/ug/fbl/accountancy-bsc-hons/",
        "campus": "Coventry University (Coventry)",
        "country": "UK",
        "address": "Priory Street, Coventry, West Midlands, CV1 5FB",
        "study_level": "Undergraduate",
        "course_duration": "3 years full-time 4 years sandwich",
        "all_intakes_available": "September 2027, November 2027, January 2028, March 2028, May 2028, July 2028",
        "yearly_tuition_fee": "UK: 2027/28 fees TBC 2026/27 fees: \u00a39,790 per year | International: 2027/28 fees TBC 2026/27 fees: \u00a317,600 per year",
        "min_ielts": "IELTS: 6.0 overall",
        "...": "..."
    }
]
```

### Logs
All actions are tracked in `scraper.log`. Check this file for INFO on progress, WARNINGS for missing fields, and ERRORS for failed requests.

## Security & Reliability Practices

- **Domain Validation**: Every URL is checked against a whitelist before fetching.
- **Graceful Redirects**: Redirects are followed but the final URL is validated to ensure it remains on the approved domain.
- **Rate Limiting**: Randomized delays prevent server hammering and mimic human browsing behavior.
- **Timeout Management**: All requests have a 15-second timeout to prevent hanging.
- **Modular Design**: Code is structured into discovery, fetching, extraction, and storage modules for maintainability.
- **Sensitive Data**: No credentials or hardcoded URLs are stored in the code; all configurations are environment-based.
