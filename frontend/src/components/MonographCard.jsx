import React from 'react';

export default function MonographCard({ profile, botanicalName }) {
  if (!profile) return null;

  const cNames = profile.common_names || {};
  const ayur = profile.ayurvedic_properties || {};
  const sanskritName = profile.sanskrit_name || cNames.sanskrit || 'N/A';
  const englishName = profile.common_name_en || cNames.english || 'N/A';
  const hindiName = cNames.hindi || 'N/A';

  return (
    <div className="monograph-card">
      <div className="monograph-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <h3 className="mono-botanical">{profile.botanical_name || botanicalName}</h3>
            {profile.habit && (
              <span className="mono-tag" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                🌿 {profile.habit}
              </span>
            )}
            {profile.id && (
              <span className="mono-tag" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                IMPR #{profile.id}
              </span>
            )}
          </div>
          <p className="mono-family" style={{ marginTop: '4px' }}>
            Family: <strong>{profile.family || 'Botanical Family'}</strong> • Sanskrit: <strong style={{ color: 'var(--accent-emerald-light)' }}>{sanskritName}</strong>
          </p>
        </div>

        {profile.dosage && (
          <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '8px', padding: '6px 12px', textAlign: 'right' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#fbbf24', letterSpacing: '0.5px', fontWeight: 600 }}>Prescribed Dosage</div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#fef3c7' }}>{profile.dosage}</div>
          </div>
        )}
      </div>

      <div className="mono-grid" style={{ marginTop: '16px' }}>
        <div>
          <p className="mono-prop-title">Vernacular & Common Names</p>
          <p className="mono-prop-val">
            <strong>English:</strong> {englishName}<br />
            <strong>Sanskrit:</strong> {sanskritName}<br />
            <strong>Hindi / Regional:</strong> {hindiName}
          </p>
        </div>

        <div>
          <p className="mono-prop-title">Morphological Parts Used</p>
          <div className="tag-list" style={{ marginTop: '4px' }}>
            {(profile.parts_used || ['Whole Plant']).map((p, i) => (
              <span key={i} className="mono-tag">🍃 {p}</span>
            ))}
          </div>
        </div>

        <div style={{ gridColumn: 'span 2' }}>
          <p className="mono-prop-title">Ayurvedic Dravyaguna Pharmacology</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px', marginTop: '6px' }}>
            <div style={{ background: 'var(--bg-card-secondary, rgba(255,255,255,0.03))', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border-color, rgba(255,255,255,0.06))' }}>
              <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Rasa (Taste)</div>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>{ayur.rasa || 'Tikta, Katu'}</div>
            </div>
            <div style={{ background: 'var(--bg-card-secondary, rgba(255,255,255,0.03))', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border-color, rgba(255,255,255,0.06))' }}>
              <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Guna (Qualities)</div>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>{ayur.guna || 'Laghu, Ruksha'}</div>
            </div>
            <div style={{ background: 'var(--bg-card-secondary, rgba(255,255,255,0.03))', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border-color, rgba(255,255,255,0.06))' }}>
              <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Virya (Potency)</div>
              <div style={{ fontSize: '12px', fontWeight: 600, color: (ayur.virya || '').toLowerCase().includes('hot') ? '#f87171' : '#60a5fa' }}>
                {(ayur.virya || '').toLowerCase().includes('hot') ? '🔥 ' : '❄️ '}
                {ayur.virya || 'Ushna (Hot)'}
              </div>
            </div>
            <div style={{ background: 'var(--bg-card-secondary, rgba(255,255,255,0.03))', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border-color, rgba(255,255,255,0.06))' }}>
              <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Vipaka (Post-Digestive)</div>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>{ayur.vipaka || 'Katu (Pungent)'}</div>
            </div>
          </div>
          {ayur.dosha_karma && (
            <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--accent-emerald-light)' }}>
              ⚡ <strong>Dosha Karma:</strong> {ayur.dosha_karma}
            </div>
          )}
        </div>

        <div style={{ gridColumn: 'span 2' }}>
          <p className="mono-prop-title">Therapeutic Indications (IMPR-100 Ground Truth)</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
            {(profile.therapeutic_indications || []).map((ind, i) => (
              <span key={i} className="rationale-tag" style={{ fontSize: '11px', padding: '3px 8px' }}>
                ✓ {ind}
              </span>
            ))}
          </div>
        </div>

        <div style={{ gridColumn: 'span 2' }}>
          <p className="mono-prop-title">Active Phytochemical Constituents</p>
          <div className="tag-list" style={{ marginTop: '4px' }}>
            {(profile.active_phytochemicals || ['Alkaloids', 'Flavonoids']).map((c, i) => (
              <span key={i} className="mono-tag">🧪 {c}</span>
            ))}
          </div>
        </div>
      </div>

      <div style={{ marginTop: '14px' }}>
        <p className="mono-prop-title">Therapeutic Actions & Uses</p>
        <p className="mono-prop-val" style={{ marginBottom: '10px' }}>
          {profile.medicinal_uses || 'Widely used in traditional Indian medicine.'}
        </p>
      </div>

      <div>
        <p className="mono-prop-title">Classical Formulations & Clinical Dosage</p>
        <p className="mono-prop-val">
          {profile.dosage_and_formulation || 'Standard powder (Churna) or decoction (Kwatha).'}
        </p>
      </div>

      {profile.precautions && (
        <div className="alert-precaution" style={{ marginTop: '12px' }}>
          ⚠️ <strong>Contraindications & Safety:</strong> {profile.precautions}
        </div>
      )}

      <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
        <button
          className="sample-pill-btn"
          onClick={() => window.print()}
          style={{ padding: '8px 16px', fontSize: '12px' }}
        >
          🖨️ Export Identification Report
        </button>
      </div>
    </div>
  );
}
