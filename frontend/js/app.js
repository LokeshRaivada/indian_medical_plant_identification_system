/**
 * Main Application Orchestration Script
 */

let selectedFile = null;
let currentThreshold = 0.70;
let allHerbariumPlants = [];

document.addEventListener('DOMContentLoaded', () => {
  setupDropzone();
  loadHerbarium();
  loadAcademicStats();
  checkSystemHealth();
});

// Tab Switcher
function switchTab(tabId) {
  const tabs = ['identify', 'recommender', 'herbarium', 'academic'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const panel = document.getElementById(`panel-${t}`);
    if (btn) btn.classList.toggle('active', t === tabId);
    if (panel) panel.classList.toggle('active', t === tabId);
  });
}

// System Health
async function checkSystemHealth() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    const badge = document.getElementById('gpu-status-badge');
    if (badge && data.device) {
      badge.textContent = `${data.device} • Online`;
    }
  } catch (e) {
    console.warn('Backend offline or health check failed');
  }
}

// Dropzone & File Handling
function setupDropzone() {
  const dropzone = document.getElementById('dropzone');
  if (!dropzone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      handleImageFile(files[0]);
    }
  });
}

function handleFileSelect(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    handleImageFile(files[0]);
  }
}

function handleImageFile(file) {
  if (!file.type.startsWith('image/')) {
    alert('Please select a valid image file (JPG, PNG, WEBP).');
    return;
  }
  selectedFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    const previewBox = document.getElementById('preview-box');
    const previewImg = document.getElementById('preview-img');
    const dropzone = document.getElementById('dropzone');
    const btnPredict = document.getElementById('btn-predict');

    if (previewImg) previewImg.src = e.target.result;
    if (previewBox) previewBox.style.display = 'block';
    if (dropzone) dropzone.style.display = 'none';
    if (btnPredict) btnPredict.disabled = false;
  };
  reader.readAsDataURL(file);
}

function clearSelectedImage(event) {
  if (event) event.stopPropagation();
  selectedFile = null;
  const fileInput = document.getElementById('file-input');
  if (fileInput) fileInput.value = '';

  const previewBox = document.getElementById('preview-box');
  const dropzone = document.getElementById('dropzone');
  const btnPredict = document.getElementById('btn-predict');

  if (previewBox) previewBox.style.display = 'none';
  if (dropzone) dropzone.style.display = 'block';
  if (btnPredict) btnPredict.disabled = true;
}

// Quick Sample Botanical Specimen Loader
async function loadSampleSpecimen(classId, displayName) {
  try {
    const res = await fetch(`/api/sample_image?class_id=${classId}`);
    if (res.ok) {
      const blob = await res.blob();
      const file = new File([blob], `${classId}.jpg`, { type: 'image/jpeg' });
      handleImageFile(file);
    } else {
      // Direct fallback to predict using class_id if test server endpoint is available
      console.log(`Triggering direct prediction for sample ${classId}`);
    }
  } catch (err) {
    console.log('Sample image endpoint fallback');
  }
}

// Threshold Slider
function updateThresholdValue(val) {
  currentThreshold = val / 100;
  const display = document.getElementById('threshold-display');
  if (display) display.textContent = `${val}%`;
}

// Run Inference & Explainable AI Prediction
async function submitPrediction() {
  if (!selectedFile) return;

  const btn = document.getElementById('btn-predict');
  const resultsEmpty = document.getElementById('results-empty');
  const resultsContent = document.getElementById('results-content');

  btn.disabled = true;
  btn.innerHTML = '<span>⏳</span> Processing DL Classification & Grad-CAM...';

  const formData = new FormData();
  formData.append('file', selectedFile);
  formData.append('threshold', currentThreshold);

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Inference error');
    }

    const data = await res.json();
    renderPredictionResults(data);

    if (resultsEmpty) resultsEmpty.style.display = 'none';
    if (resultsContent) resultsContent.style.display = 'block';
  } catch (err) {
    alert(`Prediction failed: ${err.message}`);
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>🔬</span> Classify & Generate Grad-CAM XAI';
  }
}

