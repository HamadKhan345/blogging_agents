import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json

class FeaturedImageExtractor:
    def __init__(self, timeout=10):
        """
        Initialize the FeaturedImageExtractor
        
        Args:
            timeout (int): Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_featured_image(self, url):
        """
        Extract the featured image URL from a webpage
        
        Args:
            url (str): The URL of the webpage
            
        Returns:
            str: The URL of the featured image, or None if not found
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different methods to find featured image
            image_url = (
                self._get_og_image(soup) or
                self._get_twitter_image(soup) or
                self._get_article_image(soup) or
                self._get_first_content_image(soup) or
                self._get_largest_image(soup)
            )
            
            if image_url:
                # Convert relative URLs to absolute
                return urljoin(url, image_url)
            
            return None
            
        except Exception as e:
            print(f"Error extracting image from {url}: {str(e)}")
            return None
    
    def get_featured_image(self, urls):
        """
        Extract featured image from multiple URLs, trying each one until successful
        
        Args:
            urls (list): List of URLs to try
            
        Returns:
            dict: JSON response with success status and image URL
        """
        if not urls or not isinstance(urls, list):
            return {
                "success": False,
                "image_url": None
            }
        
        for url in urls:
            if not url or not isinstance(url, str):
                continue
                
            try:
                image_url = self.extract_featured_image(url)
                
                if image_url:
                    return {
                        "success": True,
                        "image_url": image_url
                    }
                    
            except Exception as e:
                continue
        
        # If we get here, no URL was successful
        return {
            "success": False,
            "image_url": None
        }
    
    def _get_og_image(self, soup):
        """Extract Open Graph image"""
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
        return None
    
    def _get_twitter_image(self, soup):
        """Extract Twitter Card image"""
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if not twitter_image:
            twitter_image = soup.find('meta', attrs={'property': 'twitter:image'})
        
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
        return None
    
    def _get_article_image(self, soup):
        """Extract image from article or main content"""
        # Look for common article selectors
        selectors = [
            'article img',
            '.post-content img',
            '.content img',
            '.entry-content img',
            '.post-body img',
            'main img'
        ]
        
        for selector in selectors:
            img = soup.select_one(selector)
            if img and img.get('src'):
                return img['src']
        return None
    
    def _get_first_content_image(self, soup):
        """Get the first meaningful image from the page"""
        images = soup.find_all('img')
        
        for img in images:
            src = img.get('src') or img.get('data-src')
            if src and self._is_valid_image(src, img):
                return src
        return None
    
    def _get_largest_image(self, soup):
        """Find the largest image by dimensions"""
        images = soup.find_all('img')
        largest_img = None
        max_size = 0
        
        for img in images:
            src = img.get('src') or img.get('data-src')
            if not src or not self._is_valid_image(src, img):
                continue
                
            width = self._extract_number(img.get('width', '0'))
            height = self._extract_number(img.get('height', '0'))
            
            if width and height:
                size = width * height
                if size > max_size:
                    max_size = size
                    largest_img = src
        
        return largest_img
    
    def _is_valid_image(self, src, img_element):
        """Check if the image is likely to be a featured image"""
        if not src:
            return False
            
        # Skip small images, icons, and common non-content images
        skip_patterns = [
            r'icon', r'logo', r'avatar', r'profile',
            r'btn', r'button', r'social', r'share',
            r'ad', r'advertisement', r'banner'
        ]
        
        src_lower = src.lower()
        alt_text = (img_element.get('alt', '') or '').lower()
        class_name = ' '.join(img_element.get('class', [])).lower()
        
        # Check if image should be skipped
        for pattern in skip_patterns:
            if (re.search(pattern, src_lower) or 
                re.search(pattern, alt_text) or 
                re.search(pattern, class_name)):
                return False
        
        # Check minimum dimensions
        width = self._extract_number(img_element.get('width', '0'))
        height = self._extract_number(img_element.get('height', '0'))
        
        if width and height and (width < 200 or height < 200):
            return False
        
        return True
    
    def _extract_number(self, value):
        """Extract numeric value from string"""
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            match = re.search(r'\d+', value)
            return int(match.group()) if match else 0
        return 0

# Example usage
# if __name__ == "__main__":
#     extractor = FeaturedImageExtractor()
    
#     # Test with multiple URLs
#     test_urls = [
#         "",
#         "https://example.com/article",
#         "https://www.bbc.com/news"
#     ]
    
#     result = extractor.get_featured_image(test_urls)
#     print(json.dumps(result, indent=2))