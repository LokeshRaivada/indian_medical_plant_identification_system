import React, { useState, useRef } from 'react';
import ConfidenceGauge from './ConfidenceGauge';
import GradCAMViewer from './GradCAMViewer';
import MonographCard from './MonographCard';

export default function IdentificationTab() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [threshold, setThreshold] = useState(70);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const sampleSpecimens = [
    { id: '12_Withania_somnifera', label: '🌱 Ashwagandha' },
    { id: '95_Ocimum_sanctum', label: '🌿 Tulsi' },
    { id: '38_Curcuma_longa', label: '🟡 Haridra' },
    { id: '100_Aconitum_ferox', label: '⚠️ Vatsanabha (Toxic Check)' },
    { id: '10_Calotropis_procera', label: '⚠️ Arka (Latex Caution)' },
    { id: '22_Bacopa_monnieri', label: '💧 Brahmi' },
  ];

  const handleFileChange = (file) => {
    if (!file || !file.type.startsWith('image/')) {
      alert('Please select a valid image file (JPG, PNG, WEBP).');
      return;
    }
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const clearImage = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const loadSample = async (classId) => {
    try {
      const res = await fetch(`/api/sample_image?class_id=${classId}`);
      if (res.ok) {
        const blob = await res.blob();
        const file = new File([blob], `${classId}.jpg`, { type: 'image/jpeg' });
        handleFileChange(file);
      }
    } catch (err) {
      console.error('Failed to load sample:', err);
    }
  };

  const runPrediction = async () => {
    if (!selectedFile) return;
    setLoading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('threshold', threshold / 100);

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Prediction failed');
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      alert(`Prediction failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const toxicCheck = result?.toxic_check || {};
  const confusedCheck = result?.confused_check || {};

  return (
    <div className="id-grid">
      {/* Left Column: Upload & Pipeline Controls */}
      <div className="glass-card">
        <div className="card-header">
          <h2 className="card-title"><span>📷</span> PATH 1: Image Input & Inference</h2>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Leaf / Whole Plant</span>
        </div>

        <input
          type="file"
          ref={fileInputRef}
          accept="image/*"
          style={{ display: 'none' }}
          onChange={(e) => e.target.files && handleFileChange(e.target.files[0])}
        />

        {!previewUrl ? (
          <div
            className={`upload-dropzone ${dragOver ? 'dragover' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <div className="upload-icon">🍃</div>
            <p className="upload-text-main">Drop plant image here or click to browse</p>
            <p className="upload-text-sub">Preprocessed: Auto-resized (224x224) + Normalized for CNN</p>
          </div>
        ) : (
          <div className="preview-container">
            <img src={previewUrl} className="preview-image" alt="Preview" />
            <button className="btn-remove-preview" onClick={clearImage} title="Remove image">✕</button>
          </div>
        )}

        <div className="sample-section">
          <p className="sample-title">Test Specimens (Benchmarked with IMPR-100)</p>
          <div className="sample-pills">
            {sampleSpecimens.map((s) => (
              <button key={s.id} className="sample-pill-btn" onClick={() => loadSample(s.id)}>
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <div className="control-group">
          <div className="control-header">
            <span>Confidence Check Threshold</span>
            <span className="threshold-val">{threshold}%</span>
          </div>
          <input
            type="range"
            className="range-slider"
            min="50"
            max="95"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
          />
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
            Top-1 confidence below {threshold}% flags an <strong>UNCERTAIN</strong> status requiring image verification.
          </p>
        </div>

        <button
          className="btn-primary"
          onClick={runPrediction}
          disabled={!selectedFile || loading}
        >
          {loading ? '⏳ Running CNN, Toxic Check & Grad-CAM...' : '🔬 Run Multi-Stage DL Identification'}
        </button>
      </div>

      {/* Right Column: Execution Pipeline & Final Output */}
      <div className="glass-card">
        {!result ? (
          <div className="empty-state">
            <div className="empty-state-icon">🌿</div>
            <h3 style={{ fontSize: '18px', marginBottom: '6px' }}>Awaiting Specimen Input</h3>
            <p style={{ fontSize: '13px', maxWidth: '380px' }}>
              Upload a botanical photo to execute the complete workflow: Custom CNN ➔ Softmax ➔ Toxic Top-K Check ➔ Confidence Check ➔ Confused-Class Check ➔ Grad-CAM XAI.
            </p>
          </div>
        ) : (
          <div>
            {/* Top Pipeline Breadcrumbs */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px', fontSize: '11px', color: 'var(--text-secondary)' }}>
              <span className="mono-tag" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>✓ Preprocessed</span>
              <span className="mono-tag" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}>✓ Custom CNN</span>
              <span className="mono-tag" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#a78bfa' }}>✓ Softmax Output</span>
              <span className="mono-tag" style={{ background: toxicCheck.toxic_found ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.15)', color: toxicCheck.toxic_found ? '#f87171' : '#34d399' }}>
                {toxicCheck.toxic_found ? '⚠️ Toxic Alert' : '✓ Safety Checked'}
              </span>
              <span className="mono-tag" style={{ background: result.is_confident ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.2)', color: result.is_confident ? '#34d399' : '#fbbf24' }}>
                {result.is_confident ? '✓ Confident' : '⚠️ Uncertain'}
              </span>
              <span className="mono-tag" style={{ background: 'rgba(236, 72, 153, 0.15)', color: '#f472b6' }}>✓ Grad-CAM</span>
            </div>

            {/* 1. TOXIC PLANT TOP-K CHECK (Architecture Diagram: Step 6) */}
            {toxicCheck.toxic_found ? (
              <div style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '10px', padding: '14px 16px', marginBottom: '18px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#f87171', fontWeight: 700, fontSize: '14px' }}>
                  <span style={{ fontSize: '20px' }}>🚨</span>
                  <span>SAFETY ALERT: Toxic Plant Found in Top-K Candidates! (Verify Before Use)</span>
                </div>
                <p style={{ fontSize: '12px', color: '#fca5a5', marginTop: '6px' }}>
                  {toxicCheck.alert_message}
                </p>
                <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {(toxicCheck.toxic_plants || []).map((tp, idx) => (
                    <div key={idx} style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 12px', borderRadius: '6px', fontSize: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#f87171', fontWeight: 600 }}>
                        <span>Rank #{tp.rank}: {tp.botanical_name} ({tp.sanskrit_name})</span>
                        <span style={{ fontSize: '11px', background: '#ef4444', color: '#fff', padding: '1px 6px', borderRadius: '4px' }}>{tp.severity}</span>
                      </div>
                      <div style={{ fontSize: '11px', color: '#fecaca', marginTop: '4px' }}>
                        ⚠️ <strong>Warning:</strong> {tp.clinical_warning}
                      </div>
                      <div style={{ fontSize: '11px', color: '#fed7aa', marginTop: '2px' }}>
                        🛡️ <strong>Safety Protocol:</strong> {tp.ayurvedic_safety}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '8px', padding: '10px 14px', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '18px' }}>🛡️</span>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#34d399' }}>Toxic Plant Top-K Check: PASSED</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>No toxic or poisonous species detected among model candidate predictions.</div>
                </div>
              </div>
            )}

            {/* 2. CONFIDENCE CHECK (Architecture Diagram: Step 7) */}
            <ConfidenceGauge
              confidence={result.confidence}
              status={result.status}
              isConfident={result.is_confident}
              botanicalName={result.botanical_name}
              commonNames={result.common_names}
              explanation={result.explanation}
              warning={result.warning}
            />

            {/* 3. CONFUSED-CLASS CHECK (Architecture Diagram: Step 8) */}
            {confusedCheck.is_confused && (
              <div style={{ background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.35)', borderRadius: '10px', padding: '14px', margin: '18px 0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#c4b5fd', fontWeight: 700, fontSize: '13px' }}>
                  <span>🔬</span>
                  <span>CONFUSED-CLASS CHECK: Top-1 & Top-2 Close ({confusedCheck.confidence_margin_percent}% Margin)</span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  {confusedCheck.differential_guidance}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '10px' }}>
                  <div style={{ background: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
                    <div style={{ fontSize: '11px', color: '#a78bfa', fontWeight: 700 }}>CANDIDATE 1 (Top-1)</div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>{confusedCheck.candidate_1.botanical_name}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{confusedCheck.candidate_1.sanskrit_name} • {confusedCheck.candidate_1.confidence_percent}%</div>
                    <div style={{ fontSize: '11px', marginTop: '4px' }}>Family: <strong>{confusedCheck.candidate_1.family}</strong></div>
                    <div style={{ fontSize: '11px' }}>Habit: <strong>{confusedCheck.candidate_1.habit}</strong></div>
                  </div>
                  <div style={{ background: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
                    <div style={{ fontSize: '11px', color: '#a78bfa', fontWeight: 700 }}>CANDIDATE 2 (Top-2)</div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>{confusedCheck.candidate_2.botanical_name}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{confusedCheck.candidate_2.sanskrit_name} • {confusedCheck.candidate_2.confidence_percent}%</div>
                    <div style={{ fontSize: '11px', marginTop: '4px' }}>Family: <strong>{confusedCheck.candidate_2.family}</strong></div>
                    <div style={{ fontSize: '11px' }}>Habit: <strong>{confusedCheck.candidate_2.habit}</strong></div>
                  </div>
                </div>
              </div>
            )}

            {/* 4. GRAD-CAM (Architecture Diagram: Step 10) */}
            <GradCAMViewer visualizations={result.visualizations} />

            {/* Top-5 Predictions */}
            {result.top_predictions && (
              <div className="candidates-box" style={{ marginTop: '20px' }}>
                <h4 style={{ fontSize: '13px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '12px', fontWeight: 700 }}>
                  Top-K Softmax Predictions
                </h4>
                {result.top_predictions.map((c, i) => (
                  <div key={i} className="candidate-row">
                    <div className="candidate-labels">
                      <span className="candidate-name">
                        #{i + 1} {c.botanical_name} {c.common_name ? `(${c.common_name})` : ''}
                      </span>
                      <span className="candidate-percent">{c.confidence_percent}%</span>
                    </div>
                    <div className="candidate-bar-bg">
                      <div className="candidate-bar-fill" style={{ width: `${c.confidence_percent}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* 5. FINAL OUTPUT BANNER (Architecture Diagram: Bottom Container) */}
            <div style={{ background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.15), rgba(147, 51, 234, 0.15))', border: '1px solid rgba(147, 51, 234, 0.35)', borderRadius: '12px', padding: '16px', margin: '22px 0 16px' }}>
              <div style={{ fontSize: '12px', textTransform: 'uppercase', color: '#c4b5fd', fontWeight: 800, letterSpacing: '0.8px', marginBottom: '10px' }}>
                🏁 Combined Final Output Summary
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '10px' }}>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>🍃 PREDICTED PLANT</div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#fff' }}>{result.botanical_name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--accent-emerald-light)' }}>{result.sanskrit_name}</div>
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>📊 CONFIDENCE / RESULTS</div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: result.is_confident ? '#34d399' : '#fbbf24' }}>
                    {result.confidence_percent}% ({result.status})
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>⚠️ SAFETY INFORMATION</div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: toxicCheck.toxic_found ? '#f87171' : '#34d399' }}>
                    {toxicCheck.toxic_found ? '🚨 Toxic Alert' : '✓ Safe Profile'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>🖼️ GRAD-CAM XAI</div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#60a5fa' }}>Features Highlighted</div>
                </div>
              </div>
            </div>

            {/* 6. PLANT KNOWLEDGE BASE (Step 11) */}
            <MonographCard profile={result.plant_profile} botanicalName={result.botanical_name} />
          </div>
        )}
      </div>
    </div>
  );
}
