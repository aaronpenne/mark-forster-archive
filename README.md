# Mark Forster Archive

Archive of Mark Forster's productivity blog preserved as a memorial.

## Archive Structure
- **1000+ blog posts** (2006-2024) organized by date
- All reader comments preserved
- Categories, tags, and metadata maintained
- Original HTML backup included

## For Readers
Browse `archive/posts/` by year/month/day. Each post contains:
- `content.md` - formatted post content
- `data.json` - metadata and comments
- `raw.html` - original HTML

Master index: `archive/master_index.json`

## For Runners
```bash
pip install -r requirements.txt
python url_extractor.py    # Extract blog URLs
python crawler.py          # Archive all posts
```

Progress tracked in `crawler_progress.json`. Rate limited and resumable.

Original site: markforster.squarespace.com