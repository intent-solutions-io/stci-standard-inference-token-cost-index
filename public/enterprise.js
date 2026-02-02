/**
 * Enterprise Rate Benchmark - CSV Upload Edition
 *
 * Processes usage CSVs entirely client-side. No data leaves the browser.
 */

// Constants
const OUTPUT_WEIGHT = 3; // 3:1 output:input ratio for blended rate

// State
const state = {
  parsedData: null,
  marketRate: null,
};

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  fetchMarketRate();
});

function setupEventListeners() {
  // File upload
  const uploadZone = document.getElementById('upload-zone');
  const fileInput = document.getElementById('file-input');

  if (uploadZone) {
    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleDrop);
  }

  if (fileInput) {
    fileInput.addEventListener('change', handleFileSelect);
  }

  // Sample data
  document.getElementById('load-sample-btn')?.addEventListener('click', loadSampleData);

  // Reset
  document.getElementById('reset-btn')?.addEventListener('click', resetUpload);

  // Manual calculator
  document.getElementById('manual-calculate-btn')?.addEventListener('click', calculateManual);

  // Mobile nav toggle
  const navToggle = document.querySelector('.nav-toggle');
  const navMobile = document.getElementById('nav-mobile');
  if (navToggle && navMobile) {
    navToggle.addEventListener('click', () => {
      navMobile.classList.toggle('open');
    });
  }
}

// ============================================
// Market Rate
// ============================================

async function fetchMarketRate() {
  try {
    const response = await fetch('/v1/index/latest');
    if (!response.ok) throw new Error('Failed to fetch market rate');

    const data = await response.json();
    // Find STCI-FRONTIER in the indices
    const frontier = data.indices?.find(idx => idx.index_name === 'STCI-FRONTIER');
    if (frontier) {
      state.marketRate = frontier.blended_rate;
      document.getElementById('market-rate').textContent = `$${state.marketRate.toFixed(2)}`;
    }
  } catch (error) {
    console.error('Failed to fetch market rate:', error);
    document.getElementById('market-rate').textContent = 'Unavailable';
  }
}

// ============================================
// Drag & Drop
// ============================================

function handleDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.add('drag-over');
}

function handleDragLeave(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.remove('drag-over');
}

function handleDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.remove('drag-over');

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    processFile(files[0]);
  }
}

function handleFileSelect(e) {
  const files = e.target.files;
  if (files.length > 0) {
    processFile(files[0]);
  }
}

// ============================================
// CSV Processing
// ============================================

function processFile(file) {
  if (!file.name.endsWith('.csv')) {
    showError('Please upload a CSV file');
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const csv = e.target.result;
      const parsed = parseCSV(csv);
      state.parsedData = parsed;
      displayResults(parsed);
    } catch (error) {
      showError(error.message);
    }
  };
  reader.onerror = () => showError('Failed to read file');
  reader.readAsText(file);
}

function parseCSV(csvText) {
  const lines = csvText.trim().split('\n');
  if (lines.length < 2) {
    throw new Error('CSV file appears to be empty');
  }

  const headers = parseCSVLine(lines[0]).map(h => h.toLowerCase().trim());

  // Detect provider based on columns
  const provider = detectProvider(headers);
  if (!provider) {
    throw new Error('Unrecognized CSV format. Expected OpenAI or Anthropic usage export.');
  }

  // Parse rows
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const values = parseCSVLine(line);
    const row = {};
    headers.forEach((h, idx) => {
      row[h] = values[idx] || '';
    });
    rows.push(row);
  }

  // Process based on provider
  if (provider === 'openai') {
    return processOpenAIData(rows);
  } else {
    return processAnthropicData(rows);
  }
}

