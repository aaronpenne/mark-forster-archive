# Mark Forster Archive

A comprehensive archive of Mark Forster's productivity blog, preserving his influential work on time management systems like Autofocus, Do It Tomorrow, and Final Version Perfected (FVP).

## 🌐 View the Archive

**Website**: [aaronpenne.github.io/mark-forster-archive](https://aaronpenne.github.io/mark-forster-archive)

## 📚 Key Topics & Systems

### Time Management Systems
- [**Autofocus**](https://aaronpenne.github.io/mark-forster-archive/2008/12/20/autofocus/) - The original revolutionary system
- [**Do It Tomorrow**](https://aaronpenne.github.io/mark-forster-archive/2006/10/23/do-it-tomorrow-interview/) - Closed list system 
- [**Final Version Perfected (FVP)**](https://aaronpenne.github.io/mark-forster-archive/2015/05/27/a-day-with-fvp/) - Mark's ultimate system
- [**No-List Methods**](https://aaronpenne.github.io/mark-forster-archive/2016/04/17/no-list-tag/) - Later experiments

### Popular Posts
- [**"Dreams" - The Underestimated Book**](https://aaronpenne.github.io/mark-forster-archive/2008/02/28/dreams-the-underestimated-book/)
- [**Secrets of Productive People**](https://aaronpenne.github.io/mark-forster-archive/2016/02/11/secrets-of-productive-people/)
- [**100 Little Hacks to Get Work Finished**](https://aaronpenne.github.io/mark-forster-archive/2007/10/15/101-little-hacks-to-help-you-get-your-work-finished-more-qui/)
- [**A Message from Mark's Daughter Anna**](https://aaronpenne.github.io/mark-forster-archive/2015/07/23/a-message-from-marks-daughter-anna/)

### Categories
- **Articles** - Core productivity content
- **Dieting** - The "No S Diet" experiments  
- **Dreams & Goals** - Goal achievement methods
- **Reviews** - Book and system reviews
- **Road Tests** - System trials and reports

## 📖 Archive Structure

- **1,029 blog posts** (2006-2021) with full formatting preserved
- **All reader comments** maintained verbatim
- **Cross-linked navigation** between related posts
- **Categories and metadata** preserved
- **Jekyll/GitHub Pages** compatible for easy hosting

## 🔗 Navigation

- **Browse by date**: Posts organized chronologically on the website
- **Search by topic**: Use GitHub's search or browse categories
- **Follow links**: Internal post references link to archived versions
- **Original URLs**: Each post includes link to original

## 💾 For Developers

### Project Structure
```
mark-forster-archive/
├── _posts/                    # All blog posts in Jekyll format
├── _layouts/                  # Jekyll templates
├── _config.yml               # Jekyll configuration
├── crawler.py                # Main web crawler script
├── post_extractor.py         # Content extraction logic
├── link_converter.py         # URL processing utilities
├── blog_post_urls.json       # Complete URL index
└── requirements.txt          # Python dependencies
```

### Key Scripts
- **crawler.py**: Main crawler that extracts posts from markforster.squarespace.com
- **post_extractor.py**: Parses individual blog posts and extracts content/comments
- **link_converter.py**: Converts internal links to work with archived structure

### Running Locally
```bash
# Install Jekyll (if not already installed)
gem install jekyll bundler

# Serve locally
jekyll serve

# Build for production
jekyll build
```

### Content Format
All posts are stored in `_posts/` with Jekyll front matter:
```yaml
---
title: "Post Title"
author: "Mark Forster"
date: "Monday, August 14, 2006 at 16:19"
original_url: "http://markforster.squarespace.com/blog/2006/8/14/post-title.html"
layout: post
---
```

---

**Original site**: markforster.squarespace.com 
**Archive created**: 2025 as a community project