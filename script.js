function calcReadTime() {
  const article = document.querySelector('article') || document.querySelector('.essay-body');
  const readTimeEl = document.getElementById('read-time');
  if (!article || !readTimeEl) return;
  const words = article.innerText.trim().split(/\s+/).length;
  const minutes = Math.ceil(words / 238);
  readTimeEl.textContent = `${minutes} min read`;
}
document.addEventListener('DOMContentLoaded', calcReadTime);
