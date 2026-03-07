/* ─────────────────────────────────────────────
   Audience Persona Analyzer — Dashboard Script
   ───────────────────────────────────────────── */

let pieChart, barChart, sentimentChart, engagementChart, shiftChart, timelineChart;
let _lastReport = null; // store for exports

/* Muted, professional color palette */
const PALETTE = [
  '#2563eb', '#7c3aed', '#0891b2', '#059669',
  '#d97706', '#dc2626', '#4f46e5', '#0d9488',
  '#c026d3', '#ca8a04', '#e11d48', '#0284c7',
];

const SENT_COLORS = { positive: '#16a34a', neutral: '#94a3b8', negative: '#dc2626' };
const GRADE_COLORS = { A: '#16a34a', B: '#2563eb', C: '#d97706', D: '#dc2626', F: '#64748b' };

/* Chart.js global defaults */
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

    // Load data for tabs that need it
    if (tab.dataset.tab === 'history') loadHistory();
  });
});

/* ═══════════════════════════════════════════
   ANALYZE TAB
   ═══════════════════════════════════════════ */

function renderReport(rep) {
  _lastReport = rep;
  const counts = rep.buckets.map(b => b.count);
  const labels = rep.buckets.map(b => b.bucket);
  const colors = labels.map((_, i) => PALETTE[i % PALETTE.length]);

  /* KPI cards */
  document.getElementById('kpiTotal').textContent = rep.total.toLocaleString();
  const top = rep.buckets.reduce((a, b) => a.count >= b.count ? a : b, rep.buckets[0]);
  document.getElementById('kpiTopPersona').textContent = top.bucket;

  // Sentiment KPI
  if (rep.sentiment) {
    const pol = rep.sentiment.avg_polarity;
    const kpiSent = document.getElementById('kpiSentiment');
    kpiSent.textContent = (pol >= 0 ? '+' : '') + pol.toFixed(2);
    kpiSent.className = 'kpi-value ' + (pol > 0.1 ? 'positive' : pol < -0.1 ? 'negative' : '');
  }

  // Engagement KPI
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
    data: { labels, datasets: [{ data: counts, backgroundColor: colors, borderColor: '#fff', borderWidth: 2, hoverOffset: 6 }] },
    options: {
      responsive: true, maintainAspectRatio: true, cutout: '58%',
      plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyleWidth: 8, font: { size: 12, weight: '500' }, color: '#475569' } } },
      animation: { duration: 700 },
    },
  });

  barChart = new Chart(ctxBar, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Users', data: counts, backgroundColor: colors.map(c => c + '22'), borderColor: colors, borderWidth: 1.5, borderRadius: 6, borderSkipped: false }] },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 11 } } },
        y: { grid: { color: '#f1f5f9' }, border: { dash: [3, 3] }, beginAtZero: true, ticks: { color: '#94a3b8', font: { size: 11 } } },
      },
      animation: { duration: 700 },
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
        labels: ['Positive', 'Neutral', 'Negative'],
        datasets: [{ data: [sd.positive, sd.neutral, sd.negative], backgroundColor: [SENT_COLORS.positive, SENT_COLORS.neutral, SENT_COLORS.negative], borderColor: '#fff', borderWidth: 2 }],
      },
      options: {
        responsive: true, maintainAspectRatio: true, cutout: '58%',
        plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyleWidth: 8 } } },
      },
    });

    const gd = rep.engagement.grade_distribution;
    const gradeLabels = Object.keys(gd).sort();
    engagementChart = new Chart(ctxEng, {
      type: 'bar',
      data: {
        labels: gradeLabels.map(g => 'Grade ' + g),
        datasets: [{ label: 'Users', data: gradeLabels.map(g => gd[g]), backgroundColor: gradeLabels.map(g => (GRADE_COLORS[g] || '#94a3b8') + '33'), borderColor: gradeLabels.map(g => GRADE_COLORS[g] || '#94a3b8'), borderWidth: 1.5, borderRadius: 6 }],
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: '#f1f5f9' }, beginAtZero: true },
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
        <td style="font-weight:500;color:#0f172a">${c.id}</td>
        <td><span class="badge">${c.bucket}</span></td>
        <td>${(c.confidence * 100).toFixed(0)}%</td>
        <td><span class="badge ${sentClass}">${sentClass}</span></td>
        <td><strong>${c.engagement_score}</strong> <span style="color:#94a3b8">${c.engagement_grade}</span></td>`;
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
    tag.innerHTML = `${word} <span class="kw-count">${count}</span>`;
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
  if (!res.ok) throw new Error('Failed to load demo');
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
  dropZone.querySelector('.drop-text').textContent = file.name;
  dropZone.querySelector('.drop-hint').textContent = (file.size / 1024).toFixed(1) + ' KB \u2014 ready to analyze';
}

/* ── Form Submit ── */
document.getElementById('uploadForm').addEventListener('submit', async e => {
  e.preventDefault();
  const file = fileInput.files[0];
  const btn = document.getElementById('analyzeBtn');
  try {
    setStatus('status', 'Analyzing\u2026', 'loading');
    btn.classList.add('loading');
    const rep = await uploadCSV(file);
    setStatus('status', 'Analysis complete \u2014 session ' + (rep.session_id || ''), 'success');
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
    setStatus('status', 'Loading demo\u2026', 'loading');
    const rep = await loadDemo();
    setStatus('status', 'Demo loaded', 'success');
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
  const items = _lastReport.classified.map(c => ({ id: c.id, text: '' }));
  // Rebuild items from the original report
  const body = JSON.stringify({ items: _lastReport.classified.map(c => ({ id: c.id, text: c.id })) });

  // Use the demo items if available, otherwise fall back
  try {
    const res = await fetch('/export/' + format, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: _lastReport.classified.map(c => ({ id: c.id, text: c.bucket })) }),
    });
    if (!res.ok) throw new Error('Export failed');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'classified_results.' + format;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    setStatus('status', 'Export failed: ' + err.message, 'error');
  }
}


/* ═══════════════════════════════════════════
   COMPARE TAB
   ═══════════════════════════════════════════ */

document.getElementById('compareForm').addEventListener('submit', async e => {
  e.preventDefault();
  const fileA = document.getElementById('fileA').files[0];
  const fileB = document.getElementById('fileB').files[0];
  if (!fileA || !fileB) { setStatus('compareStatus', 'Please select both files', 'error'); return; }

  const btn = document.getElementById('compareBtn');
  try {
    setStatus('compareStatus', 'Comparing\u2026', 'loading');
    btn.classList.add('loading');

    const fd = new FormData();
    fd.append('file_a', fileA);
    fd.append('file_b', fileB);
    const res = await fetch('/compare', { method: 'POST', body: fd });
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || 'HTTP ' + res.status); }
    const data = await res.json();

    setStatus('compareStatus', 'Comparison complete', 'success');
    renderComparison(data);
  } catch (err) {
    setStatus('compareStatus', err.message, 'error');
  } finally {
    btn.classList.remove('loading');
  }
});

function renderComparison(data) {
  // KPIs
  const kpis = document.getElementById('compareKpis');
  kpis.innerHTML = `
    <div class="compare-stat"><div class="stat-label">Audience A</div><div class="stat-value">${data.total_a} users</div></div>
    <div class="compare-stat"><div class="stat-label">Audience B</div><div class="stat-value">${data.total_b} users</div></div>
    <div class="compare-stat"><div class="stat-label">Buckets compared</div><div class="stat-value">${data.shifts.length}</div></div>`;

  // Shift chart
  const ctx = document.getElementById('shiftChart').getContext('2d');
  if (shiftChart) shiftChart.destroy();

  const shiftLabels = data.shifts.map(s => s.bucket);
  shiftChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: shiftLabels,
      datasets: [
        { label: 'Audience A (%)', data: data.shifts.map(s => s.pct_a), backgroundColor: '#2563eb33', borderColor: '#2563eb', borderWidth: 1.5, borderRadius: 4 },
        { label: 'Audience B (%)', data: data.shifts.map(s => s.pct_b), backgroundColor: '#7c3aed33', borderColor: '#7c3aed', borderWidth: 1.5, borderRadius: 4 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { position: 'top', labels: { usePointStyle: true, pointStyleWidth: 8 } } },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: '#f1f5f9' }, beginAtZero: true, ticks: { callback: v => v + '%' } },
      },
    },
  });

  // Sentiment comparison
  if (data.sentiment_a && data.sentiment_b) {
    document.getElementById('compareSentiment').innerHTML = `
      <div class="compare-stat"><div class="stat-label">Avg polarity A</div><div class="stat-value">${data.sentiment_a.avg_polarity.toFixed(3)}</div></div>
      <div class="compare-stat"><div class="stat-label">Avg polarity B</div><div class="stat-value">${data.sentiment_b.avg_polarity.toFixed(3)}</div></div>`;
  }

  // Engagement comparison
  if (data.engagement_a && data.engagement_b) {
    document.getElementById('compareEngagement').innerHTML = `
      <div class="compare-stat"><div class="stat-label">Avg score A</div><div class="stat-value">${data.engagement_a.avg_score.toFixed(0)}</div></div>
      <div class="compare-stat"><div class="stat-label">Avg score B</div><div class="stat-value">${data.engagement_b.avg_score.toFixed(0)}</div></div>`;
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

    // Timeline chart
    if (tl.days && tl.days.length > 0) {
      const ctx = document.getElementById('timelineChart').getContext('2d');
      if (timelineChart) timelineChart.destroy();

      timelineChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: tl.days.map(d => d.date),
          datasets: [{
            label: 'Classifications',
            data: tl.days.map(d => d.total),
            borderColor: '#2563eb',
            backgroundColor: '#2563eb11',
            fill: true,
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 4,
            pointBackgroundColor: '#2563eb',
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: true,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false } },
            y: { grid: { color: '#f1f5f9' }, beginAtZero: true },
          },
        },
      });
      reveal(document.getElementById('timelineSection'));
    }

    // Session list
    if (!hist.sessions || hist.sessions.length === 0) {
      container.innerHTML = '<div class="history-placeholder"><p class="text-dim">No history yet. Analyze some data to get started.</p></div>';
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
          <span class="h-title">${s.filename || 'Session ' + s.session_id}</span>
          <span class="h-sub">${date}</span>
        </div>
        <div class="history-stats">
          <div class="h-stat"><span class="h-num">${s.total_items}</span><span class="h-label">Users</span></div>
          <div class="h-stat"><span class="h-num">${topBucket ? topBucket[0] : '\u2014'}</span><span class="h-label">Top persona</span></div>
          <div class="h-stat"><span class="h-num">${(s.avg_confidence * 100).toFixed(0)}%</span><span class="h-label">Confidence</span></div>
          ${s.avg_engagement != null ? `<div class="h-stat"><span class="h-num">${Math.round(s.avg_engagement)}</span><span class="h-label">Engagement</span></div>` : ''}
        </div>`;
      container.appendChild(div);
    }
  } catch (err) {
    container.innerHTML = `<div class="history-placeholder"><p class="text-dim">Could not load history.</p></div>`;
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
    btn.textContent = 'Running\u2026';
    btn.classList.add('loading');

    const [metRes, infoRes] = await Promise.all([
      fetch('/metrics'),
      fetch('/model_info'),
    ]);
    if (!metRes.ok) throw new Error('Failed to load metrics');
    const m = await metRes.json();
    const info = infoRes.ok ? await infoRes.json() : null;

    btn.textContent = 'Refresh';
    btn.classList.remove('loading');
    renderMetrics(m, container);
    if (info) renderModelInfo(info);
  } catch (err) {
    container.innerHTML = `<p style="color:var(--red)">${err.message}</p>`;
    btn.textContent = 'Retry';
    btn.classList.remove('loading');
  }
});

