---
title: Mark Forster Archive
layout: home
---

# Mark Forster Archive

This archive preserves 0 blog posts and their comments from Mark Forster's productivity blog.

Mark Forster was a renowned productivity expert and author who developed several influential time management systems including Autofocus, Do It Tomorrow, and Final Version Perfected (FVP).

## Search Posts

<div class="search-container">
  <input type="text" id="searchInput" class="search-input" placeholder="Search posts by title, content, or author..." />
  <div id="searchResults" class="search-results hidden"></div>
</div>

<script>
// Simple search functionality
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

// Load search data
let posts = [];

fetch('/mark-forster-archive/assets/search-data.json')
  .then(response => response.json())
  .then(data => {
    posts = data;
    console.log(`Loaded ${posts.length} posts for search`);
  })
  .catch(error => {
    console.log('Search data not available yet, crawler may still be running');
  });

searchInput.addEventListener('input', function() {
  const query = this.value.toLowerCase();
  
  if (query.length < 2) {
    searchResults.classList.add('hidden');
    return;
  }
  
  const results = posts.filter(post => 
    post.title.toLowerCase().includes(query) ||
    post.content.toLowerCase().includes(query) ||
    post.author.toLowerCase().includes(query)
  );
  
  displayResults(results);
});

function displayResults(results) {
  if (results.length === 0) {
    searchResults.innerHTML = '<div class="search-result">No results found</div>';
  } else {
    searchResults.innerHTML = results.slice(0, 10).map(post => `
      <a href="${post.url}" class="search-result">
        <div class="search-result-title">${post.title}</div>
        <div class="search-result-date">${post.date} • ${post.author}</div>
      </a>
    `).join('');
  }
  
  searchResults.classList.remove('hidden');
}
</script>

## Posts by Year

### 2007 (1 posts)

- [Test Post](/mark-forster-archive/2007/05/09/who-am-i/) (5 comments) - *Test*

---

Archive created: 2025-06-25

This memorial archive was created to preserve Mark Forster's valuable teachings for his community.