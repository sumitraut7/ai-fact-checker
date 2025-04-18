# tools/scrape_url.py
import requests
from bs4 import BeautifulSoup
import re

def scrape_url(url: str, max_length: int = 4000) -> str:
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        text = "\n".join(line for line in text.splitlines() if line.strip())

        return text[:max_length]  # Limit to avoid LLM overload
    except Exception as e:
        print(f"[scrape_url] Failed to fetch {url}: {e}")
        return ""

def extract_percentage(value: str) -> int:
    # Remove any non-digit/decimal/percent characters
    value = value.strip()

    # Handle percentage values like '76.5%' or '00076.5%'
    if "%" in value:
        numeric = re.findall(r"[\d\.]+", value)
        if numeric:
            pct = float(numeric[0])
        else:
            pct = 0.0
    else:
        # Value like 0.25 (assume it's a fraction)
        numeric = re.findall(r"[\d\.]+", value)
        if numeric:
            pct = float(numeric[0]) * 100
        else:
            pct = 0.0

    # Clamp between 0 and 100 and round
    pct = round(pct)
    return max(0, min(pct, 100))