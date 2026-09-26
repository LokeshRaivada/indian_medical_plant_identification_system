import React from 'react';

export default function ConfidenceGauge({ confidence, status, isConfident, botanicalName, commonNames, explanation, warning }) {
  const percent = Math.round(confidence * 100);
  const circumference = 2 * Math.PI * 30; // ~188.5
  const offset = circumference - (percent / 100) * circumference;

  const names = commonNames || {};
  const commonStr = `${names.english || ''} ${names.hindi ? `• ${names.hindi}` : ''} ${names.sanskrit ? `(${names.sanskrit})` : ''}`;

  return (
    <div className={`status-banner ${isConfident ? 'confident' : 'uncertain'}`}>
      <div className="confidence-radial">
        <svg>
          <circle className="radial-bg" cx="37" cy="37" r="30"></circle>
          <circle
            className={`radial-progress ${isConfident ? '' : 'uncertain'}`}
            cx="37"
            cy="37"
            r="30"
            style={{ strokeDashoffset: offset }}
          ></circle>
        </svg>
        <div className="radial-text">{percent}%</div>
      </div>

      <div className="status-info-col">
        <h3>
          <span>{botanicalName}</span>
          <span className={`status-badge ${isConfident ? 'confident' : 'uncertain'}`}>{status}</span>
        </h3>
        {commonStr.trim() && (
          <p style={{ fontSize: '14px', color: 'var(--accent-emerald-light)', fontWeight: 500, marginBottom: '4px' }}>
            {commonStr}
          </p>
        )}
        <p className="status-desc">{explanation}</p>
        {warning && (
          <div className="warning-alert">
            ⚠️ <strong>Safety Advisory:</strong> {warning}
          </div>
        )}
      </div>
    </div>
  );
}
