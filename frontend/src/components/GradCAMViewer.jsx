import React, { useState } from 'react';

export default function GradCAMViewer({ visualizations }) {
  const [viewMode, setViewMode] = useState('side'); // 'side' or 'blend'
  const [blendOpacity, setBlendOpacity] = useState(55);

  if (!visualizations) return null;

  return (
    <div>
      <div className="xai-section-title">
        <span>🔬 Grad-CAM Visual Attribution</span>
        <div className="xai-view-switcher">
          <button
            className={`xai-mode-btn ${viewMode === 'side' ? 'active' : ''}`}
            onClick={() => setViewMode('side')}
          >
            Side-by-Side
          </button>
          <button
            className={`xai-mode-btn ${viewMode === 'blend' ? 'active' : ''}`}
            onClick={() => setViewMode('blend')}
          >
            Interactive Blend
          </button>
        </div>
      </div>

      {viewMode === 'side' ? (
        <div className="xai-grid-side">
          <div className="xai-card">
            <img src={visualizations.original} className="xai-img" alt="Input Specimen" />
            <div className="xai-caption">Input Specimen</div>
          </div>
          <div className="xai-card">
            <img src={visualizations.heatmap} className="xai-img" alt="Grad-CAM Heatmap" />
            <div className="xai-caption">Grad-CAM Heatmap (Jet)</div>
          </div>
          <div className="xai-card">
            <img src={visualizations.overlay} className="xai-img" alt="Attribution Overlay" />
            <div className="xai-caption">Attribution Overlay</div>
          </div>
        </div>
      ) : (
        <div>
          <div className="xai-blend-container">
            <img src={visualizations.original} className="xai-blend-original" alt="Base Specimen" />
            <img
              src={visualizations.heatmap}
              className="xai-blend-heatmap"
              alt="Heatmap Layer"
              style={{ opacity: blendOpacity / 100 }}
            />
          </div>
          <div className="blend-slider-box">
            <div className="control-header">
              <span>Heatmap Blend Opacity</span>
              <span className="threshold-val">{blendOpacity}%</span>
            </div>
            <input
              type="range"
              className="range-slider"
              min="0"
              max="100"
              value={blendOpacity}
              onChange={(e) => setBlendOpacity(Number(e.target.value))}
            />
          </div>
        </div>
      )}
    </div>
  );
}
