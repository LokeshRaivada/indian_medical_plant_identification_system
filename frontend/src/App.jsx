import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import IdentificationTab from './components/IdentificationTab';
import RecommenderTab from './components/RecommenderTab';
import HerbariumTab from './components/HerbariumTab';
import AcademicDashboardTab from './components/AcademicDashboardTab';
import PlantModal from './components/PlantModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('identify');
  const [gpuDevice, setGpuDevice] = useState(null);
  const [selectedPlantId, setSelectedPlantId] = useState(null);

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => {
        if (data.device) setGpuDevice(data.device);
      })
      .catch((err) => console.warn('Health check error:', err));
  }, []);

  return (
    <div className="app-container">
      <Navbar gpuDevice={gpuDevice} />

      {/* Navigation Tabs */}
      <nav className="nav-tabs" role="tablist">
        <button
          className={`nav-tab-btn ${activeTab === 'identify' ? 'active' : ''}`}
          onClick={() => setActiveTab('identify')}
        >
          <span>🔍</span> Plant Identification & XAI
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'recommender' ? 'active' : ''}`}
          onClick={() => setActiveTab('recommender')}
        >
          <span>💊</span> Symptom & Disease Recommender
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'herbarium' ? 'active' : ''}`}
          onClick={() => setActiveTab('herbarium')}
        >
          <span>📖</span> 93-Species Herbarium
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'academic' ? 'active' : ''}`}
          onClick={() => setActiveTab('academic')}
        >
          <span>📊</span> Model Evaluation & XAI Dashboard
        </button>
      </nav>

      {/* Active Tab Panel */}
      {activeTab === 'identify' && <IdentificationTab />}
      {activeTab === 'recommender' && <RecommenderTab onSelectPlant={(id) => setSelectedPlantId(id)} />}
      {activeTab === 'herbarium' && <HerbariumTab onSelectPlant={(id) => setSelectedPlantId(id)} />}
      {activeTab === 'academic' && <AcademicDashboardTab />}

      {/* Modal Drawer */}
      {selectedPlantId && (
        <PlantModal
          plantId={selectedPlantId}
          onClose={() => setSelectedPlantId(null)}
        />
      )}
    </div>
  );
}
