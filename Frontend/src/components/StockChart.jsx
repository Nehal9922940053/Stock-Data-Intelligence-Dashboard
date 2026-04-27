

import { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';
import axios from 'axios';
Chart.register(...registerables);

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CHART_OPTIONS = {
  responsive: true, maintainAspectRatio: false,
  animation: { duration: 600, easing: 'easeInOutQuart' },
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: {
      display: true, position: 'top', align: 'end',
      labels: { color: '#7a90b0', font: { family: 'Space Mono', size: 10 }, boxWidth: 12, boxHeight: 2, padding: 16, usePointStyle: true, pointStyle: 'line' }
    },
    tooltip: {
      backgroundColor: '#0d1526', borderColor: 'rgba(0,210,168,0.3)', borderWidth: 1,
      titleColor: '#7a90b0', bodyColor: '#e8edf5',
      titleFont: { family: 'Space Mono', size: 10 }, bodyFont: { family: 'Space Mono', size: 12 }, padding: 12,
      callbacks: { label: ctx => ` ₹${ctx.parsed.y?.toFixed(2)}` }
    }
  },
  scales: {
    x: { grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false }, ticks: { color: '#3d5070', font: { family: 'Space Mono', size: 9 }, maxTicksLimit: 8, maxRotation: 0 }, border: { display: false } },
    y: { grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false }, ticks: { color: '#3d5070', font: { family: 'Space Mono', size: 9 }, callback: v => `₹${v}`, maxTicksLimit: 6 }, border: { display: false } }
  }
};

export default function StockChart({ symbol }) {
  const [chartData, setChartData] = useState(null);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    setChartData(null);
    axios.get(`${API}/data/${symbol}?days=${period}`).then(res => {
      const data = res.data;
      setChartData({
        labels: data.map(d => d.date.slice(5)),
        datasets: [
          { label: `${symbol} Close`, data: data.map(d => d.close), borderColor: '#00d2a8', backgroundColor: 'rgba(0,210,168,0.06)', borderWidth: 2, pointRadius: 0, pointHoverRadius: 5, fill: true, tension: 0.3, yAxisID: 'y' },
          { label: '7-day MA', data: data.map(d => d.ma_7d), borderColor: '#f59e0b', backgroundColor: 'transparent', borderWidth: 1.5, borderDash: [4, 4], pointRadius: 0, fill: false, tension: 0.3, yAxisID: 'y' }
        ]
      });
    });
  }, [symbol, period]);

  return (
    <div className="chart-container">
      <div className="chart-toolbar">
        <div><div className="chart-symbol">{symbol}</div><div className="chart-legend">Close Price · 7-day Moving Average</div></div>
        <div className="period-selector">
          {[7, 30, 90].map(p => <button key={p} onClick={() => setPeriod(p)} className={period === p ? 'active' : ''}>{p}D</button>)}
        </div>
      </div>
      <div className="chart-wrapper">
        {chartData ? <Line data={chartData} options={CHART_OPTIONS} /> : <div style={{ height: '100%', background: 'var(--bg-elevated)', borderRadius: 8 }} className="loading-skeleton" />}
      </div>
    </div>
  );
}