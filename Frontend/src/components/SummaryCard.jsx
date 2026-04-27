

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function SummaryCard({ symbol }) {
  const [summary, setSummary] = useState(null);
  const [live, setLive]       = useState(null);
  const [liveAge, setLiveAge] = useState(0);   
  const intervalRef = useRef(null);

  // Fetch 52-week summary (historical)
  useEffect(() => {
    setSummary(null);
    setLive(null);
    axios.get(`${API}/summary/${symbol}`).then(res => setSummary(res.data));
  }, [symbol]);

  // Fetch live quote every 60 seconds
  useEffect(() => {
    const fetchLive = () => {
      axios.get(`${API}/live/${symbol}`)
        .then(res => { setLive(res.data); setLiveAge(0); })
        .catch(() => {});
    };
    fetchLive();
    intervalRef.current = setInterval(fetchLive, 60_000);

    // Tick age counter every second
    const ageTick = setInterval(() => setLiveAge(a => a + 1), 1000);
    return () => {
      clearInterval(intervalRef.current);
      clearInterval(ageTick);
    };
  }, [symbol]);

  if (!summary) return (
    <div className="summary-card">
      <div style={{ height: '80px', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div className="loading-skeleton" style={{ width: 120, height: 28 }} />
        <div className="loading-skeleton" style={{ width: 80, height: 14 }} />
      </div>
      <div className="summary-stats">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="loading-skeleton" style={{ height: 70 }} />
        ))}
      </div>
    </div>
  );

  const changeFromHigh = (((summary.last_close - summary.high_52w) / summary.high_52w) * 100).toFixed(1);

  // Prefer live price if available
  const displayPrice  = live?.last_price  ?? summary.last_close;
  const displayChange = live?.change_pct  ?? null;
  const isUp          = live ? live.change_pct >= 0 : changeFromHigh >= 0;

  const volPct = summary.volatility ? (summary.volatility * 100).toFixed(1) : null;
  const volColor = summary.volatility < 0.2 ? 'var(--positive)' : summary.volatility < 0.4 ? 'var(--amber)' : 'var(--negative)';

  return (
    <div className="summary-card">
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
        <div className="summary-ticker">{symbol}</div>
        {live && (
          <div style={{
            fontSize: '0.6rem', fontFamily: 'var(--font-mono)', color: 'var(--accent)',
            background: 'var(--accent-dim)', border: '1px solid var(--border-bright)',
            borderRadius: 20, padding: '3px 9px', letterSpacing: '0.08em',
          }}>
            ● LIVE · {liveAge < 60 ? `${liveAge}s ago` : 'refreshing…'}
          </div>
        )}
      </div>

      {/* Price + change */}
      <div className="summary-label">
        {live?.exchange ?? 'NSE'}&nbsp;·&nbsp;
        <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.92rem', fontWeight: 700 }}>
          ₹{displayPrice.toFixed(2)}
        </span>
        &nbsp;&nbsp;
        {displayChange !== null ? (
          <span style={{ color: isUp ? 'var(--positive)' : 'var(--negative)', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
            {isUp ? '▲' : '▼'} {Math.abs(displayChange).toFixed(2)}% today
          </span>
        ) : (
          <span style={{ color: changeFromHigh >= 0 ? 'var(--positive)' : 'var(--negative)', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
            {changeFromHigh >= 0 ? '▲' : '▼'} {Math.abs(changeFromHigh)}% from 52W High
          </span>
        )}
      </div>

      {/* Stat grid */}
      <div className="summary-stats">
        <div>
          <span>52W High</span>
          <strong>₹{summary.high_52w.toFixed(2)}</strong>
        </div>
        <div>
          <span>52W Low</span>
          <strong>₹{summary.low_52w.toFixed(2)}</strong>
        </div>
        <div>
          <span>Avg Close</span>
          <strong>₹{summary.avg_close.toFixed(2)}</strong>
        </div>
        <div>
          <span>Live Price</span>
          <strong style={{ color: 'var(--accent)' }}>
            {live ? `₹${live.last_price.toFixed(2)}` : '—'}
          </strong>
        </div>
        {volPct && (
          <div>
            <span>Volatility</span>
            <strong style={{ color: volColor }}>{volPct}%</strong>
          </div>
        )}
        {live?.volume ? (
          <div>
            <span>Volume</span>
            <strong style={{ fontSize: '0.85rem' }}>{(live.volume / 1e5).toFixed(1)}L</strong>
          </div>
        ) : null}
      </div>
    </div>
  );
}