// Render Results & Confidence Gauge
function renderPredictionResults(data) {
  // Confidence Status Banner
  const banner = document.getElementById('status-banner');
  const badge = document.getElementById('result-badge');
  const botName = document.getElementById('result-botanical-name');
  const comName = document.getElementById('result-common-name');
  const explanation = document.getElementById('result-explanation');
  const warningBox = document.getElementById('result-warning-box');
  const radialProgress = document.getElementById('radial-progress');
  const radialText = document.getElementById('radial-text');

  const isConfident = data.is_confident;
  const confPercent = Math.round(data.confidence * 100);

  if (banner) {
    banner.className = `status-banner ${isConfident ? 'confident' : 'uncertain'}`;
  }
  if (badge) {
    badge.className = `status-badge ${isConfident ? 'confident' : 'uncertain'}`;
    badge.textContent = data.status;
  }
  if (botName) botName.textContent = data.botanical_name;
  if (comName) {
    const names = data.common_names || {};
    comName.textContent = `${names.english || ''} ${names.hindi ? `• ${names.hindi}` : ''} ${names.sanskrit ? `(${names.sanskrit})` : ''}`;
  }
  if (explanation) explanation.textContent = data.explanation;

  if (warningBox) {
    if (data.warning) {
      warningBox.style.display = 'block';
      warningBox.innerHTML = `⚠️ <strong>Safety Advisory:</strong> ${data.warning}`;
    } else {
      warningBox.style.display = 'none';
    }
  }

  // Animate Radial Progress
  if (radialText) radialText.textContent = `${confPercent}%`;
  if (radialProgress) {
    radialProgress.className = `radial-progress ${isConfident ? '' : 'uncertain'}`;
    const circumference = 2 * Math.PI * 30; // ~188.5
    const offset = circumference - (confPercent / 100) * circumference;
    radialProgress.style.strokeDashoffset = offset;
  }

  // Grad-CAM Visualizations
  if (data.visualizations) {
    renderGradCAMVisuals(data.visualizations);
  }

  // Top-5 Predictions Chart
  renderTopCandidates(data.top_predictions || []);

  // Detailed Monograph
  renderMonograph(data.plant_profile || {}, data.botanical_name);
}

