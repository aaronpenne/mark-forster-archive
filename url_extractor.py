#!/usr/bin/env python3
"""
Mark Forster Archive - URL Extractor
Extracts all blog post URLs from the archive page
"""

import requests
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('url_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class URLExtractor:
    def __init__(self):
        self.base_url = "http://markforster.squarespace.com"
        self.archive_url = "http://markforster.squarespace.com/blog-archive/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def fetch_archive_page(self):
        """Fetch the blog archive page"""
        logger.info(f"Fetching archive page: {self.archive_url}")
        try:
            response = self.session.get(self.archive_url, timeout=30)
            response.raise_for_status()
            logger.info(f"Successfully fetched archive page ({len(response.content)} bytes)")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch archive page: {e}")
            raise
    
    def extract_blog_urls(self, html_content):
        """Extract all blog post URLs from the archive page"""
        logger.info("Parsing archive page HTML")
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Find the "Entries by Title" section
        entries_section = soup.find('h3', string='Entries by Title')
        if not entries_section:
            logger.error("Could not find 'Entries by Title' section")
            return []
        
        # Get the next ul element containing all the links
        ul_element = entries_section.find_next_sibling('ul')
        if not ul_element:
            # Try finding it in the next div
            div_element = entries_section.find_next_sibling('div')
            if div_element:
                ul_element = div_element.find('ul')
        
        if not ul_element:
            logger.error("Could not find URL list after 'Entries by Title'")
            return []
        
        # Extract all blog post URLs
        blog_urls = []
        links = ul_element.find_all('a', href=True)
        
        logger.info(f"Found {len(links)} potential links")
        
        for link in links:
            href = link.get('href')
            if href and href.startswith('/blog/'):
                # Skip malformed URLs
                if '/blog/NaN/NaN/NaN/' in href:
                    logger.warning(f"Skipping malformed URL: {href}")
                    continue
                
                # Convert to absolute URL
                full_url = urljoin(self.base_url, href)
                title = link.get_text(strip=True)
                
                blog_urls.append({
                    'url': full_url,
                    'path': href,
                    'title': title
                })
        
        # Remove duplicates while preserving order
        seen_urls = set()
        unique_urls = []
        for item in blog_urls:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique_urls.append(item)
        
        logger.info(f"Extracted {len(unique_urls)} unique blog post URLs")
        return unique_urls
    
    def save_urls(self, urls, filename='blog_post_urls.json'):
        """Save extracted URLs to JSON file"""
        logger.info(f"Saving {len(urls)} URLs to {filename}")
        
        output_data = {
            'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_posts': len(urls),
            'source_url': self.archive_url,
            'posts': urls
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"URLs saved to {filename}")
    
    def run(self):
        """Main execution method"""
        logger.info("Starting URL extraction process")
        
        try:
            # Fetch archive page
            html_content = self.fetch_archive_page()
            
            # Extract URLs
            urls = self.extract_blog_urls(html_content)
            
            if not urls:
                logger.error("No URLs extracted. Check selectors or page structure.")
                return False
            
            # Save URLs
            self.save_urls(urls)
            
            # Print summary
            logger.info(f"Successfully extracted {len(urls)} blog post URLs")
            logger.info("Sample URLs:")
            for i, url_data in enumerate(urls[:5]):
                logger.info(f"  {i+1}. {url_data['title'][:50]}... -> {url_data['path']}")
            
            if len(urls) > 5:
                logger.info(f"  ... and {len(urls) - 5} more")
            
            return True
            
        except Exception as e:
            logger.error(f"URL extraction failed: {e}")
            return False

if __name__ == "__main__":
    extractor = URLExtractor()
    success = extractor.run()
    
    if success:
        print("\n✅ URL extraction completed successfully")
        print("📁 Output file: blog_post_urls.json")
        print("📋 Log file: url_extraction.log")
    else:
        print("\n❌ URL extraction failed. Check logs for details.")