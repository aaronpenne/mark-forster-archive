#!/usr/bin/env python3
"""
Mark Forster Archive - Blog Post Content Extractor
Extracts content, comments, and metadata from individual blog posts
"""

import requests
import json
import time
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
from markdownify import markdownify as md

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/post_extraction.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class PostExtractor:
    def __init__(self):
        self.base_url = "http://markforster.squarespace.com"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

        # Selectors based on our analysis
        self.selectors = {
            "title": ".journal-entry h2.title a",
            "content": ".journal-entry .body",
            "author": ".journal-entry-tag-post-body .posted-by a",
            "date": ".journal-entry-tag-post-title .posted-on",
            "post_id": ".journal-entry[id]",  # Extract ID attribute
            "categories": ".journal-entry-tag-post-body-line2 .posted-in .tag-element a",
            "comments_count": ".post-comments a",
            "comments_container": ".journal-comment-area",
            "comments": ".comment-wrapper .comment",
            "comment_body": ".comment .body",
            "comment_signature": ".comment .signature",
        }

    def fetch_post(self, url):
        """Fetch a single blog post"""
        logger.info(f"Fetching post: {url}")
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            logger.debug(f"Successfully fetched post ({len(response.content)} bytes)")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch post {url}: {e}")
            raise

    def html_to_markdown(self, html_content):
        """Convert HTML content to markdown while preserving formatting"""
        if not html_content:
            return ""

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "lxml")

        # Remove script tags and CDATA content
        for script in soup.find_all("script"):
            script.decompose()

        # Remove CDATA sections
        for cdata in soup.find_all(
            text=lambda text: isinstance(text, str) and "CDATA" in text
        ):
            cdata.replace_with("")

        # Remove any remaining JavaScript-like content
        for element in soup.find_all(text=True):
            if element and isinstance(element, str):
                # Remove CDATA and JavaScript patterns
                cleaned = re.sub(
                    r"//\s*<!\[CDATA\[.*?\]\]>//?", "", element, flags=re.DOTALL
                )
                cleaned = re.sub(
                    r"//\s*<!\s*\[CDATA\[.*?\]\]>\s*//?", "", cleaned, flags=re.DOTALL
                )
                cleaned = re.sub(
                    r"<script.*?</script>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
                )
                if cleaned != element:
                    element.replace_with(cleaned)

        # Direct approach: process each paragraph separately to preserve structure
        paragraphs = []

        # Find all paragraph elements
        for p in soup.find_all("p"):
            p_text = p.get_text().strip()
            if p_text:  # Only include non-empty paragraphs
                paragraphs.append(p_text)

        # If no paragraphs found, try to extract content from other elements
        if not paragraphs:
            # Fallback: use markdownify on the entire content
            markdown_text = md(
                str(soup),
                heading_style="ATX",
                bullets="-",
                strong_em_symbol="*",
                code_language="",
                strip=["script", "style"],
                wrap=False,
            )
            return markdown_text.strip()

        # Join paragraphs with double line breaks to preserve structure
        # This ensures each paragraph renders as a separate block in Jekyll/GitHub Pages
        markdown_text = "\n\n".join(paragraphs)

        # Handle any remaining HTML elements that might contain lists, headings, etc.
        # Remove paragraph elements from soup to avoid double processing
        for p in soup.find_all("p"):
            p.decompose()

        # Process remaining HTML elements
        remaining_html = str(soup)
        if remaining_html.strip():
            # Convert remaining HTML to markdown
            remaining_md = md(
                remaining_html,
                heading_style="ATX",
                bullets="-",
                strong_em_symbol="*",
                code_language="",
                strip=["script", "style"],
                wrap=False,
            )

            # Combine paragraph content with remaining content
            if remaining_md.strip():
                markdown_text = markdown_text + "\n\n" + remaining_md.strip()

        # Post-process to ensure proper Jekyll/GitHub Pages rendering
        # Replace single line breaks with double line breaks for proper rendering
        # This ensures that each paragraph/list item renders as a separate block

        # First, normalize any existing double line breaks
        markdown_text = re.sub(r"\n{3,}", "\n\n", markdown_text)

        # Ensure numbered lists have proper spacing
        # Add double line breaks before numbered list items
        markdown_text = re.sub(r"(\n)(\d+\.\s)", r"\1\n\2", markdown_text)

        # Ensure bullet lists have proper spacing
        # Add double line breaks before bullet list items
        markdown_text = re.sub(r"(\n)(-\s)", r"\1\n\2", markdown_text)

        # Handle special cases like "OR" separators - ensure they have proper spacing
        markdown_text = re.sub(r"(\n)(OR)(\n)", r"\1\n\2\n\3", markdown_text)

        # Clean up any excessive line breaks (more than 2 consecutive)
        markdown_text = re.sub(r"\n{3,}", "\n\n", markdown_text)

        return markdown_text.strip()

    def clean_text(self, text, preserve_formatting=False):
        """Clean and normalize text content"""
        if not text:
            return ""

        if preserve_formatting:
            # Preserve line breaks and paragraph structure
            # Clean up excessive whitespace but keep line breaks
            text = re.sub(r"[ \t]+", " ", text)  # Collapse horizontal whitespace only
            text = re.sub(
                r"\n\s*\n\s*\n+", "\n\n", text
            )  # Collapse multiple line breaks to double
            return text.strip()
        else:
            # Original behavior for titles, etc.
            text = re.sub(r"\s+", " ", text.strip())
            return text

    def extract_post_id(self, soup):
        """Extract post ID from the journal entry element"""
        journal_entry = soup.select_one(self.selectors["post_id"])
        if journal_entry and journal_entry.get("id"):
            return journal_entry.get("id").replace("item", "")
        return None

    def extract_categories(self, soup):
        """Extract categories/tags from post"""
        categories = []
        category_links = soup.select(self.selectors["categories"])
        for link in category_links:
            category = self.clean_text(link.get_text())
            if category:
                categories.append(category)
        return categories

    def extract_comments(self, soup):
        """Extract all comments from post"""
        comments = []
        comment_elements = soup.select(self.selectors["comments"])

        for comment_elem in comment_elements:
            comment_id = comment_elem.get("id", "").replace("comment", "")

            # Extract comment body
            body_elem = comment_elem.select_one(".body")
            comment_body = ""
            if body_elem:
                # Get full HTML content to preserve formatting
                comment_body = str(body_elem)
                # Also get clean text version
                comment_text = self.html_to_markdown(str(body_elem))
            else:
                comment_text = ""

            # Extract signature (author and date)
            signature_elem = comment_elem.select_one(".signature")
            author = ""
            comment_date = ""

            if signature_elem:
                signature_text = signature_elem.get_text()
                # Parse signature like "March 31, 2011 at 19:28 | Alan Baljeu"
                if " | " in signature_text:
                    date_part, author_part = signature_text.split(" | ", 1)
                    comment_date = self.parse_date_for_jekyll(
                        self.clean_text(date_part)
                    )
                    author = self.clean_text(author_part)
                else:
                    # Fallback - entire signature as author
                    author = self.clean_text(signature_text)
                    comment_date = ""

            comment_data = {
                "id": comment_id,
                "author": author,
                "date": comment_date,
                "content": comment_text,
                "content_html": comment_body,
            }

            comments.append(comment_data)

        return comments

    def fix_domain_links(self, content):
        """Replace markforster.net with markforster.squarespace.com"""
        if isinstance(content, str):
            return content.replace("markforster.net", "markforster.squarespace.com")
        return content

    def extract_post_content(self, html_content, url):
        """Extract all content from a single blog post"""
        soup = BeautifulSoup(html_content, "lxml")

        # Extract basic post information
        title_elem = soup.select_one(self.selectors["title"])
        title = self.clean_text(title_elem.get_text()) if title_elem else ""

        content_elem = soup.select_one(self.selectors["content"])
        content_html = str(content_elem) if content_elem else ""
        content_text = self.html_to_markdown(str(content_elem)) if content_elem else ""

        author_elem = soup.select_one(self.selectors["author"])
        author = self.clean_text(author_elem.get_text()) if author_elem else ""

        date_elem = soup.select_one(self.selectors["date"])
        raw_date = self.clean_text(date_elem.get_text()) if date_elem else ""
        post_date = self.parse_date_for_jekyll(raw_date)  # Convert to Jekyll format

        # Extract comments count
        comments_count_elem = soup.select_one(self.selectors["comments_count"])
        comments_count_text = (
            comments_count_elem.get_text() if comments_count_elem else "0"
        )
        comments_count = re.findall(r"\d+", comments_count_text)
        comments_count = int(comments_count[0]) if comments_count else 0

        # Extract post ID, categories, and comments
        post_id = self.extract_post_id(soup)
        categories = self.extract_categories(soup)
        comments = self.extract_comments(soup)

        # Create post data structure
        post_data = {
            "post_id": post_id,
            "url": url,
            "title": self.fix_domain_links(title),
            "author": author,
            "date": post_date,
            "content": self.fix_domain_links(content_text),
            "content_html": self.fix_domain_links(content_html),
            "categories": categories,
            "comments_count": comments_count,
            "comments": comments,
            "extracted_at": datetime.now().isoformat(),
            "raw_html": self.fix_domain_links(html_content),
        }

        logger.info(
            f"Extracted post: '{title}' ({comments_count} comments, {len(categories)} categories)"
        )
        return post_data

    def extract_single_post(self, url):
        """Extract content from a single blog post URL"""
        try:
            html_content = self.fetch_post(url)
            post_data = self.extract_post_content(html_content, url)
            return post_data
        except Exception as e:
            logger.error(f"Failed to extract post {url}: {e}")
            return None

    def save_post_data(self, post_data, output_dir="archive"):
        """Save individual post data to organized file structure"""
        if not post_data or not post_data.get("url"):
            return False

        # Create directory structure based on URL path
        url_path = urlparse(post_data["url"]).path
        # Remove /blog/ prefix and .html suffix
        clean_path = url_path.replace("/blog/", "").replace(".html", "")

        # Create nested directory structure
        post_dir = os.path.join(output_dir, "posts", clean_path)
        os.makedirs(post_dir, exist_ok=True)

        # Save different formats
        files_saved = []

        # Save full JSON data
        json_file = os.path.join(post_dir, "data.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        files_saved.append(json_file)

        # Save markdown version of content
        markdown_file = os.path.join(post_dir, "content.md")
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(f"# {post_data.get('title', 'Untitled')}\n\n")
            f.write(f"**Author:** {post_data.get('author', 'Unknown')}\n")
            f.write(f"**Date:** {post_data.get('date', 'Unknown')}\n")
            if post_data.get("categories"):
                f.write(f"**Categories:** {', '.join(post_data['categories'])}\n")
            f.write(f"**URL:** {post_data.get('url', '')}\n\n")
            f.write("---\n\n")
            f.write(post_data.get("content", ""))

            if post_data.get("comments"):
                f.write(f"\n\n## Comments ({len(post_data['comments'])})\n\n")
                for i, comment in enumerate(post_data["comments"], 1):
                    f.write(f"### Comment {i}\n")
                    f.write(f"**Author:** {comment.get('author', 'Anonymous')}\n")
                    f.write(f"**Date:** {comment.get('date', 'Unknown')}\n\n")
                    f.write(f"{comment.get('content', '')}\n\n")
                    f.write("---\n\n")
        files_saved.append(markdown_file)

        # Save raw HTML
        html_file = os.path.join(post_dir, "raw.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(post_data.get("raw_html", ""))
        files_saved.append(html_file)

        logger.info(f"Saved post to {post_dir} ({len(files_saved)} files)")
        return True

    def parse_date_for_jekyll(self, date_string):
        """Parse date string from HTML and convert to Jekyll-compatible ISO format"""
        if not date_string:
            return ""

        # Common date formats found in the blog:
        # "Wednesday, October 16, 2013 at 14:55"
        # "Friday, September 29, 2006 at 18:04"
        # "March 31, 2011 at 19:28"

        # Remove "at" and time if present
        date_part = (
            date_string.split(" at ")[0] if " at " in date_string else date_string
        )

        # Try to parse with different formats
        date_formats = [
            "%A, %B %d, %Y",  # Wednesday, October 16, 2013
            "%B %d, %Y",  # March 31, 2011
            "%Y-%m-%d",  # Already ISO format
        ]

        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_part.strip(), fmt)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # If all parsing fails, return original string
        logger.warning(f"Could not parse date: {date_string}")
        return date_string


if __name__ == "__main__":
    # Test with a single post
    extractor = PostExtractor()

    # Test with the SF Tips post that has categories
    test_url = (
        "http://markforster.squarespace.com/blog/2011/3/31/sf-tips-8-dismissal.html"
    )

    print(f"Testing content extraction with: {test_url}")
    post_data = extractor.extract_single_post(test_url)

    if post_data:
        print(f"\n✅ Successfully extracted post:")
        print(f"   Title: {post_data['title']}")
        print(f"   Author: {post_data['author']}")
        print(f"   Date: {post_data['date']}")
        print(f"   Categories: {post_data['categories']}")
        print(f"   Comments: {post_data['comments_count']}")
        print(f"   Content length: {len(post_data['content'])} chars")

        # Save the test post
        success = extractor.save_post_data(post_data)
        if success:
            print(f"   💾 Saved to archive/posts/2011/3/31/sf-tips-8-dismissal/")
    else:
        print("❌ Failed to extract post content")