function renderMetrics(m, container) {
  const accClass = m.accuracy >= 0.80 ? 'good' : m.accuracy >= 0.60 ? 'warn' : '';
  let html = `
    <div class="metrics-grid">
      <div class="metric-stat"><span class="stat-value ${accClass}">${(m.accuracy * 100).toFixed(1)}%</span><span class="stat-label">Accuracy</span></div>
      <div class="metric-stat"><span class="stat-value">${m.correct} / ${m.total}</span><span class="stat-label">Correct</span></div>
      <div class="metric-stat"><span class="stat-value">${m.confidence_stats.mean.toFixed(2)}</span><span class="stat-label">Avg confidence</span></div>
    </div>
    <table class="f1-table"><thead><tr><th>Bucket</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th><th></th></tr></thead><tbody>`;

  for (const [bucket, s] of Object.entries(m.per_bucket)) {
    const barW = Math.round(s.f1 * 100);
    html += `<tr><td style="font-weight:500">${bucket}</td><td>${(s.precision * 100).toFixed(0)}%</td><td>${(s.recall * 100).toFixed(0)}%</td><td>${(s.f1 * 100).toFixed(0)}%</td><td>${s.support}</td><td><span class="f1-bar" style="width:${barW}px"></span></td></tr>`;
  }
  html += '</tbody></table>';

  if (m.misclassified.length) {
    html += `<details style="margin-top:14px"><summary style="cursor:pointer;font-size:.82rem;color:var(--text-sec)">${m.misclassified.length} misclassified samples</summary><table class="f1-table" style="margin-top:8px"><thead><tr><th>ID</th><th>True</th><th>Predicted</th><th>Conf</th></tr></thead><tbody>`;
    for (const x of m.misclassified) {
      html += `<tr><td>${x.id}</td><td>${x.true_label}</td><td>${x.predicted}</td><td>${x.confidence.toFixed(2)}</td></tr>`;
    }
    html += '</tbody></table></details>';
  }
  container.innerHTML = html;
}

