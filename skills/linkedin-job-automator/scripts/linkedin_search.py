import argparse
import urllib.parse

def generate_linkedin_url(keywords, location):
    base_url = "https://www.linkedin.com/jobs/search/?"
    params = {
        "keywords": keywords,
        "location": location,
        "f_AL": "true"  # Filter for Easy Apply
    }
    return base_url + urllib.parse.urlencode(params)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate LinkedIn Job Search URLs")
    parser.add_argument("--keywords", type=str, required=True, help="Job keywords")
    parser.add_argument("--location", type=str, required=True, help="Job location")
    
    args = parser.parse_args()
    
    url = generate_linkedin_url(args.keywords, args.location)
    print(f"Search URL (Easy Apply filtered):")
    print(url)
