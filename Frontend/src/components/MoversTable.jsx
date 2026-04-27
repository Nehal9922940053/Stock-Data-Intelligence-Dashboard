
import { useState, useEffect } from 'react';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function MoversTable() {
  const [movers, setMovers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/movers?n=5`).then(res => {
      setMovers(res.data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="movers-table">
      <div className="movers-header">
        <span className="movers-header-icon">⬆⬇</span>
        Top Gainers &amp; Losers
      </div>
      <table>
        <thead>
          <tr><th>Symbol</th><th>Change</th><th>Last Price</th><th style={{ textAlign: 'right' }}>Signal</th></tr>
        </thead>
        <tbody>
          {loading
            ? [...Array(5)].map((_, i) => (
                <tr key={i}>
                  <td><div className="loading-skeleton" style={{ width: 80, height: 14 }} /></td>
                  <td><div className="loading-skeleton" style={{ width: 60, height: 14 }} /></td>
                  <td><div className="loading-skeleton" style={{ width: 70, height: 14 }} /></td>
                  <td><div className="loading-skeleton" style={{ width: 50, height: 14, marginLeft: 'auto' }} /></td>
                </tr>
              ))
            : movers.map(m => (
                <tr key={m.symbol} className={m.change_pct >= 0 ? 'positive' : 'negative'}>
                  <td>{m.symbol}</td>
                  <td><span className="change-pill">{m.change_pct >= 0 ? '▲' : '▼'} {Math.abs(m.change_pct)}%</span></td>
                  <td>₹{m.last_price}</td>
                  <td style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'var(--font-mono)', color: m.change_pct >= 0 ? 'var(--positive)' : 'var(--negative)', opacity: 0.7 }}>
                      {m.change_pct >= 0 ? 'BUY' : 'SELL'}
                    </span>
                  </td>
                </tr>
              ))
          }
        </tbody>
      </table>
    </div>
  );
}