function renderModelInfo(info) {
  const section = document.getElementById('modelInfoSection');
  const container = document.getElementById('modelInfoContent');

  let html = `<div class="model-info-grid">
    <div class="model-info-item"><div class="mi-label">Methods</div><div class="mi-value">${info.methods.join(' + ')}</div></div>
    <div class="model-info-item"><div class="mi-label">Weights</div><div class="mi-value">${Object.entries(info.weights).map(([k, v]) => k + ': ' + v).join(', ')}</div></div>
    <div class="model-info-item"><div class="mi-label">Accuracy</div><div class="mi-value">${(info.accuracy * 100).toFixed(1)}% on ${info.test_samples} samples</div></div>
    <div class="model-info-item"><div class="mi-label">Buckets</div><div class="mi-value">${info.buckets.join(', ')}</div></div>
  </div>`;

  if (info.tfidf_features) {
    html += '<div style="margin-top:16px">';
    for (const [bucket, features] of Object.entries(info.tfidf_features)) {
      html += `<div class="model-info-item" style="margin-bottom:8px"><div class="mi-label">${bucket} — top TF-IDF features</div><div class="feature-tags">${features.map(f => `<span class="feature-tag">${f}</span>`).join('')}</div></div>`;
    }
    html += '</div>';
  }

  container.innerHTML = html;
  reveal(section);
}

