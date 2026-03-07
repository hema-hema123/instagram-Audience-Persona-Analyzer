/* ═══════════════════════════════════════════════════════════
   Audience Persona Analyzer — Dashboard Script
   ═══════════════════════════════════════════════════════════ */

let pieChart, barChart;

/* ─── Consistent palette for charts ─── */
const PALETTE = [
  '#38bdf8', '#818cf8', '#34d399', '#fbbf24',
  '#f87171', '#a78bfa', '#fb923c', '#22d3ee',
  '#e879f9', '#2dd4bf', '#facc15', '#f472b6',
];

/* ─── Chart.js global defaults ─── */
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15,23,42,.92)';
Chart.defaults.plugins.tooltip.titleFont = { weight: '600', size: 13 };
Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.cornerRadius = 10;
Chart.defaults.plugins.tooltip.borderColor = 'rgba(56,189,248,.2)';
Chart.defaults.plugins.tooltip.borderWidth = 1;

/* ─── Helper: show / hide sections with animation ─── */
function reveal(el) {
  el.classList.remove('hidden');
  el.classList.add('fade-in');
}

function setStatus(msg, type = '') {
  const s = document.getElementById('status');
  s.textContent = msg;
  s.className = 'status-bar ' + type;
}

/* ─── Render full report ─── */
function renderReport(rep) {
  const counts = rep.buckets.map(b => b.count);
  const labels = rep.buckets.map(b => b.bucket);
  const colors = labels.map((_, i) => PALETTE[i % PALETTE.length]);

  /* ── KPI cards ── */
  document.getElementById('kpiTotal').textContent = rep.total.toLocaleString();
  document.getElementById('kpiBuckets').textContent = rep.buckets.length;
  document.getElementById('kpiKeywords').textContent = Object.keys(rep.keywords_global).length;

  const topBucket = rep.buckets.reduce((a, b) => a.count >= b.count ? a : b, rep.buckets[0]);
  document.getElementById('kpiTopPersona').textContent = topBucket.bucket;

  reveal(document.getElementById('kpiRow'));

  /* ── Pie chart ── */
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
        borderColor: 'rgba(10,15,30,.6)',
        borderWidth: 2,
        hoverOffset: 12,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '55%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { padding: 18, usePointStyle: true, pointStyleWidth: 10, font: { size: 12 } },
        },
      },
      animation: { animateScale: true, duration: 900 },
    },
  });

  /* ── Bar chart ── */
  barChart = new Chart(ctxBar, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Users',
        data: counts,
        backgroundColor: colors.map(c => c + 'cc'),
        borderColor: colors,
        borderWidth: 1,
        borderRadius: 8,
        borderSkipped: false,
        hoverBackgroundColor: colors,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
        y: { grid: { color: 'rgba(148,163,184,.08)' }, beginAtZero: true, ticks: { font: { size: 11 } } },
      },
      animation: { duration: 800 },
    },
  });

  reveal(document.getElementById('chartsSection'));

  /* ── Table ── */
  const tbody = document.querySelector('#bucketTable tbody');
  tbody.innerHTML = '';
  for (const b of rep.buckets) {
    const tr = document.createElement('tr');
    const ex = (b.examples || []).join(', ');
    tr.innerHTML = `<td>${b.bucket}</td><td><strong>${b.count}</strong></td><td style="color:var(--text-dim)">${ex || '—'}</td>`;
    tbody.appendChild(tr);
  }
  reveal(document.getElementById('tableSection'));

  /* ── Keywords as tags ── */
  const kwContainer = document.getElementById('keywords');
  kwContainer.innerHTML = '';
  for (const [word, count] of Object.entries(rep.keywords_global)) {
    const tag = document.createElement('span');
    tag.className = 'kw-tag';
    tag.innerHTML = `${word}<span class="kw-count">×${count}</span>`;
    kwContainer.appendChild(tag);
  }
  reveal(document.getElementById('keywordsSection'));
}

/* ─── API calls ─── */
async function uploadCSV(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/report_csv', { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || ('HTTP ' + res.status));
  }
  return res.json();
}

async function loadDemo() {
  const res = await fetch('/demo_report');
  if (!res.ok) throw new Error('Failed to load demo');
  return res.json();
}

/* ─── Drag & Drop ─── */
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
    dropZone.classList.add('file-selected');
    dropZone.querySelector('.drop-text').textContent = file.name;
    dropZone.querySelector('.drop-hint').textContent = `${(file.size / 1024).toFixed(1)} KB — ready to analyze`;
  }
});
fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) {
    dropZone.classList.add('file-selected');
    dropZone.querySelector('.drop-text').textContent = fileInput.files[0].name;
    dropZone.querySelector('.drop-hint').textContent = `${(fileInput.files[0].size / 1024).toFixed(1)} KB — ready to analyze`;
  }
});

/* ─── Form submit ─── */
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const file = fileInput.files[0];
  const btn = document.getElementById('analyzeBtn');
  try {
    setStatus('⏳ Analyzing your audience…', 'loading');
    btn.classList.add('loading');
    btn.querySelector('.btn-icon').textContent = '⏳';
    const rep = await uploadCSV(file);
    setStatus('✅ Analysis complete!', 'success');
    renderReport(rep);
  } catch (err) {
    setStatus('❌ ' + err.message, 'error');
  } finally {
    btn.classList.remove('loading');
    btn.querySelector('.btn-icon').textContent = '⚡';
  }
});

/* ─── Demo button ─── */
document.getElementById('demoBtn').addEventListener('click', async () => {
  try {
    setStatus('⏳ Loading demo data…', 'loading');
    const rep = await loadDemo();
    setStatus('✅ Demo loaded!', 'success');
    renderReport(rep);
  } catch (err) {
    setStatus('❌ ' + err.message, 'error');
  }
});
