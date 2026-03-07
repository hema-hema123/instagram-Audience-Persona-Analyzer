/* ─────────────────────────────────────────────
   PERSONA//ANALYZER — CYBERPUNK DASHBOARD
   Neon brutalist Chart.js + interactions
   ───────────────────────────────────────────── */

let pieChart, barChart, sentimentChart, engagementChart, shiftChart, timelineChart;
let _lastReport = null;

/* ── Neon cyberpunk palette ── */
const PALETTE = [
  '#00D9FF', '#FF006E', '#FFBE0B', '#06FFA5',
  '#8338EC', '#FF2E63', '#00B4D8', '#FB5607',
  '#7209B7', '#3A86FF', '#F72585', '#4CC9F0',
];

const SENT_COLORS = { positive: '#06FFA5', neutral: '#8338EC', negative: '#FF006E' };
const GRADE_COLORS = { A: '#06FFA5', B: '#00D9FF', C: '#FFBE0B', D: '#FF006E', F: '#4A5180' };

/* ── Chart.js global defaults — dark neon ── */
Chart.defaults.color = '#8B92B8';
Chart.defaults.font.family = "'Arial Black', 'Impact', system-ui, sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.tooltip.backgroundColor = '#0D1130';
Chart.defaults.plugins.tooltip.titleColor = '#00D9FF';
Chart.defaults.plugins.tooltip.bodyColor = '#E8ECF8';
Chart.defaults.plugins.tooltip.titleFont = { weight: '900', size: 12 };
Chart.defaults.plugins.tooltip.bodyFont = { size: 11 };
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.cornerRadius = 0;
Chart.defaults.plugins.tooltip.borderColor = '#00D9FF';
Chart.defaults.plugins.tooltip.borderWidth = 2;
Chart.defaults.plugins.legend.labels.color = '#8B92B8';

/* ── Helpers ── */
function reveal(el) { el.classList.remove('hidden'); el.classList.add('fade-in'); }
function hide(el) { el.classList.add('hidden'); el.classList.remove('fade-in'); }

function setStatus(id, msg, type) {
  const s = document.getElementById(id);
  s.textContent = msg;
  s.className = 'status-msg' + (type ? ' ' + type : '');
}

/* ── Tab Navigation ── */
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    if (tab.dataset.tab === 'history') loadHistory();
  });
});

/* ═══════════════════════════════════════════
   ANALYZE TAB
   ═══════════════════════════════════════════ */