function renderTopCandidates(candidates) {
  const container = document.getElementById('top-candidates-container');
  if (!container) return;
  container.innerHTML = '';

  candidates.forEach(c => {
    const row = document.createElement('div');
    row.className = 'candidate-row';
    row.innerHTML = `
      <div class="candidate-labels">
        <span class="candidate-name">${c.botanical_name} ${c.common_name ? `(${c.common_name})` : ''}</span>
        <span class="candidate-percent">${c.confidence_percent}%</span>
      </div>
      <div class="candidate-bar-bg">
        <div class="candidate-bar-fill" style="width: ${c.confidence_percent}%"></div>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderMonograph(profile, fallbackName) {
  const monoBotanical = document.getElementById('mono-botanical');
  const monoFamily = document.getElementById('mono-family');
  const monoCommon = document.getElementById('mono-common-names');
  const monoParts = document.getElementById('mono-parts-used');
  const monoAyurveda = document.getElementById('mono-ayurveda');
  const monoPhyto = document.getElementById('mono-phytochemicals');
  const monoUses = document.getElementById('mono-uses');
  const monoForm = document.getElementById('mono-formulation');
  const monoPrecaution = document.getElementById('mono-precaution-box');

  if (monoBotanical) monoBotanical.textContent = profile.botanical_name || fallbackName;
  if (monoFamily) monoFamily.textContent = `Family: ${profile.family || 'Botanical Family'}`;

  const cNames = profile.common_names || {};
  if (monoCommon) {
    monoCommon.textContent = `English: ${cNames.english || 'N/A'} | Hindi: ${cNames.hindi || 'N/A'} | Sanskrit: ${cNames.sanskrit || 'N/A'}`;
  }

  if (monoParts) {
    monoParts.innerHTML = (profile.parts_used || ['Whole Plant']).map(p => 
      `<span class="mono-tag">🍃 ${p}</span>`
    ).join('');
  }

  if (monoAyurveda) {
    const ayur = profile.ayurvedic_properties || {};
    monoAyurveda.innerHTML = `
      <strong>Rasa:</strong> ${ayur.rasa || 'Tikta, Katu'}<br>
      <strong>Virya:</strong> ${ayur.virya || 'Ushna'}<br>
      <strong>Dosha Karma:</strong> ${ayur.dosha_karma || 'Pacifies Vata & Kapha'}
    `;
  }

  if (monoPhyto) {
    monoPhyto.innerHTML = (profile.active_phytochemicals || ['Alkaloids', 'Flavonoids']).map(ch => 
      `<span class="mono-tag">🧪 ${ch}</span>`
    ).join('');
  }

  if (monoUses) monoUses.textContent = profile.medicinal_uses || 'Widely used in traditional formulations.';
  if (monoForm) monoForm.textContent = profile.dosage_and_formulation || 'Standard powder (Churna) or decoction (Kwatha).';

  if (monoPrecaution) {
    if (profile.precautions) {
      monoPrecaution.style.display = 'block';
      monoPrecaution.innerHTML = `⚠️ <strong>Contraindications & Safety:</strong> ${profile.precautions}`;
    } else {
      monoPrecaution.style.display = 'none';
    }
  }
}

// Herbarium Directory
async function loadHerbarium() {
  try {
    const res = await fetch('/api/plants');
    const data = await res.json();
    allHerbariumPlants = data.plants || [];
    renderHerbariumGrid(allHerbariumPlants);
  } catch (err) {
    console.error('Failed to load herbarium:', err);
  }
}

function filterHerbarium(searchTerm = null) {
  const searchInput = document.getElementById('herb-search');
  const systemFilter = document.getElementById('herb-system-filter');

  const query = (searchTerm !== null ? searchTerm : (searchInput ? searchInput.value : '')).toLowerCase();
  const system = systemFilter ? systemFilter.value.toLowerCase() : '';

  const filtered = allHerbariumPlants.filter(p => {
    const matchesQuery = !query || 
      p.botanical_name.toLowerCase().includes(query) ||
      p.common_name_en.toLowerCase().includes(query) ||
      p.common_name_hi.toLowerCase().includes(query) ||
      p.common_name_sa.toLowerCase().includes(query);

    const matchesSystem = !system || 
      (p.systems || []).some(s => s.toLowerCase().includes(system));

    return matchesQuery && matchesSystem;
  });

  renderHerbariumGrid(filtered);
}

function renderHerbariumGrid(plants) {
  const grid = document.getElementById('herbarium-grid');
  if (!grid) return;
  grid.innerHTML = '';

  plants.forEach(p => {
    const card = document.createElement('div');
    card.className = 'herb-item-card';
    card.onclick = () => openPlantModal(p.id);

    card.innerHTML = `
      <div class="herb-item-botanical">${p.botanical_name}</div>
      <div class="herb-item-names">${p.common_name_hi || p.common_name_en} ${p.common_name_sa ? `• ${p.common_name_sa}` : ''}</div>
      <div class="herb-item-family">${p.family}</div>
      <div style="margin-top: 8px; font-size: 11px; color: var(--accent-emerald-light);">
        Parts: ${(p.parts_used || []).slice(0, 2).join(', ')}
      </div>
    `;
    grid.appendChild(card);
  });
}

// Modal Drawer
async function openPlantModal(plantId) {
  const modal = document.getElementById('plant-modal');
  const content = document.getElementById('modal-content');
  if (!modal || !content) return;

  try {
    const res = await fetch(`/api/plants/${plantId}`);
    const plant = await res.json();

    const parts = (plant.parts_used || []).map(p => `<span class="mono-tag">${p}</span>`).join(' ');
    const chemicals = (plant.active_phytochemicals || []).map(c => `<span class="mono-tag">🧪 ${c}</span>`).join(' ');
    const indications = (plant.therapeutic_indications || []).map(i => `<span class="rationale-tag">${i}</span>`).join(' ');

    content.innerHTML = `
      <h2 style="font-size: 22px; font-weight: 800; font-style: italic; color: var(--accent-emerald-light);">${plant.botanical_name}</h2>
      <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 16px;">
        Family: ${plant.family} | English: ${plant.common_names?.english || 'N/A'} | Hindi: ${plant.common_names?.hindi || 'N/A'} | Sanskrit: ${plant.common_names?.sanskrit || 'N/A'}
      </p>

      <div style="margin-bottom: 14px;">
        <p class="mono-prop-title">Therapeutic Indications</p>
        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">${indications}</div>
      </div>

      <div style="margin-bottom: 14px;">
        <p class="mono-prop-title">Parts Used</p>
        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">${parts}</div>
      </div>

      <div style="margin-bottom: 14px;">
        <p class="mono-prop-title">Phytochemical Profile</p>
        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">${chemicals}</div>
      </div>

      <div style="margin-bottom: 14px;">
        <p class="mono-prop-title">Medicinal Properties & Pharmacology</p>
        <p style="font-size: 13px; color: var(--text-primary);">${plant.medicinal_uses}</p>
      </div>

      <div style="margin-bottom: 14px;">
        <p class="mono-prop-title">Classical Ayurvedic Formulations</p>
        <p style="font-size: 13px; color: var(--text-primary);">${plant.dosage_and_formulation}</p>
      </div>

      ${plant.precautions ? `
        <div class="alert-precaution">
          ⚠️ <strong>Safety Warning:</strong> ${plant.precautions}
        </div>
      ` : ''}
    `;

    modal.style.display = 'flex';
  } catch (err) {
    console.error('Failed to load plant detail:', err);
  }
}

function closeModal() {
  const modal = document.getElementById('plant-modal');
  if (modal) modal.style.display = 'none';
}

// Academic Stats
async function loadAcademicStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();

    const dStats = data.dataset_stats || {};
    if (dStats.num_classes) {
      document.getElementById('metric-classes').textContent = dStats.num_classes;
      document.getElementById('metric-train').textContent = (dStats.train_count || 20253).toLocaleString();
      document.getElementById('metric-val').textContent = (dStats.val_count || 3575).toLocaleString();
      document.getElementById('metric-test').textContent = (dStats.test_count || 9300).toLocaleString();
    }
  } catch (e) {
    console.warn('Academic stats not loaded yet');
  }
}
