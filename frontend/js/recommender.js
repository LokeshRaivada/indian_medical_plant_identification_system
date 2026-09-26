/**
 * Ayurvedic Symptom & Disease Recommender Frontend Module
 */

async function executeRecommendation() {
  const searchInput = document.getElementById('rec-search-input');
  const partFilter = document.getElementById('rec-filter-part');
  const systemFilter = document.getElementById('rec-filter-system');
  const resultsGrid = document.getElementById('rec-results-grid');
  const emptyState = document.getElementById('rec-empty-state');

  const query = searchInput ? searchInput.value.trim() : '';
  const part = partFilter ? partFilter.value : '';
  const system = systemFilter ? systemFilter.value : '';

  if (!query && !part && !system) {
    if (resultsGrid) resultsGrid.innerHTML = '';
    if (emptyState) emptyState.style.display = 'flex';
    return;
  }

  try {
    const res = await fetch('/api/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        part: part || null,
        system: system || null,
        max_results: 8
      })
    });

    const data = await res.json();
    renderRecommendationCards(data.recommendations || []);
  } catch (err) {
    console.error('Failed to fetch recommendations:', err);
  }
}

function selectSymptomChip(queryText) {
  const input = document.getElementById('rec-search-input');
  if (input) {
    input.value = queryText;
    executeRecommendation();
  }
}

function renderRecommendationCards(recs) {
  const resultsGrid = document.getElementById('rec-results-grid');
  const emptyState = document.getElementById('rec-empty-state');

  if (!resultsGrid) return;
  resultsGrid.innerHTML = '';

  if (!recs || recs.length === 0) {
    if (emptyState) {
      emptyState.style.display = 'flex';
      emptyState.querySelector('p').textContent = 'No matching medicinal plants found. Try broader symptoms like "cough", "fever", "arthritis", or "diabetes".';
    }
    return;
  }

  if (emptyState) emptyState.style.display = 'none';

  recs.forEach(plant => {
    const card = document.createElement('div');
    card.className = 'rec-card';

    const commonName = plant.common_names?.english || plant.common_names?.hindi || '';
    const sanskritName = plant.common_names?.sanskrit ? `(${plant.common_names.sanskrit})` : '';

    const rationaleTags = (plant.match_rationale || []).map(r => 
      `<span class="rationale-tag">${r}</span>`
    ).join('');

    const partsUsed = (plant.parts_used || []).join(', ');

    card.innerHTML = `
      <div class="rec-header">
        <div>
          <h3 class="rec-botanical">${plant.botanical_name}</h3>
          <p class="rec-common">${commonName} ${sanskritName} • <span style="color: var(--text-muted);">${plant.family || ''}</span></p>
        </div>
        <span class="match-score-badge">${plant.relevance_score}% Match</span>
      </div>

      <div class="rec-rationale-box">
        ${rationaleTags}
      </div>

      <p class="rec-body-text">${plant.medicinal_summary || ''}</p>

      <div style="font-size: 12px; margin-bottom: 6px;">
        <strong style="color: var(--text-secondary);">Parts Used:</strong> <span style="color: var(--accent-emerald-light);">${partsUsed}</span>
      </div>

      <div style="font-size: 12px; margin-bottom: 10px;">
        <strong style="color: var(--text-secondary);">Classical Formulation:</strong> <span style="color: var(--text-primary);">${plant.formulation || 'Standard decoction or powder.'}</span>
      </div>

      ${plant.precautions ? `
        <div style="padding: 8px 12px; background: rgba(245, 158, 11, 0.1); border-left: 2px solid var(--accent-amber); font-size: 11px; color: #fde68a; border-radius: 4px;">
          ⚠️ <strong>Precaution:</strong> ${plant.precautions}
        </div>
      ` : ''}

      <div style="margin-top: 14px; text-align: right;">
        <button class="sample-pill-btn" onclick="openPlantModal('${plant.plant_id}')">View Full Monograph →</button>
      </div>
    `;

    resultsGrid.appendChild(card);
  });
}
