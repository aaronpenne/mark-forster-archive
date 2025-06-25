---
layout: default
title: "Mark Forster Archive"
---

# Mark Forster Archive

A comprehensive archive of Mark Forster's productivity blog, preserving his influential work on time management systems like Autofocus, Do It Tomorrow, and Final Version Perfected (FVP).

## Recent Posts

{% raw %}{% for post in site.posts limit:10 %}
- [{{ post.title }}]({{ post.url }}) - {{ post.date | date: "%B %-d, %Y" }}
{% endfor %}{% endraw %}

## Key Systems

- **[Autofocus](/2008/12/20/autofocus/)** - The original revolutionary system
- **[Do It Tomorrow](/2006/10/23/do-it-tomorrow-interview/)** - Closed list system 
- **[Final Version Perfected (FVP)](/2015/05/27/a-day-with-fvp/)** - Mark's ultimate system
- **[No-List Methods](/2016/04/17/no-list-tag/)** - Later experiments

## Browse by Year

{% raw %}{% assign postsByYear = site.posts | group_by_exp:"post", "post.date | date: '%Y'" %}
{% for year in postsByYear %}
### {{ year.name }}
{% for post in year.items limit:5 %}
- [{{ post.title }}]({{ post.url }}) - {{ post.date | date: "%B %-d" }}
{% endfor %}
{% if year.items.size > 5 %}
*... and {{ year.items.size | minus: 5 }} more posts*
{% endif %}
{% endfor %}{% endraw %}

---

**Original site**: [markforster.squarespace.com](http://markforster.squarespace.com) (no longer maintained)  
**Archive created**: 2025 as a community project 