import os
import requests
import urllib.parse
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')


def search_web(query, num_results=5):
    try:
        search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for element in soup.select('.result')[:num_results]:
                title_element = element.select_one('.result__title')
                title = title_element.get_text().strip() if title_element else "No title"
                link_element = element.select_one('a.result__a')
                url = link_element['href'] if link_element and 'href' in link_element.attrs else ''
                snippet_el = element.select_one('.result__snippet')
                snippet = snippet_el.get_text().strip() if snippet_el else "No description"
                if title != "No title" and url:
                    results.append({'title': title, 'url': url, 'snippet': snippet})
            return results
        return []
    except Exception as e:
        print(f"web search error: {e}")
        return []


def get_webpage_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for s in soup(["script", "style"]):
                s.extract()
            lines = (line.strip() for line in soup.get_text().splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text[:2000]
        return ""
    except Exception as e:
        print(f"fetch webpage error: {e}")
        return ""


def generate_content_with_references(article_content, url, complexity):
    try:
        title = article_content['title']
        content = article_content['content']
        search_queries = [title]
        paragraphs = content.split('\n\n')
        for para in paragraphs[:3]:
            if len(para) > 100:
                first_sentence = re.split(r'[.!?]', para)[0]
                if len(first_sentence) > 30:
                    search_queries.append(first_sentence)
        if len(search_queries) < 2:
            search_queries.append(f"{title} technology news")
        search_queries = search_queries[:3]

        all_results = []
        for q in search_queries:
            all_results.extend(search_web(q, 3))
        seen = set()
        unique_results = []
        for r in all_results:
            if r['url'] not in seen:
                seen.add(r['url'])
                unique_results.append(r)
        top_results = unique_results[:5]
        for r in top_results:
            r['content'] = get_webpage_content(r['url']) or r['snippet']

        hook_instruction = ""
        if complexity['length'] == 'short' and complexity['complexity'] == 'simple':
            hook_instruction = "Start with a very short, punchy hook (1 sentence max)"
        elif complexity['length'] == 'long' or complexity['complexity'] == 'complex':
            hook_instruction = "Start with a medium-length hook (2 sentences) that captures the complexity of the topic"
        else:
            hook_instruction = "Start with a short hook (1 sentence) that is catchy and informative"

        source_instruction = f"Include the source at the end in this exact format: 'Source: {article_content.get('source_name','Source')} ({url})'" if url else "If no source URL is provided, suggest some potential sources based on the content in the format 'Source: [Source Name] (link)'"

        refs_text = ""
        for i, ref in enumerate(top_results):
            refs_text += f"Reference {i+1}:\nTitle: {ref['title']}\nURL: {ref['url']}\nContent: {ref['content'][:500]}...\n\n"

        prompt = f"""
        Create a WhatsApp-friendly summary with:\n
        1. {hook_instruction}\n
        2. Minimal emojis and *asterisks* for bold\n
        3. 3-5 key points\n
        4. {source_instruction}\n
        Article Title: {article_content['title']}\n
        Article URL: {url}\n
        Article Content: {article_content['content'][:3000]}\n
        Additional References:\n
        {refs_text}
        """

        headers_m = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {MISTRAL_API_KEY}"
        }
        payload = {
            "model": "mistral-large-latest",
            "messages": [
                {"role": "system", "content": "You are a tech news summarizer for WhatsApp."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }
        resp = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers_m, json=payload)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        print(f"Mistral API error: {resp.status_code} - {resp.text}")
        return "Unable to generate content with references. Please try again or switch to ChatGPT model."
    except Exception as e:
        print(f"generate with refs error: {e}")
        return f"Error generating content with references: {e}"


