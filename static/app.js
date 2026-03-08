/* Frontend logic for the customer segmentation dashboard */

const COLORS = {
    green: '#00a86b', greenBg: 'rgba(0,168,107,0.2)',
    blue: '#58a6ff', blueBg: 'rgba(88,166,255,0.2)',
    orange: '#d29922', orangeBg: 'rgba(210,153,34,0.2)',
    purple: '#bc8cff', purpleBg: 'rgba(188,140,255,0.2)',
    red: '#f85149', redBg: 'rgba(248,81,73,0.2)',
    cyan: '#56d4dd', cyanBg: 'rgba(86,212,221,0.2)',
    text: '#8b949e', grid: '#2d333b',
};
const SEG_COLORS = ['#00a86b', '#58a6ff', '#d29922', '#bc8cff', '#f85149', '#56d4dd'];
const SEG_BG = ['rgba(0,168,107,0.2)', 'rgba(88,166,255,0.2)', 'rgba(210,153,34,0.2)',
    'rgba(188,140,255,0.2)', 'rgba(248,81,73,0.2)', 'rgba(86,212,221,0.2)'];

Chart.defaults.color = COLORS.text;
Chart.defaults.borderColor = COLORS.grid;
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 14;

const charts = {};
let segmentData = null;

async function fetchJSON(url, opts) {
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(`${res.status}`);
    return res.json();
}

// Tab Navigation

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    });
});

// Sub-tabs
document.querySelectorAll('.sub-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.sub-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`sub-${btn.dataset.subtab}`).classList.add('active');
    });
});

// 1. Executive Summary

async function loadExecutive() {
    const data = await fetchJSON('/api/executive_summary');
    const m = data.headline_metrics;

    document.getElementById('headerMeta').textContent =
        `${m.total_customers.toLocaleString()} customers | ${m.total_orders.toLocaleString()} orders | ${m.segments} segments`;

    document.getElementById('execKPIs').innerHTML = [
        { label: 'Total Customers', val: m.total_customers.toLocaleString(), cls: 'green' },
        { label: 'Total Orders', val: m.total_orders.toLocaleString(), cls: 'blue' },
        { label: 'Total Revenue', val: `$${m.total_revenue.toLocaleString()}`, cls: 'orange' },
        { label: 'Avg Spend', val: `$${m.avg_spend}`, cls: 'purple' },
        { label: 'Avg Satisfaction', val: `${m.avg_satisfaction}/5`, cls: 'cyan' },
        { label: 'High Risk Customers', val: m.high_risk_customers.toLocaleString(), cls: 'red' },
    ].map(k => `<div class="kpi-card"><div class="kpi-label">${k.label}</div><div class="kpi-value ${k.cls}">${k.val}</div></div>`).join('');

    document.getElementById('execFindings').innerHTML = data.findings.map(f =>
        `<div class="finding-card ${f.type}">
            <div class="finding-title">${f.title}</div>
            <div class="finding-detail">${f.detail}</div>
        </div>`
    ).join('');

    document.getElementById('execOpportunities').innerHTML = data.opportunities.map(o =>
        `<div class="opp-card">
            <div><div class="opp-segment">${o.segment}</div><div class="opp-action">${o.action}</div></div>
            <span class="impact-badge ${o.impact}">${o.impact}</span>
        </div>`
    ).join('');

    document.getElementById('execMethodology').innerHTML = data.methodology.map((m, i) =>
        `<div class="meth-item"><span class="meth-number">${i + 1}</span>${m}</div>`
    ).join('');
}

// 2. Overview Tab

