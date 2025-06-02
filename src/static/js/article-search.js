// -------------------------------------------------------------
// article-search.js
// Submete o formulário de busca de artigos quando filtros mudam
// -------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
  const searchForm = document.getElementById("article-search-form");
  const searchInput = document.getElementById("search-query");
  const categorySelect = document.getElementById("category-filter");
  const tagSelect = document.getElementById("tag-filter");
  const archivedCheckbox = document.getElementById("include-archived");

  if (!searchForm) return;

  [categorySelect, tagSelect, archivedCheckbox].forEach((element) => {
    if (element) {
      element.addEventListener("change", function () {
        searchForm.submit();
      });
    }
  });

  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        searchForm.submit();
      }, 500);
    });
  }
});
