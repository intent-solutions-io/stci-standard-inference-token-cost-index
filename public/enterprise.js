/**
 * Enterprise Usage Dashboard
 *
 * Handles provider connections, usage tracking, and benchmarking.
 */

// State
const enterpriseState = {
  enterpriseId: null,
  providers: {},
  usage: null,
  benchmark: null,
  usageChart: null,
};

// DOM Elements
const connectSection = document.getElementById('connect-section');
const dashboardSection = document.getElementById('dashboard-section');
const enterpriseIdSection = document.getElementById('enterprise-id-section');

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  // Check for stored enterprise ID
  enterpriseState.enterpriseId = localStorage.getItem('enterpriseId');

  if (enterpriseState.enterpriseId) {
    loadDashboard();
  }

  // Set up event listeners
  setupEventListeners();

  // Mobile nav toggle
  const navToggle = document.querySelector('.nav-toggle');
  const navMobile = document.getElementById('nav-mobile');
  if (navToggle && navMobile) {
    navToggle.addEventListener('click', () => {
      navMobile.classList.toggle('open');
    });
  }
});

function setupEventListeners() {
  // OpenAI connect
  document.getElementById('openai-connect-btn')?.addEventListener('click', () => {
    connectProvider('openai');
  });

  // Anthropic connect
  document.getElementById('anthropic-connect-btn')?.addEventListener('click', () => {
    connectProvider('anthropic');
  });

  // Sync buttons
  document.getElementById('openai-sync-btn')?.addEventListener('click', () => {
    syncProvider('openai');
  });
  document.getElementById('anthropic-sync-btn')?.addEventListener('click', () => {
    syncProvider('anthropic');
  });
  document.getElementById('sync-all-btn')?.addEventListener('click', syncAll);

  // Export
  document.getElementById('export-btn')?.addEventListener('click', exportReport);

  // Share benchmarks toggle
  document.getElementById('share-benchmarks')?.addEventListener('change', toggleBenchmarkSharing);
}

// ============================================
// Provider Connection
// ============================================

async function connectProvider(provider) {
  const keyInput = document.getElementById(`${provider}-key`);
  const connectBtn = document.getElementById(`${provider}-connect-btn`);
  const apiKey = keyInput?.value?.trim();

  if (!apiKey) {
    showError(`Please enter your ${provider} Admin API key`);
    return;
  }

  // Validate key format
  if (provider === 'openai' && !apiKey.startsWith('sk-admin-')) {
    showError('OpenAI Admin key should start with sk-admin-');
    return;
  }
  if (provider === 'anthropic' && !apiKey.startsWith('sk-ant-admin-')) {
    showError('Anthropic Admin key should start with sk-ant-admin-');
    return;
  }

  // Show loading state
  const originalText = connectBtn.textContent;
  connectBtn.textContent = 'Connecting...';
  connectBtn.disabled = true;

  try {
    const response = await fetch(`/api/v1/enterprise/connect/${provider}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ admin_api_key: apiKey }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Connection failed');
    }

    // Store enterprise ID
    enterpriseState.enterpriseId = data.enterprise_id;
    localStorage.setItem('enterpriseId', data.enterprise_id);

    // Update UI
    showProviderConnected(provider);
    updateEnterpriseIdDisplay();

    // Clear the input
    keyInput.value = '';

    // Load dashboard if this is first connection
    loadDashboard();

  } catch (error) {
    showError(error.message);
  } finally {
    connectBtn.textContent = originalText;
    connectBtn.disabled = false;
  }
}

function showProviderConnected(provider) {
  const form = document.getElementById(`${provider}-form`);
  const connected = document.getElementById(`${provider}-connected`);
  const status = document.getElementById(`${provider}-status`);

  if (form) form.style.display = 'none';
  if (connected) connected.style.display = 'flex';
  if (status) {
    status.textContent = 'Connected';
    status.classList.add('connected');
  }

  enterpriseState.providers[provider] = { connected: true };
}

function updateEnterpriseIdDisplay() {
  if (enterpriseState.enterpriseId) {
    enterpriseIdSection.style.display = 'block';
    document.getElementById('enterprise-id-display').textContent = enterpriseState.enterpriseId;
  }
}

// ============================================
// Dashboard Loading
// ============================================

async function loadDashboard() {
  if (!enterpriseState.enterpriseId) return;

  try {
    // Load providers
    await loadProviders();

    // Load usage data
    await loadUsage();

    // Load benchmarks
    await loadBenchmarks();

    // Show dashboard
    dashboardSection.style.display = 'block';
    updateEnterpriseIdDisplay();

  } catch (error) {
    console.error('Failed to load dashboard:', error);
  }
}

async function loadProviders() {
  try {
    const response = await fetch('/api/v1/enterprise/providers', {
      headers: {
        'Authorization': `Bearer enterprise_${enterpriseState.enterpriseId}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401 || response.status === 404) {
        // Enterprise not found, clear state
        localStorage.removeItem('enterpriseId');
        enterpriseState.enterpriseId = null;
        return;
      }
      throw new Error('Failed to load providers');
    }

    const data = await response.json();

    for (const provider of data.providers) {
      showProviderConnected(provider.provider);
    }

  } catch (error) {
    console.error('Failed to load providers:', error);
  }
}

