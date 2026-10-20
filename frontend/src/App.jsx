import React, { useState } from 'react';
import TeacherStudio from './components/TeacherStudio';
import StudentPlayer from './components/StudentPlayer';
import FailsafeAuditModal from './components/FailsafeAuditModal';
import { BookOpen, UserCheck, ShieldCheck, Sparkles, Layers, Cpu } from 'lucide-react';

export default function App() {
  const [currentView, setCurrentView] = useState('student'); // 'teacher' | 'student'
  const [selectedLectureId, setSelectedLectureId] = useState('lec_binary_search_101');
  const [auditModalPersId, setAuditModalPersId] = useState(null);

  const handleSelectLectureForStudent = (lecId) => {
    setSelectedLectureId(lecId);
    setCurrentView('student');
  };

  const handleOpenAuditModal = (persId) => {
    setAuditModalPersId(persId);
  };

  const handleCloseAuditModal = () => {
    setAuditModalPersId(null);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Sticky Global Navigation */}
      <header className="navbar">
        <div className="logo-group">
          <div className="logo-badge">
            <Sparkles size={22} />
          </div>
          <div>
            <div className="logo-title">ForOne</div>
            <div className="logo-subtitle">AI-PERSONALIZED EDUCATION PLATFORM</div>
          </div>
        </div>

        {/* View Switcher Pills */}
        <div className="nav-tabs">
          <button
            onClick={() => setCurrentView('teacher')}
            className={`nav-tab-btn ${currentView === 'teacher' ? 'active' : ''}`}
          >
            <BookOpen size={16} /> Teacher Studio
          </button>

          <button
            onClick={() => setCurrentView('student')}
            className={`nav-tab-btn ${currentView === 'student' ? 'active' : ''}`}
          >
            <UserCheck size={16} /> Student Portal
          </button>
        </div>

        {/* Global Failsafe Status Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            onClick={() => handleOpenAuditModal('pers_witty_4b465a')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              padding: '0.45rem 0.9rem',
              borderRadius: 'var(--radius-full)',
              cursor: 'pointer'
            }}
          >
            <ShieldCheck size={18} color="#10b981" />
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#34d399' }}>
              Failsafe Quality Gate: ACTIVE
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1 }}>
        {currentView === 'teacher' && (
          <TeacherStudio
            onSelectLectureForStudent={handleSelectLectureForStudent}
            onOpenFailsafeModal={handleOpenAuditModal}
          />
        )}

        {currentView === 'student' && (
          <StudentPlayer
            initialLectureId={selectedLectureId}
            onOpenAuditModal={handleOpenAuditModal}
          />
        )}
      </main>

      {/* Global Failsafe Audit Modal */}
      {auditModalPersId && (
        <FailsafeAuditModal
          personalizedId={auditModalPersId}
          onClose={handleCloseAuditModal}
        />
      )}

      {/* Sleek Minimal Footer */}
      <footer style={{ borderTop: '1px solid var(--border-color)', padding: '1.25rem 2rem', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        ForOne: AI-Personalized Education Platform • 100% Free-Tier & Local Open-Source Architecture • Zero Pedagogical Hallucinations
      </footer>
    </div>
  );
}
