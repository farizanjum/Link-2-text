from flask import Blueprint, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import random
import openai
import os
import json
import shutil
import urllib.parse
import os
from newspaper import Article
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from Routes.bing_search import get_tech_ai_images
from Routes.web_search import generate_content_with_references
from dotenv import load_dotenv
from base64 import b64decode
from openai import OpenAI

api_bp = Blueprint('api', __name__)

load_dotenv() # Loads variables from .env

openai_key = os.getenv("OPENAI_API_KEY")
mistral_key = os.getenv("MISTRAL_API_KEY")
BASIC_AUTH_USERNAME = os.getenv("BASIC_AUTH_USERNAME")
BASIC_AUTH_PASSWORD = os.getenv("BASIC_AUTH_PASSWORD")

# Headers for web scraping
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Path to saved cover images
COVER_IMAGES_DIR = '/home/ubuntu/upload/search_images'
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Static')
STATIC_IMAGES_DIR = os.path.join(STATIC_DIR, 'images')
TECH_LOGOS_DIR = os.path.join(STATIC_IMAGES_DIR, 'tech_logos')

# Ensure static images directory exists
os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
os.makedirs(TECH_LOGOS_DIR, exist_ok=True)

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# Copy cover images to static directory for serving
def copy_cover_images():
    if os.path.exists(COVER_IMAGES_DIR):
        for filename in os.listdir(COVER_IMAGES_DIR):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                src_path = os.path.join(COVER_IMAGES_DIR, filename)
                dst_path = os.path.join(STATIC_IMAGES_DIR, filename)
                if not os.path.exists(dst_path):
                    shutil.copy2(src_path, dst_path)

# Copy images on module load
copy_cover_images()

