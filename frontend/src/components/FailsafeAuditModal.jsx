import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertOctagon, CheckCircle2, XCircle, Search, RefreshCw, Sparkles, ArrowRight } from 'lucide-react';

export default function FailsafeAuditModal({ personalizedId, onClose }) {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all' | 'matched' | 'missing'
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    if (personalizedId) {
      loadReport(personalizedId);
    }
  }, [personalizedId]);

  const loadReport = async (persId) => {
    try {
      setLoading(true);
      const res = await fetch(`http://127.0.0.1:8000/api/failsafe/${persId}`);
      const data = await res.json();
      setReportData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSideBySideSimulation = async () => {
    setSimulating(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/failsafe/simulate_demo', {
        method: 'POST'
      });
      const data = await res.json();
      // Load failing or passing report
      if (data.failing_case?.personalized_id) {
        await loadReport(data.failing_case.personalized_id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSimulating(false);
    }
  };

  const audit = reportData?.audit_report;
  const isApproved = reportData?.status === 'approved';
  const factsMatrix = audit?.facts_matrix || [];

  const filteredFacts = factsMatrix.filter((f) => {
    if (filter === 'matched') return f.matched;
    if (filter === 'missing') return !f.matched;
    return true;
  });

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(16px)', zIndex: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '1100px', maxHeight: '90vh', overflowY: 'auto', padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', border: isApproved ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(239, 68, 68, 0.4)' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.3rem' }}>
              <span className={`badge ${isApproved ? 'badge-approved' : 'badge-danger'}`} style={{ fontSize: '0.8rem', padding: '0.35rem 0.8rem' }}>
                {isApproved ? <ShieldCheck size={16} /> : <AlertOctagon size={16} />}
                {isApproved ? 'FAILSAFE STATUS: APPROVED (100% FIDELITY)' : 'FAILSAFE ALERT: QUALITY GATE REJECTED'}
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Target Persona: <strong style={{ color: '#fff' }}>{reportData?.persona_name}</strong>
              </span>
            </div>
            <h2 style={{ fontSize: '1.6rem', fontWeight: 800 }}>
              Dual Speech-to-Text Factual Comparative Audit
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
              Lecture: {reportData?.lecture_title} • Compares Master Lecture STT ($T_&#123;master&#125;$) against Generated Video STT ($T_&#123;gen&#125;$).
            </p>
          </div>

          <button onClick={onClose} className="btn btn-secondary" style={{ padding: '0.5rem 1rem' }}>
            Close Inspector
          </button>
        </div>

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Loading audit verification data...
          </div>
        ) : (
          <>
            {/* Metric Tiles */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Fidelity Score</span>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: isApproved ? '#34d399' : '#f87171', marginTop: '0.2rem' }}>
                  {reportData?.fidelity_score}%
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Threshold: &gt;= 95%</span>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Syllabus Facts</span>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.2rem' }}>
                  {audit?.total_facts || 0}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Decomposed from Master STT</span>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Verified in Video</span>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#34d399', marginTop: '0.2rem' }}>
                  {audit?.matched_facts || 0}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Confirmed via Whisper STT</span>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Missing / Hallucinated</span>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: (audit?.missing_facts_count || 0) > 0 ? '#f87171' : '#34d399', marginTop: '0.2rem' }}>
                  {audit?.missing_facts_count || 0}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                  {(audit?.missing_facts_count || 0) > 0 ? 'FAILSAFE TRIGGERED' : 'Zero Omissions'}
                </span>
              </div>
            </div>

            {/* Error Banner if Rejected */}
            {!isApproved && reportData?.error_message && (
              <div style={{ padding: '1rem 1.25rem', background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                <AlertOctagon size={24} color="#ef4444" />
                <div>
                  <strong style={{ color: '#f87171', fontSize: '0.9rem' }}>FAILSAFE ENFORCEMENT ACTIVE:</strong>
                  <p style={{ color: '#fca5a5', fontSize: '0.825rem', marginTop: '0.15rem' }}>
                    {reportData.error_message} This video has been quarantined and blocked from student release.
                  </p>
                </div>
              </div>
            )}

            {/* Filter Tabs */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => setFilter('all')}
                  className="btn btn-secondary"
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', background: filter === 'all' ? 'var(--primary)' : 'rgba(255,255,255,0.06)' }}
                >
                  All Propositions ({factsMatrix.length})
                </button>
                <button
                  onClick={() => setFilter('matched')}
                  className="btn btn-secondary"
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', background: filter === 'matched' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(255,255,255,0.06)' }}
                >
                  Verified Matched ({factsMatrix.filter(f => f.matched).length})
                </button>
                <button
                  onClick={() => setFilter('missing')}
                  className="btn btn-secondary"
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', background: filter === 'missing' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(255,255,255,0.06)' }}
                >
                  Omitted / Distorted ({factsMatrix.filter(f => !f.matched).length})
                </button>
              </div>

              {/* Hackathon Judge Simulation Trigger */}
              <button
                onClick={handleRunSideBySideSimulation}
                disabled={simulating}
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '0.45rem 0.9rem', border: '1px solid rgba(139, 92, 246, 0.4)', color: '#c084fc' }}
              >
                <Sparkles size={14} />
                {simulating ? 'Running Simulation...' : 'Simulate Side-by-Side Pass vs Error Test'}
              </button>
            </div>

            {/* Granular Comparison Diff Table */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ background: 'rgba(255,255,255,0.04)', borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '0.75rem 1rem', width: '90px' }}>Fact ID</th>
                    <th style={{ padding: '0.75rem 1rem', width: '120px' }}>Category</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Expected Master Syllabus Proposition</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Generated Video Evidence (T_gen)</th>
                    <th style={{ padding: '0.75rem 1rem', width: '120px', textAlign: 'center' }}>Failsafe Check</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredFacts.map((fact) => (
                    <tr
                      key={fact.fact_id}
                      style={{
                        borderBottom: '1px solid rgba(255,255,255,0.05)',
                        background: fact.matched ? 'transparent' : 'rgba(239, 68, 68, 0.05)'
                      }}
                    >
                      <td style={{ padding: '0.85rem 1rem', fontWeight: 700, color: '#60a5fa' }}>
                        {fact.fact_id}
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', padding: '0.15rem 0.45rem', borderRadius: '4px', background: fact.criticality === 'critical' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255,255,255,0.08)', color: fact.criticality === 'critical' ? '#f87171' : 'var(--text-secondary)' }}>
                          {fact.category}
                        </span>
                      </td>
                      <td style={{ padding: '0.85rem 1rem', color: '#f8fafc', lineHeight: 1.4 }}>
                        {fact.statement}
                      </td>
                      <td style={{ padding: '0.85rem 1rem', color: fact.matched ? '#cbd5e1' : '#fca5a5', fontStyle: fact.matched ? 'normal' : 'italic', lineHeight: 1.4 }}>
                        {fact.evidence_snippet}
                      </td>
                      <td style={{ padding: '0.85rem 1rem', textAlign: 'center' }}>
                        {fact.matched ? (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', color: '#34d399', fontWeight: 700, fontSize: '0.75rem' }}>
                            <CheckCircle2 size={16} /> VERIFIED
                          </span>
                        ) : (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', color: '#f87171', fontWeight: 700, fontSize: '0.75rem' }}>
                            <XCircle size={16} /> OMITTED
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
