import os
import requests
import json
import urllib.parse
import random
import string
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bing Search API key
# In production, this should be stored as an environment variable
BING_API_KEY = os.getenv('BING_API_KEY', '')

def generate_random_string(length=10):
    """Generate a random string for cache busting"""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def search_bing_images(query, count=5):
    """
    Search for images using Bing Image Search API
    
    Args:
        query (str): Search query
        count (int): Number of images to return
        
    Returns:
        list: List of image URLs
    """
    try:
        # If no API key is available, use fallback method
        if not BING_API_KEY:
            return search_bing_images_fallback(query, count)
        
        # Bing Image Search API endpoint
        endpoint = "https://api.bing.microsoft.com/v7.0/images/search"
        
        # Request headers
        headers = {
            "Ocp-Apim-Subscription-Key": BING_API_KEY
        }
        
        # Request parameters
        params = {
            "q": query,
            "count": count,
            "offset": 0,
            "mkt": "en-US",
            "safeSearch": "Moderate"
        }
        
        # Send request
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        
        # Parse response
        search_results = response.json()
        
        # Extract image URLs
        image_urls = []
        if "value" in search_results:
            for image in search_results["value"]:
                image_urls.append(image["contentUrl"])
        
        return image_urls
    
    except Exception as e:
        print(f"Error in Bing Image Search API: {str(e)}")
        # Fall back to alternative method if API fails
        return search_bing_images_fallback(query, count)

def search_bing_images_fallback(query, count=5):
    """
    Fallback method to search for images using Bing web search
    
    Args:
        query (str): Search query
        count (int): Number of images to return
        
    Returns:
        list: List of image URLs
    """
    try:
        # Add a random parameter to avoid caching
        random_param = generate_random_string()
        
        # Construct search URL
        search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&form=HDRSC2&first=1&tsc=ImageHoverTitle&rand={random_param}"
        
        # Request headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.bing.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        # Send request
        response = requests.get(search_url, headers=headers)
        
        if response.status_code == 200:
            # Extract image URLs using string manipulation (simple approach)
            content = response.text
            image_urls = []
            
            # Look for image URLs in the response
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
                    if image_url not in image_urls and image_url.startswith('http'):
                        image_urls.append(image_url)
                    
                    start_index = end_index
            
            return image_urls[:count]
        
        return []
    
    except Exception as e:
        print(f"Error in Bing Image Search fallback: {str(e)}")
        return []

def get_tech_ai_images(query, title="", count=5):
    """
    Get relevant tech/AI images based on query and title
    
    Args:
        query (str): Main search query
        title (str): Article title for additional context
        count (int): Number of images to return
        
    Returns:
        list: List of image URLs
    """
    try:
        # Combine query with tech/AI keywords for better results
        search_terms = []
        
        # Add the main query
        search_terms.append(query)
        
        # Add title if provided
        if title:
            search_terms.append(title)
        
        # Add tech/AI related terms if not already in query
        tech_terms = ["technology", "tech", "digital", "AI", "artificial intelligence"]
        query_lower = query.lower()
        
        for term in tech_terms:
            if term.lower() not in query_lower:
                search_terms.append(term)
                break
        
        # Construct final search query
        final_query = " ".join(search_terms[:3])  # Limit to 3 terms for better results
        
        # Search for images
        return search_bing_images(final_query, count)
    
    except Exception as e:
        print(f"Error getting tech/AI images: {str(e)}")
        return []

# Example usage
if __name__ == "__main__":
    # Test the function
    images = get_tech_ai_images("AI-powered rollups", "Early AI investor finds his next big bet")
    print(images)
