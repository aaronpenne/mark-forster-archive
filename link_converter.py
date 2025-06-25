#!/usr/bin/env python3
"""
Link Converter for Mark Forster Archive
Converts internal blog links to relative paths for local navigation
"""

import os
import re
import json
from pathlib import Path
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkConverter:
    def __init__(self, archive_dir="archive"):
        self.archive_dir = Path(archive_dir)
        self.base_url = "http://markforster.squarespace.com"
        self.blog_pattern = re.compile(r'http://markforster\.squarespace\.com/blog/(\d{4})/(\d{1,2})/(\d{1,2})/([\w-]+)\.html')
        
        # Build URL to path mapping
        self.url_to_path = {}
        self.build_url_mapping()
    
    def build_url_mapping(self):
        """Build mapping from URLs to local file paths"""
        logger.info("Building URL to path mapping...")
        
        for post_dir in self.archive_dir.rglob("*/"):
            if post_dir.is_dir() and (post_dir / "data.json").exists():
                try:
                    with open(post_dir / "data.json", 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        url = data.get('url', '')
                        if url:
                            # Store both HTML and Markdown paths
                            rel_path = post_dir.relative_to(self.archive_dir)
                            self.url_to_path[url] = {
                                'html': rel_path / 'raw.html',
                                'md': rel_path / 'content.md',
                                'dir': rel_path
                            }
                except Exception as e:
                    logger.warning(f"Error reading {post_dir / 'data.json'}: {e}")
        
        logger.info(f"Built mapping for {len(self.url_to_path)} posts")
    
    def url_to_relative_path(self, url, current_path, target_format='html'):
        """Convert URL to relative path from current file location"""
        if url in self.url_to_path:
            target_path = self.url_to_path[url][target_format]
            current_dir = current_path.parent
            
            # Calculate relative path
            try:
                rel_path = os.path.relpath(target_path, current_dir)
                return rel_path
            except ValueError:
                # Fallback to absolute path if relative calculation fails
                return str(target_path)
        return url
    
    def convert_links_in_html(self, html_content, current_path):
        """Convert internal blog links in HTML content to relative paths"""
        def replace_link(match):
            url = match.group(0)
            if url.startswith('href="http://markforster.squarespace.com/blog/'):
                # Extract the full URL
                full_url = url.split('"')[1]
                rel_path = self.url_to_relative_path(full_url, current_path, 'html')
                return f'href="{rel_path}"'
            return url
        
        # Match href attributes with internal blog links
        pattern = r'href="http://markforster\.squarespace\.com/blog/[^"]*"'
        return re.sub(pattern, replace_link, html_content)
    
    def convert_links_in_markdown(self, md_content, current_path):
        """Convert internal blog links in Markdown content to relative paths"""
        def replace_link(match):
            url = match.group(1)
            rel_path = self.url_to_relative_path(url, current_path, 'md')
            return f']({rel_path})'
        
        # Match markdown links [text](url)
        pattern = r']\((http://markforster\.squarespace\.com/blog/[^)]*)\)'
        return re.sub(pattern, replace_link, md_content)
    
    def convert_all_files(self):
        """Convert links in all archived files"""
        logger.info("Converting internal links to relative paths...")
        
        converted_count = 0
        for post_dir in self.archive_dir.rglob("*/"):
            if not post_dir.is_dir():
                continue
                
            html_file = post_dir / "raw.html"
            md_file = post_dir / "content.md"
            
            # Convert HTML file
            if html_file.exists():
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    converted_content = self.convert_links_in_html(content, html_file)
                    
                    if converted_content != content:
                        with open(html_file, 'w', encoding='utf-8') as f:
                            f.write(converted_content)
                        logger.debug(f"Updated links in {html_file}")
                        converted_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {html_file}: {e}")
            
            # Convert Markdown file
            if md_file.exists():
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    converted_content = self.convert_links_in_markdown(content, md_file)
                    
                    if converted_content != content:
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write(converted_content)
                        logger.debug(f"Updated links in {md_file}")
                        
                except Exception as e:
                    logger.error(f"Error processing {md_file}: {e}")
        
        logger.info(f"Link conversion complete. Updated {converted_count} files.")
    
    def create_index_html(self):
        """Create an index.html file for easy navigation"""
        logger.info("Creating navigation index...")
        
        # Group posts by year/month
        posts_by_date = {}
        for url, paths in self.url_to_path.items():
            try:
                # Load post data
                data_file = self.archive_dir / paths['dir'] / 'data.json'
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract date parts from path
                date_parts = str(paths['dir']).split('/')
                if len(date_parts) >= 3:
                    year, month = date_parts[1], date_parts[2]
                    date_key = f"{year}-{month.zfill(2)}"
                    
                    if date_key not in posts_by_date:
                        posts_by_date[date_key] = []
                    
                    posts_by_date[date_key].append({
                        'title': data.get('title', 'Untitled'),
                        'date': data.get('date', ''),
                        'html_path': paths['html'],
                        'md_path': paths['md'],
                        'comments_count': data.get('comments_count', 0)
                    })
            except Exception as e:
                logger.warning(f"Error processing {paths['dir']}: {e}")
        
        # Sort posts within each month by date
        for date_key in posts_by_date:
            posts_by_date[date_key].sort(key=lambda x: x['date'])
        
        # Generate HTML index
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mark Forster Archive - Navigation Index</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; border-bottom: 2px solid #333; }
        h2 { color: #666; margin-top: 30px; }
        .post { margin: 10px 0; padding: 10px; border-left: 3px solid #ccc; }
        .post-title { font-weight: bold; margin-bottom: 5px; }
        .post-meta { font-size: 0.9em; color: #666; margin-bottom: 5px; }
        .post-links a { margin-right: 15px; text-decoration: none; }
        .post-links a:hover { text-decoration: underline; }
        .html-link { color: #2196F3; }
        .md-link { color: #4CAF50; }
        .stats { background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Mark Forster Archive</h1>
    <div class="stats">
        <strong>Archive Statistics:</strong><br>
        Total Posts: {total_posts}<br>
        Date Range: {date_range}<br>
        Archive completed: {archive_date}
    </div>
    
    <p>This archive preserves the complete blog posts and comments from Mark Forster's productivity blog.
    Each post is available in two formats:</p>
    <ul>
        <li><strong>HTML</strong> - Original formatted version with all styling</li>
        <li><strong>Markdown</strong> - Clean text version with comments included</li>
    </ul>
""".format(
            total_posts=len(self.url_to_path),
            date_range=f"{min(posts_by_date.keys())} to {max(posts_by_date.keys())}" if posts_by_date else "N/A",
            archive_date="2025-06-25"
        )
        
        # Add posts grouped by month
        for date_key in sorted(posts_by_date.keys(), reverse=True):
            year, month = date_key.split('-')
            month_name = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(month)-1]
            
            html_content += f"\n    <h2>{month_name} {year} ({len(posts_by_date[date_key])} posts)</h2>\n"
            
            for post in posts_by_date[date_key]:
                comments_text = f" ({post['comments_count']} comments)" if post['comments_count'] > 0 else ""
                html_content += f"""
    <div class="post">
        <div class="post-title">{post['title']}</div>
        <div class="post-meta">{post['date']}{comments_text}</div>
        <div class="post-links">
            <a href="{post['html_path']}" class="html-link">View HTML</a>
            <a href="{post['md_path']}" class="md-link">View Markdown</a>
        </div>
    </div>"""
        
        html_content += "\n</body>\n</html>"
        
        # Write index file
        index_file = self.archive_dir / "index.html"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Created navigation index at {index_file}")

def main():
    converter = LinkConverter()
    converter.convert_all_files()
    converter.create_index_html()
    
    print("\n✅ Link conversion complete!")
    print("📁 Open archive/index.html in your browser to navigate the archive")
    print("🔗 All internal blog links now point to local files for offline browsing")

if __name__ == "__main__":
    main()