async function loadOverview() {
    const [data, churnData] = await Promise.all([
        fetchJSON('/api/segments'),
        fetchJSON('/api/churn_scores'),
    ]);
    segmentData = data;

    document.getElementById('kpiGrid').innerHTML = [
        { label: 'Total Customers', val: data.total_customers.toLocaleString(), cls: 'green' },
        { label: 'Total Orders', val: data.total_orders.toLocaleString(), cls: 'blue' },
        { label: 'Avg Spend', val: `$${data.overall_avg_spend}`, cls: 'orange' },
        { label: 'Avg Satisfaction', val: `${data.overall_avg_satisfaction}/5`, cls: 'purple' },
        { label: 'Avg Churn Score', val: churnData.avg_churn_score, cls: 'red' },
    ].map(k => `<div class="kpi-card"><div class="kpi-label">${k.label}</div><div class="kpi-value ${k.cls}">${k.val}</div></div>`).join('');

    // Segment donut
    if (charts.donut) charts.donut.destroy();
    charts.donut = new Chart(document.getElementById('segmentDonut'), {
        type: 'doughnut',
        data: {
            labels: data.segments.map(s => s.name),
            datasets: [{ data: data.segments.map(s => s.size), backgroundColor: SEG_COLORS, borderColor: '#1c2129', borderWidth: 3 }]
        },
        options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom' } } }
    });

    // Churn donut
    const churnLabels = Object.keys(churnData.distribution);
    const churnValues = Object.values(churnData.distribution);
    const churnColors = churnLabels.map(l => l === 'High' ? COLORS.red : l === 'Medium' ? COLORS.orange : COLORS.green);
    if (charts.churn) charts.churn.destroy();
    charts.churn = new Chart(document.getElementById('churnDonut'), {
        type: 'doughnut',
        data: {
            labels: churnLabels,
            datasets: [{ data: churnValues, backgroundColor: churnColors, borderColor: '#1c2129', borderWidth: 3 }]
        },
        options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom' } } }
    });

    // Segment bar
    const barLabels = ['Avg Spend', 'Satisfaction', 'Avg Orders', 'Order Ahead %'];
    if (charts.segBar) charts.segBar.destroy();
    charts.segBar = new Chart(document.getElementById('segmentBar'), {
        type: 'bar',
        data: {
            labels: barLabels,
            datasets: data.segments.map((s, i) => ({
                label: s.name, data: [s.avg_spend, s.avg_satisfaction, s.avg_orders, s.order_ahead_rate],
                backgroundColor: SEG_BG[i], borderColor: SEG_COLORS[i], borderWidth: 1.5,
            }))
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } },
            scales: { y: { beginAtZero: true, grid: { color: COLORS.grid } }, x: { grid: { display: false } } }
        }
    });

    // At-risk table
    document.getElementById('atRiskTable').innerHTML = `
        <table class="compare-table">
            <thead><tr><th>Customer</th><th>Churn Score</th><th>Risk</th><th>Orders</th><th>Spend</th><th>Revenue</th><th>Recency</th><th>Satisfaction</th></tr></thead>
            <tbody>${churnData.top_at_risk.map(c => `
                <tr>
                    <td style="font-weight:600">${c.customer_id}</td>
                    <td style="color:${c.churn_score > 66 ? COLORS.red : COLORS.orange};font-weight:600">${c.churn_score}</td>
                    <td>${c.churn_risk}</td>
                    <td>${c.total_orders}</td>
                    <td>$${c.avg_total_spend.toFixed(2)}</td>
                    <td>$${c.total_revenue.toFixed(2)}</td>
                    <td>${c.recency_days}d</td>
                    <td>${c.avg_customer_satisfaction.toFixed(1)}</td>
                </tr>`).join('')}</tbody>
        </table>`;

    // Populate simulator segment dropdown
    const sel = document.getElementById('simSegment');
    sel.innerHTML = data.segments.map(s => `<option value="${s.name}">${s.name} (${s.size.toLocaleString()})</option>`).join('');
}

// 3. Customer 360 Search

const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
let searchTimeout;

searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    const q = searchInput.value.trim();
    if (q.length < 3) { searchResults.classList.remove('show'); return; }
    searchTimeout = setTimeout(async () => {
        const data = await fetchJSON(`/api/customer_search?q=${encodeURIComponent(q)}`);
        if (!data.results.length) {
            searchResults.innerHTML = '<div style="padding:12px 16px;color:var(--text-muted)">No customers found</div>';
        } else {
            searchResults.innerHTML = data.results.map(r => `
                <div class="search-result-item" data-id="${r.customer_id}">
                    <div><div class="search-result-id">${r.customer_id}</div><div class="search-result-meta">${r.segment}</div></div>
                    <div class="search-result-meta">${r.total_orders} orders | $${r.avg_spend} | Risk: ${r.churn_risk}</div>
                </div>`).join('');
            searchResults.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', () => { loadCustomer(item.dataset.id); searchResults.classList.remove('show'); searchInput.value = item.dataset.id; });
            });
        }
        searchResults.classList.add('show');
    }, 300);
});

searchInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') { const q = searchInput.value.trim().toUpperCase(); if (q) { loadCustomer(q); searchResults.classList.remove('show'); } }
});
document.addEventListener('click', e => { if (!e.target.closest('.search-box')) searchResults.classList.remove('show'); });

async function loadCustomer(id) {
    const profile = document.getElementById('customerProfile');
    const empty = document.getElementById('lookupEmpty');
    try {
        const [data, timeline] = await Promise.all([
            fetchJSON(`/api/customer/${id}`),
            fetchJSON(`/api/customer/${id}/timeline`),
        ]);
        const c = data.customer;
        const h = data.order_history;

        document.getElementById('profileId').textContent = c.customer_id;
        document.getElementById('profileBadge').textContent = c.segment_name;
        const churnBdg = document.getElementById('profileChurn');
        churnBdg.textContent = `Churn: ${c.churn_risk}`;
        churnBdg.className = `churn-badge ${c.churn_risk}`;
        document.getElementById('profileDates').textContent =
            `${h.first_order} to ${h.last_order} | ${c.customer_age_group || '--'} | ${c.customer_gender || '--'} | ${c.region || '--'}`;

        const stats = [
            ['Total Orders', h.total_orders], ['Avg Spend', `$${c.avg_total_spend.toFixed(2)}`],
            ['Total Revenue', `$${c.total_revenue.toFixed(2)}`], ['Cart Size', c.avg_cart_size.toFixed(1)],
            ['Customizations', c.avg_num_customizations.toFixed(1)], ['Satisfaction', `${c.avg_customer_satisfaction.toFixed(1)}/5`],
            ['Fulfillment', `${c.avg_fulfillment_time.toFixed(1)} min`], ['Order Ahead', `${(c.order_ahead_rate * 100).toFixed(0)}%`],
            ['Food Orders', `${(c.food_order_rate * 100).toFixed(0)}%`], ['Rewards', c.is_rewards_member ? 'Yes' : 'No'],
            ['Fav Drink', c.favorite_drink_category || '--'], ['Churn Score', c.churn_score],
        ];
        document.getElementById('profileStats').innerHTML = stats.map(([l, v]) =>
            `<div class="profile-stat"><div class="profile-stat-label">${l}</div><div class="profile-stat-value">${v}</div></div>`).join('');

        // Action recs
        document.getElementById('recGrid').innerHTML = data.recommendations.map(r =>
            `<div class="rec-card ${r.priority}"><div class="rec-type ${r.type}">${r.type.replace('_', ' ')}</div><div class="rec-title">${r.title}</div><div class="rec-desc">${r.desc}</div></div>`).join('');

        // Timeline charts
        if (timeline.monthly.labels.length > 0) {
            if (charts.tlSpend) charts.tlSpend.destroy();
            charts.tlSpend = new Chart(document.getElementById('timelineSpend'), {
                type: 'line',
                data: { labels: timeline.monthly.labels, datasets: [{ label: 'Avg Spend', data: timeline.monthly.avg_spend, borderColor: COLORS.green, backgroundColor: COLORS.greenBg, fill: true, tension: 0.3 }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: COLORS.grid } }, x: { grid: { display: false } } } }
            });
            if (charts.tlOrders) charts.tlOrders.destroy();
            charts.tlOrders = new Chart(document.getElementById('timelineOrders'), {
                type: 'bar',
                data: { labels: timeline.monthly.labels, datasets: [{ label: 'Orders', data: timeline.monthly.orders, backgroundColor: COLORS.blueBg, borderColor: COLORS.blue, borderWidth: 1.5, borderRadius: 4 }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: COLORS.grid } }, x: { grid: { display: false } } } }
            });
        }

        // Spend trend badge
        const tb = document.getElementById('spendTrend');
        tb.textContent = `Spending trend: ${timeline.spend_trend}`;
        tb.className = `trend-badge ${timeline.spend_trend}`;

        // Peer radar
        const peer = timeline.peer_comparison;
        // Normalize to 0-100
        const maxVals = peer.labels.map((_, i) => Math.max(peer.customer[i], peer.segment_avg[i]) || 1);
        if (charts.peerRadar) charts.peerRadar.destroy();
        charts.peerRadar = new Chart(document.getElementById('peerRadar'), {
            type: 'radar',
            data: {
                labels: peer.labels,
                datasets: [
                    { label: 'This Customer', data: peer.customer.map((v, i) => (v / maxVals[i] * 100).toFixed(1)), borderColor: COLORS.green, backgroundColor: COLORS.greenBg, borderWidth: 2, pointRadius: 4, pointBackgroundColor: COLORS.green },
                    { label: 'Segment Avg', data: peer.segment_avg.map((v, i) => (v / maxVals[i] * 100).toFixed(1)), borderColor: COLORS.blue, backgroundColor: COLORS.blueBg, borderWidth: 2, pointRadius: 4, pointBackgroundColor: COLORS.blue },
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { r: { beginAtZero: true, max: 100, grid: { color: COLORS.grid }, pointLabels: { font: { size: 11 } }, ticks: { display: false } } },
                plugins: { legend: { position: 'bottom' } },
            }
        });

        profile.classList.add('show');
        empty.style.display = 'none';
    } catch (err) {
        profile.classList.remove('show');
        empty.style.display = 'block';
        empty.textContent = `Customer "${id}" not found.`;
    }
}

