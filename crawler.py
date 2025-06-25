#!/usr/bin/env python3
"""
Mark Forster Archive - Main Crawler
Processes all blog posts from the extracted URL list
"""

import json
import time
import os
import sys
from post_extractor import PostExtractor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MarkForsterCrawler:
    def __init__(self, urls_file='blog_post_urls.json', output_dir='archive'):
        self.urls_file = urls_file
        self.output_dir = output_dir
        self.extractor = PostExtractor()
        self.progress_file = 'crawler_progress.json'
        
        # Load URL list
        self.urls = self.load_urls()
        self.total_posts = len(self.urls)
        
        # Load previous progress if exists
        self.completed_urls = self.load_progress()
        
        # Rate limiting
        self.delay_between_requests = 2  # seconds
        
    def load_urls(self):
        """Load the list of blog post URLs"""
        logger.info(f"Loading URLs from {self.urls_file}")
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            urls = [post['url'] for post in data['posts']]
            logger.info(f"Loaded {len(urls)} URLs to process")
            return urls
        except FileNotFoundError:
            logger.error(f"URLs file not found: {self.urls_file}")
            logger.error("Please run url_extractor.py first to generate the URLs list")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load URLs: {e}")
            sys.exit(1)
    
    def load_progress(self):
        """Load previous crawling progress"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                completed = set(progress_data.get('completed_urls', []))
                logger.info(f"Resuming crawl: {len(completed)} posts already completed")
                return completed
            except Exception as e:
                logger.warning(f"Could not load progress file: {e}")
        return set()
    
    def save_progress(self, completed_url):
        """Save crawling progress"""
        self.completed_urls.add(completed_url)
        
        progress_data = {
            'completed_urls': list(self.completed_urls),
            'total_posts': self.total_posts,
            'completed_count': len(self.completed_urls),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save progress: {e}")
    
    def create_master_index(self):
        """Create a master index of all archived posts"""
        logger.info("Creating master index...")
        
        index_data = {
            'archive_created': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_posts': len(self.completed_urls),
            'source_site': 'http://markforster.squarespace.com',
            'posts': []
        }
        
        # Scan archive directory for post data
        posts_dir = os.path.join(self.output_dir, 'posts')
        if os.path.exists(posts_dir):
            for root, dirs, files in os.walk(posts_dir):
                if 'data.json' in files:
                    data_file = os.path.join(root, 'data.json')
                    try:
                        with open(data_file, 'r', encoding='utf-8') as f:
                            post_data = json.load(f)
                        
                        # Add summary info to index
                        index_entry = {
                            'title': post_data.get('title', ''),
                            'url': post_data.get('url', ''),
                            'author': post_data.get('author', ''),
                            'date': post_data.get('date', ''),
                            'categories': post_data.get('categories', []),
                            'comments_count': post_data.get('comments_count', 0),
                            'archive_path': os.path.relpath(root, self.output_dir)
                        }
                        index_data['posts'].append(index_entry)
                        
                    except Exception as e:
                        logger.warning(f"Could not index post {data_file}: {e}")
        
        # Sort posts by date (newest first)
        index_data['posts'].sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # Save master index
        index_file = os.path.join(self.output_dir, 'master_index.json')
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Master index created with {len(index_data['posts'])} posts")
        return index_file
    
    def crawl_posts(self, limit=None, test_mode=False):
        """Crawl all blog posts"""
        # Filter out already completed URLs
        remaining_urls = [url for url in self.urls if url not in self.completed_urls]
        
        if limit:
            remaining_urls = remaining_urls[:limit]
            logger.info(f"Test mode: processing {len(remaining_urls)} posts")
        
        if not remaining_urls:
            logger.info("All posts already completed!")
            return True
        
        logger.info(f"Starting crawl of {len(remaining_urls)} posts")
        logger.info(f"Progress: {len(self.completed_urls)}/{self.total_posts} completed")
        
        success_count = 0
        error_count = 0
        
        for i, url in enumerate(remaining_urls, 1):
            logger.info(f"\n[{i}/{len(remaining_urls)}] Processing: {url}")
            
            try:
                # Extract post content
                post_data = self.extractor.extract_single_post(url)
                
                if post_data:
                    # Save post data
                    save_success = self.extractor.save_post_data(post_data, self.output_dir)
                    
                    if save_success:
                        success_count += 1
                        self.save_progress(url)
                        logger.info(f"✅ Successfully archived post {i}/{len(remaining_urls)}")
                    else:
                        error_count += 1
                        logger.error(f"❌ Failed to save post {i}/{len(remaining_urls)}")
                else:
                    error_count += 1
                    logger.error(f"❌ Failed to extract post {i}/{len(remaining_urls)}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing {url}: {e}")
            
            # Rate limiting
            if i < len(remaining_urls):  # Don't delay after last item
                logger.debug(f"Waiting {self.delay_between_requests} seconds...")
                time.sleep(self.delay_between_requests)
            
            # Progress checkpoint every 50 posts
            if i % 50 == 0:
                logger.info(f"📊 Checkpoint: {i}/{len(remaining_urls)} processed, {success_count} successful, {error_count} errors")
        
        # Final summary
        total_completed = len(self.completed_urls)
        logger.info(f"\n🎯 Crawl completed!")
        logger.info(f"   Successfully processed: {success_count}")
        logger.info(f"   Errors: {error_count}")
        logger.info(f"   Total archived: {total_completed}/{self.total_posts}")
        logger.info(f"   Success rate: {(success_count/(success_count+error_count)*100):.1f}%" if (success_count+error_count) > 0 else "N/A")
        
        return error_count == 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Mark Forster Archive Crawler')
    parser.add_argument('--test', '-t', type=int, metavar='N', 
                       help='Test mode: only process N posts')
    parser.add_argument('--output', '-o', default='archive',
                       help='Output directory (default: archive)')
    
    args = parser.parse_args()
    
    # Create crawler
    crawler = MarkForsterCrawler(output_dir=args.output)
    
    print(f"🚀 Mark Forster Archive Crawler")
    print(f"📊 Posts to process: {len([url for url in crawler.urls if url not in crawler.completed_urls])}")
    print(f"📁 Output directory: {args.output}")
    
    if args.test:
        print(f"🧪 Test mode: processing only {args.test} posts")
    
    print("\nStarting crawl...\n")
    
    # Run the crawler
    try:
        success = crawler.crawl_posts(limit=args.test, test_mode=bool(args.test))
        
        # Create master index
        index_file = crawler.create_master_index()
        print(f"\n📝 Master index created: {index_file}")
        
        if success:
            print("\n✅ Archive completed successfully!")
        else:
            print("\n⚠️  Archive completed with some errors. Check logs.")
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Crawl interrupted by user")
        print("Progress has been saved. Run again to resume.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)