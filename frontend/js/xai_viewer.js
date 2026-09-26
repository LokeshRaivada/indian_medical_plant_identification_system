/**
 * Grad-CAM Explainable AI Interactive Visualizer Module
 */

let currentVisualizations = null;

function switchXAIMode(mode) {
  const btnSide = document.getElementById('btn-view-side');
  const btnBlend = document.getElementById('btn-view-blend');
  const sideView = document.getElementById('xai-side-view');
  const blendView = document.getElementById('xai-blend-view');
  const blendSliderBox = document.getElementById('xai-blend-slider-box');

  if (mode === 'side') {
    btnSide.classList.add('active');
    btnBlend.classList.remove('active');
    sideView.style.display = 'grid';
    blendView.style.display = 'none';
    blendSliderBox.style.display = 'none';
  } else {
    btnBlend.classList.add('active');
    btnSide.classList.remove('active');
    sideView.style.display = 'none';
    blendView.style.display = 'block';
    blendSliderBox.style.display = 'block';
  }
}

function updateBlendOpacity(val) {
  const opacityVal = val / 100;
  const heatImg = document.getElementById('xai-blend-heat');
  const label = document.getElementById('blend-opacity-val');
  if (heatImg) heatImg.style.opacity = opacityVal;
  if (label) label.textContent = `${val}%`;
}

function renderGradCAMVisuals(visuals) {
  currentVisualizations = visuals;

  // Side-by-Side Images
  const imgOrig = document.getElementById('xai-img-orig');
  const imgCam = document.getElementById('xai-img-cam');
  const imgOverlay = document.getElementById('xai-img-overlay');

  if (imgOrig) imgOrig.src = visuals.original;
  if (imgCam) imgCam.src = visuals.heatmap;
  if (imgOverlay) imgOverlay.src = visuals.overlay;

  // Layered Blend Images
  const blendBase = document.getElementById('xai-blend-base');
  const blendHeat = document.getElementById('xai-blend-heat');
  if (blendBase) blendBase.src = visuals.original;
  if (blendHeat) blendHeat.src = visuals.heatmap;
}
