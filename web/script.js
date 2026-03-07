/* ─────────────────────────────────────────────
   Audience Persona Analyzer — Dashboard Script
   ───────────────────────────────────────────── */

let pieChart, barChart;

/* Muted, professional color palette */
const PALETTE = [
  '#2563eb', '#7c3aed', '#0891b2', '#059669',
  '#d97706', '#dc2626', '#4f46e5', '#0d9488',
  '#c026d3', '#ca8a04', '#e11d48', '#0284c7',
];

/* Chart.js global defaults — light, clean look */
Chart.defaults.color = '#64748b';
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.tooltip.backgroundColor = '#fff';
Chart.defaults.plugins.tooltip.titleColor = '#0f172a';
Chart.defaults.plugins.tooltip.bodyColor = '#475569';
Chart.defaults.plugins.tooltip.titleFont = { weight: '600', size: 13 };
Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.borderColor = '#e2e8f0';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.boxShadow = '0 4px 12px rgba(0,0,0,.08)';

/* Helpers */
function reveal(el) {
  el.classList.remove('hidden');
  el.classList.add('fade-in');
}

function setStatus(msg, type) {
  const s = document.getElementById('status');
  s.textContent = msg;
  s.className = 'status-msg' + (type ? ' ' + type : '');
}

/* ── Render Report ── */
function renderReport(rep) {
  const counts = rep.buckets.map(b => b.count);
  const labels = rep.buckets.map(b => b.bucket);
  const colors = labels.map((_, i) => PALETTE[i % PALETTE.length]);

  /* KPI cards */
  document.getElementById('kpiTotal').textContent = rep.total.toLocaleString();
  document.getElementById('kpiBuckets').textContent = rep.buckets.length;
  document.getElementById('kpiKeywords').textContent = Object.keys(rep.keywords_global).length;

  const top = rep.buckets.reduce((a, b) => a.count >= b.count ? a : b, rep.buckets[0]);
  document.getElementById('kpiTopPersona').textContent = top.bucket;

  reveal(document.getElementById('kpiRow'));

  /* Charts */
  const ctxPie = document.getElementById('pieChart').getContext('2d');
  const ctxBar = document.getElementById('barChart').getContext('2d');
  if (pieChart) pieChart.destroy();
  if (barChart) barChart.destroy();

  pieChart = new Chart(ctxPie, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: counts,
        backgroundColor: colors,
        borderColor: '#fff',
        borderWidth: 2,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '58%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 16,
            usePointStyle: true,
            pointStyleWidth: 8,
            font: { size: 12, weight: '500' },
            color: '#475569',
          },
        },
      },
      animation: { duration: 700 },
    },
  });

  barChart = new Chart(ctxBar, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Users',
        data: counts,
        backgroundColor: colors.map(c => c + '22'),
        borderColor: colors,
        borderWidth: 1.5,
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#64748b', font: { size: 11 } },
        },
        y: {
          grid: { color: '#f1f5f9' },
          border: { dash: [3, 3] },
          beginAtZero: true,
          ticks: { color: '#94a3b8', font: { size: 11 } },
        },
      },
      animation: { duration: 700 },
    },
  });

  reveal(document.getElementById('chartsSection'));

  /* Table */
  const tbody = document.querySelector('#bucketTable tbody');
  tbody.innerHTML = '';
  for (const b of rep.buckets) {
    const tr = document.createElement('tr');
    const ex = (b.examples || []).join(', ');
    tr.innerHTML = `<td style="font-weight:500;color:#0f172a">${b.bucket}</td><td>${b.count}</td><td>${ex || '\u2014'}</td>`;
    tbody.appendChild(tr);
  }
  reveal(document.getElementById('tableSection'));

  /* Keywords */
  const kw = document.getElementById('keywords');
  kw.innerHTML = '';
  for (const [word, count] of Object.entries(rep.keywords_global)) {
    const tag = document.createElement('span');
    tag.className = 'kw-tag';
    tag.innerHTML = `${word} <span class="kw-count">${count}</span>`;
    kw.appendChild(tag);
  }
  reveal(document.getElementById('keywordsSection'));
}

/* ── API ── */
async function uploadCSV(file) {
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch('/report_csv', { method: 'POST', body: fd });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'HTTP ' + res.status);
  }
  return res.json();
}

async function loadDemo() {
  const res = await fetch('/demo_report');
  if (!res.ok) throw new Error('Failed to load demo');
  return res.json();
}

/* ── Drag & Drop ── */
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('csvFile');

['dragenter', 'dragover'].forEach(evt =>
  dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add('drag-over'); })
);
['dragleave', 'drop'].forEach(evt =>
  dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove('drag-over'); })
);

dropZone.addEventListener('drop', e => {
  const file = e.dataTransfer.files[0];
  if (file) {
    fileInput.files = e.dataTransfer.files;
    showFileSelected(file);
  }
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) showFileSelected(fileInput.files[0]);
});

function showFileSelected(file) {
  dropZone.classList.add('file-selected');
  dropZone.querySelector('.drop-text').textContent = file.name;
  dropZone.querySelector('.drop-hint').textContent =
    (file.size / 1024).toFixed(1) + ' KB \u2014 ready to analyze';
}

/* ── Form Submit ── */
document.getElementById('uploadForm').addEventListener('submit', async e => {
  e.preventDefault();
  const file = fileInput.files[0];
  const btn = document.getElementById('analyzeBtn');
  try {
    setStatus('Analyzing\u2026', 'loading');
    btn.classList.add('loading');
    const rep = await uploadCSV(file);
    setStatus('Analysis complete', 'success');
    renderReport(rep);
  } catch (err) {
    setStatus(err.message, 'error');
  } finally {
    btn.classList.remove('loading');
  }
});

/* ── Demo ── */
document.getElementById('demoBtn').addEventListener('click', async () => {
  try {
    setStatus('Loading demo\u2026', 'loading');
    const rep = await loadDemo();
    setStatus('Demo loaded', 'success');
    renderReport(rep);
  } catch (err) {
    setStatus(err.message, 'error');
  }
});
