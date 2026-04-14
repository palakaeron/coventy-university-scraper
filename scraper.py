import os
import time
import random
import json
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("BASE_URL", "https://www.coventry.ac.uk/study-at-coventry/undergraduate-study/course-finder/")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "coventry_courses.json")
DELAY_MIN = float(os.getenv("DELAY_MIN", 1.5))
DELAY_MAX = float(os.getenv("DELAY_MAX", 3.5))
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
TIMEOUT = int(os.getenv("TIMEOUT", 15))

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_domain(url):
    """Ensure the URL belongs to coventry.ac.uk."""
    parsed = urlparse(url)
    return parsed.netloc == "www.coventry.ac.uk"

def fetch_page(session, url):
    """Fetch HTML content of a URL with error handling and rate limiting."""
    if not validate_domain(url):
        logger.error(f"Domain validation failed for URL: {url}")
        raise ValueError(f"URL {url} is not in the allowed domain.")
    
    headers = {"User-Agent": USER_AGENT}
    try:
        # Rate limiting
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        
        response = session.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        # Verify final URL domain after redirects
        if not validate_domain(response.url):
            logger.error(f"Redirected to unauthorized domain: {response.url}")
            raise ValueError(f"Redirected to unauthorized domain: {response.url}")
            
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

def discover_course_urls(session):
    """Crawl the course finder page to find 5 unique course URLs."""
    logger.info(f"Discovering course URLs from {BASE_URL}")
    html = fetch_page(session, BASE_URL)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    links = soup.find_all('a', href=True)
    
    course_urls = set()
    for link in links:
        href = link['href']
        # Match common course URL patterns
        if '/course-structure/ug/' in href or '/course-structure/pg/' in href:
            full_url = urljoin("https://www.coventry.ac.uk", href)
            # Basic validation to avoid query params and focus on clean URLs
            clean_url = full_url.split('?')[0]
            if validate_domain(clean_url):
                course_urls.add(clean_url)
                if len(course_urls) >= 5:
                    break
    
    return list(course_urls)

def extract_course_data(html, url):
    """Extract required fields from the course detail page."""
    soup = BeautifulSoup(html, 'lxml')
    data = {}
    
    # Helper to safely extract text
    def get_text(selector, name="field"):
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else "NA"
        except Exception as e:
            logger.warning(f"Error extracting {name} from {url}: {e}")
            return "NA"

    # Field extraction with try/except
    try:
        data['program_course_name'] = get_text("h1", "program_course_name")
        if data['program_course_name'] == "NA":
             # Fallback to .course-title h1
             data['program_course_name'] = get_text(".course-title h1", "program_course_name fallback")
    except: data['program_course_name'] = "NA"

    data['university_name'] = "Coventry University"
    data['course_website_url'] = url
    
    try:
        data['campus'] = get_text(".feature-box.location .campus", "campus")
        if data['campus'] == "NA":
             # Try broader search for location
             for box in soup.select(".feature-box"):
                 if "Location" in box.get_text():
                     data['campus'] = box.select_one("p").get_text(strip=True)
                     break
    except: data['campus'] = "NA"

    data['country'] = "UK"
    data['address'] = "Priory Street, Coventry, West Midlands, CV1 5FB" # Standard for Coventry University

    try:
        data['study_level'] = get_text(".campus-label.-title", "study_level")
    except: data['study_level'] = "NA"

    try:
        data['course_duration'] = "NA"
        for box in soup.select(".feature-box"):
            if "Duration" in box.get_text():
                data['course_duration'] = box.select_one("p").get_text(strip=True, separator=" ")
                break
    except: data['course_duration'] = "NA"

    try:
        data['all_intakes_available'] = "NA"
        for box in soup.select(".feature-box"):
            if "Start date" in box.get_text():
                data['all_intakes_available'] = box.select_one("p").get_text(strip=True, separator=", ")
                break
    except: data['all_intakes_available'] = "NA"

    data['mandatory_documents_required'] = "NA" # Usually not explicitly listed in a single field

    try:
        fees_uk = "NA"
        fees_int = "NA"
        fee_td_uk = soup.select_one("td.Fees-UK-FullTime")
        if fee_td_uk:
            fees_uk = fee_td_uk.get_text(strip=True, separator=" ")
        
        fee_td_int = soup.select_one("td.Fees-International-FullTime")
        if fee_td_int:
            fees_int = fee_td_int.get_text(strip=True, separator=" ")
        
        data['yearly_tuition_fee'] = f"UK: {fees_uk} | International: {fees_int}"
    except: data['yearly_tuition_fee'] = "NA"

    try:
        data['scholarship_availability'] = "NA"
        if soup.find(string=lambda s: "scholarship" in s.lower()):
            data['scholarship_availability'] = "Yes (Refer to Fees and Funding section)"
    except: data['scholarship_availability'] = "NA"

    # Entry Requirements - Specific fields
    
    try:
        entry_tab = soup.select_one("#entry-tab2")
        if entry_tab:
            entry_text = entry_tab.get_text()
            
            # min_ielts
            if "IELTS" in entry_text:
                for li in entry_tab.select("li"):
                    if "IELTS" in li.get_text():
                        data['min_ielts'] = li.get_text(strip=True)
                        break
            else: data['min_ielts'] = "NA"
        else:
            data['min_ielts'] = "NA"
    except: data['min_ielts'] = "NA"

    # Default others to NA if not found on main page
    fields_to_default = [
        'gre_gmat_mandatory_min_score', 'indian_regional_institution_restrictions',
        'class_12_boards_accepted', 'gap_year_max_accepted', 'min_duolingo',
        'english_waiver_class12', 'english_waiver_moi', 'kaplan_test_of_english',
        'min_pte', 'min_toefl', 'ug_academic_min_gpa', 'twelfth_pass_min_cgpa',
        'mandatory_work_exp', 'max_backlogs'
    ]
    for field in fields_to_default:
        data[field] = "NA"

    # Log missing fields
    for k, v in data.items():
        if v == "NA":
            logger.warning(f"Field '{k}' missing for {url}")

    return data

def save_output(data):
    """Save the list of course objects to a JSON file."""
    if not data:
        logger.error("No data to save.")
        return
    
    # Deduplicate by URL
    seen_urls = set()
    unique_data = []
    for item in data:
        if item['course_website_url'] not in seen_urls:
            unique_data.append(item)
            seen_urls.add(item['course_website_url'])
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_data[:5], f, indent=4)
    logger.info(f"Saved {len(unique_data[:5])} courses to {OUTPUT_FILE}")

def main():
    logger.info("Starting Coventry University Scraper")
    session = requests.Session()
    
    try:
        course_urls = discover_course_urls(session)
        if not course_urls:
            logger.error("Could not find any course URLs.")
            return

        logger.info(f"Found {len(course_urls)} course URLs. Processing top 5.")
        
        results = []
        for url in course_urls[:5]:
            logger.info(f"Processing: {url}")
            html = fetch_page(session, url)
            if html:
                course_data = extract_course_data(html, url)
                results.append(course_data)
            else:
                logger.error(f"Skipping {url} due to fetch failure.")
        
        save_output(results)
        logger.info("Scraper execution completed successfully.")
        
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
