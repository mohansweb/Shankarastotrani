(function () {
  'use strict';

  // 1. Theme Toggle
  const root = document.documentElement;
  const savedTheme = localStorage.getItem('shankarastotrani-theme');
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    root.setAttribute('data-theme', 'dark');
  }

  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) {
    const syncThemeBtn = () => {
      const isDark = root.getAttribute('data-theme') === 'dark';
      themeBtn.setAttribute('aria-pressed', String(isDark));
      themeBtn.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    };
    syncThemeBtn();
    themeBtn.addEventListener('click', () => {
      const isDark = root.getAttribute('data-theme') === 'dark';
      if (isDark) {
        root.removeAttribute('data-theme');
        localStorage.setItem('shankarastotrani-theme', 'light');
      } else {
        root.setAttribute('data-theme', 'dark');
        localStorage.setItem('shankarastotrani-theme', 'dark');
      }
      syncThemeBtn();
    });
  }

  // 2. Mobile Navigation Toggle
  const menuBtn = document.getElementById('menu-toggle');
  const mainNav = document.getElementById('main-nav');
  if (menuBtn && mainNav) {
    menuBtn.addEventListener('click', () => {
      const open = mainNav.classList.toggle('is-open');
      menuBtn.setAttribute('aria-expanded', String(open));
    });
  }

  // 3. Reading Font Size Controls
  const savedScale = parseFloat(localStorage.getItem('shankarastotrani-scale') || '1');
  let currentScale = Number.isFinite(savedScale) ? Math.min(1.4, Math.max(0.85, savedScale)) : 1;
  root.style.setProperty('--reader-scale', String(currentScale));

  const setScale = (next) => {
    currentScale = Math.min(1.4, Math.max(0.85, Math.round(next * 20) / 20));
    root.style.setProperty('--reader-scale', String(currentScale));
    localStorage.setItem('shankarastotrani-scale', String(currentScale));
  };

  document.getElementById('font-dec')?.addEventListener('click', () => setScale(currentScale - 0.1));
  document.getElementById('font-reset')?.addEventListener('click', () => setScale(1));
  document.getElementById('font-inc')?.addEventListener('click', () => setScale(currentScale + 0.1));

  // 4. Homepage Instant Search & Category Filters
  const searchInput = document.getElementById('hymn-search');
  const cardsGrid = document.getElementById('hymns-grid');
  const filterPills = document.querySelectorAll('.pill[data-filter]');
  const resultsCount = document.getElementById('results-count');
  const emptyState = document.getElementById('empty-state');

  if (cardsGrid && (searchInput || filterPills.length)) {
    let activeFilter = 'all';
    let searchIndex = null;

    // Lazy-load full-text search index for searching inside verses & commentary
    fetch('search-index.json')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (Array.isArray(data)) {
          searchIndex = new Map(data.map((item) => [item.slug, item.text.toLowerCase()]));
          applyFilters();
        }
      })
      .catch(() => {});

    const cards = Array.from(cardsGrid.querySelectorAll('.card'));

    function applyFilters() {
      const query = (searchInput?.value || '').trim().toLowerCase();
      let visible = 0;

      for (const card of cards) {
        const slug = card.dataset.slug || '';
        const cats = (card.dataset.categories || '').split('|');
        const cardText = (card.dataset.search || '').toLowerCase();
        const fullText = searchIndex?.get(slug) || '';

        const matchesFilter = activeFilter === 'all' || cats.includes(activeFilter);
        const matchesQuery = !query || cardText.includes(query) || fullText.includes(query);

        const show = matchesFilter && matchesQuery;
        card.style.display = show ? '' : 'none';
        if (show) visible++;
      }

      if (resultsCount) {
        resultsCount.textContent = `Showing ${visible} of ${cards.length} articles`;
      }
      if (emptyState) {
        emptyState.classList.toggle('is-visible', visible === 0);
      }
    }

    searchInput?.addEventListener('input', applyFilters);

    filterPills.forEach((pill) => {
      pill.addEventListener('click', () => {
        filterPills.forEach((p) => {
          p.classList.remove('is-active');
          p.setAttribute('aria-pressed', 'false');
        });
        pill.classList.add('is-active');
        pill.setAttribute('aria-pressed', 'true');
        activeFilter = pill.dataset.filter || 'all';
        applyFilters();
      });
    });
  }

  // 5. Back to Top
  const topBtn = document.getElementById('back-to-top');
  if (topBtn) {
    window.addEventListener('scroll', () => {
      topBtn.classList.toggle('is-visible', window.scrollY > 450);
    }, { passive: true });
    topBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
})();
