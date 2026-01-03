async function loadIndex() {
  try {
    const res = await fetch('/v1/index/latest');
    const data = await res.json();

    if (data.indices) {
      updateCard('frontier', data.indices['STCI-FRONTIER']);
      updateCard('efficient', data.indices['STCI-EFFICIENT']);
      updateCard('open', data.indices['STCI-OPEN']);

      document.getElementById('updated').textContent =
        `Last updated: ${data.date} ${data.computed_at?.split('T')[1]?.slice(0,5) || ''} UTC`;
    }
  } catch (e) {
    console.error('Failed to load index:', e);
    document.getElementById('updated').textContent = 'Failed to load data';
  }
}

function updateCard(id, indexData) {
  if (!indexData) return;

  const valueEl = document.getElementById(`${id}-value`);
  const changeEl = document.getElementById(`${id}-change`);

  valueEl.textContent = `$${indexData.blended_rate.toFixed(2)}/1M`;

  // Show model count
  changeEl.textContent = `${indexData.model_count} models`;
  changeEl.className = 'change';
}

loadIndex();
