import os
import requests
import urllib.parse
import random
import string
from dotenv import load_dotenv

load_dotenv()

BING_API_KEY = os.getenv('BING_API_KEY', '')


def generate_random_string(length: int = 10) -> str:
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def search_bing_images(query: str, count: int = 5):
    try:
        if not BING_API_KEY:
            return search_bing_images_fallback(query, count)

        endpoint = "https://api.bing.microsoft.com/v7.0/images/search"
        headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
        params = {
            "q": query,
            "count": count,
            "offset": 0,
            "mkt": "en-US",
            "safeSearch": "Moderate",
        }
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        image_urls = []
        if "value" in data:
            for image in data["value"]:
                image_urls.append(image.get("contentUrl"))
        return image_urls
    except Exception as e:
        print(f"Bing Image Search API error: {e}")
        return search_bing_images_fallback(query, count)


def search_bing_images_fallback(query: str, count: int = 5):
    try:
        random_param = generate_random_string()
        search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&form=HDRSC2&first=1&tsc=ImageHoverTitle&rand={random_param}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            content = response.text
            image_urls = []
            start_marker = '"murl":"'
            end_marker = '"'
            start_index = 0
            for _ in range(count):
                start_index = content.find(start_marker, start_index)
                if start_index == -1:
                    break
                start_index += len(start_marker)
                end_index = content.find(end_marker, start_index)
                if end_index != -1:
                    image_url = content[start_index:end_index].replace('\\', '')
                    if image_url.startswith('http') and image_url not in image_urls:
                        image_urls.append(image_url)
                    start_index = end_index
            return image_urls[:count]
        return []
    except Exception as e:
        print(f"Bing Image fallback error: {e}")
        return []


essential_terms = ["technology", "tech", "digital", "AI", "artificial intelligence"]


def get_tech_ai_images(query: str, title: str = "", count: int = 5):
    try:
        terms = [query]
        if title:
            terms.append(title)
        lower_query = query.lower()
        for term in essential_terms:
            if term.lower() not in lower_query:
                terms.append(term)
                break
        final_query = " ".join(terms[:3])
        return search_bing_images(final_query, count)
    except Exception as e:
        print(f"get_tech_ai_images error: {e}")
        return []


