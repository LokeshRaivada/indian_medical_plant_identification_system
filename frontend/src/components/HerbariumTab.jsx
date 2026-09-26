import React, { useState, useEffect } from 'react';

export default function HerbariumTab({ onSelectPlant }) {
  const [plants, setPlants] = useState([]);
  const [search, setSearch] = useState('');
  const [system, setSystem] = useState('');
  const [habit, setHabit] = useState('');
  const [potency, setPotency] = useState('');

  useEffect(() => {
    fetch('/api/plants')
      .then((res) => res.json())
      .then((data) => setPlants(data.plants || []))
      .catch((err) => console.error('Failed to load plants:', err));
  }, []);

  const filteredPlants = plants.filter((p) => {
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      p.botanical_name.toLowerCase().includes(q) ||
      (p.common_name_en && p.common_name_en.toLowerCase().includes(q)) ||
      (p.common_name_hi && p.common_name_hi.toLowerCase().includes(q)) ||
      (p.common_name_sa && p.common_name_sa.toLowerCase().includes(q)) ||
      (p.sanskrit_name && p.sanskrit_name.toLowerCase().includes(q)) ||
      (p.family && p.family.toLowerCase().includes(q));

    const matchesSystem =
      !system ||
      (p.systems || []).some((s) => s.toLowerCase().includes(system.toLowerCase()));

    const matchesHabit =
      !habit ||
      (p.habit && p.habit.toLowerCase().includes(habit.toLowerCase()));

    const matchesPotency =
      !potency ||
      (p.potency && p.potency.toLowerCase().includes(potency.toLowerCase()));

    return matchesSearch && matchesSystem && matchesHabit && matchesPotency;
  });

  return (
    <div>
      <div className="herbarium-toolbar" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
        <input
          type="text"
          className="herb-search"
          placeholder="Search Sanskrit, Latin, English..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ gridColumn: 'span 2' }}
        />
        <select
          className="herb-filter-select"
          value={habit}
          onChange={(e) => setHabit(e.target.value)}
        >
          <option value="">All Plant Habits</option>
          <option value="Tree">Trees</option>
          <option value="Shrub">Shrubs</option>
          <option value="Climber">Climbers</option>
          <option value="Creeper">Creepers</option>
          <option value="Herb">Herbs / Grass</option>
        </select>
        <select
          className="herb-filter-select"
          value={potency}
          onChange={(e) => setPotency(e.target.value)}
        >
          <option value="">All Potencies (Virya)</option>
          <option value="Hot">🔥 Hot (Ushna)</option>
          <option value="Cold">❄️ Cold (Sheeta)</option>
          <option value="Warm">⚡ Warm (Anushna)</option>
        </select>
        <select
          className="herb-filter-select"
          value={system}
          onChange={(e) => setSystem(e.target.value)}
        >
          <option value="">All Body Systems</option>
          <option value="respiratory">Respiratory System</option>
          <option value="musculoskeletal">Musculoskeletal System</option>
          <option value="nervous">Nervous System</option>
          <option value="digestive">Digestive System</option>
          <option value="cardiovascular">Cardiovascular System</option>
          <option value="urinary">Urinary / Kidney</option>
          <option value="integumentary">Skin (Integumentary)</option>
          <option value="endocrine">Endocrine / Metabolism</option>
        </select>
      </div>

      <div style={{ margin: '14px 0 10px', fontSize: '13px', color: 'var(--text-secondary)' }}>
        Displaying <strong>{filteredPlants.length}</strong> of {plants.length} authentic Indian Medicinal Plant species (IMPR-100 Benchmark)
      </div>

      <div className="herb-grid">
        {filteredPlants.map((p) => {
          const isHot = (p.potency || '').toLowerCase().includes('hot');
          return (
            <div
              key={p.id}
              className="herb-item-card"
              onClick={() => onSelectPlant(p.id)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '4px' }}>
                <div className="herb-item-botanical">{p.botanical_name}</div>
                {p.potency && (
                  <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: isHot ? 'rgba(239,68,68,0.15)' : 'rgba(59,130,246,0.15)', color: isHot ? '#f87171' : '#60a5fa', fontWeight: 600 }}>
                    {isHot ? '🔥 Ushna' : '❄️ Sheeta'}
                  </span>
                )}
              </div>

              <div className="herb-item-names" style={{ color: 'var(--accent-emerald-light)', fontWeight: 600, marginTop: '2px' }}>
                {p.sanskrit_name || p.common_name_sa || p.common_name_hi}
                <span style={{ color: 'var(--text-secondary)', fontWeight: 400, fontSize: '12px' }}>
                  {' '}({p.common_name_en || 'Medicinal'})
                </span>
              </div>

              <div className="herb-item-family" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '6px' }}>
                <span>{p.family}</span>
                {p.habit && <span style={{ color: '#34d399' }}>• {p.habit}</span>}
              </div>

              {p.dosage && (
                <div style={{ marginTop: '6px', fontSize: '11px', color: '#fbbf24' }}>
                  Dosage: <strong>{p.dosage}</strong>
                </div>
              )}

              {p.indications && p.indications.length > 0 && (
                <div style={{ marginTop: '6px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {p.indications.slice(0, 2).map((ind, idx) => (
                    <span key={idx} style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' }}>
                      {ind}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
