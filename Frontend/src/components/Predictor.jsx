

import { useState } from 'react';
import { Line } from 'react-chartjs-2';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const PRED_OPTIONS = {
  responsive: true, maintainAspectRatio: false, animation: { duration: 800, easing: 'easeOutQuart' },
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: { backgroundColor: '#0d1526', borderColor: 'rgba(153,102,255,0.3)', borderWidth: 1, titleColor: '#7a90b0', bodyColor: '#e8edf5', titleFont: { family: 'Space Mono', size: 10 }, bodyFont: { family: 'Space Mono', size: 12 }, padding: 12, callbacks: { label: ctx => ` ₹${ctx.parsed.y?.toFixed(2)} (forecast)` } }
  },
  scales: {
    x: { grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false }, ticks: { color: '#3d5070', font: { family: 'Space Mono', size: 9 }, maxRotation: 0 }, border: { display: false } },
    y: { grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false }, ticks: { color: '#3d5070', font: { family: 'Space Mono', size: 9 }, callback: v => `₹${v}`, maxTicksLimit: 5 }, border: { display: false } }
  }
};

export default function Predictor({ symbol }) {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);

  const predict = () => {
    setLoading(true);
    setForecast(null);
    axios.get(`${API}/predict/${symbol}`).then(res => {
      const pred = res.data.forecast;
      const lastDate = new Date();
      const labels = [];
      for (let i = 1; i <= pred.length; i++) {
        let d = new Date(lastDate);
        d.setDate(lastDate.getDate() + i);
        labels.push(d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }));
      }
      setForecast({ labels, data: pred });
      setLoading(false);
    });
  };

  return (
    <div className="predictor-card">
      <div className="predictor-header">
        <div className="predictor-title">
          <span>🔮</span> Price Prediction
          <span className="predictor-badge">7-day Forecast</span>
        </div>
        <button className="predict-btn" onClick={predict} disabled={loading}>
          {loading ? '⟳ Computing...' : '→ Run Prediction'}
        </button>
      </div>
      {forecast && (
        <div className="predictor-chart-wrapper">
          <Line data={{ labels: forecast.labels, datasets: [{ label: `${symbol} Forecast`, data: forecast.data, borderColor: '#a855f7', backgroundColor: 'rgba(168,85,247,0.08)', borderWidth: 2, borderDash: [6, 3], pointRadius: 4, pointBackgroundColor: '#a855f7', pointBorderColor: '#0d1526', pointBorderWidth: 2, fill: true, tension: 0.4 }] }} options={PRED_OPTIONS} />
        </div>
      )}
      {!forecast && !loading && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.8rem', fontStyle: 'italic' }}>
          Click "Run Prediction" to generate a 7-day price forecast using ML
        </div>
      )}
    </div>
  );
}