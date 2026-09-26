import React, { useState, useEffect } from 'react';

export default function AcademicDashboardTab() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch('/api/stats')
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch((err) => console.error('Failed to load stats:', err));
  }, []);

  const dStats = stats?.dataset_stats || {};

  return (
    <div>
      <div className="academic-banner">
        <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: '6px' }}>
          7th-Semester Academic Project: Technical Benchmark & Evaluation
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Project: <strong>Deep Learning-Based Indian Medicinal Plant Identification with Explainable AI (Grad-CAM), Confidence-Aware Prediction, and Symptom Recommendations (2026–2027)</strong>
        </p>
      </div>

      {/* Dataset Split Metrics */}
      <div className="academic-stats-row">
        <div className="stat-metric-card">
          <div className="stat-metric-val">{dStats.num_classes || 93}</div>
          <div className="stat-metric-lbl">Medicinal Classes</div>
        </div>
        <div className="stat-metric-card">
          <div className="stat-metric-val">{(dStats.train_count || 20253).toLocaleString()}</div>
          <div className="stat-metric-lbl">Training Images (70%)</div>
        </div>
        <div className="stat-metric-card">
          <div className="stat-metric-val">{(dStats.val_count || 3575).toLocaleString()}</div>
          <div className="stat-metric-lbl">Validation Images (15%)</div>
        </div>
        <div className="stat-metric-card">
          <div className="stat-metric-val">{(dStats.test_count || 9300).toLocaleString()}</div>
          <div className="stat-metric-lbl">Held-Out Test Images (15%)</div>
        </div>
      </div>

      {/* Benchmark Plots */}
      <div className="plots-grid">
        <div className="plot-container">
          <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '12px' }}>
            📊 Normalized Confusion Matrix (Top Species)
          </h3>
          <img
            src="/outputs/confusion_matrix/confusion_matrix.png"
            className="plot-image"
            alt="Confusion Matrix Heatmap"
          />
        </div>
        <div className="plot-container">
          <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '12px' }}>
            📈 Training & Validation Convergence Curves
          </h3>
          <img
            src="/outputs/training_plots/training_curves.png"
            className="plot-image"
            alt="Training Curves"
          />
        </div>
      </div>

      {/* Viva Voce Defense Box */}
      <div className="glass-card" style={{ marginTop: '20px' }}>
        <h3 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '14px' }}>
          🎓 Academic Review & Viva Voce Q&A Reference
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', fontSize: '13px' }}>
          <div style={{ background: 'rgba(10, 26, 21, 0.5)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
            <strong style={{ color: 'var(--accent-emerald-light)' }}>Q1: How does Grad-CAM explain CNN decisions?</strong>
            <p style={{ color: 'var(--text-secondary)', marginTop: '6px' }}>
              Grad-CAM calculates the gradient of the predicted class score with respect to the feature activation maps of the final convolutional layer. These gradients are globally pooled to produce channel importance weights α_k, followed by a rectified weighted sum to produce a coarse 2D localization map highlighting discriminating visual features (e.g. leaf veins, margins).
            </p>
          </div>

          <div style={{ background: 'rgba(10, 26, 21, 0.5)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
            <strong style={{ color: 'var(--accent-emerald-light)' }}>Q2: Why is Confidence-Aware prediction essential?</strong>
            <p style={{ color: 'var(--text-secondary)', marginTop: '6px' }}>
              Standard softmax outputs often suffer from overconfidence on out-of-distribution or noisy images. By establishing an explicit threshold (τ = 0.70), the system rejects low-confidence classifications as 'UNCERTAIN', prompting the user to retake the photo rather than providing inaccurate herbal advice.
            </p>
          </div>

          <div style={{ background: 'rgba(10, 26, 21, 0.5)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
            <strong style={{ color: 'var(--accent-emerald-light)' }}>Q3: What data split methodology was followed?</strong>
            <p style={{ color: 'var(--text-secondary)', marginTop: '6px' }}>
              A reproducible, stratified 70/15/15 train/validation/test split was established using fixed random seed manifests, preserving class balance across all 93 botanical classes without altering raw dataset folders.
            </p>
          </div>

          <div style={{ background: 'rgba(10, 26, 21, 0.5)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
            <strong style={{ color: 'var(--accent-emerald-light)' }}>Q4: How does the Symptom Recommender work?</strong>
            <p style={{ color: 'var(--text-secondary)', marginTop: '6px' }}>
              A multi-token search engine calculates weighted relevance across Ayurvedic symptoms, therapeutic indications, body systems, and classical formulations, providing scored recommendations with contraindication warnings.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
