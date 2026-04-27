
import { useState, useEffect } from 'react';
import axios from 'axios';
import CompanyList from './components/CompanyList';
import StockChart from './components/StockChart';
import SummaryCard from './components/SummaryCard';
import ComparisonChart from './components/ComparisonChart';
import MoversTable from './components/MoversTable';
import Predictor from './components/Predictor';
import CorrelationCard from './components/CorrelationCard';
import './App.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [companies, setCompanies]       = useState([]);
  const [selected, setSelected]         = useState(null);
  const [compareMode, setCompareMode]   = useState(false);
  const [compareSymbol, setCompareSymbol] = useState('');
  const [compareActive, setCompareActive] = useState(false);
  const [activeTab, setActiveTab]       = useState('chart'); // 'chart' | 'correlation'

  useEffect(() => {
    axios.get(`${API}/companies`).then(res => setCompanies(res.data));
  }, []);

  const handleSelect = (symbol) => {
    setSelected(symbol);
    setCompareMode(false);
    setCompareActive(false);
    setActiveTab('chart');
  };

  const handleToggleCompare = () => {
    setCompareMode(!compareMode);
    setCompareActive(false);
  };

  return (
    <div className="app-container">
      <header className="dashboard-header">
        <div className="header-brand">
          <div className="header-logo">📈</div>
          <span className="header-title">Stock<span>Intelligence</span></span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Tab switcher */}
          <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '3px' }}>
            {['chart', 'correlation'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  padding: '4px 14px', border: 'none', cursor: 'pointer', fontSize: '0.72rem',
                  fontWeight: 700, fontFamily: 'var(--font-mono)', borderRadius: '5px', letterSpacing: '0.04em',
                  background: activeTab === tab ? 'var(--accent)' : 'transparent',
                  color: activeTab === tab ? 'var(--bg-base)' : 'var(--text-secondary)',
                  transition: 'all 0.15s',
                }}
              >
                {tab === 'chart' ? '📊 Charts' : '🔗 Correlation'}
              </button>
            ))}
          </div>
          <div className="header-badge">● DELAYED 15m</div>
        </div>
      </header>

      <div className="dashboard-layout">
        <aside className="sidebar">
          <div className="sidebar-section-label">Markets</div>
          <CompanyList companies={companies} selected={selected} onSelect={handleSelect} />
          <div className="sidebar-divider" />
          <div className="sidebar-controls">
            <button className={`compare-btn ${compareMode ? 'active' : ''}`} onClick={handleToggleCompare}>
              ⇄ {compareMode ? 'Close Compare' : 'Compare Stocks'}
            </button>
          </div>
        </aside>

        <main className="main-content">
          <div className="content-grid">

            {/* ── Correlation tab ──────────────────────────────────── */}
            {activeTab === 'correlation' && (
              <CorrelationCard companies={companies} />
            )}

            {/* ── Charts tab ───────────────────────────────────────── */}
            {activeTab === 'chart' && (
              <>
                {/* Compare mode */}
                {compareMode && (
                  <div className="compare-panel">
                    <div className="compare-header"><span>⇄</span> Compare Two Stocks</div>
                    <div className="compare-inputs">
                      <div className="compare-input-group">
                        <span className="compare-input-label">Symbol A</span>
                        <input type="text" placeholder="e.g. INFY" value={selected || ''} onChange={e => setSelected(e.target.value.toUpperCase())} />
                      </div>
                      <div className="compare-input-group">
                        <span className="compare-input-label">Symbol B</span>
                        <input type="text" placeholder="e.g. TCS" value={compareSymbol} onChange={e => setCompareSymbol(e.target.value.toUpperCase())} />
                      </div>
                      <button className="compare-go-btn" onClick={() => { if (selected && compareSymbol) setCompareActive(true); }}>
                        Run Comparison →
                      </button>
                    </div>
                    {compareActive && selected && compareSymbol && (
                      <ComparisonChart symbol1={selected} symbol2={compareSymbol} />
                    )}
                  </div>
                )}

                {/* Stock detail */}
                {selected && !compareMode && (
                  <>
                    <SummaryCard symbol={selected} />
                    <StockChart symbol={selected} />
                    <Predictor symbol={selected} />
                  </>
                )}

                {/* Empty state */}
                {!selected && !compareMode && (
                  <div className="empty-state">
                    <div className="empty-state-icon">📊</div>
                    <div className="empty-state-title">Select a company to begin</div>
                    <div className="empty-state-sub">
                      Choose any symbol from the sidebar to view price charts, summary stats, and AI predictions.
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Always show movers */}
            <MoversTable />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;