// 4. Drink Recommendations

const drinkSearch = document.getElementById('drinkSearchInput');
drinkSearch.addEventListener('keydown', async e => {
    if (e.key !== 'Enter') return;
    const id = drinkSearch.value.trim().toUpperCase();
    if (!id) return;
    try {
        const data = await fetchJSON(`/api/recommendations/drinks/${id}`);
        document.getElementById('drinkRecTitle').textContent = `Recommendations for ${data.customer_id} (${data.segment})`;
        document.getElementById('drinksTried').innerHTML =
            data.drinks_tried.map(d => `<span class="pill">${d}</span>`).join('');
        document.getElementById('drinkRecGrid').innerHTML = data.recommendations.map(r => `
            <div class="drink-rec-card">
                <div class="drink-name">${r.drink}</div>
                <div class="drink-score">Score: ${r.score.toFixed(1)}</div>
                <div class="drink-reason">${r.reason}</div>
                <div class="drink-method">${r.method.replace('_', ' ')}</div>
            </div>`).join('');
        document.getElementById('drinkRecResults').style.display = 'block';
        document.getElementById('drinkRecEmpty').style.display = 'none';
    } catch {
        document.getElementById('drinkRecResults').style.display = 'none';
        document.getElementById('drinkRecEmpty').style.display = 'block';
        document.getElementById('drinkRecEmpty').textContent = `Customer "${id}" not found.`;
    }
});

// 5. Campaign Simulator

let simIntensity = 1.0;
document.querySelectorAll('.int-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.int-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        simIntensity = parseFloat(btn.dataset.val);
    });
});

