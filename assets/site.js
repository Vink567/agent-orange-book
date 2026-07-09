
(() => {
  const pdfUrl = document.body.dataset.pdfUrl;
  if (pdfUrl) {
    document.querySelectorAll('[data-download-link]').forEach((link) => {
      link.href = pdfUrl;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    });
  }

  const progress = document.querySelector('.progress span');
  const backTop = document.querySelector('[data-back-top]');
  const tocLinks = Array.from(document.querySelectorAll('.toc-link'));
  const headings = tocLinks
    .map((link) => document.getElementById(decodeURIComponent(link.hash.slice(1))))
    .filter(Boolean);

  function updateProgress() {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const ratio = max > 0 ? Math.min(scrollTop / max, 1) : 0;
    progress.style.width = `${ratio * 100}%`;
    backTop.classList.toggle('is-visible', scrollTop > 600);
  }

  window.addEventListener('scroll', updateProgress, { passive: true });
  window.addEventListener('resize', updateProgress);
  updateProgress();

  backTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  if ('IntersectionObserver' in window && headings.length) {
    const byId = new Map(tocLinks.map((link) => [decodeURIComponent(link.hash.slice(1)), link]));
    const observer = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!visible) return;
      tocLinks.forEach((link) => link.classList.remove('is-active'));
      byId.get(visible.target.id)?.classList.add('is-active');
    }, { rootMargin: '-18% 0px -70% 0px', threshold: 0.01 });

    headings.forEach((heading) => observer.observe(heading));
  }
})();
