

import { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CMP_OPTIONS = {
  responsive: true, maintainAspectRatio: false, animation: { duration: 700 },
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: true, position: 'top', align: 'end', labels: { color: '#7a90b0', font: { family: 'Space Mono', size: 10 }, boxWidth: 12, boxHeight: 2, usePointStyle: true, pointStyle: 'line', padding: 16 } },
    tooltip: { backgroundColor: '#0d1526', borderColor: 'rgba(0,210,168,0.3)', borderWidth: 1, titleColor: '#7a90b0', bodyColor: '#e8edf5', titleFont: { family: 'Space Mono', size: 10 }, bodyFont: { family: 'Space Mono', size: 12 }, padding: 12, callbacks: { label: ctx => ` ₹${ctx.parsed.y?.toFixed(2)}` } }
  },
  scales: {
    x: { grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false }, ticks: { color: '#3d5070', font: { family: 'Space Mono', size: 9 }, maxTicksLimit: 8, maxRotation: 0 }, border: { display: false } },
    y: { grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false }, ticks: { color: '#3d5070', font: { family: 'Space Mono', size: 9 }, callback: v => `₹${v}`, maxTicksLimit: 6 }, border: { display: false } }
  }
};

export default function ComparisonChart({ symbol1, symbol2 }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    setData(null);
    axios.get(`${API}/compare?symbol1=${symbol1}&symbol2=${symbol2}`).then(res => {
      const d = res.data;
      setData({
        labels: d.dates.map(dt => dt.slice(5)),
        datasets: [
          { label: symbol1, data: d.symbol1, borderColor: '#00d2a8', backgroundColor: 'rgba(0,210,168,0.05)', borderWidth: 2, pointRadius: 0, pointHoverRadius: 5, fill: true, tension: 0.3 },
          { label: symbol2, data: d.symbol2, borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.05)', borderWidth: 2, pointRadius: 0, pointHoverRadius: 5, fill: true, tension: 0.3 }
        ]
      });
    });
  }, [symbol1, symbol2]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1rem', fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 700 }}>
        <span style={{ color: '#00d2a8' }}>{symbol1}</span>
        <span style={{ color: 'var(--text-muted)' }}>vs</span>
        <span style={{ color: '#3b82f6' }}>{symbol2}</span>
      </div>
      <div style={{ height: 320 }}>
        {data ? <Line data={data} options={CMP_OPTIONS} /> : <div className="loading-skeleton" style={{ height: '100%', borderRadius: 8 }} />}
      </div>
    </div>
  );
}