function renderReport(rep) {
  _lastReport = rep;
  const counts = rep.buckets.map(b => b.count);
  const labels = rep.buckets.map(b => b.bucket.toUpperCase());
  const colors = labels.map((_, i) => PALETTE[i % PALETTE.length]);

  /* KPI cards */
  document.getElementById('kpiTotal').textContent = rep.total.toLocaleString();
  const top = rep.buckets.reduce((a, b) => a.count >= b.count ? a : b, rep.buckets[0]);
  document.getElementById('kpiTopPersona').textContent = top.bucket.toUpperCase();

  if (rep.sentiment) {
    const pol = rep.sentiment.avg_polarity;
    const kpiSent = document.getElementById('kpiSentiment');
    kpiSent.textContent = (pol >= 0 ? '+' : '') + pol.toFixed(2);
    kpiSent.className = 'kpi-value ' + (pol > 0.1 ? 'positive' : pol < -0.1 ? 'negative' : '');
  }

  if (rep.engagement) {
    const avg = rep.engagement.avg_score;
    const kpiEng = document.getElementById('kpiEngagement');
    const grade = avg >= 85 ? 'A' : avg >= 70 ? 'B' : avg >= 55 ? 'C' : avg >= 40 ? 'D' : 'F';
    kpiEng.textContent = Math.round(avg) + ' (' + grade + ')';
    kpiEng.className = 'kpi-value grade-' + grade.toLowerCase();
  }

  reveal(document.getElementById('kpiRow'));

  /* Persona Charts */
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
        backgroundColor: colors.map(c => c + '44'),
        borderColor: colors,
        borderWidth: 3,
        hoverOffset: 8,
        hoverBorderWidth: 4,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: true, cutout: '62%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyleWidth: 8, font: { size: 10, weight: '900' } } },
      },
      animation: { duration: 800, easing: 'easeOutQuart' },
    },
  });

  barChart = new Chart(ctxBar, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'USERS',
        data: counts,
        backgroundColor: colors.map(c => c + '33'),
        borderColor: colors,
        borderWidth: 3,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#8B92B8', font: { size: 9, weight: '900' } } },
        y: { grid: { color: '#1E255533' }, border: { dash: [4, 4] }, beginAtZero: true, ticks: { color: '#4A5180', font: { size: 10 } } },
      },
      animation: { duration: 800 },
    },
  });

  reveal(document.getElementById('chartsSection'));

  /* Sentiment + Engagement Charts */
  if (rep.sentiment && rep.engagement) {
    const ctxSent = document.getElementById('sentimentChart').getContext('2d');
    const ctxEng = document.getElementById('engagementChart').getContext('2d');
    if (sentimentChart) sentimentChart.destroy();
    if (engagementChart) engagementChart.destroy();

    const sd = rep.sentiment.distribution;
    sentimentChart = new Chart(ctxSent, {
      type: 'doughnut',
      data: {
        labels: ['POSITIVE', 'NEUTRAL', 'NEGATIVE'],
        datasets: [{
          data: [sd.positive, sd.neutral, sd.negative],
          backgroundColor: [SENT_COLORS.positive + '44', SENT_COLORS.neutral + '44', SENT_COLORS.negative + '44'],
          borderColor: [SENT_COLORS.positive, SENT_COLORS.neutral, SENT_COLORS.negative],
          borderWidth: 3,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: true, cutout: '62%',
        plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyleWidth: 8, font: { weight: '900', size: 10 } } } },
      },
    });

    const gd = rep.engagement.grade_distribution;
    const gradeLabels = Object.keys(gd).sort();
    engagementChart = new Chart(ctxEng, {
      type: 'bar',
      data: {
        labels: gradeLabels.map(g => 'GRADE ' + g),
        datasets: [{
          label: 'USERS',
          data: gradeLabels.map(g => gd[g]),
          backgroundColor: gradeLabels.map(g => (GRADE_COLORS[g] || '#4A5180') + '33'),
          borderColor: gradeLabels.map(g => GRADE_COLORS[g] || '#4A5180'),
          borderWidth: 3,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { weight: '900', size: 9 } } },
          y: { grid: { color: '#1E255533' }, beginAtZero: true },
        },
      },
    });

    reveal(document.getElementById('insightsSection'));
  }

  /* Detailed Table */
  if (rep.classified && rep.classified.length) {
    const tbody = document.querySelector('#detailTable tbody');
    tbody.innerHTML = '';
    for (const c of rep.classified) {
      const tr = document.createElement('tr');
      const sentClass = c.sentiment || 'neutral';
      tr.innerHTML = `
        <td style="font-weight:900;color:#E8ECF8;font-family:monospace">${c.id}</td>
        <td><span class="badge">${c.bucket.toUpperCase()}</span></td>
        <td style="color:#00D9FF;font-weight:900">${(c.confidence * 100).toFixed(0)}%</td>
        <td><span class="badge ${sentClass}">${sentClass.toUpperCase()}</span></td>
        <td><strong style="color:#FFBE0B">${c.engagement_score}</strong> <span style="color:#4A5180">${c.engagement_grade}</span></td>`;
      tbody.appendChild(tr);
    }
    reveal(document.getElementById('tableSection'));
  }

  /* Keywords */
  const kw = document.getElementById('keywords');
  kw.innerHTML = '';
  for (const [word, count] of Object.entries(rep.keywords_global)) {
    const tag = document.createElement('span');
    tag.className = 'kw-tag';
    tag.innerHTML = `${word.toUpperCase()} <span class="kw-count">${count}</span>`;
    kw.appendChild(tag);
  }
  reveal(document.getElementById('keywordsSection'));
}

/* ── API calls ── */
async function uploadCSV(file) {
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch('/report_csv', { method: 'POST', body: fd });
  if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || 'HTTP ' + res.status); }
  return res.json();
}

async function loadDemo() {
  const res = await fetch('/demo_report');
  if (!res.ok) throw new Error('DEMO LOAD FAILED');
  return res.json();
}

/* ── Drag & Drop ── */
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('csvFile');

['dragenter', 'dragover'].forEach(evt => dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add('drag-over'); }));
['dragleave', 'drop'].forEach(evt => dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove('drag-over'); }));

dropZone.addEventListener('drop', e => {
  const file = e.dataTransfer.files[0];
  if (file) { fileInput.files = e.dataTransfer.files; showFileSelected(file); }
});
fileInput.addEventListener('change', () => { if (fileInput.files[0]) showFileSelected(fileInput.files[0]); });

