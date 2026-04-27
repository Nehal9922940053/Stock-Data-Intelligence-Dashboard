

import { useState } from 'react';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function rColor(r) {
  if (r >= 0.7)  return '#00e68a';   // strong positive — green
  if (r >= 0.4)  return '#f59e0b';   // moderate positive — amber
  if (r >= -0.4) return '#7a90b0';   // weak / neutral — grey
  if (r >= -0.7) return '#f59e0b';   // moderate negative — amber
  return '#ff4d6d';                   // strong negative — red
}


function CorrelationGauge({ r }) {
  // Map r ∈ [-1, +1] to pct ∈ [0%, 100%]
  const pct = ((r + 1) / 2) * 100;
  const color = rColor(r);

  return (
    <div style={{ margin: '1rem 0 0.5rem' }}>
      {/* Scale labels */}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '4px' }}>
        <span>−1</span><span>−0.5</span><span>0</span><span>+0.5</span><span>+1</span>
      </div>
      {/* Track */}
      <div style={{ position: 'relative', height: 8, background: 'var(--bg-elevated)', borderRadius: 4, border: '1px solid var(--border)' }}>
        {/* Zero line */}
        <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: 'var(--text-muted)', opacity: 0.4 }} />
        {/* Marker */}
        <div style={{
          position: 'absolute',
          left: `calc(${pct}% - 6px)`,
          top: -4,
          width: 12,
          height: 16,
          background: color,
          borderRadius: 3,
          boxShadow: `0 0 8px ${color}60`,
          transition: 'left 0.6s ease',
        }} />
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function CorrelationCard({ companies }) {
  const [sym1, setSym1]       = useState('INFY');
  const [sym2, setSym2]       = useState('TCS');
  const [days, setDays]       = useState(90);
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const run = () => {
    if (!sym1 || !sym2 || sym1 === sym2) {
      setError('Select two different symbols.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    axios.get(`${API}/correlation?symbol1=${sym1}&symbol2=${sym2}&days=${days}`)
      .then(res => { setResult(res.data); setLoading(false); })
      .catch(err => {
        setError(err.response?.data?.detail || 'Request failed');
        setLoading(false);
      });
  };

  return (
    <div className="predictor-card">
      {/* Header */}
      <div className="predictor-header">
        <div className="predictor-title">
          <span>🔗</span> Correlation Analysis
          <span className="predictor-badge">Pearson r</span>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: '1rem' }}>
        <div className="compare-input-group">
          <span className="compare-input-label">Stock A</span>
          <select
            value={sym1}
            onChange={e => setSym1(e.target.value)}
            style={{ padding: '0.5rem 0.75rem', background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', cursor: 'pointer' }}
          >
            {(companies || []).map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="compare-input-group">
          <span className="compare-input-label">Stock B</span>
          <select
            value={sym2}
            onChange={e => setSym2(e.target.value)}
            style={{ padding: '0.5rem 0.75rem', background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', cursor: 'pointer' }}
          >
            {(companies || []).map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="compare-input-group">
          <span className="compare-input-label">Window</span>
          <select
            value={days}
            onChange={e => setDays(Number(e.target.value))}
            style={{ padding: '0.5rem 0.75rem', background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', cursor: 'pointer' }}
          >
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
            <option value={180}>180 days</option>
            <option value={252}>1 year</option>
          </select>
        </div>

        <button className="predict-btn" onClick={run} disabled={loading} style={{ alignSelf: 'flex-end' }}>
          {loading ? '⟳ Calculating...' : '→ Analyse'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ padding: '0.75rem 1rem', background: 'rgba(255,77,109,0.08)', border: '1px solid rgba(255,77,109,0.25)', borderRadius: 'var(--radius-sm)', color: 'var(--negative)', fontSize: '0.82rem', marginBottom: '1rem' }}>
          ⚠ {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '1.25rem' }}>

          {/* Big r value */}
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem', marginBottom: '0.25rem' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '2.2rem', fontWeight: 700, color: rColor(result.pearson_r), letterSpacing: '-0.02em' }}>
              {result.pearson_r >= 0 ? '+' : ''}{result.pearson_r.toFixed(3)}
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>
              Pearson r
            </span>
          </div>

          {/* Symbol pair */}
          <div style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
            <span style={{ color: '#00d2a8' }}>{result.symbol1}</span>
            <span style={{ color: 'var(--text-muted)' }}> × </span>
            <span style={{ color: '#3b82f6' }}>{result.symbol2}</span>
            <span style={{ color: 'var(--text-muted)', marginLeft: 8 }}>({result.days_used} trading days)</span>
          </div>

          {/* Gauge */}
          <CorrelationGauge r={result.pearson_r} />

          {/* Interpretation */}
          <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.9rem', background: 'var(--bg-card)', border: '1px solid var(--border-bright)', borderRadius: 'var(--radius-sm)', fontSize: '0.82rem', color: 'var(--text-primary)', borderLeft: `3px solid ${rColor(result.pearson_r)}` }}>
            {result.interpretation}
          </div>

          {/* What this means explainer */}
          <div style={{ marginTop: '0.75rem', fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            r = +1 means the stocks move perfectly together · r = 0 means no relationship · r = −1 means they move in opposite directions.
            Useful for portfolio diversification — combining low-correlation stocks reduces overall risk.
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', fontStyle: 'italic' }}>
          Select two stocks and click "Analyse" to compute their price correlation
        </div>
      )}
    </div>
  );
}




