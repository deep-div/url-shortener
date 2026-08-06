import { useState } from 'react';

export default function LocationChart({ countryData, cityData }) {
  const [tab, setTab] = useState('country');
  const data = tab === 'country' ? countryData : cityData;

  if ((!countryData || Object.keys(countryData).length === 0) &&
      (!cityData || Object.keys(cityData).length === 0)) return null;

  const sorted = data ? Object.entries(data).sort((a, b) => b[1] - a[1]) : [];

  return (
    <div className="donut-card location-card">
      <div className="location-tabs">
        <button
          className={`location-tab${tab === 'country' ? ' active' : ''}`}
          onClick={() => setTab('country')}
        >
          Countries
        </button>
        <button
          className={`location-tab${tab === 'city' ? ' active' : ''}`}
          onClick={() => setTab('city')}
        >
          Cities
        </button>
      </div>

      <div className="donut-list-header">
        <span>{tab === 'country' ? 'Country' : 'City'}</span>
        <span>Clicks</span>
      </div>
      <div className="donut-list">
        {sorted.map(([name, value]) => (
          <div key={name} className="donut-list-row">
            <span className="donut-list-name">{name || 'Unknown'}</span>
            <span className="donut-list-count">{value.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