document.getElementById('simRunBtn').addEventListener('click', async () => {
    const segment = document.getElementById('simSegment').value;
    const campaign_type = document.getElementById('simCampaign').value;

    const data = await fetchJSON('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segment, campaign_type, intensity: simIntensity }),
    });

    const resultsDiv = document.getElementById('simResults');
    resultsDiv.style.display = 'block';

    const skip = ['segment', 'campaign_type', 'segment_size', 'intensity', 'recommendation', 'roi_estimate'];
    const metrics = Object.entries(data).filter(([k]) => !skip.includes(k));

    const formatVal = (k, v) => {
        if (typeof v === 'number') {
            if (k.includes('revenue') || k.includes('spend') || k.includes('cost')) return `$${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
            if (k.includes('pct') || k.includes('rate') || k.includes('lift') || k.includes('roi')) return `${v}%`;
            return v.toLocaleString();
        }
        return v;
    };

    const isPositive = (k, v) => {
        if (typeof v !== 'number') return '';
        if (k.includes('change') || k.includes('lift') || k.includes('roi')) return v >= 0 ? 'positive' : 'negative';
        return '';
    };

    document.getElementById('simResultsContent').innerHTML = `
        <div style="margin-bottom:12px;font-size:13px;color:var(--text-muted)">
            Segment: <strong>${data.segment}</strong> | Campaign: <strong>${data.campaign_type}</strong> |
            Intensity: <strong>${data.intensity}x</strong> | Size: <strong>${data.segment_size.toLocaleString()}</strong>
        </div>
        ${metrics.map(([k, v]) => `
            <div class="sim-metric">
                <span class="sim-metric-label">${k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</span>
                <span class="sim-metric-value ${isPositive(k, v)}">${formatVal(k, v)}</span>
            </div>`).join('')}
        ${data.roi_estimate ? `<div class="sim-metric"><span class="sim-metric-label">ROI Estimate</span><span class="sim-metric-value" style="color:var(--accent-light)">${data.roi_estimate}</span></div>` : ''}
        ${data.recommendation ? `<div class="sim-rec">${data.recommendation}</div>` : ''}
    `;
});

// 6. Segment Explorer

async function loadExplorer() {
    // Load available features first
    const initial = await fetchJSON('/api/explorer?feature_x=avg_total_spend&feature_y=total_orders&limit=2000');
    const feats = initial.available_features;
    const selX = document.getElementById('explorerX');
    const selY = document.getElementById('explorerY');
    selX.innerHTML = feats.map(f => `<option value="${f}" ${f === 'avg_total_spend' ? 'selected' : ''}>${f}</option>`).join('');
    selY.innerHTML = feats.map(f => `<option value="${f}" ${f === 'total_orders' ? 'selected' : ''}>${f}</option>`).join('');

    renderScatter(initial);

    document.getElementById('explorerBtn').addEventListener('click', async () => {
        const data = await fetchJSON(`/api/explorer?feature_x=${selX.value}&feature_y=${selY.value}&limit=2000`);
        renderScatter(data);
    });

    // Radar + compare bar
    const cmpData = await fetchJSON('/api/compare');
    const radarLabels = ['Spend', 'Orders', 'Cart', 'Custom.', 'Satisfaction', 'Food %', 'Ahead %', 'Fulfill.'];
    const radarKeys = ['avg_total_spend', 'total_orders', 'avg_cart_size', 'avg_num_customizations',
        'avg_customer_satisfaction', 'food_order_rate', 'order_ahead_rate', 'avg_fulfillment_time'];
    const allVals = {};
    radarKeys.forEach(k => {
        const idx = cmpData.metric_keys.indexOf(k);
        const vals = Object.values(cmpData.segments).map(s => s.values[idx]);
        allVals[k] = { min: Math.min(...vals), max: Math.max(...vals) };
    });
    if (charts.radar) charts.radar.destroy();
    charts.radar = new Chart(document.getElementById('radarChart'), {
        type: 'radar',
        data: {
            labels: radarLabels,
            datasets: Object.entries(cmpData.segments).map(([name, s], i) => ({
                label: name,
                data: radarKeys.map(k => { const idx = cmpData.metric_keys.indexOf(k); const v = s.values[idx]; const range = allVals[k].max - allVals[k].min; return range > 0 ? ((v - allVals[k].min) / range * 100).toFixed(1) : 50; }),
                backgroundColor: SEG_BG[i], borderColor: SEG_COLORS[i], borderWidth: 2, pointRadius: 4, pointBackgroundColor: SEG_COLORS[i],
            }))
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { r: { beginAtZero: true, max: 100, grid: { color: COLORS.grid }, pointLabels: { font: { size: 11 } }, ticks: { display: false } } }, plugins: { legend: { position: 'bottom' } } }
    });

    if (charts.compareBar) charts.compareBar.destroy();
    charts.compareBar = new Chart(document.getElementById('compareBar'), {
        type: 'bar',
        data: { labels: cmpData.labels, datasets: Object.entries(cmpData.segments).map(([name, s], i) => ({ label: name, data: s.values, backgroundColor: SEG_BG[i], borderColor: SEG_COLORS[i], borderWidth: 1.5 })) },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { position: 'bottom' } }, scales: { x: { beginAtZero: true, grid: { color: COLORS.grid } }, y: { grid: { display: false } } } }
    });

    // Segment cards
    if (segmentData) {
        document.getElementById('segmentCards').innerHTML = segmentData.segments.map((s, i) => {
            const topDrinks = Object.keys(s.top_drinks || {}).slice(0, 3).join(', ');
            return `<div class="segment-card">
                <div class="segment-name" style="color:${SEG_COLORS[i]}">${s.name}</div>
                <div class="segment-size">${s.size.toLocaleString()} customers (${s.pct}%)</div>
                <div class="segment-metrics">
                    <div class="seg-metric"><span class="seg-metric-label">Avg Spend</span><span class="seg-metric-value">$${s.avg_spend}</span></div>
                    <div class="seg-metric"><span class="seg-metric-label">Avg Orders</span><span class="seg-metric-value">${s.avg_orders}</span></div>
                    <div class="seg-metric"><span class="seg-metric-label">Satisfaction</span><span class="seg-metric-value">${s.avg_satisfaction}/5</span></div>
                    <div class="seg-metric"><span class="seg-metric-label">Cart Size</span><span class="seg-metric-value">${s.avg_cart_size}</span></div>
                    <div class="seg-metric"><span class="seg-metric-label">Order Ahead</span><span class="seg-metric-value">${s.order_ahead_rate}%</span></div>
                    <div class="seg-metric"><span class="seg-metric-label">Rewards</span><span class="seg-metric-value">${s.rewards_rate}%</span></div>
                    <div class="seg-metric"><span class="seg-metric-label">Food Rate</span><span class="seg-metric-value">${s.food_order_rate}%</span></div>
                    <div class="seg-metric"><span class="seg-metric-label">Recency</span><span class="seg-metric-value">${s.avg_recency}d</span></div>
                </div>
                <div style="margin-top:10px;font-size:12px;color:var(--text-muted)">Top drinks: ${topDrinks || '--'}</div>
            </div>`;
        }).join('');
    }
}

function renderScatter(data) {
    // Group by segment
    const grouped = {};
    data.points.forEach(p => {
        if (!grouped[p.segment]) grouped[p.segment] = [];
        grouped[p.segment].push({ x: p.x, y: p.y });
    });

    if (charts.scatter) charts.scatter.destroy();
    charts.scatter = new Chart(document.getElementById('explorerScatter'), {
        type: 'scatter',
        data: {
            datasets: Object.entries(grouped).map(([name, pts], i) => ({
                label: name, data: pts,
                backgroundColor: SEG_BG[i % SEG_BG.length],
                borderColor: SEG_COLORS[i % SEG_COLORS.length],
                borderWidth: 1, pointRadius: 3, pointHoverRadius: 5,
            }))
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } },
            scales: {
                x: { title: { display: true, text: data.feature_x }, grid: { color: COLORS.grid } },
                y: { title: { display: true, text: data.feature_y }, grid: { color: COLORS.grid } },
            }
        }
    });
}

// 7. Trends

async function loadTrends() {
    const data = await fetchJSON('/api/trends');

    if (charts.day) charts.day.destroy();
    charts.day = new Chart(document.getElementById('dayChart'), {
        type: 'bar',
        data: { labels: data.by_day.labels, datasets: [{ label: 'Orders', data: data.by_day.values, backgroundColor: COLORS.greenBg, borderColor: COLORS.green, borderWidth: 1.5, borderRadius: 6 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: COLORS.grid } }, x: { grid: { display: false } } } }
    });

    if (charts.hour) charts.hour.destroy();
    charts.hour = new Chart(document.getElementById('hourChart'), {
        type: 'line',
        data: { labels: data.by_hour.labels, datasets: [{ label: 'Orders', data: data.by_hour.values, borderColor: COLORS.blue, backgroundColor: COLORS.blueBg, fill: true, tension: 0.3, pointRadius: 3, pointBackgroundColor: COLORS.blue }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: COLORS.grid } }, x: { grid: { display: false } } } }
    });

    if (charts.channel) charts.channel.destroy();
    charts.channel = new Chart(document.getElementById('channelChart'), {
        type: 'doughnut',
        data: { labels: data.by_channel.labels, datasets: [{ data: data.by_channel.values, backgroundColor: [COLORS.green, COLORS.blue, COLORS.orange, COLORS.purple, COLORS.cyan], borderColor: '#1c2129', borderWidth: 3 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '55%', plugins: { legend: { position: 'right' } } }
    });

    if (charts.drink) charts.drink.destroy();
    charts.drink = new Chart(document.getElementById('drinkChart'), {
        type: 'bar',
        data: { labels: data.by_drink.labels, datasets: [{ label: 'Orders', data: data.by_drink.values, backgroundColor: [COLORS.greenBg, COLORS.blueBg, COLORS.orangeBg, COLORS.purpleBg, COLORS.redBg, COLORS.cyanBg], borderColor: [COLORS.green, COLORS.blue, COLORS.orange, COLORS.purple, COLORS.red, COLORS.cyan], borderWidth: 1.5, borderRadius: 6 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, grid: { color: COLORS.grid } }, y: { grid: { display: false } } } }
    });

    if (charts.monthly) charts.monthly.destroy();
    charts.monthly = new Chart(document.getElementById('monthlyChart'), {
        type: 'line',
        data: {
            labels: data.monthly.labels,
            datasets: [
                { label: 'Orders', data: data.monthly.orders, borderColor: COLORS.green, backgroundColor: COLORS.greenBg, fill: true, tension: 0.3, yAxisID: 'y' },
                { label: 'Avg Spend ($)', data: data.monthly.avg_spend, borderColor: COLORS.orange, backgroundColor: 'transparent', borderDash: [5, 5], tension: 0.3, yAxisID: 'y1' }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false, interaction: { intersect: false, mode: 'index' },
            plugins: { legend: { position: 'bottom' } },
            scales: {
                y: { beginAtZero: true, grid: { color: COLORS.grid }, title: { display: true, text: 'Orders' } },
                y1: { position: 'right', beginAtZero: true, grid: { display: false }, title: { display: true, text: 'Avg Spend ($)' } },
                x: { grid: { display: false } },
            }
        }
    });
}

// Init

async function init() {
    try {
        await loadExecutive();
        await loadOverview();
        await loadExplorer();
        await loadTrends();
    } catch (err) {
        console.error('Init error:', err);
    }
}

init();
