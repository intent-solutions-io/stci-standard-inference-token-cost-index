/**
 * Intelligence Page - Data-driven LLM Pricing Analysis
 * All statistics computed from events data - NO HARDCODED VALUES
 */

(function() {
  'use strict';

  // ============================================
  // Configuration
  // ============================================
  const CONFIG = {
    dataUrl: '/data/pricing-events.v1.json',
    jsonldUrl: '/data/pricing-events.jsonld.json',
    apiUrl: '/v1/index/latest',
    cacheKey: 'ipi-events-cache',
    apiCacheKey: 'ipi-api-cache',
    cacheTTL: 60 * 60 * 1000, // 1 hour
    eventsPerPage: 10,
    debounceMs: 300,
    chartColors: {
      'gpt-4': '#10b981',
      'gpt-4o': '#34d399',
      'gpt-3.5': '#6ee7b7',
      'o1': '#059669',
      'claude-3': '#8b5cf6',
      'claude-3.5': '#a78bfa',
      'claude-4': '#7c3aed',
      'gemini-1.5': '#f59e0b',
      'gemini-2': '#fbbf24',
      'deepseek-v3': '#ef4444',
      'deepseek-r1': '#f87171',
      'other': '#6b7280'
    }
  };

  // ============================================
  // State
  // ============================================
  let state = {
    events: [],
    filteredEvents: [],
    displayedCount: 0,
    filters: {
      provider: '',
      type: '',
      severity: '',
      search: ''
    },
    chart: null,
    fuse: null
  };

  // ============================================
  // Utility Functions
  // ============================================
  function $(selector) {
    return document.querySelector(selector);
  }

  function $$(selector) {
    return document.querySelectorAll(selector);
  }

  function debounce(fn, ms) {
    let timeout;
    return function(...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), ms);
    };
  }

  function formatCurrency(value, decimals = 2) {
    if (value === null || value === undefined) return '--';
    return '$' + value.toFixed(decimals);
  }

  function formatPercent(value) {
    if (value === null || value === undefined) return '--';
    const sign = value > 0 ? '+' : '';
    return sign + (value * 100).toFixed(0) + '%';
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  }

  function monthsBetween(date1, date2) {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    return Math.round((d2 - d1) / (30 * 24 * 60 * 60 * 1000));
  }

  // ============================================
  // Data Loading
  // ============================================
  async function loadData() {
    // Try cache first
    const cached = localStorage.getItem(CONFIG.cacheKey);
    if (cached) {
      try {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CONFIG.cacheTTL) {
          return data;
        }
      } catch (e) {
        localStorage.removeItem(CONFIG.cacheKey);
      }
    }

    // Fetch fresh data
    try {
      const response = await fetch(CONFIG.dataUrl);
      if (!response.ok) throw new Error('Failed to fetch events data');
      const data = await response.json();

      // Cache it
      localStorage.setItem(CONFIG.cacheKey, JSON.stringify({
        data,
        timestamp: Date.now()
      }));

      return data;
    } catch (error) {
      console.error('Error loading events:', error);

      // Return cached data if available (even if stale)
      if (cached) {
        const { data } = JSON.parse(cached);
        showStaleBanner();
        return data;
      }

      throw error;
    }
  }

  async function loadApiData() {
    const cached = localStorage.getItem(CONFIG.apiCacheKey);
    if (cached) {
      try {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CONFIG.cacheTTL) {
          return { data, fresh: true, age: Date.now() - timestamp };
        }
      } catch (e) {
        localStorage.removeItem(CONFIG.apiCacheKey);
      }
    }

    try {
      const response = await fetch(CONFIG.apiUrl);
      if (!response.ok) throw new Error('API request failed');
      const data = await response.json();

      localStorage.setItem(CONFIG.apiCacheKey, JSON.stringify({
        data,
        timestamp: Date.now()
      }));

      return { data, fresh: true, age: 0 };
    } catch (error) {
      console.error('Error loading API data:', error);

      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        return { data, fresh: false, age: Date.now() - timestamp };
      }

      return null;
    }
  }

  async function loadJsonLd() {
    try {
      const response = await fetch(CONFIG.jsonldUrl);
      if (!response.ok) return null;
      return await response.json();
    } catch (e) {
      return null;
    }
  }

  function showStaleBanner() {
    const banner = $('#stale-banner');
    if (banner) banner.hidden = false;
  }

  // ============================================
  // Stats Computation (NO HARDCODED VALUES)
  // ============================================
  function computeStats(events) {
    if (!events || events.length === 0) {
      return {
        totalEvents: 0,
        priceDrops: 0,
        priceIncreases: 0,
        newModels: 0,
        structuralChanges: 0,
        providers: 0,
        models: 0,
        timeSpanMonths: 0,
        avgDeflation: 0
      };
    }

    const dates = events.map(e => e.date).sort();
    const minDate = dates[0];
    const maxDate = dates[dates.length - 1];

    // Calculate average deflation from price drops
    const priceDropEvents = events.filter(e => e.type === 'price_drop' && e.change);
    let avgDeflation = 0;
    if (priceDropEvents.length > 0) {
      const totalDeflation = priceDropEvents.reduce((sum, e) => {
        const inputDrop = Math.abs(e.change.input || 0);
        const outputDrop = Math.abs(e.change.output || 0);
        return sum + Math.max(inputDrop, outputDrop);
      }, 0);
      avgDeflation = totalDeflation / priceDropEvents.length;
    }

    return {
      totalEvents: events.length,
      priceDrops: events.filter(e => e.type === 'price_drop').length,
      priceIncreases: events.filter(e => e.type === 'price_increase').length,
      newModels: events.filter(e => e.type === 'new_model').length,
      structuralChanges: events.filter(e => e.type === 'structural').length,
      providers: [...new Set(events.map(e => e.provider))].length,
      models: [...new Set(events.map(e => e.model).filter(Boolean))].length,
      timeSpanMonths: monthsBetween(minDate, maxDate),
      avgDeflation
    };
  }

  function renderStats(stats) {
    // Hero stats
    $('#stat-events').textContent = stats.totalEvents;
    $('#stat-timespan').textContent = stats.timeSpanMonths;
    $('#stat-deflation').textContent = formatPercent(-stats.avgDeflation);

    // Summary cards
    $('#stat-total-events').textContent = stats.totalEvents;
    $('#stat-price-drops').textContent = stats.priceDrops;
    $('#stat-new-models').textContent = stats.newModels;
    $('#stat-providers').textContent = stats.providers;
  }

  // ============================================
  // Chart Rendering
  // ============================================
  function initChart(events) {
    const canvas = $('#price-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    // Group events by model family
    const datasets = {};
    events.forEach(event => {
      if (!event.newPrice) return;

      const family = event.modelFamily || 'other';
      if (!datasets[family]) {
        const color = CONFIG.chartColors[family] || CONFIG.chartColors.other;
        datasets[family] = {
          label: family.toUpperCase().replace(/-/g, ' '),
          data: [],
          borderColor: color,
          backgroundColor: color + '15',
          fill: true,
          tension: 0.3,
          pointRadius: 5,
          pointHoverRadius: 8,
          borderWidth: 2
        };
      }

      datasets[family].data.push({
        x: new Date(event.date),
        y: event.newPrice.input,
        eventId: event.id,
        label: event.headline
      });
    });

    // Sort data points by date
    Object.values(datasets).forEach(ds => {
      ds.data.sort((a, b) => a.x - b.x);
    });

    const ctx = canvas.getContext('2d');
    state.chart = new Chart(ctx, {
      type: 'line',
      data: {
        datasets: Object.values(datasets)
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'nearest',
          intersect: true
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: '#1a1a1a',
            titleColor: '#fff',
            bodyColor: '#a0a0a0',
            borderColor: '#333',
            borderWidth: 1,
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}/MTok`;
              },
              afterLabel: function(context) {
                return context.raw.label;
              }
            }
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'month',
              displayFormats: {
                month: 'MMM yyyy'
              }
            },
            grid: {
              color: '#2a2a2a'
            },
            ticks: {
              color: '#6a6a6a'
            }
          },
          y: {
            type: 'linear',
            title: {
              display: true,
              text: '$/Million Input Tokens',
              color: '#6a6a6a'
            },
            grid: {
              color: '#2a2a2a'
            },
            ticks: {
              color: '#6a6a6a',
              callback: function(value) {
                return '$' + value;
              }
            }
          }
        },
        onClick: function(e, elements) {
          if (elements.length > 0) {
            const element = elements[0];
            const data = state.chart.data.datasets[element.datasetIndex].data[element.index];
            if (data.eventId) {
              scrollToEvent(data.eventId);
            }
          }
        }
      }
    });

    // Render legend
    renderChartLegend(datasets);
  }

  function renderChartLegend(datasets) {
    const container = $('#chart-legend');
    if (!container) return;

    container.innerHTML = Object.entries(datasets).map(([key, ds]) => `
      <span class="chart-legend-item" data-family="${key}">
        <span class="legend-color" style="background: ${ds.borderColor}"></span>
        ${ds.label}
      </span>
    `).join('');
  }

  function setChartScale(scale) {
    if (!state.chart) return;
    state.chart.options.scales.y.type = scale;
    state.chart.update();
  }

  function scrollToEvent(eventId) {
    const eventCard = document.querySelector(`[data-event-id="${eventId}"]`);
    if (eventCard) {
      eventCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
      eventCard.classList.add('highlight');
      setTimeout(() => eventCard.classList.remove('highlight'), 2000);
    }
  }

  // ============================================
  // Timeline Rendering
  // ============================================
  function initTimeline(events) {
    // Populate provider filter
    const providers = [...new Set(events.map(e => e.provider))].sort();
    const providerSelect = $('#filter-provider');
    if (providerSelect) {
      providers.forEach(p => {
        const option = document.createElement('option');
        option.value = p;
        option.textContent = p;
        providerSelect.appendChild(option);
      });
    }

    // Initialize Fuse.js for search
    if (typeof Fuse !== 'undefined') {
      state.fuse = new Fuse(events, {
        keys: ['headline', 'description', 'model', 'provider', 'tags'],
        threshold: 0.3
      });
    }

    // Read filters from URL
    readFiltersFromUrl();

    // Apply initial filters
    applyFilters();
  }

  function applyFilters() {
    let filtered = [...state.events];

    // Provider filter
    if (state.filters.provider) {
      filtered = filtered.filter(e => e.provider === state.filters.provider);
    }

    // Type filter
    if (state.filters.type) {
      filtered = filtered.filter(e => e.type === state.filters.type);
    }

    // Severity filter
    if (state.filters.severity) {
      filtered = filtered.filter(e => e.severity === state.filters.severity);
    }

    // Search filter
    if (state.filters.search && state.fuse) {
      const results = state.fuse.search(state.filters.search);
      const matchIds = new Set(results.map(r => r.item.id));
      filtered = filtered.filter(e => matchIds.has(e.id));
    }

    // Sort by date descending (newest first)
    filtered.sort((a, b) => new Date(b.date) - new Date(a.date));

    state.filteredEvents = filtered;
    state.displayedCount = 0;

    renderTimeline();
    updateResultsCount();
    updateUrlWithFilters();
  }

  function renderTimeline() {
    const container = $('#timeline-container');
    const loadMoreContainer = $('#load-more-container');
    const loading = $('#timeline-loading');

    if (!container) return;

    if (loading) loading.hidden = true;
    container.setAttribute('aria-busy', 'false');

    const eventsToShow = state.filteredEvents.slice(0, state.displayedCount + CONFIG.eventsPerPage);
    state.displayedCount = eventsToShow.length;

    container.innerHTML = eventsToShow.map(renderEventCard).join('');

    // Show/hide load more button
    if (loadMoreContainer) {
      loadMoreContainer.hidden = state.displayedCount >= state.filteredEvents.length;
    }
  }

  function renderEventCard(event) {
    const severityClass = `severity-${event.severity}`;
    const typeLabel = event.type.replace(/_/g, ' ');

    let priceHtml = '';
    if (event.newPrice) {
      priceHtml = `
        <div class="event-price">
          <span class="price-label">Price:</span>
          <span class="price-value">${formatCurrency(event.newPrice.input)} / ${formatCurrency(event.newPrice.output)}</span>
          <span class="price-unit">per MTok (in/out)</span>
        </div>
      `;
    }

    let changeHtml = '';
    if (event.change) {
      const inputChange = formatPercent(event.change.input);
      const outputChange = formatPercent(event.change.output);
      const changeClass = event.change.input < 0 ? 'positive' : 'negative';
      changeHtml = `
        <div class="event-change ${changeClass}">
          ${inputChange} input / ${outputChange} output
        </div>
      `;
    }

    return `
      <article class="intel-event-card ${severityClass}" data-event-id="${event.id}">
        <div class="event-header">
          <time class="event-date" datetime="${event.date}">${formatDate(event.date)}</time>
          <span class="event-provider">${event.provider}</span>
          <span class="event-type">${typeLabel}</span>
          <span class="event-severity">${event.severity}</span>
        </div>
        <h3 class="event-headline">${event.headline}</h3>
        <p class="event-description">${event.description}</p>
        ${priceHtml}
        ${changeHtml}
        <div class="event-evidence">
          <a href="${event.sourceUrl}" target="_blank" rel="noopener noreferrer" class="event-source">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            Source
          </a>
          <span class="event-confidence confidence-${event.confidence}">
            ${event.confidence} confidence
          </span>
          ${event.notes ? `<span class="event-notes" title="${event.notes}">Note</span>` : ''}
        </div>
        ${event.tags ? `<div class="event-tags">${event.tags.map(t => `<span class="tag">${t}</span>`).join('')}</div>` : ''}
      </article>
    `;
  }

  function updateResultsCount() {
    const countEl = $('#results-count');
    if (countEl) {
      countEl.textContent = `${state.filteredEvents.length} events`;
    }
  }

  function loadMoreEvents() {
    const container = $('#timeline-container');
    const start = state.displayedCount;
    const end = Math.min(start + CONFIG.eventsPerPage, state.filteredEvents.length);

    const newEvents = state.filteredEvents.slice(start, end);
    newEvents.forEach(event => {
      container.insertAdjacentHTML('beforeend', renderEventCard(event));
    });

    state.displayedCount = end;

    const loadMoreContainer = $('#load-more-container');
    if (loadMoreContainer) {
      loadMoreContainer.hidden = state.displayedCount >= state.filteredEvents.length;
    }
  }

  // ============================================
  // URL State Management
  // ============================================
  function readFiltersFromUrl() {
    const params = new URLSearchParams(window.location.search);
    state.filters.provider = params.get('provider') || '';
    state.filters.type = params.get('type') || '';
    state.filters.severity = params.get('severity') || '';
    state.filters.search = params.get('q') || '';

    // Update UI
    const providerSelect = $('#filter-provider');
    if (providerSelect) providerSelect.value = state.filters.provider;

    const typeSelect = $('#filter-type');
    if (typeSelect) typeSelect.value = state.filters.type;

    const severitySelect = $('#filter-severity');
    if (severitySelect) severitySelect.value = state.filters.severity;

    const searchInput = $('#filter-search');
    if (searchInput) searchInput.value = state.filters.search;
  }

  function updateUrlWithFilters() {
    const params = new URLSearchParams();
    if (state.filters.provider) params.set('provider', state.filters.provider);
    if (state.filters.type) params.set('type', state.filters.type);
    if (state.filters.severity) params.set('severity', state.filters.severity);
    if (state.filters.search) params.set('q', state.filters.search);

    const newUrl = params.toString()
      ? `${window.location.pathname}?${params.toString()}`
      : window.location.pathname;

    history.replaceState(null, '', newUrl);
  }

  function copyFilteredLink() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
      const btn = $('#copy-link');
      const originalText = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(() => btn.textContent = originalText, 2000);
    });
  }

  // ============================================
  // Export Functions
  // ============================================
  function exportCSV() {
    const headers = ['Date', 'Provider', 'Model', 'Type', 'Severity', 'Headline', 'Input Price', 'Output Price', 'Source'];
    const rows = state.filteredEvents.map(e => [
      e.date,
      e.provider,
      e.model || '',
      e.type,
      e.severity,
      `"${e.headline.replace(/"/g, '""')}"`,
      e.newPrice?.input || '',
      e.newPrice?.output || '',
      e.sourceUrl
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    downloadFile(csv, 'llm-pricing-events.csv', 'text/csv');
  }

  function exportJSON() {
    const data = {
      exportedAt: new Date().toISOString(),
      eventCount: state.filteredEvents.length,
      events: state.filteredEvents
    };
    downloadFile(JSON.stringify(data, null, 2), 'llm-pricing-events.json', 'application/json');
  }

  function downloadFile(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ============================================
  // Calculator
  // ============================================
  function initCalculator() {
    // Mode toggle
    $$('.calc-mode-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        $$('.calc-mode-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        $$('.intel-calc-mode').forEach(m => m.hidden = true);
        $(`#calc-${mode}-mode`).hidden = false;
      });
    });

    // Range value display
    const batchInput = $('#calc-batch-fraction');
    if (batchInput) {
      batchInput.addEventListener('input', () => {
        $('#calc-batch-value').textContent = batchInput.value + '%';
      });
    }

    const cacheInput = $('#calc-cache-rate');
    if (cacheInput) {
      cacheInput.addEventListener('input', () => {
        $('#calc-cache-value').textContent = cacheInput.value + '%';
      });
    }
  }

  function calculateSavings() {
    const resultsContainer = $('#calc-results');
    if (!resultsContainer) return;

    // Determine mode
    const activeMode = $('.calc-mode-btn.active')?.dataset.mode || 'quick';

    let result;
    if (activeMode === 'quick') {
      result = calculateQuickSavings();
    } else if (activeMode === 'advanced') {
      result = calculateAdvancedSavings();
    } else {
      result = calculateContractBenchmark();
    }

    resultsContainer.innerHTML = renderCalculatorResults(result);
  }

  function calculateQuickSavings() {
    const monthlySpend = parseFloat($('#calc-monthly-spend').value) || 0;
    const tier = $('#calc-model-tier').value;
    const startDate = $('#calc-start-date').value;

    // Find price events for the tier since start date
    const relevantEvents = state.events.filter(e => {
      if (new Date(e.date) < new Date(startDate)) return false;
      if (e.type !== 'price_drop') return false;
      // Match tier loosely
      if (tier === 'frontier' && ['gpt-4', 'gpt-4o', 'claude-3', 'claude-3.5', 'claude-4', 'o1'].includes(e.modelFamily)) return true;
      if (tier === 'efficient' && ['gpt-3.5', 'gpt-4o', 'gemini-1.5', 'gemini-2'].includes(e.modelFamily)) return true;
      if (tier === 'open' && ['deepseek-v3', 'deepseek-r1', 'llama'].includes(e.modelFamily)) return true;
      return false;
    });

    // Calculate multiplicative savings
    let currentSpend = monthlySpend;
    const stack = [];

    relevantEvents.forEach(event => {
      const avgDrop = (Math.abs(event.change?.input || 0) + Math.abs(event.change?.output || 0)) / 2;
      const savings = currentSpend * avgDrop;
      stack.push({
        step: event.headline,
        date: event.date,
        reduction: avgDrop,
        before: currentSpend,
        savings: savings
      });
      currentSpend -= savings;
    });

    return {
      type: 'quick',
      originalSpend: monthlySpend,
      finalSpend: currentSpend,
      totalSavings: monthlySpend - currentSpend,
      savingsPercent: (monthlySpend - currentSpend) / monthlySpend,
      stack,
      tier,
      startDate
    };
  }

  function calculateAdvancedSavings() {
    const monthlySpend = parseFloat($('#calc-adv-spend').value) || 0;
    const batchFraction = parseFloat($('#calc-batch-fraction').value) / 100 || 0;
    const cacheRate = parseFloat($('#calc-cache-rate').value) / 100 || 0;

    let currentSpend = monthlySpend;
    const stack = [];

    // Batch discount (50% on batchable portion)
    if (batchFraction > 0) {
      const batchDiscount = 0.50;
      const savings = currentSpend * batchFraction * batchDiscount;
      stack.push({
        step: 'Batch API Discount',
        description: `${(batchFraction * 100).toFixed(0)}% of requests batched at 50% discount`,
        before: currentSpend,
        savings: savings
      });
      currentSpend -= savings;
    }

    // Cache discount (varies, assume cached tokens are ~10% of cost)
    if (cacheRate > 0) {
      const cacheDiscount = 0.90; // Cached tokens are 90% cheaper
      const savings = currentSpend * cacheRate * cacheDiscount;
      stack.push({
        step: 'Prompt Caching',
        description: `${(cacheRate * 100).toFixed(0)}% cache hit rate at 90% discount`,
        before: currentSpend,
        savings: savings
      });
      currentSpend -= savings;
    }

    return {
      type: 'advanced',
      originalSpend: monthlySpend,
      finalSpend: currentSpend,
      totalSavings: monthlySpend - currentSpend,
      savingsPercent: (monthlySpend - currentSpend) / monthlySpend,
      stack
    };
  }

  function calculateContractBenchmark() {
    const inputRate = parseFloat($('#calc-contract-input').value) || 0;
    const outputRate = parseFloat($('#calc-contract-output').value) || 0;
    const provider = $('#calc-contract-provider').value;

    // Find current list prices for provider
    const providerEvents = state.events
      .filter(e => e.provider === provider && e.newPrice)
      .sort((a, b) => new Date(b.date) - new Date(a.date));

    const latestEvent = providerEvents[0];

    if (!latestEvent) {
      return {
        type: 'contract',
        error: 'No pricing data available for this provider'
      };
    }

    const listInput = latestEvent.newPrice.input;
    const listOutput = latestEvent.newPrice.output;

    const inputDiff = ((inputRate - listInput) / listInput) * 100;
    const outputDiff = ((outputRate - listOutput) / listOutput) * 100;

    // Find best-in-tier
    const allPrices = state.events
      .filter(e => e.newPrice)
      .sort((a, b) => a.newPrice.input - b.newPrice.input);
    const bestInTier = allPrices[0];

    return {
      type: 'contract',
      provider,
      contractRates: { input: inputRate, output: outputRate },
      listRates: { input: listInput, output: listOutput },
      inputDiff,
      outputDiff,
      latestModel: latestEvent.model,
      latestDate: latestEvent.date,
      bestInTier: bestInTier ? {
        provider: bestInTier.provider,
        model: bestInTier.model,
        input: bestInTier.newPrice.input,
        output: bestInTier.newPrice.output
      } : null,
      renegotiationTrigger: inputDiff > 30 || outputDiff > 30
    };
  }

  function renderCalculatorResults(result) {
    if (result.error) {
      return `<div class="calc-error">${result.error}</div>`;
    }

    if (result.type === 'quick' || result.type === 'advanced') {
      const stackHtml = result.stack.map((item, i) => `
        <div class="calc-stack-item">
          <div class="stack-step">${i + 1}. ${item.step}</div>
          ${item.description ? `<div class="stack-desc">${item.description}</div>` : ''}
          ${item.date ? `<div class="stack-date">${formatDate(item.date)}</div>` : ''}
          <div class="stack-savings">-${formatCurrency(item.savings)}</div>
        </div>
      `).join('');

      return `
        <div class="calc-result-summary">
          <div class="calc-result-main">
            <div class="calc-original">
              <span class="calc-label">Original Spend</span>
              <span class="calc-value">${formatCurrency(result.originalSpend)}/mo</span>
            </div>
            <div class="calc-arrow">→</div>
            <div class="calc-final">
              <span class="calc-label">After Savings</span>
              <span class="calc-value">${formatCurrency(result.finalSpend)}/mo</span>
            </div>
          </div>
          <div class="calc-total-savings">
            <span class="savings-amount">${formatCurrency(result.totalSavings)}/mo saved</span>
            <span class="savings-percent">(${(result.savingsPercent * 100).toFixed(0)}% reduction)</span>
          </div>
        </div>
        <div class="calc-stack">
          <h4>Savings Breakdown (Multiplicative)</h4>
          ${stackHtml || '<p>No price drops found in this period.</p>'}
        </div>
      `;
    }

    if (result.type === 'contract') {
      const inputClass = result.inputDiff > 0 ? 'overpaying' : 'underpaying';
      const outputClass = result.outputDiff > 0 ? 'overpaying' : 'underpaying';

      return `
        <div class="calc-contract-result">
          <h4>Contract vs. List Price Comparison</h4>
          <div class="contract-comparison">
            <div class="comparison-row">
              <span class="comparison-label">Input Rate</span>
              <span class="comparison-contract">${formatCurrency(result.contractRates.input)}</span>
              <span class="comparison-vs">vs</span>
              <span class="comparison-list">${formatCurrency(result.listRates.input)}</span>
              <span class="comparison-diff ${inputClass}">${result.inputDiff > 0 ? '+' : ''}${result.inputDiff.toFixed(1)}%</span>
            </div>
            <div class="comparison-row">
              <span class="comparison-label">Output Rate</span>
              <span class="comparison-contract">${formatCurrency(result.contractRates.output)}</span>
              <span class="comparison-vs">vs</span>
              <span class="comparison-list">${formatCurrency(result.listRates.output)}</span>
              <span class="comparison-diff ${outputClass}">${result.outputDiff > 0 ? '+' : ''}${result.outputDiff.toFixed(1)}%</span>
            </div>
          </div>
          <p class="comparison-context">Compared to ${result.latestModel} list prices (${formatDate(result.latestDate)})</p>
          ${result.renegotiationTrigger ? `
            <div class="renegotiation-alert">
              <strong>Renegotiation Trigger:</strong> Your contract rates are >30% above current list prices. Consider renegotiating.
            </div>
          ` : ''}
          ${result.bestInTier ? `
            <div class="best-in-tier">
              <h5>Best Available Rate</h5>
              <p>${result.bestInTier.provider} ${result.bestInTier.model}: ${formatCurrency(result.bestInTier.input)} / ${formatCurrency(result.bestInTier.output)}</p>
            </div>
          ` : ''}
        </div>
      `;
    }

    return '';
  }

  // ============================================
  // Market Snapshot
  // ============================================
  async function loadMarketSnapshot() {
    const result = await loadApiData();

    if (!result) {
      showStaleBanner();
      return;
    }

    const { data, fresh, age } = result;
    renderSnapshot(data, fresh, age);
  }

  function renderSnapshot(data, fresh, age) {
    // Freshness badge
    const badge = $('#freshness-badge');
    if (badge) {
      const hours = age / (60 * 60 * 1000);
      if (hours < 1) {
        badge.className = 'freshness-badge fresh';
        badge.textContent = 'Live';
      } else if (hours < 6) {
        badge.className = 'freshness-badge recent';
        badge.textContent = `${Math.round(hours)}h ago`;
      } else {
        badge.className = 'freshness-badge stale';
        badge.textContent = `${Math.round(hours)}h ago`;
      }
    }

    if (!fresh) {
      showStaleBanner();
    }

    // Render index values - API returns STCI-FRONTIER, STCI-EFFICIENT, STCI-OPEN
    if (data.indices) {
      const indices = data.indices;
      const frontier = indices['STCI-FRONTIER'] || indices.frontier;
      const efficient = indices['STCI-EFFICIENT'] || indices.efficient;
      const open = indices['STCI-OPEN'] || indices.open;

      $('#snapshot-frontier').textContent = formatCurrency(frontier?.blended_rate || frontier?.blended, 2);
      $('#snapshot-efficient').textContent = formatCurrency(efficient?.blended_rate || efficient?.blended, 2);
      $('#snapshot-open').textContent = formatCurrency(open?.blended_rate || open?.blended, 2);
    }
  }

  // ============================================
  // Data Table
  // ============================================
  function toggleDataTable() {
    const wrapper = $('#data-table-wrapper');
    const btn = $('#show-data-table');
    if (!wrapper || !btn) return;

    const isHidden = wrapper.hidden;
    wrapper.hidden = !isHidden;
    btn.setAttribute('aria-expanded', isHidden);
    btn.textContent = isHidden ? 'Hide Data Table' : 'Show Data Table';

    if (isHidden) {
      renderDataTable();
    }
  }

  function renderDataTable() {
    const tbody = $('#price-data-tbody');
    if (!tbody) return;

    const eventsWithPrices = state.events.filter(e => e.newPrice);
    tbody.innerHTML = eventsWithPrices.map(e => `
      <tr>
        <td>${formatDate(e.date)}</td>
        <td>${e.provider}</td>
        <td>${e.model || '-'}</td>
        <td>${formatCurrency(e.newPrice.input)}</td>
        <td>${formatCurrency(e.newPrice.output)}</td>
      </tr>
    `).join('');
  }

  // ============================================
  // Subscribe Form
  // ============================================
  function initSubscribeForm() {
    const form = $('#subscribe-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Honeypot check
      const honeypot = form.querySelector('[name="website"]');
      if (honeypot && honeypot.value) {
        console.log('Honeypot triggered');
        return;
      }

      const email = $('#subscribe-email').value.trim().toLowerCase();
      const prefs = {
        critical: form.querySelector('[name="pref-critical"]')?.checked || false,
        newModels: form.querySelector('[name="pref-new-models"]')?.checked || false,
        weekly: form.querySelector('[name="pref-weekly"]')?.checked || false
      };

      const btn = form.querySelector('button[type="submit"]');
      btn.textContent = 'Saving...';
      btn.disabled = true;

      try {
        // Save to Firestore
        if (window.firebaseDb) {
          const { db, doc, setDoc, collection, addDoc, serverTimestamp } = window.firebaseDb;
          const emailId = email.replace(/[.#$\/\[\]]/g, '_');

          // Save subscriber
          await setDoc(doc(db, 'subscribers', emailId), {
            email: email,
            preferences: prefs,
            createdAt: serverTimestamp(),
            source: 'intelligence-page'
          });

          // Trigger notification email via Firebase Extension
          const prefsList = [];
          if (prefs.critical) prefsList.push('Critical Alerts');
          if (prefs.newModels) prefsList.push('New Models');
          if (prefs.weekly) prefsList.push('Weekly Digest');

          await addDoc(collection(db, 'mail'), {
            to: 'jeremy@intentsolutions.io',
            message: {
              subject: 'New Subscriber - Inference Price Index',
              text: `New subscriber: ${email}\n\nPreferences: ${prefsList.join(', ') || 'None selected'}\n\nSource: intelligence-page`,
              html: `<h2>New Subscriber</h2>
                <p><strong>Email:</strong> ${email}</p>
                <p><strong>Preferences:</strong> ${prefsList.join(', ') || 'None selected'}</p>
                <p><strong>Source:</strong> intelligence-page</p>`
            }
          });
        }

        btn.textContent = 'Subscribed!';
        setTimeout(() => {
          btn.textContent = 'Subscribe';
          btn.disabled = false;
          form.reset();
        }, 3000);
      } catch (error) {
        console.error('Subscribe error:', error);
        btn.textContent = 'Error - Try Again';
        btn.disabled = false;
        setTimeout(() => {
          btn.textContent = 'Subscribe';
        }, 3000);
      }
    });
  }

  // ============================================
  // Event Listeners
  // ============================================
  function initEventListeners() {
    // Filter changes
    const debouncedFilter = debounce(() => applyFilters(), CONFIG.debounceMs);

    $('#filter-provider')?.addEventListener('change', (e) => {
      state.filters.provider = e.target.value;
      applyFilters();
    });

    $('#filter-type')?.addEventListener('change', (e) => {
      state.filters.type = e.target.value;
      applyFilters();
    });

    $('#filter-severity')?.addEventListener('change', (e) => {
      state.filters.severity = e.target.value;
      applyFilters();
    });

    $('#filter-search')?.addEventListener('input', (e) => {
      state.filters.search = e.target.value;
      debouncedFilter();
    });

    // Clear filters
    $('#clear-filters')?.addEventListener('click', () => {
      state.filters = { provider: '', type: '', severity: '', search: '' };
      $('#filter-provider').value = '';
      $('#filter-type').value = '';
      $('#filter-severity').value = '';
      $('#filter-search').value = '';
      applyFilters();
    });

    // Copy link
    $('#copy-link')?.addEventListener('click', copyFilteredLink);

    // Export
    $('#export-csv')?.addEventListener('click', exportCSV);
    $('#export-json')?.addEventListener('click', exportJSON);

    // Load more
    $('#load-more')?.addEventListener('click', loadMoreEvents);

    // Chart scale toggle
    $$('.chart-scale-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        $$('.chart-scale-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        setChartScale(btn.dataset.scale);
      });
    });

    // Data table toggle
    $('#show-data-table')?.addEventListener('click', toggleDataTable);

    // Calculator
    $('#calculate-savings')?.addEventListener('click', calculateSavings);
  }

  // ============================================
  // Initialization
  // ============================================
  async function init() {
    try {
      // Load events data
      const data = await loadData();
      state.events = data.events || [];

      // Compute and render stats
      const stats = computeStats(state.events);
      renderStats(stats);

      // Initialize chart
      initChart(state.events);

      // Initialize timeline
      initTimeline(state.events);

      // Initialize calculator
      initCalculator();

      // Load JSON-LD
      const jsonld = await loadJsonLd();
      if (jsonld) {
        const script = $('#jsonld-data');
        if (script) script.textContent = JSON.stringify(jsonld);
      }

      // Load market snapshot
      loadMarketSnapshot();

      // Initialize subscribe form
      initSubscribeForm();

      // Initialize event listeners
      initEventListeners();

    } catch (error) {
      console.error('Failed to initialize intelligence page:', error);

      // Show error state
      const loading = $('#timeline-loading');
      if (loading) {
        loading.innerHTML = `
          <p style="color: var(--accent-red);">Failed to load pricing data.</p>
          <p>Please try refreshing the page.</p>
        `;
      }
    }
  }

  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
