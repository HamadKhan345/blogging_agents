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
        self.max_file_size = 5 * 1024 * 1024  # 5MB in bytes
        self.valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
    
    def extract_featured_image(self, url):
        """
        Extract the featured image URL from a webpage
        
        Args:
            url (str): The URL of the webpage
            
        Returns:
            str: The URL of the best featured image, or None if not found
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Collect all potential image candidates
            candidates = []
            
            # Try different methods to find featured images
            og_image = self._get_og_image(soup)
            if og_image:
                candidates.append(og_image)
            
            twitter_image = self._get_twitter_image(soup)
            if twitter_image:
                candidates.append(twitter_image)
            
            article_images = self._get_article_images(soup, limit=3)
            candidates.extend(article_images)
            
            content_images = self._get_content_images(soup, limit=5)
            candidates.extend(content_images)
            
            # Remove duplicates while preserving order
            unique_candidates = []
            seen = set()
            for candidate in candidates:
                absolute_url = urljoin(url, candidate)
                if absolute_url not in seen:
                    seen.add(absolute_url)
                    unique_candidates.append(absolute_url)
            
            # Check top 5 candidates
            top_candidates = unique_candidates[:5]
            
            # Find the best valid image
            best_image = self._find_best_image(top_candidates)
            
            return best_image
            
        except Exception as e:
            print(f"Error extracting image from {url}: {str(e)}")
            return None
    
    def _find_best_image(self, image_urls):
        """
        Find the best image from a list of candidates based on size, format, and dimensions
        
        Args:
            image_urls (list): List of image URLs to check
            
        Returns:
            str: URL of the best image, or None if no valid image found
        """
        valid_images = []
        
        for img_url in image_urls:
            if self._is_valid_image_url(img_url):
                image_info = self._get_image_info(img_url)
                if image_info:
                    valid_images.append(image_info)
        
        if not valid_images:
            return None
        
        # Sort by quality score (larger dimensions = better, but prefer reasonable aspect ratios)
        valid_images.sort(key=self._calculate_image_score, reverse=True)
        
        return valid_images[0]['url']
    
    def _is_valid_image_url(self, url):
        """Check if URL has valid image extension"""
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            
            # Remove query parameters for extension check
            if '?' in path:
                path = path.split('?')[0]
            
            # Check if it ends with valid extension
            for ext in self.valid_extensions:
                if path.endswith(f'.{ext}'):
                    return True
            
            return False
        except:
            return False
    
    def _get_image_info(self, url):
        """
        Get image information including size and dimensions
        
        Args:
            url (str): Image URL
            
        Returns:
            dict: Image info or None if invalid
        """
        try:
            # Make a HEAD request first to check content-length
            head_response = self.session.head(url, timeout=self.timeout)
            
            if head_response.status_code == 200:
                content_length = head_response.headers.get('content-length')
                if content_length and int(content_length) > self.max_file_size:
                    return None
            
            # If HEAD request doesn't give us content-length, try GET with stream
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Check actual size by reading content
            content = b''
            size = 0
            for chunk in response.iter_content(chunk_size=8192):
                size += len(chunk)
                if size > self.max_file_size:
                    return None
                content += chunk
            
            # Try to get image dimensions (basic check)
            width, height = self._get_image_dimensions_from_content(content)
            
            return {
                'url': url,
                'size': size,
                'width': width or 0,
                'height': height or 0
            }
            
        except Exception as e:
            print(f"Error checking image {url}: {str(e)}")
            return None
    
    def _get_image_dimensions_from_content(self, content):
        """Extract basic image dimensions from content"""
        try:
            # This is a basic implementation - for production, you might want to use PIL
            if content.startswith(b'\xff\xd8\xff'):  # JPEG
                return self._get_jpeg_dimensions(content)
            elif content.startswith(b'\x89PNG'):  # PNG
                return self._get_png_dimensions(content)
            elif content.startswith(b'RIFF') and b'WEBP' in content[:12]:  # WebP
                return self._get_webp_dimensions(content)
        except:
            pass
        return None, None
    
    def _get_jpeg_dimensions(self, content):
        """Extract JPEG dimensions"""
        try:
            i = 2
            while i < len(content) - 9:
                if content[i:i+2] == b'\xff\xc0':
                    height = int.from_bytes(content[i+5:i+7], 'big')
                    width = int.from_bytes(content[i+7:i+9], 'big')
                    return width, height
                i += 1
        except:
            pass
        return None, None
    
    def _get_png_dimensions(self, content):
        """Extract PNG dimensions"""
        try:
            if len(content) >= 24:
                width = int.from_bytes(content[16:20], 'big')
                height = int.from_bytes(content[20:24], 'big')
                return width, height
        except:
            pass
        return None, None
    
    def _get_webp_dimensions(self, content):
        """Extract WebP dimensions (basic)"""
        try:
            if b'VP8 ' in content[:20]:
                # Simple VP8 format
                for i in range(12, min(30, len(content) - 4)):
                    if content[i:i+4] == b'VP8 ':
                        width = int.from_bytes(content[i+6:i+8], 'little') & 0x3fff
                        height = int.from_bytes(content[i+8:i+10], 'little') & 0x3fff
                        return width, height
        except:
            pass
        return None, None
    
    def _calculate_image_score(self, image_info):
        """Calculate a quality score for an image"""
        width = image_info['width']
        height = image_info['height']
        
        if width == 0 or height == 0:
            return 0
        
        # Prefer images with reasonable dimensions
        area = width * height
        aspect_ratio = max(width, height) / min(width, height)
        
        # Penalize extreme aspect ratios
        aspect_penalty = 1.0 if aspect_ratio <= 3.0 else 0.5
        
        # Prefer larger images but with diminishing returns
        size_score = min(area / 100000, 10)  # Normalize to 0-10 range
        
        return size_score * aspect_penalty
    
    def _get_article_images(self, soup, limit=3):
        """Extract images from article or main content"""
        images = []
        selectors = [
            'article img',
            '.post-content img',
            '.content img',
            '.entry-content img',
            '.post-body img',
            'main img'
        ]
        
        for selector in selectors:
            imgs = soup.select(selector)
            for img in imgs[:limit]:
                src = img.get('src') or img.get('data-src')
                if src and self._is_content_image(src, img):
                    images.append(src)
                    if len(images) >= limit:
                        break
            if len(images) >= limit:
                break
        
        return images
    
    def _get_content_images(self, soup, limit=5):
        """Get meaningful images from the page content"""
        images = []
        all_imgs = soup.find_all('img')
        
        for img in all_imgs:
            if len(images) >= limit:
                break
                
            src = img.get('src') or img.get('data-src')
            if src and self._is_content_image(src, img):
                images.append(src)
        
        return images
    
    def _is_content_image(self, src, img_element):
        """Check if the image is likely to be a content image"""
        if not src:
            return False
            
        # Skip small images, icons, and common non-content images
        skip_patterns = [
            r'icon', r'logo', r'avatar', r'profile',
            r'btn', r'button', r'social', r'share',
            r'ad', r'advertisement', r'banner',
            r'pixel', r'track'
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
        
        return True

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