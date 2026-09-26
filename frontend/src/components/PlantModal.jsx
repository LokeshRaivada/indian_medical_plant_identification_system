import React, { useState, useEffect } from 'react';

export default function PlantModal({ plantId, onClose }) {
  const [plant, setPlant] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!plantId) return;
    setLoading(true);
    fetch(`/api/plants/${plantId}`)
      .then((res) => res.json())
      .then((data) => {
        setPlant(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load plant:', err);
        setLoading(false);
      });
  }, [plantId]);

  if (!plantId) return null;

  const ayur = plant?.ayurvedic_properties || {};

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-dialog">
        <button className="btn-close-modal" onClick={onClose}>✕</button>

        {loading || !plant ? (
          <p style={{ textAlign: 'center', padding: '40px' }}>Loading botanical monograph...</p>
        ) : (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <h2 style={{ fontSize: '22px', fontWeight: 800, fontStyle: 'italic', color: 'var(--accent-emerald-light)' }}>
                    {plant.botanical_name}
                  </h2>
                  {plant.habit && (
                    <span className="mono-tag" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                      🌿 {plant.habit}
                    </span>
                  )}
                  {plant.id && (
                    <span className="mono-tag" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                      IMPR #{plant.id}
                    </span>
                  )}
                </div>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Family: <strong>{plant.family}</strong> • Sanskrit: <strong style={{ color: 'var(--accent-emerald-light)' }}>{plant.sanskrit_name || plant.common_names?.sanskrit || 'N/A'}</strong> • English: <strong>{plant.common_name_en || plant.common_names?.english || 'N/A'}</strong>
                </p>
              </div>

              {plant.dosage && (
                <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '8px', padding: '6px 12px', textAlign: 'right' }}>
                  <div style={{ fontSize: '10px', textTransform: 'uppercase', color: '#fbbf24', letterSpacing: '0.5px', fontWeight: 600 }}>Prescribed Dosage</div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#fef3c7' }}>{plant.dosage}</div>
                </div>
              )}
            </div>

            {/* Ayurvedic Dravyaguna Pharmacology */}
            <div style={{ marginBottom: '14px', marginTop: '12px' }}>
              <p className="mono-prop-title">Ayurvedic Pharmacology (Dravyaguna)</p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px', marginTop: '6px' }}>
                <div style={{ background: 'var(--bg-card-secondary, rgba(255,255,255,0.03))', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border-color, rgba(255,255,255,0.06))' }}>
                  <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Rasa (Taste)</div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>{ayur.rasa || 'N/A'}</div>
                </div>
                <div style={{ background: 'var(--bg-card-secondary, rgba(255,255,255,0.03))', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border-color, rgba(255,255,255,0.06))' }}>
                  <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Guna (Qualities)</div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>{ayur.guna || 'N/A'}</div>
                </div>
                <div style={{ background: 'var(--bg-card-secondary, rgba(255,255,255,0.03))', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border-color, rgba(255,255,255,0.06))' }}>
                  <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Virya (Potency)</div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: (ayur.virya || '').toLowerCase().includes('hot') ? '#f87171' : '#60a5fa' }}>
                    {(ayur.virya || '').toLowerCase().includes('hot') ? '🔥 ' : '❄️ '}
                    {ayur.virya || 'N/A'}
                  </div>
                </div>
                <div style={{ background: 'var(--bg-card-secondary, rgba(255,255,255,0.03))', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border-color, rgba(255,255,255,0.06))' }}>
                  <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Vipaka (Digestive)</div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>{ayur.vipaka || 'N/A'}</div>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <p className="mono-prop-title">Therapeutic Indications (IMPR-100)</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                {(plant.therapeutic_indications || []).map((ind, i) => (
                  <span key={i} className="rationale-tag" style={{ fontSize: '11px', padding: '3px 8px' }}>
                    ✓ {ind}
                  </span>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <p className="mono-prop-title">Parts Used</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                {(plant.parts_used || []).map((part, i) => (
                  <span key={i} className="mono-tag">🍃 {part}</span>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <p className="mono-prop-title">Phytochemical Profile</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                {(plant.active_phytochemicals || []).map((ch, i) => (
                  <span key={i} className="mono-tag">🧪 {ch}</span>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <p className="mono-prop-title">Medicinal Properties & Pharmacology</p>
              <p style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: '1.6' }}>{plant.medicinal_uses}</p>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <p className="mono-prop-title">Classical Formulations & Clinical Dosage</p>
              <p style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{plant.dosage_and_formulation}</p>
            </div>

            {plant.precautions && (
              <div className="alert-precaution" style={{ marginTop: '12px' }}>
                ⚠️ <strong>Safety Warning & Precautions:</strong> {plant.precautions}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
