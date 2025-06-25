#!/usr/bin/env python3
"""
Mark Forster Archive - GitHub Pages Crawler
Creates a simplified, interconnected Markdown archive for GitHub Pages
"""

import json
import time
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from post_extractor import PostExtractor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/github_pages_crawler.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class GitHubPagesCrawler:
    def __init__(self, urls_file="blog_post_urls.json", output_dir="_posts"):
        self.urls_file = urls_file
        self.output_dir = output_dir
        self.extractor = PostExtractor()
        self.progress_file = "logs/github_pages_progress.json"

        # URL to path mapping for link conversion
        self.url_to_path = {}

        # Load URL list
        self.urls = self.load_urls()
        self.total_posts = len(self.urls)

        # Load previous progress if exists
        self.completed_urls = self.load_progress()

        # Rate limiting
        self.delay_between_requests = 2  # seconds

        # Master index data
        self.index_data = []

    def load_urls(self):
        """Load the list of blog post URLs"""
        logger.info(f"Loading URLs from {self.urls_file}")
        try:
            with open(self.urls_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            urls = [post["url"] for post in data["posts"]]
            logger.info(f"Loaded {len(urls)} URLs to process")
            return urls
        except FileNotFoundError:
            logger.error(f"URLs file {self.urls_file} not found")
            sys.exit(1)

    def load_progress(self):
        """Load previous crawling progress"""
        try:
            with open(self.progress_file, "r") as f:
                progress = json.load(f)
                logger.info(
                    f"Resuming crawl: {progress['completed_count']} posts already completed"
                )
                return set(progress["completed_urls"])
        except FileNotFoundError:
            logger.info("Starting fresh crawl")
            return set()

    def save_progress(self, completed_urls):
        """Save current progress"""
        progress = {
            "completed_urls": list(completed_urls),
            "total_posts": self.total_posts,
            "completed_count": len(completed_urls),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        with open(self.progress_file, "w") as f:
            json.dump(progress, f, indent=2)

    def url_to_markdown_path(self, url):
        """Convert blog URL to markdown file path"""
        # Extract date and slug from URL
        # http://markforster.squarespace.com/blog/2016/3/30/post-slug.html
        pattern = r"/blog/(\d{4})/(\d{1,2})/(\d{1,2})/([\w-]+)\.html"
        match = re.search(pattern, url)

        if match:
            year, month, day, slug = match.groups()
            # Create path: _posts/2016-03-30-post-slug.md (Jekyll convention)
            return f"{self.output_dir}/{year}-{month.zfill(2)}-{day.zfill(2)}-{slug}.md"
        else:
            # Fallback for unusual URLs
            slug = url.split("/")[-1].replace(".html", "")
            return f"{self.output_dir}/misc-{slug}.md"

    def build_url_mapping(self):
        """Build mapping from URLs to markdown file paths"""
        logger.info("Building URL to path mapping for link conversion...")
        for url in self.urls:
            path = self.url_to_markdown_path(url)
            self.url_to_path[url] = path
        logger.info(f"Built mapping for {len(self.url_to_path)} URLs")

    def convert_internal_links(self, content, current_file_path):
        """Convert internal blog links to relative markdown paths"""

        def replace_link(match):
            url = match.group(1)
            if url in self.url_to_path:
                target_path = self.url_to_path[url]
                # Calculate relative path from current file to target
                current_dir = Path(current_file_path).parent
                target_file = Path(target_path)
                try:
                    rel_path = os.path.relpath(target_file, current_dir)
                    return f"]({rel_path})"
                except ValueError:
                    return f"]({target_path})"  # Fallback to absolute
            return f"]({url})"  # Keep original if not found

        # Convert markdown links [text](url)
        pattern = r"]\((http://markforster\.squarespace\.com/blog/[^)]*)\)"
        return re.sub(pattern, replace_link, content)

    def extract_and_save_post(self, url):
        """Extract a single post and save as markdown with converted links"""
        try:
            # Extract post data
            post_data = self.extractor.extract_single_post(url)

            if not post_data:
                logger.error(f"Failed to extract post from {url}")
                return False

            # Generate markdown file path
            md_path = self.url_to_markdown_path(url)

            # Create directory if needed
            os.makedirs(os.path.dirname(md_path), exist_ok=True)

            # Create markdown content
            md_content = self.create_markdown_content(post_data, md_path)

            # Convert internal links
            md_content = self.convert_internal_links(md_content, md_path)

            # Write markdown file
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            # Add to index
            self.add_to_index(post_data, md_path)

            logger.info(f"✅ Saved: {md_path}")
            return True

        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return False

    def create_markdown_content(self, post_data, file_path):
        """Create formatted markdown content"""
        content = []

        # Front matter for GitHub Pages
        content.append("---")

        # Handle title
        title = post_data.get("title", "Untitled").replace('"', '\\"') or "Untitled"
        content.append(f'title: "{title}"')

        # Handle author
        author = post_data.get("author", "Mark Forster") or "Mark Forster"
        content.append(f'author: "{author}"')

        # Handle date - extract from filename if post date is empty
        post_date = post_data.get("date", "")
        if not post_date:
            # Extract date from file path: YYYY-MM-DD
            date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", file_path)
            if date_match:
                year, month, day = date_match.groups()
                post_date = f"{year}-{month}-{day}"

        if post_date:
            # Ensure date is in Jekyll-compatible format (YYYY-MM-DD)
            if re.match(r"^\d{4}-\d{2}-\d{2}$", post_date):
                content.append(f"date: {post_date}")  # No quotes for ISO date
            else:
                content.append(f'date: "{post_date}"')  # Quotes for non-ISO dates

        # Handle categories
        if post_data.get("categories"):
            categories = []
            for cat in post_data["categories"]:
                if isinstance(cat, dict):
                    categories.append(cat.get("name", str(cat)))
                else:
                    categories.append(str(cat))
            if categories:
                content.append(f"categories: {categories}")

        # Original URL
        original_url = post_data.get("url", "")
        if original_url:
            content.append(f'original_url: "{original_url}"')

        content.append("layout: post")
        content.append("---")
        content.append("")

        # Post content
        post_content = post_data.get("content", "")
        if post_content:
            content.append(post_content)
            content.append("")

        # Comments section
        comments = post_data.get("comments", [])
        if comments:
            content.append("## Comments")
            content.append("")

            for i, comment in enumerate(comments, 1):
                if comment.get("author"):
                    content.append(f"**Author:** {comment['author']}")
                if comment.get("date"):
                    content.append(f"**Date:** {comment['date']}")
                content.append("")

                comment_text = comment.get("content", "")
                if comment_text:
                    content.append(comment_text)

                content.append("")
                content.append("---")
                content.append("")

        return "\n".join(content)

    def add_to_index(self, post_data, file_path):
        """Add post to master index"""
        # Extract date parts for sorting
        date_str = post_data.get("date", "")

        index_entry = {
            "title": post_data.get("title", "Untitled"),
            "date": date_str,
            "author": post_data.get("author", "Mark Forster"),
            "categories": [
                cat.get("name", str(cat)) if isinstance(cat, dict) else str(cat)
                for cat in post_data.get("categories", [])
            ],
            "comments_count": post_data.get("comments_count", 0),
            "file_path": file_path,
            "url": post_data.get("url", ""),
        }

        self.index_data.append(index_entry)

    def create_github_pages_index(self):
        """Create main index.md for GitHub Pages"""
        logger.info("Creating GitHub Pages index...")

        # Sort posts by date (newest first)
        sorted_posts = sorted(self.index_data, key=lambda x: x["date"], reverse=True)

        # Group posts by year
        posts_by_year = {}
        for post in sorted_posts:
            year = post["date"][:4] if len(post["date"]) >= 4 else "Unknown"
            if year not in posts_by_year:
                posts_by_year[year] = []
            posts_by_year[year].append(post)

        # Create index content
        index_content = [
            "---",
            "title: Mark Forster Archive",
            "layout: home",
            "---",
            "",
            "# Mark Forster Archive",
            "",
            f"This archive preserves {len(self.index_data)} blog posts and their comments from Mark Forster's productivity blog.",
            "",
            "Mark Forster was a renowned productivity expert and author who developed several influential time management systems including Autofocus, Do It Tomorrow, and Final Version Perfected (FVP).",
            "",
            "## Posts by Year",
            "",
        ]

        # Add posts grouped by year
        for year in sorted(posts_by_year.keys(), reverse=True):
            if year == "Unknown":
                continue

            posts = posts_by_year[year]
            index_content.append(f"### {year} ({len(posts)} posts)")
            index_content.append("")

            for post in posts:
                # Create GitHub Pages URL with repository name
                # Extract date and slug from file path: _posts/YYYY-MM-DD-slug.md
                file_path = post["file_path"]
                filename = os.path.basename(file_path)

                # Parse filename to get date and slug
                # Format: YYYY-MM-DD-slug.md
                if filename.endswith(".md"):
                    filename = filename[:-3]  # Remove .md extension

                parts = filename.split("-", 3)  # Split into [YYYY, MM, DD, slug]
                if len(parts) >= 4:
                    year_part, month_part, day_part, slug = parts
                    # Create GitHub Pages URL: /mark-forster-archive/YYYY/MM/DD/slug/
                    github_url = f"/mark-forster-archive/{year_part}/{month_part}/{day_part}/{slug}/"
                else:
                    # Fallback to relative path if filename doesn't match expected format
                    github_url = f"/mark-forster-archive/{filename}/"

                comments_text = (
                    f" ({post['comments_count']} comments)"
                    if post["comments_count"] > 0
                    else ""
                )

                categories_text = ""
                if post["categories"]:
                    categories_text = f" - *{', '.join(post['categories'])}*"

                index_content.append(
                    f"- [{post['title']}]({github_url}){comments_text}{categories_text}"
                )

            index_content.append("")

        # Write index file
        with open("index.md", "w", encoding="utf-8") as f:
            f.write("\n".join(index_content))

        logger.info("Created index.md for GitHub Pages")

    def create_config_yml(self):
        """Create _config.yml for GitHub Pages"""
        config_content = """# Mark Forster Archive - GitHub Pages Configuration

title: Mark Forster Archive
description: A comprehensive archive of Mark Forster's productivity blog posts and community discussions
baseurl: ""
url: ""

# Theme
theme: minima

# Plugins
plugins:
  - jekyll-feed
  - jekyll-sitemap

# Build settings
markdown: kramdown
highlighter: rouge

# Collections
collections:
  posts:
    output: true
    permalink: /:categories/:year/:month/:day/:title/

# Navigation
header_pages:
  - index.md

# Social links (optional)
# github_username: username
# twitter_username: username

# Exclude from processing
exclude:
  - README.md
  - requirements.txt
  - "*.py"
  - "*.log"
  - "*.json"
  - venv/
  - __pycache__/
"""

        with open("_config.yml", "w") as f:
            f.write(config_content)

        logger.info("Created _config.yml for GitHub Pages")

    def crawl_all_posts(self):
        """Main crawling function"""
        logger.info("Starting GitHub Pages archive creation...")

        # Build URL mapping first
        self.build_url_mapping()

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Filter out already completed URLs
        remaining_urls = [url for url in self.urls if url not in self.completed_urls]

        if not remaining_urls:
            logger.info("All posts already completed!")
            return

        logger.info(f"Starting crawl of {len(remaining_urls)} posts")
        logger.info(
            f"Progress: {len(self.completed_urls)}/{self.total_posts} completed"
        )

        # Process each URL
        for i, url in enumerate(remaining_urls, 1):
            logger.info(f"\n[{i}/{len(remaining_urls)}] Processing: {url}")

            if self.extract_and_save_post(url):
                self.completed_urls.add(url)
                self.save_progress(self.completed_urls)
                logger.info(f"✅ Successfully archived post {i}/{len(remaining_urls)}")
            else:
                logger.error(f"❌ Failed to archive post {i}/{len(remaining_urls)}")

            # Rate limiting
            if i < len(remaining_urls):  # Don't delay after last item
                time.sleep(self.delay_between_requests)

        # Create GitHub Pages files
        self.create_github_pages_index()
        self.create_config_yml()

        logger.info(f"\n🎉 Archive creation complete!")
        logger.info(f"📊 Processed {len(self.completed_urls)} posts")
        logger.info(f"📁 Files created in '{self.output_dir}/' directory")
        logger.info(f"🌐 Main index: index.md")
        logger.info(f"⚙️  GitHub Pages config: _config.yml")


def main():
    crawler = GitHubPagesCrawler()
    crawler.crawl_all_posts()


if __name__ == "__main__":
    main()
