document.getElementById('menu-btn')?.addEventListener('click', () =>
  document.getElementById('sidebar').classList.toggle('open'));

const root = document.documentElement;
const btns = document.querySelectorAll('.theme-btn');
const rotulo = () => btns.forEach(b => b.textContent = root.dataset.theme === 'dark' ? ' Modo claro' : ' Modo escuro');
rotulo();
btns.forEach(b => b.addEventListener('click', () => {
  root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
  try { localStorage.setItem('tema', root.dataset.theme); } catch (e) {}
  if (document.getElementById('chart-data')) location.reload(); else rotulo();
}));
