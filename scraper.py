import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import time
from newspaper import Article

# Handle different readability package versions
try:
    from readability import Document
except ImportError:
    Document = None


class WebScraper:
    def __init__(self, timeout: int = 10, delay: float = 1.0):
        """
        Initialize the WebScraper with configurable timeout and delay between requests.
        
        Args:
            timeout (int): Request timeout in seconds
            delay (float): Delay between requests to be respectful to servers
        """
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_single_url(self, url: str) -> Dict:
        """
        Scrape a single URL and extract title, main content, and citations.
        
        Args:
            url (str): The URL to scrape
            
        Returns:
            Dict: JSON-like dictionary containing title, content, citations, and metadata
        """
        try:
            # Get the webpage
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Try newspaper3k first for better content extraction
            article_data = self._extract_with_newspaper(url)
            
            # Fallback to BeautifulSoup if newspaper fails
            if not article_data['content'] or len(article_data['content']) < 100:
                article_data = self._extract_with_beautifulsoup(response.text, url)
            
            result = {
                'url': url,
                'title': article_data['title'],
                'main_content': article_data['content']
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                'url': url,
                'title': '',
                'main_content': ''
            }
        except Exception as e:
            return {
                'url': url,
                'title': '',
                'main_content': ''
            }
    
    def _extract_with_newspaper(self, url: str) -> Dict:
        """Extract content using newspaper3k library."""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return {
                'title': article.title or '',
                'content': article.text or '',
                'publish_date': str(article.publish_date) if article.publish_date else ''
            }
        except:
            return {'title': '', 'content': '', 'publish_date': ''}
    
    def _extract_with_beautifulsoup(self, html: str, url: str) -> Dict:
        """Extract content using BeautifulSoup as a fallback method."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup)
        
        # Try readability for main content if available
        content = ""
        if Document is not None:
            try:
                doc = Document(html)
                content_html = doc.summary()
                content_soup = BeautifulSoup(content_html, 'html.parser')
                content = content_soup.get_text(strip=True, separator=' ')
            except:
                # Fallback content extraction
                content = self._extract_main_content(soup)
        else:
            # Fallback content extraction when readability is not available
            content = self._extract_main_content(soup)
        
        # Try to extract publish date
        publish_date = self._extract_publish_date(soup)
        
        return {
            'title': title,
            'content': content,
            'publish_date': publish_date
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the title from the webpage."""
        # Try multiple title sources in order of preference
        title_selectors = [
            'h1',
            'title',
            '[property="og:title"]',
            '[name="twitter:title"]',
            '.entry-title',
            '.post-title',
            '.article-title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get('content') if element.get('content') else element.get_text(strip=True)
                if title and len(title) > 5:
                    return title
        
        return "Untitled"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the webpage."""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            element.decompose()
        
        # Try common content selectors
        content_selectors = [
            'article',
            '[role="main"]',
            '.entry-content',
            '.post-content',
            '.article-content',
            '.content',
            'main',
            '.main-content'
        ]
        
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                text = content_element.get_text(strip=True, separator=' ')
                if len(text) > 100:  # Only return if substantial content
                    return text
        
        # Fallback: get text from body, excluding common non-content elements
        body = soup.find('body')
        if body:
            # Remove common non-content sections
            for unwanted in body.find_all(['nav', 'footer', 'header', 'aside', '.sidebar', '.widget']):
                unwanted.decompose()
            
            paragraphs = body.find_all('p')
            if paragraphs:
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
                return content
        
        return soup.get_text(strip=True, separator=' ')
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """Extract publish date."""
        date_selectors = [
            '[property="article:published_time"]',
            '[name="date"]',
            '[pubdate]',
            'time[datetime]',
            '.date',
            '.publish-date'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date = element.get('datetime') or element.get('content') or element.get_text(strip=True)
                if date:
                    return date
        
        return ""
    
    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple URLs and return a list of results.
        
        Args:
            urls (List[str]): List of URLs to scrape
            
        Returns:
            List[Dict]: List of dictionaries containing scraped data for each URL
        """
        results = []
        
        for i, url in enumerate(urls):
            print(f"Scraping {i+1}/{len(urls)}: {url}")
            result = self.scrape_single_url(url)
            results.append(result)
            
            # Be respectful to servers
            if i < len(urls) - 1:
                time.sleep(self.delay)
        
        return results
    
    def save_to_json(self, data: List[Dict], filename: str) -> None:
        """
        Save scraped data to a JSON file.
        
        Args:
            data (List[Dict]): Scraped data to save
            filename (str): Output filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")
    
    def get_summary_stats(self, results: List[Dict]) -> Dict:
        """
        Get summary statistics of the scraped data.
        
        Args:
            results (List[Dict]): Results from scraping
            
        Returns:
            Dict: Summary statistics
        """
        total_urls = len(results)
        successful = sum(1 for r in results if r['title'] and r['main_content'])
        failed = total_urls - successful
        total_words = sum(len(r['main_content'].split()) if r['main_content'] else 0 for r in results)
        
        return {
            'total_urls': total_urls,
            'successful_scrapes': successful,
            'failed_scrapes': failed,
            'success_rate': f"{(successful/total_urls)*100:.1f}%" if total_urls > 0 else "0%",
            'total_words_scraped': total_words,
            'average_words_per_article': total_words // successful if successful > 0 else 0
        }