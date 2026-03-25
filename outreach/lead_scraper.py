"""
Synaptix AI — Local Business Lead Scraper
==========================================
Scrapes Google Maps for home service businesses in Baltimore County area.
Outputs a CSV of leads ready for outreach.

Usage:
    python lead_scraper.py                    # Default: all trades, Baltimore County
    python lead_scraper.py --trade plumber    # Specific trade
    python lead_scraper.py --area "Towson MD" # Specific area
"""

import csv
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

# Target areas around UMBC
AREAS = [
    "Catonsville MD",
    "Baltimore MD",
    "Ellicott City MD",
    "Towson MD",
    "Arbutus MD",
    "Columbia MD",
    "Dundalk MD",
    "Parkville MD",
    "Owings Mills MD",
    "Pikesville MD",
]

# Home service trades to target
TRADES = [
    "HVAC",
    "plumber",
    "electrician",
    "roofing contractor",
    "landscaping",
    "house painter",
    "home remodeling",
    "pest control",
    "garage door repair",
    "handyman",
    "carpet cleaning",
    "window cleaning",
    "gutter cleaning",
    "tree service",
    "fence contractor",
]

OUTPUT_DIR = Path(__file__).parent
CSV_FILE = OUTPUT_DIR / "leads.csv"


def search_google_maps_free(query: str, limit: int = 5) -> list[dict]:
    """
    Search for businesses using Google's unofficial Places autocomplete.
    For production, use Google Places API ($17/1000 requests) or alternatives.

    This version uses a simple web search approach that doesn't require an API key.
    """
    # Note: For actual scraping, you'd want to use one of:
    # 1. Google Places API (paid, most reliable)
    # 2. Yelp Fusion API (free tier: 5000 calls/day)
    # 3. SerpAPI (free tier: 100 searches/month)
    # 4. Manual search + browser automation

    # For now, generate a structured search task list
    return [{
        "query": query,
        "note": "Search this on Google Maps and add results to leads.csv"
    }]


def generate_search_tasks() -> list[dict]:
    """Generate all search queries to run manually or with an API."""
    tasks = []
    for trade in TRADES:
        for area in AREAS:
            query = f"{trade} near {area}"
            tasks.append({
                "trade": trade,
                "area": area,
                "query": query,
                "google_maps_url": f"https://www.google.com/maps/search/{urllib.parse.quote(query)}",
            })
    return tasks


def create_leads_csv():
    """Create an empty leads CSV with headers."""
    headers = [
        "business_name", "trade", "owner_name", "phone", "email",
        "website", "address", "area", "google_rating", "review_count",
        "has_website_form", "response_time_guess", "notes",
        "outreach_status", "outreach_date", "follow_up_date"
    ]
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
    print(f"Created {CSV_FILE}")


def add_lead(business_name: str, trade: str, phone: str = "", email: str = "",
             website: str = "", address: str = "", area: str = "",
             rating: str = "", reviews: str = "", notes: str = ""):
    """Add a lead to the CSV."""
    row = [
        business_name, trade, "", phone, email, website, address, area,
        rating, reviews, "", "", notes, "new", "", ""
    ]
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def print_search_tasks():
    """Print all Google Maps search URLs to manually find leads."""
    tasks = generate_search_tasks()
    print(f"\n{'='*60}")
    print(f"  SYNAPTIX AI — Lead Search Tasks")
    print(f"  {len(tasks)} searches across {len(AREAS)} areas x {len(TRADES)} trades")
    print(f"{'='*60}\n")

    for i, task in enumerate(tasks, 1):
        print(f"  {i:3d}. {task['query']}")
        print(f"       {task['google_maps_url']}")
        print()

    print(f"\nInstructions:")
    print(f"1. Open each Google Maps URL above")
    print(f"2. For each business, note: name, phone, website, rating")
    print(f"3. Add them to leads.csv using: python lead_scraper.py --add")
    print(f"\nOr use the Yelp API approach below for automation.\n")


def setup_yelp_scraper():
    """Print instructions for Yelp Fusion API (free, 5000 calls/day)."""
    print("""
    ============================================
    AUTOMATED LEAD SCRAPING WITH YELP API (FREE)
    ============================================

    1. Go to: https://www.yelp.com/developers/v3/manage_app
    2. Create a free account and app
    3. Get your API key
    4. Set environment variable: YELP_API_KEY=your_key_here
    5. Run: python lead_scraper.py --yelp

    Free tier: 5,000 API calls per day (plenty for local scraping)

    Alternative free options:
    - SerpAPI: 100 free searches/month (https://serpapi.com)
    - Google Places: $200 free credit/month (https://console.cloud.google.com)
    """)


def scrape_yelp(api_key: str):
    """Scrape Yelp Fusion API for home service businesses."""
    import os

    if not api_key:
        api_key = os.environ.get("YELP_API_KEY", "")

    if not api_key:
        print("Error: Set YELP_API_KEY environment variable first")
        setup_yelp_scraper()
        return

    base_url = "https://api.yelp.com/v3/businesses/search"
    total_leads = 0

    for trade in TRADES:
        for area in AREAS:
            params = urllib.parse.urlencode({
                "term": trade,
                "location": area,
                "limit": 10,
                "sort_by": "rating",
            })
            url = f"{base_url}?{params}"

            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            })

            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    businesses = data.get("businesses", [])

                    for biz in businesses:
                        add_lead(
                            business_name=biz.get("name", ""),
                            trade=trade,
                            phone=biz.get("phone", ""),
                            website=biz.get("url", ""),
                            address=", ".join(biz.get("location", {}).get("display_address", [])),
                            area=area,
                            rating=str(biz.get("rating", "")),
                            reviews=str(biz.get("review_count", "")),
                        )
                        total_leads += 1

                print(f"  {trade} in {area}: {len(businesses)} businesses found")
                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"  Error: {trade} in {area}: {e}")
                time.sleep(1)

    print(f"\nDone! {total_leads} leads saved to {CSV_FILE}")


def main():
    args = sys.argv[1:]

    if not CSV_FILE.exists():
        create_leads_csv()

    if "--yelp" in args:
        api_key = ""
        for i, a in enumerate(args):
            if a == "--key" and i + 1 < len(args):
                api_key = args[i + 1]
        scrape_yelp(api_key)

    elif "--tasks" in args or len(args) == 0:
        print_search_tasks()

    elif "--setup" in args:
        setup_yelp_scraper()

    elif "--create" in args:
        create_leads_csv()
        print("Fresh leads.csv created")

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