@api_bp.route('/process', methods=['POST'])
def process_url():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get model selection (default to ChatGPT if not specified)
    model = data.get('model', 'chatgpt')
    
    # Check if web search is enabled
    use_web_search = data.get('use_web_search', False)

    # Enforce Basic Auth only for ChatGPT model
    if model.lower() == 'chatgpt':
        auth_header = request.headers.get('Authorization', '')
        if not _is_authorized(auth_header):
            return jsonify({'error': 'Unauthorized: ChatGPT requires login'}), 401
    
    # Check if URL or text is provided
    if 'url' in data and data['url']:
        # Process URL
        try:
            article_content = extract_article_content(data['url'])
            
            if not article_content:
                return jsonify({'error': 'Could not extract content from the provided URL'}), 400
            
            # Extract keywords for image search
            keywords = extract_keywords(article_content)
            
            # Determine article complexity and length
            complexity = determine_complexity(article_content)
            
            # Get cover image using OpenGraph metadata first
            image_urls = get_article_images(data['url'])
            
            # Add tech logo images
            tech_logo_urls = get_tech_logo_images()
            
            # If no OpenGraph images, use Bing image search as fallback
            if not image_urls or len(image_urls) < 3:
                # Create a search query from keywords and title
                search_query = ' '.join(keywords[:3])
                bing_images = get_tech_ai_images(search_query, article_content['title'], 5)
                
                # Combine OpenGraph and Bing images, removing duplicates
                if image_urls:
                    for img in bing_images:
                        if img not in image_urls:
                            image_urls.append(img)
                else:
                    image_urls = bing_images
            
            # Add tech logos to the image options
            for logo in tech_logo_urls:
                if logo not in image_urls:
                    image_urls.append(logo)
            
            # Generate formatted content with adaptive hook and proper source link
            if use_web_search:
                # Use web search for either model
                formatted_content = generate_content_with_references(article_content, data['url'], complexity)
            else:
                # Use standard model without web search
                if model.lower() == 'mistral':
                    formatted_content = generate_formatted_content_mistral(article_content, data['url'], complexity)
                else:
                    formatted_content = generate_formatted_content_chatgpt(article_content, data['url'], complexity)
            
            return jsonify({
                'formatted_content': formatted_content,
                'image_urls': image_urls,
                'title': article_content['title'],
                'keywords': keywords,
                'source_url': data['url']
            })
        
        except Exception as e:
            print(f"Error processing URL: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    elif 'text' in data and data['text']:
        # Process direct text input
        try:
            # Create a content object similar to what extract_article_content returns
            text_content = {
                'title': data.get('title', 'User Provided Text'),
                'url': '',
                'content': data['text']
            }
            
            # Extract keywords for image search
            keywords = extract_keywords(text_content)
            
            # Determine text complexity and length
            complexity = determine_complexity(text_content)
            
            # Get tech logo images
            tech_logo_urls = get_tech_logo_images()
            
            # Get relevant images based on keywords and title using Bing
            search_query = ' '.join(keywords[:3])
            image_urls = get_tech_ai_images(search_query, text_content['title'], 5)
            
            # Add tech logos to the image options
            for logo in tech_logo_urls:
                if logo not in image_urls:
                    image_urls.append(logo)
            
            # If no images found, use local images as fallback
            if not image_urls:
                image_urls = get_local_images()
            
            # Generate formatted content with adaptive hook and proper source attribution
            if use_web_search:
                # Use web search for either model
                formatted_content = generate_content_with_references(text_content, '', complexity)
            else:
                # Use standard model without web search
                if model.lower() == 'mistral':
                    formatted_content = generate_formatted_content_mistral(text_content, '', complexity)
                else:
                    formatted_content = generate_formatted_content_chatgpt(text_content, '', complexity)
            
            return jsonify({
                'formatted_content': formatted_content,
                'image_urls': image_urls,
                'title': text_content['title'],
                'keywords': keywords
            })
        
        except Exception as e:
            print(f"Error processing text: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    elif 'format_only' in data and data['format_only'] and 'text' in data:
        # Format-only mode using Mistral
        try:
            text_content = {
                'title': data.get('title', 'Text Formatting'),
                'content': data['text']
            }
            
            # Use Mistral for formatting only
            formatted_content = format_text_only_mistral(text_content)
            
            return jsonify({
                'formatted_content': formatted_content
            })
        
        except Exception as e:
            print(f"Error formatting text: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    else:
        return jsonify({'error': 'Either URL or text is required'}), 400

def extract_article_content(url):
    try:
        # Use newspaper3k for article extraction
        article = Article(url)
        article.download()
        article.parse()
        
        # Extract source name (domain name)
        domain = urllib.parse.urlparse(url).netloc
        source_name = domain.replace('www.', '').split('.')[0].capitalize()
        
        # Combine title and article
        content = {
            'title': article.title,
            'url': url,
            'content': article.text,
            'source_name': source_name
        }
        
        return content
    
    except Exception as e:
        print(f"Error extracting content with newspaper3k: {str(e)}")
        
        # Fallback to BeautifulSoup if newspaper3k fails
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Extract title
            title = soup.title.string if soup.title else ""
            
            # Extract main content (this is a simplified approach)
            # For better results, you might need site-specific extractors
            article = ""
            
            # Try to find article content in common containers
            article_containers = soup.find_all(['article', 'div', 'section'], 
                                          class_=re.compile(r'article|content|post|entry|main'))
            
            if article_containers:
                for container in article_containers:
                    paragraphs = container.find_all('p')
                    for p in paragraphs:
                        article += p.get_text() + "\n\n"
            
            # If no article containers found, try to get all paragraphs
            if not article:
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    if len(p.get_text()) > 50:  # Only include substantial paragraphs
                        article += p.get_text() + "\n\n"
            
            # Extract source name (domain name)
            domain = urllib.parse.urlparse(url).netloc
            source_name = domain.replace('www.', '').split('.')[0].capitalize()
            
            # Combine title and article
            content = {
                'title': title,
                'url': url,
                'content': article.strip(),
                'source_name': source_name
            }
            
            return content
        
        except Exception as fallback_error:
            print(f"Error in fallback extraction: {str(fallback_error)}")
            return None

def extract_keywords(article_content):
    """
    Extract relevant keywords from article content for image search
    """
    try:
        # Combine title and content for keyword extraction
        text = article_content['title'] + " " + article_content['content']
        
        # Tokenize and convert to lowercase
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and non-alphabetic tokens
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [word for word in tokens if word.isalpha() and word not in stop_words and len(word) > 3]
        
        # Count word frequencies
        word_freq = Counter(filtered_tokens)
        
        # Get the most common words (keywords)
        keywords = [word for word, count in word_freq.most_common(5)]
        
        # Add tech/AI related terms if they're in the title
        tech_terms = ['ai', 'artificial intelligence', 'machine learning', 'technology', 'tech', 'digital']
        title_lower = article_content['title'].lower()
        for term in tech_terms:
            if term in title_lower and term not in keywords:
                keywords.append(term)
        
        # Ensure we have at least 2 keywords
        if len(keywords) < 2:
            keywords.extend(['technology', 'digital'])
            keywords = keywords[:5]  # Limit to 5 keywords
        
        return keywords
    
    except Exception as e:
        print(f"Error extracting keywords: {str(e)}")
        return ['technology', 'digital']  # Default fallback keywords

def determine_complexity(article_content):
    """
    Determine article complexity and length to adjust hook length
    """
    content = article_content['content']
    word_count = len(content.split())
    
    # Calculate average sentence length
    sentences = content.split('.')
    if len(sentences) > 0:
        avg_sentence_length = word_count / len(sentences)
    else:
        avg_sentence_length = 0
    
    # Calculate average word length
    words = content.split()
    if len(words) > 0:
        avg_word_length = sum(len(word) for word in words) / len(words)
    else:
        avg_word_length = 0
    
    # Determine complexity based on word count, sentence length, and word length
    if word_count < 300:
        length = 'short'
    elif word_count < 800:
        length = 'medium'
    else:
        length = 'long'
    
    if avg_sentence_length < 15 and avg_word_length < 5:
        complexity = 'simple'
    elif avg_sentence_length > 25 or avg_word_length > 6:
        complexity = 'complex'
    else:
        complexity = 'moderate'
    
    return {
        'length': length,
        'complexity': complexity,
        'word_count': word_count
    }

def generate_formatted_content_chatgpt(article_content, url, complexity):
    try:
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
            source_instruction = "If no source URL is provided, do not include any source attribution or links"
        
        # Prepare prompt for OpenAI
        prompt = f"""
        Create a WhatsApp-friendly summary of this tech/AI article with the following requirements:
        
        1. {hook_instruction}. NO greetings or introductions.
        2. Format the content with proper structure, including:
           - Bold text for important points using *asterisks*
           - Use emojis sparingly (maximum 3-4 total) and only when they add value
           - Include 3-5 key points from the article, each on a new line with a bullet point emoji (like 🔹, 📌, or 🔸)
           - Format key points like this: "🔹 *Key point title or first few words* rest of the point description"
        3. End with a "Why it matters" section, preceded by an appropriate emoji like 🔍 or 💡
        4. {source_instruction}
        
        Article Title: {article_content['title']}
        Article URL: {url}
        Article Content: {article_content['content'][:4000]}  # Limit content to avoid token limits
        
        Make it concise but informative, perfect for sharing in a WhatsApp group about tech and AI news.
        Follow this exact formatting style:
        
        🎥 *Microsoft Bing* just levelled up with its new *free AI video generator* powered by OpenAI's Sora model!

        🌟 *Key Points:*
        - *Bing Video Creator* turns text prompts into videos, now available in the Bing app.
        - First free access to OpenAI's Sora video generation, exclusive to Microsoft Bing.
        - *10 free video clips* for all Microsoft account users, then 100 Microsoft Rewards points per video.
        - Videos generated in vertical 9:16 ratio, perfect for *TikTok and Instagram*. Horizontal uploads coming soon.
        - Initial limitations: *desktop unavailability*, *long generation times*, and *fixed 5-second duration*.

        *Why it matters:* Microsoft's integration of Sora opens up AI video generation to a wider audience, showcasing the growing accessibility of AI tools in everyday platforms and encouraging more user engagement and creativity.

        Source: TechCrunch (https://techcrunch.com/2025/06/02/microsoft-bing-gets-a-free-sora-powered-ai-video-generator/)
        """
        
        # Call OpenAI API
        try:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a tech news summarizer that creates engaging, well-formatted content for WhatsApp sharing. You use minimal emojis, bold formatting with *asterisks*, and create catchy hooks. You start directly with the hook, no greetings or introductions. You ALWAYS include the source with the exact URL at the end in the format 'Source: [Source Name] (URL)'. NEVER include fake or made-up sources. Follow the exact formatting style shown in the examples."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            
            # Extract and return the generated content
            formatted_content = response.choices[0].message.content
            return formatted_content
        except Exception as api_error:
            print(f"OpenAI API error: {str(api_error)}")
            # Return a more user-friendly error message
            return "Unable to generate content with ChatGPT. Please try again or switch to Mistral model."
    
    except Exception as e:
        print(f"Error in content generation function: {str(e)}")
        return f"Error generating content: {str(e)}"

def generate_formatted_content_mistral(article_content, url, complexity):
    try:
        # Adjust hook length based on article complexity and length
        hook_instruction = ""
        if complexity['length'] == 'short' and complexity['complexity'] == 'simple':
            hook_instruction = "Start with a very short, punchy hook (1 sentence max)"
        elif complexity['length'] == 'long' or complexity['complexity'] == 'complex':
            hook_instruction = "Start with a medium-length hook (2 sentences) that captures the complexity of the topic"
        else:
            hook_instruction = "Start with a short hook (1 sentence) that is catchy and informative"
        
        # Prepare source attribution instruction - FIXED to prevent fake sources
        source_instruction = ""
        if url:
            source_name = article_content.get('source_name', 'Source')
            source_instruction = f"Include ONLY this exact source at the end: 'Source: {source_name} ({url})'. DO NOT add any other sources, references, or links."
        else:
            source_instruction = "If no source URL is provided, do not include any source attribution or links. DO NOT make up or suggest any sources."
        
        # Prepare prompt for Mistral
        prompt = f"""
        Create a WhatsApp-friendly summary of this tech/AI article with the following requirements:
        
        1. {hook_instruction}. NO greetings or introductions.
        2. Format the content with proper structure, including:
           - Bold text for important points using *asterisks*
           - Use emojis sparingly (maximum 3-4 total) and only when they add value
           - Include 3-5 key points from the article, each on a new line with a bullet point emoji (like 🔹, 📌, or 🔸)
           - Format key points like this: "🔹 *Key point title or first few words* rest of the point description"
        3. End with a "Why it matters" section, preceded by an appropriate emoji like 🔍 or 💡
        4. {source_instruction}
        
        Article Title: {article_content['title']}
        Article URL: {url}
        Article Content: {article_content['content'][:4000]}  # Limit content to avoid token limits
        
        Make it concise but informative, perfect for sharing in a WhatsApp group about tech and AI news.
        Follow this exact formatting style:
        
        🎥 *Microsoft Bing* just levelled up with its new *free AI video generator* powered by OpenAI's Sora model!

        🌟 *Key Points:*
        - *Bing Video Creator* turns text prompts into videos, now available in the Bing app.
        - First free access to OpenAI's Sora video generation, exclusive to Microsoft Bing.
        - *10 free video clips* for all Microsoft account users, then 100 Microsoft Rewards points per video.
        - Videos generated in vertical 9:16 ratio, perfect for *TikTok and Instagram*. Horizontal uploads coming soon.
        - Initial limitations: *desktop unavailability*, *long generation times*, and *fixed 5-second duration*.

        *Why it matters:* Microsoft's integration of Sora opens up AI video generation to a wider audience, showcasing the growing accessibility of AI tools in everyday platforms and encouraging more user engagement and creativity.

        Source: TechCrunch (https://techcrunch.com/2025/06/02/microsoft-bing-gets-a-free-sora-powered-ai-video-generator/)
        """
        
        # Call Mistral API
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {mistral_key}"
            }
            
            payload = {
                "model": "mistral-large-latest",
                "messages": [
                    {"role": "system", "content": "You are a tech news summarizer that creates engaging, well-formatted content for WhatsApp sharing. You use minimal emojis, bold formatting with *asterisks*, and create catchy hooks. You start directly with the hook, no greetings or introductions. IMPORTANT: You must ONLY include the exact source URL provided to you. NEVER add any other sources, references, or links. NEVER suggest alternative sources. If no source URL is provided, do not include any source attribution at all. Follow the exact formatting style shown in the examples."},
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
                
                # Post-process to ensure only the correct source is included
                if url:
                    # Check if there are any fake sources and remove them
                    source_pattern = r'Source: .*?\(.*?\)'
                    source_matches = re.findall(source_pattern, formatted_content)
                    
                    # If we have multiple sources or incorrect sources, fix them
                    if len(source_matches) > 1 or (len(source_matches) == 1 and url not in source_matches[0]):
                        # Remove all source attributions
                        formatted_content = re.sub(source_pattern, '', formatted_content)
                        # Add the correct source at the end
                        source_name = article_content.get('source_name', 'Source')
                        formatted_content = formatted_content.strip() + f"\n\nSource: {source_name} ({url})"
                    
                    # Check for suggested sources pattern and remove them
                    suggested_pattern = r'(?:Additional|Suggested|Recommended).*?(?:Sources?|References?|Context).*?:.*?(?:\n\n|\Z)'
                    formatted_content = re.sub(suggested_pattern, '', formatted_content, flags=re.DOTALL|re.IGNORECASE)
                else:
                    # If no URL was provided, remove any source attributions
                    source_pattern = r'Source: .*?(?:\n\n|\Z)'
                    formatted_content = re.sub(source_pattern, '', formatted_content, flags=re.DOTALL)
                    
                    # Remove any suggested sources
                    suggested_pattern = r'(?:Additional|Suggested|Recommended).*?(?:Sources?|References?|Context).*?:.*?(?:\n\n|\Z)'
                    formatted_content = re.sub(suggested_pattern, '', formatted_content, flags=re.DOTALL|re.IGNORECASE)
                
                return formatted_content.strip()
            else:
                print(f"Mistral API error: {response.status_code} - {response.text}")
                return "Unable to generate content with Mistral. Please try again or switch to ChatGPT model."
                
        except Exception as api_error:
            print(f"Mistral API error: {str(api_error)}")
            # Return a more user-friendly error message
            return "Unable to generate content with Mistral. Please try again or switch to ChatGPT model."
    
    except Exception as e:
        print(f"Error in Mistral content generation function: {str(e)}")
        return f"Error generating content with Mistral: {str(e)}"

def format_text_only_mistral(text_content):
    """
    Format text only using Mistral API (no content generation)
    """
    try:
        # Prepare prompt for Mistral
        prompt = f"""
        Format this text for WhatsApp sharing with the following requirements:
        
        1. Start with a short, catchy hook. NO greetings or introductions.
        2. Format the content with proper structure, including:
           - Bold text for important points using *asterisks*
           - Use emojis sparingly (maximum 3-4 total) and only when they add value
           - Include 3-5 key points, each on a new line with a bullet point emoji (like 🔹, 📌, or 🔸)
           - Format key points like this: "🔹 *Key point title or first few words* rest of the point description"
        3. End with a brief "Why it matters" section, preceded by an appropriate emoji like 🔍 or 💡
        
        Text Title: {text_content['title']}
        Text Content: {text_content['content'][:4000]}  # Limit content to avoid token limits
        
        Make it concise but informative, perfect for sharing in a WhatsApp group.
        Follow this exact formatting style:
        
        🎥 *Microsoft Bing* just levelled up with its new *free AI video generator* powered by OpenAI's Sora model!

        🌟 *Key Points:*
        - *Bing Video Creator* turns text prompts into videos, now available in the Bing app.
        - First free access to OpenAI's Sora video generation, exclusive to Microsoft Bing.
        - *10 free video clips* for all Microsoft account users, then 100 Microsoft Rewards points per video.
        - Videos generated in vertical 9:16 ratio, perfect for *TikTok and Instagram*. Horizontal uploads coming soon.
        - Initial limitations: *desktop unavailability*, *long generation times*, and *fixed 5-second duration*.

        *Why it matters:* Microsoft's integration of Sora opens up AI video generation to a wider audience, showcasing the growing accessibility of AI tools in everyday platforms and encouraging more user engagement and creativity.
        """
        
        # Call Mistral API
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {mistral_key}"
        }
        
        payload = {
            "model": "mistral-large-latest",
            "messages": [
                {"role": "system", "content": "You are a text formatter that creates engaging, well-structured content for WhatsApp sharing. You use minimal emojis, bold formatting with *asterisks*, and create catchy hooks. You start directly with the hook, no greetings or introductions. DO NOT add any sources, references, or links. Follow the exact formatting style shown in the examples."},
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
            
            # Remove any source attributions or suggested sources
            source_pattern = r'Source: .*?(?:\n\n|\Z)'
            formatted_content = re.sub(source_pattern, '', formatted_content, flags=re.DOTALL)
            
            suggested_pattern = r'(?:Additional|Suggested|Recommended).*?(?:Sources?|References?|Context).*?:.*?(?:\n\n|\Z)'
            formatted_content = re.sub(suggested_pattern, '', formatted_content, flags=re.DOTALL|re.IGNORECASE)
            
            return formatted_content.strip()
        else:
            print(f"Mistral API error: {response.status_code} - {response.text}")
            return f"Error formatting text: API returned status code {response.status_code}"
            
    except Exception as e:
        print(f"Error in text formatting function: {str(e)}")
        return f"Error formatting text: {str(e)}"

def get_article_images(url):
    """
    Extract images from article using OpenGraph metadata
    """
    try:
        # Use newspaper3k to extract top image
        article = Article(url)
        article.download()
        article.parse()
        
        images = []
        
        # Add top image if available
        if article.top_image:
            images.append(article.top_image)
        
        # Add other images if available
        if article.images:
            # Add up to 4 more images (5 total max)
            for img in list(article.images)[:4]:
                if img != article.top_image and img not in images:
                    images.append(img)
        
        # If we have images, return them
        if images:
            return images
        
        # If no images found, return empty list for fallback
        return []
    
    except Exception as e:
        print(f"Error extracting article images: {str(e)}")
        return []

def get_tech_logo_images():
    """
    Return paths to tech logo images
    """
    logo_urls = []
    
    # Get all image files from tech logos directory
    if os.path.exists(TECH_LOGOS_DIR):
        for filename in os.listdir(TECH_LOGOS_DIR):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                logo_urls.append(f'/images/tech_logos/{filename}')
    
    return logo_urls

def get_local_images():
    """
    Return paths to available cover images in the static directory
    """
    image_urls = []
    
    # Get all image files from static directory
    for filename in os.listdir(STATIC_IMAGES_DIR):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            image_urls.append(f'/images/{filename}')
    
    # Add tech logo images
    tech_logos = get_tech_logo_images()
    for logo in tech_logos:
        if logo not in image_urls:
            image_urls.append(logo)
    
    return image_urls


def _is_authorized(auth_header: str) -> bool:
    """Validate Basic Auth header for ChatGPT usage."""
    if not auth_header.startswith('Basic '):
        return False
    try:
        decoded = b64decode(auth_header.split(' ', 1)[1]).decode('utf-8')
        if ':' not in decoded:
            return False
        username, password = decoded.split(':', 1)
        return username == BASIC_AUTH_USERNAME and password == BASIC_AUTH_PASSWORD
    except Exception:
        return False