function showFileSelected(file) {
  dropZone.classList.add('file-selected');
  dropZone.querySelector('.drop-text').textContent = '\u2588 ' + file.name.toUpperCase();
  dropZone.querySelector('.drop-hint').textContent = (file.size / 1024).toFixed(1) + ' KB // READY';
}

/* ── Form Submit ── */
document.getElementById('uploadForm').addEventListener('submit', async e => {
  e.preventDefault();
  const file = fileInput.files[0];
  const btn = document.getElementById('analyzeBtn');
  try {
    setStatus('status', 'ANALYZING...', 'loading');
    btn.classList.add('loading');
    const rep = await uploadCSV(file);
    setStatus('status', 'ANALYSIS COMPLETE // SESSION ' + (rep.session_id || ''), 'success');
    renderReport(rep);
  } catch (err) {
    setStatus('status', err.message, 'error');
  } finally {
    btn.classList.remove('loading');
  }
});

/* ── Demo ── */
document.getElementById('demoBtn').addEventListener('click', async () => {
  try {
    setStatus('status', 'LOADING DEMO...', 'loading');
    const rep = await loadDemo();
    setStatus('status', 'DEMO LOADED', 'success');
    renderReport(rep);
  } catch (err) {
    setStatus('status', err.message, 'error');
  }
});

/* ── Export Buttons ── */
document.getElementById('exportCsvBtn').addEventListener('click', () => exportData('csv'));
document.getElementById('exportJsonBtn').addEventListener('click', () => exportData('json'));

async function exportData(format) {
  if (!_lastReport || !_lastReport.classified) return;
  try {
    const res = await fetch('/export/' + format, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: _lastReport.classified.map(c => ({ id: c.id, text: c.bucket })) }),
    });
    if (!res.ok) throw new Error('EXPORT FAILED');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'classified_results.' + format;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    setStatus('status', 'EXPORT FAILED: ' + err.message, 'error');
  }
}


/* ═══════════════════════════════════════════
   COMPARE TAB
   ═══════════════════════════════════════════ */

document.getElementById('compareForm').addEventListener('submit', async e => {
  e.preventDefault();
  const fileA = document.getElementById('fileA').files[0];
  const fileB = document.getElementById('fileB').files[0];
  if (!fileA || !fileB) { setStatus('compareStatus', 'SELECT BOTH FILES', 'error'); return; }

  const btn = document.getElementById('compareBtn');
  try {
    setStatus('compareStatus', 'COMPARING...', 'loading');
    btn.classList.add('loading');

    const fd = new FormData();
    fd.append('file_a', fileA);
    fd.append('file_b', fileB);
    const res = await fetch('/compare', { method: 'POST', body: fd });
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || 'HTTP ' + res.status); }
    const data = await res.json();

    setStatus('compareStatus', 'COMPARISON COMPLETE', 'success');
    renderComparison(data);
  } catch (err) {
    setStatus('compareStatus', err.message, 'error');
  } finally {
    btn.classList.remove('loading');
  }
});

function renderComparison(data) {
  const kpis = document.getElementById('compareKpis');
  kpis.innerHTML = `
    <div class="compare-stat"><div class="stat-label">AUDIENCE_A</div><div class="stat-value">${data.total_a} USERS</div></div>
    <div class="compare-stat"><div class="stat-label">AUDIENCE_B</div><div class="stat-value">${data.total_b} USERS</div></div>
    <div class="compare-stat"><div class="stat-label">BUCKETS</div><div class="stat-value">${data.shifts.length}</div></div>`;

  const ctx = document.getElementById('shiftChart').getContext('2d');
  if (shiftChart) shiftChart.destroy();

  const shiftLabels = data.shifts.map(s => s.bucket.toUpperCase());
  shiftChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: shiftLabels,
      datasets: [
        { label: 'A (%)', data: data.shifts.map(s => s.pct_a), backgroundColor: '#00D9FF33', borderColor: '#00D9FF', borderWidth: 3 },
        { label: 'B (%)', data: data.shifts.map(s => s.pct_b), backgroundColor: '#FF006E33', borderColor: '#FF006E', borderWidth: 3 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { position: 'top', labels: { usePointStyle: true, pointStyleWidth: 8, font: { weight: '900', size: 10 } } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { weight: '900', size: 9 } } },
        y: { grid: { color: '#1E255533' }, beginAtZero: true, ticks: { callback: v => v + '%' } },
      },
    },
  });

  if (data.sentiment_a && data.sentiment_b) {
    document.getElementById('compareSentiment').innerHTML = `
      <div class="compare-stat"><div class="stat-label">AVG POLARITY A</div><div class="stat-value" style="color:#00D9FF">${data.sentiment_a.avg_polarity.toFixed(3)}</div></div>
      <div class="compare-stat"><div class="stat-label">AVG POLARITY B</div><div class="stat-value" style="color:#FF006E">${data.sentiment_b.avg_polarity.toFixed(3)}</div></div>`;
  }

  if (data.engagement_a && data.engagement_b) {
    document.getElementById('compareEngagement').innerHTML = `
      <div class="compare-stat"><div class="stat-label">AVG SCORE A</div><div class="stat-value" style="color:#00D9FF">${data.engagement_a.avg_score.toFixed(0)}</div></div>
      <div class="compare-stat"><div class="stat-label">AVG SCORE B</div><div class="stat-value" style="color:#FF006E">${data.engagement_b.avg_score.toFixed(0)}</div></div>`;
  }

  reveal(document.getElementById('compareResults'));
}


