import os
import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Mistral API key
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

def search_web(query, num_results=5):
    """
    Perform a web search and return relevant results
    
    Args:
        query (str): Search query
        num_results (int): Number of results to return
        
    Returns:
        list: List of search results with title, snippet, and URL
    """
    try:
        # Construct search URL (using DuckDuckGo as it doesn't require API key)
        search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        # Request headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Send request
        response = requests.get(search_url, headers=headers)
        
        if response.status_code == 200:
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results
            results = []
            result_elements = soup.select('.result')
            
            for element in result_elements[:num_results]:
                # Extract title
                title_element = element.select_one('.result__title')
                title = title_element.get_text().strip() if title_element else "No title"
                
                # Extract URL
                url_element = element.select_one('.result__url')
                url = url_element.get_text().strip() if url_element else ""
                
                # If URL is relative or incomplete, try to get it from the link
                if not url.startswith('http'):
                    link_element = element.select_one('a.result__a')
                    if link_element and 'href' in link_element.attrs:
                        url = link_element['href']
                
                # Extract snippet
                snippet_element = element.select_one('.result__snippet')
                snippet = snippet_element.get_text().strip() if snippet_element else "No description"
                
                # Add to results
                if title != "No title" and url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
            
            return results
        
        # Fallback to Bing if DuckDuckGo fails
        return search_bing(query, num_results)
    
    except Exception as e:
        print(f"Error in web search: {str(e)}")
        # Fallback to Bing
        return search_bing(query, num_results)

def search_bing(query, num_results=5):
    """
    Fallback search using Bing
    
    Args:
        query (str): Search query
        num_results (int): Number of results to return
        
    Returns:
        list: List of search results with title, snippet, and URL
    """
    try:
        # Construct search URL
        search_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
        
        # Request headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.bing.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Send request
        response = requests.get(search_url, headers=headers)
        
        if response.status_code == 200:
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results
            results = []
            result_elements = soup.select('.b_algo')
            
            for element in result_elements[:num_results]:
                # Extract title
                title_element = element.select_one('h2')
                title = title_element.get_text().strip() if title_element else "No title"
                
                # Extract URL
                url_element = element.select_one('a')
                url = url_element['href'] if url_element and 'href' in url_element.attrs else ""
                
                # Extract snippet
                snippet_element = element.select_one('.b_caption p')
                snippet = snippet_element.get_text().strip() if snippet_element else "No description"
                
                # Add to results
                if title != "No title" and url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
            
            return results
        
        return []
    
    except Exception as e:
        print(f"Error in Bing search: {str(e)}")
        return []

def get_webpage_content(url):
    """
    Get content from a webpage
    
    Args:
        url (str): URL to fetch
        
    Returns:
        str: Extracted text content
    """
    try:
        # Request headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Send request
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading and trailing space
            lines = (line.strip() for line in text.splitlines())
            
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit to 2000 characters
            return text[:2000]
        
        return ""
    
    except Exception as e:
        print(f"Error fetching webpage: {str(e)}")
        return ""

def generate_content_with_references(article_content, url, complexity):
    """
    Generate content with web search references using Mistral API
    
    Args:
        article_content (dict): Article content
        url (str): Source URL
        complexity (dict): Article complexity metrics
        
    Returns:
        str: Generated content with references
    """
    try:
        # Extract main topics from article
        title = article_content['title']
        content = article_content['content']
        
        # Create search queries based on title and content
        search_queries = []
        
        # Add title as first query
        search_queries.append(title)
        
        # Extract potential subtopics from content
        paragraphs = content.split('\n\n')
        for i, para in enumerate(paragraphs[:3]):  # Use first 3 paragraphs
            if len(para) > 100:  # Only substantial paragraphs
                # Extract first sentence
                first_sentence = re.split(r'[.!?]', para)[0]
                if len(first_sentence) > 30:  # Only meaningful sentences
                    search_queries.append(first_sentence)
        
        # Ensure we have at least 2 queries
        if len(search_queries) < 2:
            search_queries.append(f"{title} technology news")
        
        # Limit to 3 queries
        search_queries = search_queries[:3]
        
        # Perform web searches
        all_results = []
        for query in search_queries:
            results = search_web(query, 3)  # Get top 3 results per query
            all_results.extend(results)
        
        # Remove duplicates
        unique_results = []
        seen_urls = set()
        for result in all_results:
            if result['url'] not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result['url'])
        
        # Limit to top 5 results
        top_results = unique_results[:5]
        
        # Fetch additional content from top results
        for result in top_results:
            additional_content = get_webpage_content(result['url'])
            if additional_content:
                result['content'] = additional_content
            else:
                result['content'] = result['snippet']
        
        # Adjust hook length based on article complexity and length
        hook_instruction = ""
        if complexity['length'] == 'short' and complexity['complexity'] == 'simple':
            hook_instruction = "Start with a very short, punchy hook (1 sentence max)"
        elif complexity['length'] == 'long' or complexity['complexity'] == 'complex':
            hook_instruction = "Start with a medium-length hook (2 sentences) that captures the complexity of the topic"
        else:
            hook_instruction = "Start with a short hook (1 sentence) that is catchy and informative"
        
        # Prepare source attribution instruction
        source_instruction = ""
        if url:
            source_name = article_content.get('source_name', 'Source')
            source_instruction = f"Include the source at the end in this exact format: 'Source: {source_name} ({url})'"
        else:
            source_instruction = "If no source URL is provided, suggest some potential sources based on the content in this format: 'Source: [Source Name] (link)'"
        
        # Prepare references for prompt
        references_text = ""
        for i, ref in enumerate(top_results):
            references_text += f"Reference {i+1}:\nTitle: {ref['title']}\nURL: {ref['url']}\nContent: {ref['content'][:500]}...\n\n"
        
        # Prepare prompt for Mistral
        prompt = f"""
        Create a WhatsApp-friendly summary of this tech/AI article with the following requirements:
        
        1. {hook_instruction}. NO greetings or introductions.
        2. Format the content with proper structure, including:
           - Bold text for important points using *asterisks*
           - Use emojis sparingly (maximum 3-4 total) and only when they add value
           - Include 3-5 key points from the article
        3. End with "Why it matters" section
        4. {source_instruction}
        5. Use the provided references to enhance the content with additional context and facts
        
        Article Title: {article_content['title']}
        Article URL: {url}
        Article Content: {article_content['content'][:3000]}
        
        Additional References:
        {references_text}
        
        Make it concise but informative, perfect for sharing in a WhatsApp group about tech and AI news.
        """
        
        # Call Mistral API
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {MISTRAL_API_KEY}"
        }
        
        payload = {
            "model": "mistral-large-latest",
            "messages": [
                {"role": "system", "content": "You are a tech news summarizer that creates engaging, well-formatted content for WhatsApp sharing. You use minimal emojis, bold formatting with *asterisks*, and create catchy hooks. You start directly with the hook, no greetings or introductions. You ALWAYS include the source with the exact URL at the end in the format 'Source: [Source Name] (URL)'. You incorporate information from multiple references to create comprehensive, well-researched content."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            formatted_content = result["choices"][0]["message"]["content"]
            return formatted_content
        else:
            print(f"Mistral API error: {response.status_code} - {response.text}")
            return "Unable to generate content with references. Please try again or switch to ChatGPT model."
            
    except Exception as e:
        print(f"Error generating content with references: {str(e)}")
        return f"Error generating content with references: {str(e)}"

# Example usage
if __name__ == "__main__":
    # Test the function
    results = search_web("AI-powered rollups startup")
    print(json.dumps(results, indent=2))
