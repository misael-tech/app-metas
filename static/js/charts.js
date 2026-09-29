(function () {
  const el = document.getElementById('chart-data');
  if (!el || !window.Chart) return;
  const d = JSON.parse(el.textContent);
  const css = getComputedStyle(document.documentElement);
  const c = n => css.getPropertyValue(n).trim();
  Chart.defaults.color = c('--muted'); Chart.defaults.borderColor = c('--border');
  const brl = v => 'R$ ' + Number(v).toLocaleString('pt-BR', {minimumFractionDigits: 2});
  const base = {responsive: true, maintainAspectRatio: false, plugins: {legend: {position: 'bottom'}}};
  const money = {scales: {y: {beginAtZero: true, ticks: {callback: brl}}},
                 plugins: {legend: {position: 'bottom'}, tooltip: {callbacks: {label: i => `${i.dataset.label}: ${brl(i.raw)}`}}}};
  const make = (id, cfg) => { const e = document.getElementById(id); if (e) new Chart(e, cfg); };

  if (d.nomes) {
    make('c-meta', {type: 'bar', data: {labels: d.nomes, datasets: [
      {label: 'Meta', data: d.metas, backgroundColor: c('--primary-light'), borderColor: c('--primary'), borderWidth: 1},
      {label: 'Vendido', data: d.vendidos, backgroundColor: c('--primary')}]}, options: {...base, ...money}});
    make('c-pct', {type: 'bar', data: {labels: d.nomes, datasets: [
      {label: 'Atingimento (%)', data: d.pcts, backgroundColor: d.pcts.map(p => p >= 100 ? c('--ok') : p >= 80 ? c('--warn') : c('--bad'))}]},
      options: {...base, indexAxis: 'y', plugins: {legend: {display: false}}, scales: {x: {beginAtZero: true}}}});
  }
  if (d.dias) {
    const ds = [{label: 'Vendido', data: d.valores, borderColor: c('--primary'), backgroundColor: c('--primary-light'), fill: true, tension: .3}];
    if (d.meta_diaria) ds.push({label: 'Meta diária', data: d.dias.map(() => d.meta_diaria), borderColor: c('--muted'), borderDash: [6, 4], pointRadius: 0});
    make('c-dias', {type: 'line', data: {labels: d.dias, datasets: ds}, options: {...base, ...money}});
  }
  if (d.hist_rotulos) {
    make('c-hist', {type: 'bar', data: {labels: d.hist_rotulos, datasets: [
      {label: 'Meta', data: d.hist_metas, backgroundColor: c('--primary-light'), borderColor: c('--primary'), borderWidth: 1},
      {label: 'Vendido', data: d.hist_vendidos, backgroundColor: c('--primary')}]}, options: {...base, ...money}});
  }
})();