function parseCSVLine(line) {
  // RFC 4180 compliant CSV parsing with escaped quote handling
  const result = [];
  let current = '';
  let inQuotes = false;
  let i = 0;

  while (i < line.length) {
    const char = line[i];

    if (inQuotes) {
      if (char === '"') {
        // Check for escaped quote ("")
        if (i + 1 < line.length && line[i + 1] === '"') {
          current += '"';
          i += 2;
          continue;
        } else {
          // End of quoted field
          inQuotes = false;
          i++;
          continue;
        }
      } else {
        current += char;
      }
    } else {
      if (char === '"') {
        // Start of quoted field
        inQuotes = true;
      } else if (char === ',') {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    i++;
  }
  result.push(current.trim());
  return result;
}

function detectProvider(headers) {
  // OpenAI columns (typical export)
  // date, model, usage_type, input_tokens, output_tokens, cost
  // or: timestamp, model, context_tokens, generated_tokens, total_cost
  const openaiIndicators = ['cost', 'usage_type', 'context_tokens', 'generated_tokens'];
  const hasOpenAI = openaiIndicators.some(col => headers.includes(col));

  // Anthropic columns (typical export)
  // date, model, input_tokens, output_tokens, total_cost
  // or: timestamp, model_id, input_tokens, output_tokens, cost_usd
  const anthropicIndicators = ['total_cost', 'cost_usd', 'model_id'];
  const hasAnthropic = anthropicIndicators.some(col => headers.includes(col));

  // Check for common patterns
  if (hasOpenAI && !hasAnthropic) return 'openai';
  if (hasAnthropic && !hasOpenAI) return 'anthropic';

  // Fallback: check for model names in data
  // Both have input_tokens and output_tokens, so check column names
  if (headers.includes('context_tokens') || headers.includes('generated_tokens')) {
    return 'openai';
  }

  // If we have the basic columns, assume generic format
  if (headers.includes('input_tokens') && headers.includes('output_tokens')) {
    // Check cost column naming
    if (headers.includes('cost') || headers.includes('total_cost')) {
      return 'openai'; // Default to OpenAI-like processing
    }
  }

  return null;
}

function processOpenAIData(rows) {
  const byModel = {};
  let totalInput = 0;
  let totalOutput = 0;
  let totalCost = 0;

  for (const row of rows) {
    const model = row.model || row.model_id || 'unknown';
    const inputTokens = parseNumber(row.input_tokens || row.context_tokens || row.prompt_tokens);
    const outputTokens = parseNumber(row.output_tokens || row.generated_tokens || row.completion_tokens);
    const cost = parseNumber(row.cost || row.total_cost || row.cost_usd);

    totalInput += inputTokens;
    totalOutput += outputTokens;
    totalCost += cost;

    if (!byModel[model]) {
      byModel[model] = { inputTokens: 0, outputTokens: 0, cost: 0 };
    }
    byModel[model].inputTokens += inputTokens;
    byModel[model].outputTokens += outputTokens;
    byModel[model].cost += cost;
  }

  return {
    provider: 'OpenAI',
    totalInput,
    totalOutput,
    totalCost,
    byModel,
    effectiveRate: calculateEffectiveRate(totalInput, totalOutput, totalCost),
  };
}

function processAnthropicData(rows) {
  const byModel = {};
  let totalInput = 0;
  let totalOutput = 0;
  let totalCost = 0;

  for (const row of rows) {
    const model = row.model || row.model_id || 'unknown';
    const inputTokens = parseNumber(row.input_tokens);
    const outputTokens = parseNumber(row.output_tokens);
    const cost = parseNumber(row.total_cost || row.cost_usd || row.cost);

    totalInput += inputTokens;
    totalOutput += outputTokens;
    totalCost += cost;

    if (!byModel[model]) {
      byModel[model] = { inputTokens: 0, outputTokens: 0, cost: 0 };
    }
    byModel[model].inputTokens += inputTokens;
    byModel[model].outputTokens += outputTokens;
    byModel[model].cost += cost;
  }

  return {
    provider: 'Anthropic',
    totalInput,
    totalOutput,
    totalCost,
    byModel,
    effectiveRate: calculateEffectiveRate(totalInput, totalOutput, totalCost),
  };
}

function parseNumber(val) {
  if (val === undefined || val === null || val === '') return 0;
  const num = parseFloat(String(val).replace(/[,$]/g, ''));
  return isNaN(num) ? 0 : num;
}

function calculateEffectiveRate(inputTokens, outputTokens, totalCost) {
  // Blended tokens = input + (output * OUTPUT_WEIGHT)
  const blendedTokens = inputTokens + (outputTokens * OUTPUT_WEIGHT);
  if (blendedTokens === 0) return 0;
  // Rate per 1M tokens
  return (totalCost / blendedTokens) * 1_000_000;
}

// ============================================
// Display Results
// ============================================

function displayResults(data) {
  // Hide upload section, show results
  document.getElementById('upload-section').style.display = 'none';
  document.getElementById('results-section').style.display = 'block';

  // Your rate
  document.getElementById('your-rate').textContent = `$${data.effectiveRate.toFixed(2)}`;

  // Discount/premium badge
  updateDiscountBadge(data.effectiveRate);

  // Stats
  document.getElementById('total-spend').textContent = formatCurrency(data.totalCost);
  document.getElementById('input-tokens').textContent = formatTokens(data.totalInput);
  document.getElementById('output-tokens').textContent = formatTokens(data.totalOutput);
  document.getElementById('detected-provider').textContent = data.provider;

  // Model breakdown table
  renderModelTable(data.byModel);

  // Scroll to results
  document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

function updateDiscountBadge(yourRate) {
  const badge = document.getElementById('discount-badge');

  if (!state.marketRate) {
    badge.textContent = 'Market rate unavailable';
    badge.className = 'discount-badge';
    return;
  }

  const diff = ((state.marketRate - yourRate) / state.marketRate) * 100;

  if (diff > 0) {
    badge.textContent = `${diff.toFixed(0)}% below market`;
    badge.className = 'discount-badge positive';
  } else if (diff < 0) {
    badge.textContent = `${Math.abs(diff).toFixed(0)}% above market`;
    badge.className = 'discount-badge negative';
  } else {
    badge.textContent = 'At market rate';
    badge.className = 'discount-badge';
  }
}

function renderModelTable(byModel) {
  const tbody = document.getElementById('model-table-body');
  tbody.innerHTML = '';

  const models = Object.entries(byModel).sort((a, b) => b[1].cost - a[1].cost);

  for (const [model, data] of models) {
    const rate = calculateEffectiveRate(data.inputTokens, data.outputTokens, data.cost);
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${escapeHtml(model)}</td>
      <td>${formatTokens(data.inputTokens)}</td>
      <td>${formatTokens(data.outputTokens)}</td>
      <td>${formatCurrency(data.cost)}</td>
      <td>$${rate.toFixed(2)}/1M</td>
    `;
    tbody.appendChild(row);
  }
}

// ============================================
// Manual Calculator
// ============================================

function calculateManual() {
  const inputTokens = parseNumber(document.getElementById('manual-input-tokens').value);
  const outputTokens = parseNumber(document.getElementById('manual-output-tokens').value);
  const spend = parseNumber(document.getElementById('manual-spend').value);

  if (inputTokens === 0 && outputTokens === 0) {
    showError('Please enter token counts');
    return;
  }
  if (spend === 0) {
    showError('Please enter your total spend');
    return;
  }

  const rate = calculateEffectiveRate(inputTokens, outputTokens, spend);

  // Show result
  const resultDiv = document.getElementById('manual-result');
  resultDiv.style.display = 'block';
  document.getElementById('manual-rate-value').textContent = `$${rate.toFixed(2)}`;

  // Comparison
  const comparisonDiv = document.getElementById('manual-comparison');
  if (state.marketRate) {
    const diff = ((state.marketRate - rate) / state.marketRate) * 100;
    if (diff > 0) {
      comparisonDiv.innerHTML = `<span class="comparison-positive">${diff.toFixed(0)}% below STCI-FRONTIER ($${state.marketRate.toFixed(2)})</span>`;
    } else if (diff < 0) {
      comparisonDiv.innerHTML = `<span class="comparison-negative">${Math.abs(diff).toFixed(0)}% above STCI-FRONTIER ($${state.marketRate.toFixed(2)})</span>`;
    } else {
      comparisonDiv.innerHTML = `<span>At STCI-FRONTIER market rate ($${state.marketRate.toFixed(2)})</span>`;
    }
  } else {
    comparisonDiv.innerHTML = '<span>Market rate unavailable for comparison</span>';
  }
}

// ============================================
// Sample Data
// ============================================

async function loadSampleData() {
  try {
    const response = await fetch('/samples/openai-usage-sample.csv');
    if (!response.ok) throw new Error('Could not load sample data.');
    const csvText = await response.text();
    const parsed = parseCSV(csvText);
    // Override provider name for clarity in the UI
    parsed.provider = 'Sample Data';
    state.parsedData = parsed;
    displayResults(parsed);
  } catch (error) {
    showError(error.message);
  }
}

// ============================================
// Reset
// ============================================

function resetUpload() {
  state.parsedData = null;
  document.getElementById('results-section').style.display = 'none';
  document.getElementById('upload-section').style.display = 'block';
  document.getElementById('file-input').value = '';

  // Scroll back to upload
  document.getElementById('upload-section').scrollIntoView({ behavior: 'smooth' });
}

// ============================================
// Utilities
// ============================================

function formatTokens(tokens) {
  if (tokens >= 1_000_000_000) {
    return (tokens / 1_000_000_000).toFixed(1) + 'B';
  } else if (tokens >= 1_000_000) {
    return (tokens / 1_000_000).toFixed(1) + 'M';
  } else if (tokens >= 1_000) {
    return (tokens / 1_000).toFixed(1) + 'K';
  }
  return tokens.toLocaleString();
}

function formatCurrency(amount) {
  return '$' + amount.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showError(message) {
  showToast(message, 'error');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) {
    // Fallback to alert if container doesn't exist
    alert(message);
    return;
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.add('toast-visible');
  });

  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    toast.classList.remove('toast-visible');
    setTimeout(() => toast.remove(), 300);
  }, 5000);
}
