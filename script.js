function calcReadTime() {
  const content = document.querySelector('.essay-content');
  const readTimeEl = document.getElementById('read-time');
  if (!content || !readTimeEl) return;
  const words = content.innerText.trim().split(/\s+/).length;
  const minutes = Math.ceil(words / 238);
  readTimeEl.textContent = minutes + ' min read';
}
document.addEventListener('DOMContentLoaded', calcReadTime);
