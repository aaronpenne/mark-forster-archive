#!/usr/bin/env python3
"""
Script to regenerate the index with correct post count from existing posts
"""

import os
import re
from datetime import datetime


def extract_post_info_from_md(file_path):
    """Extract post information from markdown file front matter"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract front matter
        front_matter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not front_matter_match:
            return None

        front_matter = front_matter_match.group(1)

        # Extract title - handle various quote patterns
        title = "Untitled"
        title_match = re.search(r'title:\s*"([^"]*)"', front_matter)
        if title_match:
            title = title_match.group(1)
        else:
            # Try pattern for escaped quotes: title: "\"Title\""
            title_match = re.search(r'title:\s*"\\"([^"]*)\\""', front_matter)
            if title_match:
                title = title_match.group(1)
            else:
                # Try pattern without quotes: title: Title
                title_match = re.search(r"title:\s*([^\n]+)", front_matter)
                if title_match:
                    title = title_match.group(1).strip()

        # Extract date
        date_match = re.search(r"date:\s*(\d{4}-\d{2}-\d{2})", front_matter)
        date = date_match.group(1) if date_match else ""

        # Extract author
        author_match = re.search(r'author:\s*"([^"]*)"', front_matter)
        author = author_match.group(1) if author_match else "Mark Forster"

        # Extract categories
        categories = []
        categories_match = re.search(r"categories:\s*\[(.*?)\]", front_matter)
        if categories_match:
            categories_str = categories_match.group(1)
            categories = [
                cat.strip().strip("\"'")
                for cat in categories_str.split(",")
                if cat.strip()
            ]

        # Extract original URL
        url_match = re.search(r'original_url:\s*"([^"]*)"', front_matter)
        original_url = url_match.group(1) if url_match else ""

        # Count comments in the content
        comments_count = 0
        if "## Comments" in content:
            comments_sections = content.split("## Comments")
            if len(comments_sections) > 1:
                comments_content = comments_sections[1]
                # Count comment headers
                comments_count = len(re.findall(r"### Comment \d+", comments_content))

        return {
            "title": title,
            "date": date,
            "author": author,
            "categories": categories,
            "original_url": original_url,
            "comments_count": comments_count,
            "file_path": file_path,
        }
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def regenerate_index():
    """Regenerate the index with correct post count"""
    posts_dir = "_posts"
    posts_data = []

    # Scan all markdown files in _posts directory
    for filename in os.listdir(posts_dir):
        if filename.endswith(".md"):
            file_path = os.path.join(posts_dir, filename)
            post_info = extract_post_info_from_md(file_path)
            if post_info:
                posts_data.append(post_info)

    # Sort posts by date (newest first)
    posts_data.sort(key=lambda x: x["date"], reverse=True)

    # Create index content
    index_content = [
        "---",
        "title: Mark Forster Archive",
        "layout: home",
        "---",
        "",
        f"This archive preserves {len(posts_data)} blog posts and their comments from Mark Forster's productivity blog.",
        "",
        "Mark Forster is a renowned productivity expert and author who developed several influential time management systems including Autofocus, Do It Tomorrow, and Final Version Perfected (FVP).",
        "",
    ]

    # Add all posts in chronological order (newest first)
    for post in posts_data:
        # Create GitHub Pages URL
        filename = os.path.basename(post["file_path"])
        if filename.endswith(".md"):
            filename_no_ext = filename[:-3]  # Remove .md extension
        else:
            filename_no_ext = filename

        parts = filename_no_ext.split("-", 3)  # Split into [YYYY, MM, DD, slug]
        if len(parts) >= 4:
            year_part, month_part, day_part, slug = parts
            github_url = (
                f"/mark-forster-archive/{year_part}/{month_part}/{day_part}/{slug}/"
            )
        else:
            github_url = f"/mark-forster-archive/{filename_no_ext}/"

        link_text = post["title"].strip() if post["title"].strip() else filename_no_ext
        comments_text = (
            f" ({post['comments_count']} comments)"
            if post["comments_count"] > 0
            else ""
        )
        categories_text = (
            f" - *{', '.join(post['categories'])}*" if post["categories"] else ""
        )

        index_content.append(
            f"- [{link_text}]({github_url}){comments_text}{categories_text}"
        )

    # Write index file
    with open("index.md", "w", encoding="utf-8") as f:
        f.write("\n".join(index_content))

    print(f"✅ Regenerated index with {len(posts_data)} posts")
    print(f"📁 Index saved to index.md")


if __name__ == "__main__":
    regenerate_index()