/* ═══════════════════════════════════════════
   HISTORY TAB
   ═══════════════════════════════════════════ */

async function loadHistory() {
  const container = document.getElementById('historyList');
  try {
    const [histRes, tlRes] = await Promise.all([
      fetch('/history?limit=20'),
      fetch('/timeline?days=30'),
    ]);
    const hist = await histRes.json();
    const tl = await tlRes.json();

    if (tl.days && tl.days.length > 0) {
      const ctx = document.getElementById('timelineChart').getContext('2d');
      if (timelineChart) timelineChart.destroy();

      timelineChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: tl.days.map(d => d.date),
          datasets: [{
            label: 'CLASSIFICATIONS',
            data: tl.days.map(d => d.total),
            borderColor: '#00D9FF',
            backgroundColor: '#00D9FF11',
            fill: true,
            tension: 0,
            borderWidth: 3,
            pointRadius: 5,
            pointBackgroundColor: '#0D1130',
            pointBorderColor: '#00D9FF',
            pointBorderWidth: 3,
            pointHoverBackgroundColor: '#00D9FF',
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: true,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { font: { size: 9, weight: '900' } } },
            y: { grid: { color: '#1E255533' }, beginAtZero: true },
          },
        },
      });
      reveal(document.getElementById('timelineSection'));
    }

    if (!hist.sessions || hist.sessions.length === 0) {
      container.innerHTML = '<div class="history-placeholder"><p class="text-dim">NO HISTORY YET. ANALYZE SOME DATA TO GET STARTED.</p></div>';
      return;
    }

    container.innerHTML = '';
    for (const s of hist.sessions) {
      const div = document.createElement('div');
      div.className = 'history-card';
      const date = new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
      const topBucket = Object.entries(s.distribution).sort((a, b) => b[1] - a[1])[0];
      div.innerHTML = `
        <div class="history-meta">
          <span class="h-title">${(s.filename || 'SESSION_' + s.session_id).toUpperCase()}</span>
          <span class="h-sub">${date}</span>
        </div>
        <div class="history-stats">
          <div class="h-stat"><span class="h-num">${s.total_items}</span><span class="h-label">USERS</span></div>
          <div class="h-stat"><span class="h-num">${topBucket ? topBucket[0].toUpperCase() : '\u2014'}</span><span class="h-label">TOP</span></div>
          <div class="h-stat"><span class="h-num">${(s.avg_confidence * 100).toFixed(0)}%</span><span class="h-label">CONF</span></div>
          ${s.avg_engagement != null ? `<div class="h-stat"><span class="h-num">${Math.round(s.avg_engagement)}</span><span class="h-label">ENG</span></div>` : ''}
        </div>`;
      container.appendChild(div);
    }
  } catch (err) {
    container.innerHTML = '<div class="history-placeholder"><p class="text-dim">COULD NOT LOAD HISTORY.</p></div>';
  }
}

document.getElementById('refreshHistoryBtn').addEventListener('click', loadHistory);


/* ═══════════════════════════════════════════
   MODEL TAB
   ═══════════════════════════════════════════ */

