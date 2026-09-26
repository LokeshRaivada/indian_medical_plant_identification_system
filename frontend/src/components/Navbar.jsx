import React from 'react';

export default function Navbar({ gpuDevice }) {
  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon">🌿</div>
        <div>
          <h1 className="brand-title">Medicinal Plant AI & XAI Hub</h1>
          <p className="brand-subtitle">
            React.js • Flask • PyTorch Deep Learning • Grad-CAM Explainable AI • Ayurvedic Recommender
          </p>
        </div>
      </div>
      <div className="system-status-pills">
        <div className="status-pill">
          <span className="status-dot"></span>
          <span>{gpuDevice ? `${gpuDevice} • Online` : 'CUDA RTX 3050 Online'}</span>
        </div>
        <div className="status-pill">
          <span>📚 93 Medicinal Species</span>
        </div>
      </div>
    </header>
  );
}