async function loadUsage() {
  try {
    // Get current month date range
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), 1);
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);

    const startStr = start.toISOString().split('T')[0];
    const endStr = end.toISOString().split('T')[0];

    const response = await fetch(
      `/api/v1/enterprise/usage?start=${startStr}&end=${endStr}`,
      {
        headers: {
          'Authorization': `Bearer enterprise_${enterpriseState.enterpriseId}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to load usage');
    }

    const data = await response.json();
    enterpriseState.usage = data;

    // Update UI
    updateUsageDisplay(data);

  } catch (error) {
    console.error('Failed to load usage:', error);
  }
}

function updateUsageDisplay(data) {
  // Effective rate
  const yourRate = data.effective_rates?.blended;
  document.getElementById('your-rate').textContent = yourRate
    ? `$${yourRate.toFixed(2)}`
    : '--';

  // Market rate
  const marketRate = data.benchmark?.stci_frontier_blended;
  document.getElementById('market-rate').textContent = marketRate
    ? `$${marketRate.toFixed(2)}`
    : '--';

  // Discount
  const discount = data.benchmark?.your_discount;
  const discountBadge = document.getElementById('discount-badge');
  if (discount && discount > 0) {
    discountBadge.textContent = `${(discount * 100).toFixed(0)}% below market`;
    discountBadge.classList.add('positive');
  } else if (discount && discount < 0) {
    discountBadge.textContent = `${Math.abs(discount * 100).toFixed(0)}% above market`;
    discountBadge.classList.add('negative');
  } else {
    discountBadge.textContent = 'No comparison available';
  }

  // Stats
  document.getElementById('month-spend').textContent = data.totals?.total_cost_usd
    ? `$${data.totals.total_cost_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : '$0.00';

  document.getElementById('input-tokens').textContent = data.totals?.input_tokens
    ? formatTokens(data.totals.input_tokens)
    : '0';

  document.getElementById('output-tokens').textContent = data.totals?.output_tokens
    ? formatTokens(data.totals.output_tokens)
    : '0';

  document.getElementById('request-count').textContent = data.totals?.request_count
    ? data.totals.request_count.toLocaleString()
    : '0';

  // Chart
  if (data.by_day && data.by_day.length > 0) {
    renderUsageChart(data.by_day);
  }
}

function formatTokens(tokens) {
  if (tokens >= 1_000_000_000) {
    return (tokens / 1_000_000_000).toFixed(1) + 'B';
  } else if (tokens >= 1_000_000) {
    return (tokens / 1_000_000).toFixed(1) + 'M';
  } else if (tokens >= 1_000) {
    return (tokens / 1_000).toFixed(1) + 'K';
  }
  return tokens.toString();
}

function renderUsageChart(byDay) {
  const ctx = document.getElementById('usage-chart')?.getContext('2d');
  if (!ctx) return;

  // Destroy existing chart
  if (enterpriseState.usageChart) {
    enterpriseState.usageChart.destroy();
  }

  const labels = byDay.map(d => d.date);
  const inputData = byDay.map(d => d.input_tokens / 1_000_000);
  const outputData = byDay.map(d => d.output_tokens / 1_000_000);
  const costData = byDay.map(d => d.cost_usd);

  enterpriseState.usageChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Input Tokens (M)',
          data: inputData,
          backgroundColor: 'rgba(16, 185, 129, 0.7)',
          yAxisID: 'y',
        },
        {
          label: 'Output Tokens (M)',
          data: outputData,
          backgroundColor: 'rgba(59, 130, 246, 0.7)',
          yAxisID: 'y',
        },
        {
          label: 'Cost ($)',
          data: costData,
          type: 'line',
          borderColor: 'rgba(139, 92, 246, 1)',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          yAxisID: 'y1',
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.1)' },
          ticks: { color: '#a0a0a0' },
        },
        y: {
          type: 'linear',
          position: 'left',
          grid: { color: 'rgba(255,255,255,0.1)' },
          ticks: { color: '#a0a0a0' },
          title: {
            display: true,
            text: 'Tokens (M)',
            color: '#a0a0a0',
          },
        },
        y1: {
          type: 'linear',
          position: 'right',
          grid: { drawOnChartArea: false },
          ticks: { color: '#a0a0a0' },
          title: {
            display: true,
            text: 'Cost ($)',
            color: '#a0a0a0',
          },
        },
      },
      plugins: {
        legend: {
          labels: { color: '#a0a0a0' },
        },
      },
    },
  });
}