document.getElementById('loadMetricsBtn').addEventListener('click', async () => {
  const btn = document.getElementById('loadMetricsBtn');
  const container = document.getElementById('metricsContent');
  try {
    btn.textContent = 'RUNNING...';
    btn.classList.add('loading');

    const [metRes, infoRes] = await Promise.all([
      fetch('/metrics'),
      fetch('/model_info'),
    ]);
    if (!metRes.ok) throw new Error('FAILED TO LOAD METRICS');
    const m = await metRes.json();
    const info = infoRes.ok ? await infoRes.json() : null;

    btn.textContent = 'REFRESH';
    btn.classList.remove('loading');
    renderMetrics(m, container);
    if (info) renderModelInfo(info);
  } catch (err) {
    container.innerHTML = `<p style="color:#FF006E">${err.message}</p>`;
    btn.textContent = 'RETRY';
    btn.classList.remove('loading');
  }
});

function renderMetrics(m, container) {
  const accClass = m.accuracy >= 0.80 ? 'good' : m.accuracy >= 0.60 ? 'warn' : '';
  let html = `
    <div class="metrics-grid">
      <div class="metric-stat"><span class="stat-value ${accClass}">${(m.accuracy * 100).toFixed(1)}%</span><span class="stat-label">ACCURACY</span></div>
      <div class="metric-stat"><span class="stat-value">${m.correct} / ${m.total}</span><span class="stat-label">CORRECT</span></div>
      <div class="metric-stat"><span class="stat-value">${m.confidence_stats.mean.toFixed(2)}</span><span class="stat-label">AVG CONFIDENCE</span></div>
    </div>
    <table class="f1-table"><thead><tr><th>BUCKET</th><th>PRECISION</th><th>RECALL</th><th>F1</th><th>SUPPORT</th><th></th></tr></thead><tbody>`;

  for (const [bucket, s] of Object.entries(m.per_bucket)) {
    const barW = Math.round(s.f1 * 120);
    html += `<tr><td style="font-weight:900;color:#E8ECF8">${bucket.toUpperCase()}</td><td>${(s.precision * 100).toFixed(0)}%</td><td>${(s.recall * 100).toFixed(0)}%</td><td style="color:#FFBE0B;font-weight:900">${(s.f1 * 100).toFixed(0)}%</td><td>${s.support}</td><td><span class="f1-bar" style="width:${barW}px"></span></td></tr>`;
  }
  html += '</tbody></table>';

  if (m.misclassified.length) {
    html += `<details style="margin-top:16px"><summary style="cursor:pointer;font-family:monospace;font-size:.75rem;color:#8B92B8;text-transform:uppercase;letter-spacing:.06em">\u25B6 ${m.misclassified.length} MISCLASSIFIED SAMPLES</summary><table class="f1-table" style="margin-top:10px"><thead><tr><th>ID</th><th>TRUE</th><th>PREDICTED</th><th>CONF</th></tr></thead><tbody>`;
    for (const x of m.misclassified) {
      html += `<tr><td>${x.id}</td><td style="color:#06FFA5">${x.true_label.toUpperCase()}</td><td style="color:#FF006E">${x.predicted.toUpperCase()}</td><td>${x.confidence.toFixed(2)}</td></tr>`;
    }
    html += '</tbody></table></details>';
  }
  container.innerHTML = html;
}

function renderModelInfo(info) {
  const section = document.getElementById('modelInfoSection');
  const container = document.getElementById('modelInfoContent');

  let html = `<div class="model-info-grid">
    <div class="model-info-item"><div class="mi-label">METHODS</div><div class="mi-value">${info.methods.join(' + ').toUpperCase()}</div></div>
    <div class="model-info-item"><div class="mi-label">WEIGHTS</div><div class="mi-value">${Object.entries(info.weights).map(([k, v]) => k.toUpperCase() + ': ' + v).join(' // ')}</div></div>
    <div class="model-info-item"><div class="mi-label">ACCURACY</div><div class="mi-value" style="color:#06FFA5">${(info.accuracy * 100).toFixed(1)}% ON ${info.test_samples} SAMPLES</div></div>
    <div class="model-info-item"><div class="mi-label">BUCKETS</div><div class="mi-value">${info.buckets.join(' \u2502 ').toUpperCase()}</div></div>
  </div>`;

  if (info.tfidf_features) {
    html += '<div style="margin-top:18px">';
    for (const [bucket, features] of Object.entries(info.tfidf_features)) {
      html += `<div class="model-info-item" style="margin-bottom:10px"><div class="mi-label">${bucket.toUpperCase()} // TOP TF-IDF FEATURES</div><div class="feature-tags">${features.map(f => `<span class="feature-tag">${f.toUpperCase()}</span>`).join('')}</div></div>`;
    }
    html += '</div>';
  }

  container.innerHTML = html;
  reveal(section);
}

