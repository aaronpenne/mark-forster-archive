---
layout: default
title: "Mark Forster Archive"
---

# Mark Forster Archive

A comprehensive archive of Mark Forster's productivity blog, preserving his influential work on time management systems like Autofocus, Do It Tomorrow, and Final Version Perfected (FVP).

## Search Posts

<div class="search-container">
  <input type="text" class="search-input" placeholder="Search posts by title or content..." id="searchInput">
  <div class="search-results hidden" id="searchResults"></div>
</div>

## Recent Posts

{% raw %}{% for post in site.posts limit:10 %}
- [{{ post.title }}]({{ post.url }}) - {{ post.date | date: "%B %-d, %Y" }}
{% endfor %}{% endraw %}

## Key Systems

- **[Autofocus](/2008/12/20/autofocus/)** - The original revolutionary system
- **[Do It Tomorrow](/2006/10/23/do-it-tomorrow-interview/)** - Closed list system 
- **[Final Version Perfected (FVP)](/2015/05/27/a-day-with-fvp/)** - Mark's ultimate system
- **[No-List Methods](/2016/04/17/no-list-tag/)** - Later experiments

## Sample Posts

- [An Easy Challenge Revisited](/2006/08/14/an-easy-challenge-revisited/) - August 14, 2006
- [Back to School](/2006/09/16/back-to-school/) - September 16, 2006
- [Business Life Review](/2006/09/29/business-life-review/) - September 29, 2006
- [Do It Tomorrow Interview](/2006/10/23/do-it-tomorrow-interview/) - October 23, 2006
- [Autofocus](/2008/12/20/autofocus/) - December 20, 2008

## Browse All Posts

[View all posts by date](/posts/)

---

**Original site**: [markforster.squarespace.com](http://markforster.squarespace.com) (no longer maintained)  
**Archive created**: 2025 as a community project

<script>
// Search functionality
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('searchInput');
  const searchResults = document.getElementById('searchResults');
  
  // Get all posts data
  const posts = [
    {% raw %}{% for post in site.posts %}
    {
      title: "{{ post.title | escape }}",
      url: "{{ post.url }}",
      date: "{{ post.date | date: '%B %-d, %Y' }}",
      excerpt: "{{ post.excerpt | strip_html | truncatewords: 30 | escape }}"
    }{% unless forloop.last %},{% endunless %}
    {% endfor %}{% endraw %}
  ];

  searchInput.addEventListener('input', function() {
    const query = this.value.toLowerCase();
    
    if (query.length < 2) {
      searchResults.innerHTML = '';
      searchResults.classList.add('hidden');
      return;
    }

    const filteredPosts = posts.filter(post => 
      post.title.toLowerCase().includes(query) ||
      post.excerpt.toLowerCase().includes(query)
    );

    displayResults(filteredPosts);
  });

  function displayResults(results) {
    searchResults.innerHTML = '';
    
    if (results.length === 0) {
      searchResults.innerHTML = '<div class="search-result">No posts found</div>';
    } else {
      results.slice(0, 10).forEach(post => {
        const resultDiv = document.createElement('a');
        resultDiv.href = post.url;
        resultDiv.className = 'search-result';
        resultDiv.innerHTML = `
          <div class="search-result-title">${post.title}</div>
          <div class="search-result-date">${post.date}</div>
        `;
        searchResults.appendChild(resultDiv);
      });
    }
    
    searchResults.classList.remove('hidden');
  }
});
</script> 