// ============================================
// Benchmarks
// ============================================

async function loadBenchmarks() {
  try {
    const response = await fetch('/api/v1/benchmarks/current', {
      headers: {
        'Authorization': `Bearer enterprise_${enterpriseState.enterpriseId}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to load benchmarks');
    }

    const data = await response.json();
    enterpriseState.benchmark = data;

    updateBenchmarkDisplay(data);

  } catch (error) {
    console.error('Failed to load benchmarks:', error);
  }
}

function updateBenchmarkDisplay(data) {
  const resultEl = document.getElementById('benchmark-result');
  const markerEl = document.getElementById('your-marker');

  if (data.your_position) {
    const percentile = data.your_position.percentile;
    resultEl.innerHTML = `Your rate is better than <strong>${percentile}%</strong> of enterprises`;

    // Position marker (0% = left/best, 100% = right/worst)
    // percentile 90 means better than 90%, so marker at 10%
    const markerPosition = 100 - percentile;
    markerEl.style.left = `${markerPosition}%`;
    markerEl.style.display = 'block';
  } else {
    resultEl.innerHTML = 'Connect a provider and sync data to see your benchmark position.';
    markerEl.style.display = 'none';
  }
}

function toggleBenchmarkSharing() {
  // TODO: Implement opt-in for anonymous benchmarks
  const checkbox = document.getElementById('share-benchmarks');
  console.log('Benchmark sharing:', checkbox.checked);
}

// ============================================
// Sync
// ============================================

async function syncProvider(provider) {
  const syncBtn = document.getElementById(`${provider}-sync-btn`);
  if (!syncBtn) return;

  const originalText = syncBtn.textContent;
  syncBtn.textContent = 'Syncing...';
  syncBtn.disabled = true;

  try {
    const response = await fetch('/api/v1/enterprise/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer enterprise_${enterpriseState.enterpriseId}`,
      },
      body: JSON.stringify({}),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Sync failed');
    }

    showSuccess(`Synced! Processed ${formatTokens(data.totals.input_tokens + data.totals.output_tokens)} tokens.`);

    // Reload usage data
    await loadUsage();

  } catch (error) {
    showError(error.message);
  } finally {
    syncBtn.textContent = originalText;
    syncBtn.disabled = false;
  }
}

async function syncAll() {
  const syncBtn = document.getElementById('sync-all-btn');
  if (!syncBtn) return;

  const originalText = syncBtn.textContent;
  syncBtn.textContent = 'Syncing...';
  syncBtn.disabled = true;

  try {
    const response = await fetch('/api/v1/enterprise/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer enterprise_${enterpriseState.enterpriseId}`,
      },
      body: JSON.stringify({}),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Sync failed');
    }

    showSuccess('All providers synced successfully!');

    // Reload dashboard
    await loadUsage();
    await loadBenchmarks();

  } catch (error) {
    showError(error.message);
  } finally {
    syncBtn.textContent = originalText;
    syncBtn.disabled = false;
  }
}

// ============================================
// Export
// ============================================

function exportReport() {
  if (!enterpriseState.usage) {
    showError('No usage data to export');
    return;
  }

  const data = enterpriseState.usage;
  const report = {
    generated_at: new Date().toISOString(),
    enterprise_id: enterpriseState.enterpriseId,
    period: data.period,
    totals: data.totals,
    effective_rates: data.effective_rates,
    benchmark: data.benchmark,
    daily_breakdown: data.by_day,
  };

  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `usage-report-${data.period.start}-${data.period.end}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// ============================================
// UI Helpers
// ============================================

function showError(message) {
  // Simple alert for now, could be replaced with a toast
  alert(`Error: ${message}`);
}

function showSuccess(message) {
  // Simple alert for now, could be replaced with a toast
  alert(message);
}
