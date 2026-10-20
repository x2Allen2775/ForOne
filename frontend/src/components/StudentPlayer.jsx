import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, Volume2, ShieldCheck, AlertOctagon, Sparkles, HelpCircle, MessageSquare, BookOpen, Check, X, Award, ExternalLink } from 'lucide-react';

export default function StudentPlayer({ initialLectureId, onOpenAuditModal }) {
  const [lectures, setLectures] = useState([]);
  const [selectedLectureId, setSelectedLectureId] = useState(initialLectureId || '');
  const [lectureDetail, setLectureDetail] = useState(null);
  const [personas, setPersonas] = useState([]);
  const [selectedPersonaId, setSelectedPersonaId] = useState('witty');
  const [variants, setVariants] = useState([]);
  const [currentVariant, setCurrentVariant] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState(null);

  // Playback state
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  // Sidebar Tab state ('transcript' | 'quiz' | 'tutor')
  const [activeTab, setActiveTab] = useState('transcript');

  // Quiz state
  const [quizData, setQuizData] = useState(null);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);

  // Tutor state
  const [chatMessages, setChatMessages] = useState([
    { sender: 'tutor', text: 'Hello! I am your 24/7 ForOne AI Tutor. Ask me any question about this lecture—I am strictly grounded in the verified curriculum facts without judgment.' }
  ]);
  const [inputMsg, setInputMsg] = useState('');
  const [askingTutor, setAskingTutor] = useState(false);

  // Load lectures and personas on mount
  useEffect(() => {
    fetchLectures();
    fetchPersonas();
  }, []);

  // When selectedLectureId changes
  useEffect(() => {
    if (selectedLectureId) {
      loadLectureDetails(selectedLectureId);
      loadVariants(selectedLectureId);
      loadQuiz(selectedLectureId);
    }
  }, [selectedLectureId]);

  const fetchLectures = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/lectures');
      const data = await res.json();
      setLectures(data.lectures || []);
      if (!selectedLectureId && data.lectures && data.lectures.length > 0) {
        setSelectedLectureId(data.lectures[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchPersonas = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/personalize/personas');
      const data = await res.json();
      setPersonas(data.personas || []);
    } catch (err) {
      console.error(err);
    }
  };

  const loadLectureDetails = async (lecId) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/lectures/${lecId}`);
      const data = await res.json();
      setLectureDetail(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadVariants = async (lecId) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/personalize/lecture/${lecId}`);
      const data = await res.json();
      const vars = data.variants || [];
      setVariants(vars);
      // Auto-select latest approved matched persona variant if available
      const matched = vars
        .filter(v => v.persona_id === selectedPersonaId && v.status === 'approved')
        .sort((a, b) => (b.id > a.id ? 1 : -1))[0] || vars.find(v => v.persona_id === selectedPersonaId);

      setCurrentVariant(matched || null);
    } catch (err) {
      console.error(err);
    }
  };

  const loadQuiz = async (lecId) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/tutor/quiz/${lecId}`);
      const data = await res.json();
      setQuizData(data);
      setSelectedAnswers({});
      setQuizSubmitted(false);
    } catch (err) {
      console.error(err);
    }
  };

  // Change Persona: Immediately update active variant to the selected persona
  const handleSelectPersona = (personaId) => {
    setSelectedPersonaId(personaId);
    const existing = variants
      .filter(v => v.persona_id === personaId && v.status === 'approved')
      .sort((a, b) => (b.id > a.id ? 1 : -1))[0] || variants.find(v => v.persona_id === personaId);

    setCurrentVariant(existing || null);
    setGenerateError(null);
    setIsPlaying(false);
  };

  // Trigger Persona Generation
  const handleGeneratePersonalization = async (simulateError = false) => {
    if (!selectedLectureId) return;
    setGenerating(true);
    setGenerateError(null);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/personalize/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lecture_id: selectedLectureId,
          persona_id: selectedPersonaId,
          simulate_error: simulateError
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Generation failed');
      }

      await loadVariants(selectedLectureId);

      // Select new variant
      const updatedVariant = await (await fetch(`http://127.0.0.1:8000/api/personalize/${data.personalized_id}`)).json();
      setCurrentVariant(updatedVariant.personalized_lecture);

      if (data.status === 'rejected_failsafe') {
        setGenerateError(data.error_message || 'Video rejected by Failsafe Quality Gate due to fact omission.');
      }
    } catch (err) {
      console.error(err);
      setGenerateError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  // Video playback handlers
  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
      setDuration(videoRef.current.duration || 0);
    }
  };

  const handleSpeedChange = (speed) => {
    setPlaybackSpeed(speed);
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
    }
  };

  // Chat with tutor
  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!inputMsg.trim()) return;

    const userText = inputMsg;
    setInputMsg('');
    setChatMessages(prev => [...prev, { sender: 'user', text: userText }]);
    setAskingTutor(true);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/tutor/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lecture_id: selectedLectureId,
          message: userText
        })
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, {
        sender: 'tutor',
        text: data.reply,
        facts: data.grounded_facts_used
      }]);
    } catch (err) {
      setChatMessages(prev => [...prev, {
        sender: 'tutor',
        text: 'Sorry, I am having trouble connecting to the verified syllabus knowledge base right now.'
      }]);
    } finally {
      setAskingTutor(false);
    }
  };

  const activePersona = personas.find(p => p.id === selectedPersonaId);

  const videoSrc = currentVariant && currentVariant.status === 'approved'
    ? `http://127.0.0.1:8000/api/personalize/${currentVariant.id}/video`
    : lectureDetail && lectureDetail.lecture
    ? `http://127.0.0.1:8000/api/lectures/${selectedLectureId}/video`
    : null;

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Top Header / Selector */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <span className="badge badge-primary" style={{ marginBottom: '0.4rem' }}>
            STUDENT HYPER-PERSONALIZED PORTAL
          </span>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>
            {lectureDetail?.lecture?.title || 'Select a Lecture'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            {lectureDetail?.lecture?.subject} • Instructor: {lectureDetail?.lecture?.instructor}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <select
            value={selectedLectureId}
            onChange={(e) => setSelectedLectureId(e.target.value)}
            style={{
              padding: '0.6rem 1rem',
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              color: '#fff',
              fontSize: '0.85rem'
            }}
          >
            {lectures.map((l) => (
              <option key={l.id} value={l.id} style={{ background: '#0d1424' }}>
                {l.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Persona Selection Bar */}
      <div style={{ marginBottom: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Choose Your Learning Persona
          </h2>
          {currentVariant && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Currently Active: <strong style={{ color: '#fff' }}>{currentVariant.persona_name || 'Master Lecture'}</strong>
            </span>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          {personas.map((p) => {
            const isSelected = selectedPersonaId === p.id;
            const hasVariant = variants.some(v => v.persona_id === p.id && v.status === 'approved');
            const hasFailedVariant = variants.some(v => v.persona_id === p.id && v.status === 'rejected_failsafe');

            return (
              <div
                key={p.id}
                onClick={() => handleSelectPersona(p.id)}
                className="glass-panel"
                style={{
                  padding: '1.1rem',
                  cursor: 'pointer',
                  border: isSelected ? `2px solid ${p.accent_color}` : '1px solid var(--border-color)',
                  background: isSelected ? 'rgba(255,255,255,0.08)' : 'var(--bg-card)',
                  transform: isSelected ? 'translateY(-2px)' : 'none',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: isSelected ? '#fff' : 'var(--text-primary)' }}>
                    {p.name}
                  </h3>
                  {hasVariant && (
                    <span className="badge badge-approved" style={{ fontSize: '0.65rem' }}>
                      <Check size={10} /> Ready
                    </span>
                  )}
                  {hasFailedVariant && (
                    <span className="badge badge-danger" style={{ fontSize: '0.65rem' }}>
                      <AlertOctagon size={10} /> Failsafe Blocked
                    </span>
                  )}
                </div>
                <span style={{ fontSize: '0.75rem', color: p.accent_color, fontWeight: 600, display: 'block', marginBottom: '0.4rem' }}>
                  {p.tag}
                </span>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.35 }}>
                  {p.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Failsafe Gate Status Bar */}
      {currentVariant && (
        <div
          className="glass-panel"
          style={{
            padding: '1rem 1.5rem',
            marginBottom: '1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderLeft: `5px solid ${currentVariant.status === 'approved' ? '#10b981' : '#ef4444'}`,
            background: currentVariant.status === 'approved' ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.08)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {currentVariant.status === 'approved' ? (
              <ShieldCheck size={28} color="#10b981" />
            ) : (
              <AlertOctagon size={28} color="#ef4444" className="anim-pulse" />
            )}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <strong style={{ fontSize: '0.95rem', color: currentVariant.status === 'approved' ? '#34d399' : '#f87171' }}>
                  {currentVariant.status === 'approved'
                    ? 'FAILSAFE QUALITY GATE: VERIFIED & APPROVED'
                    : 'FAILSAFE QUALITY GATE: REJECTED (OMISSION DETECTED)'}
                </strong>
                <span className={`badge ${currentVariant.status === 'approved' ? 'badge-approved' : 'badge-danger'}`}>
                  Fidelity: {currentVariant.fact_fidelity_score}%
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                {currentVariant.status === 'approved'
                  ? 'Dual speech-to-text comparison verified that every minute detail, formula, and step of the master lecture is preserved.'
                  : currentVariant.error_message || 'Video generation failed strict factual verification threshold.'}
              </p>
            </div>
          </div>

          <button
            onClick={() => onOpenAuditModal(currentVariant.id)}
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.5rem 1rem' }}
          >
            <ExternalLink size={14} /> Open Failsafe Audit Diff
          </button>
        </div>
      )}

      {/* Main Grid: Video Player (Left) + Interactive Sideboard (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1.2fr', gap: '1.75rem' }}>
        {/* Left Column: Player & Generation Trigger */}
        <div>
          <div
            className="glass-panel"
            style={{
              overflow: 'hidden',
              position: 'relative',
              background: '#020617',
              borderRadius: 'var(--radius-md)',
              boxShadow: '0 20px 40px rgba(0,0,0,0.8)'
            }}
          >
            {/* Live Characterisation Badge Overlay on Video */}
            <div style={{
              position: 'absolute',
              top: '12px',
              left: '12px',
              zIndex: 10,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'rgba(2, 6, 23, 0.85)',
              backdropFilter: 'blur(8px)',
              padding: '6px 12px',
              borderRadius: '20px',
              border: `1.5px solid ${activePersona?.accent_color || '#3b82f6'}`,
              boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
            }}>
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: activePersona?.accent_color || '#3b82f6',
                boxShadow: `0 0 6px ${activePersona?.accent_color || '#3b82f6'}`
              }} />
              <span style={{ fontSize: '0.78rem', fontWeight: 800, color: '#fff', letterSpacing: '0.03em' }}>
                {currentVariant?.status === 'approved' ? activePersona?.name : `${activePersona?.name || 'Persona'} (Original Video)`}
              </span>
              <span style={{ fontSize: '0.7rem', color: activePersona?.accent_color || '#3b82f6', fontWeight: 600 }}>
                • {activePersona?.tag}
              </span>
            </div>

            {videoSrc ? (
              <video
                key={videoSrc}
                ref={videoRef}
                src={videoSrc}
                onTimeUpdate={handleTimeUpdate}
                onEnded={() => setIsPlaying(false)}
                style={{ width: '100%', height: 'auto', display: 'block', maxHeight: '460px' }}
                onClick={togglePlay}
              />
            ) : (
              <div style={{ height: '360px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '1rem', color: 'var(--text-muted)' }}>
                <BookOpen size={48} />
                <p>No video available yet. Click below to personalize this lecture!</p>
              </div>
            )}

            {/* Custom Control Overlay */}
            {videoSrc && (
              <div style={{ padding: '0.75rem 1.25rem', background: 'rgba(7, 11, 20, 0.9)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <button
                    onClick={togglePlay}
                    style={{ background: 'var(--primary)', border: 'none', borderRadius: '50%', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', cursor: 'pointer' }}
                  >
                    {isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: '2px' }} />}
                  </button>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {Math.floor(currentTime)}s / {Math.floor(duration)}s
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Speed:</span>
                  {[0.75, 1, 1.25, 1.5].map((s) => (
                    <button
                      key={s}
                      onClick={() => handleSpeedChange(s)}
                      style={{
                        background: playbackSpeed === s ? 'var(--primary)' : 'rgba(255,255,255,0.06)',
                        border: 'none',
                        color: playbackSpeed === s ? '#fff' : 'var(--text-secondary)',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        cursor: 'pointer'
                      }}
                    >
                      {s}x
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Action Row: Personalize Button & Failure Demo Button */}
          <div style={{ marginTop: '1.25rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => handleGeneratePersonalization(false)}
              disabled={generating}
              className="btn btn-primary"
              style={{ flex: 1, padding: '0.85rem' }}
            >
              <Sparkles size={18} />
              {generating ? 'Processing Personalization & Verifying Facts...' : `Personalize for ${personas.find(p => p.id === selectedPersonaId)?.name || 'Me'}`}
            </button>

            {/* Failsafe Error Trigger Demonstration for Judges */}
            <button
              onClick={() => handleGeneratePersonalization(true)}
              disabled={generating}
              className="btn btn-secondary"
              style={{ border: '1px solid rgba(239, 68, 68, 0.4)', color: '#f87171', padding: '0.85rem' }}
              title="Intentionally omits a critical syllabus fact to demonstrate that the Failsafe Engine catches the error!"
            >
              <AlertOctagon size={18} />
              Test Failsafe Rejection (Omit Fact)
            </button>
          </div>

          {generateError && (
            <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-sm)', color: '#fca5a5', fontSize: '0.85rem', display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
              <AlertOctagon size={16} color="#ef4444" />
              <span>{generateError}</span>
            </div>
          )}
        </div>

        {/* Right Column: Tabbed Interactive Panel (Transcript / Quiz / Tutor) */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '620px' }}>
          {/* Tab Headers */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.2)' }}>
            <button
              onClick={() => setActiveTab('transcript')}
              style={{
                flex: 1,
                padding: '0.85rem',
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'transcript' ? '2px solid var(--primary)' : '2px solid transparent',
                color: activeTab === 'transcript' ? '#fff' : 'var(--text-secondary)',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem'
              }}
            >
              <BookOpen size={16} /> Interactive Transcript
            </button>

            <button
              onClick={() => setActiveTab('quiz')}
              style={{
                flex: 1,
                padding: '0.85rem',
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'quiz' ? '2px solid var(--primary)' : '2px solid transparent',
                color: activeTab === 'quiz' ? '#fff' : 'var(--text-secondary)',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem'
              }}
            >
              <Award size={16} /> Micro-Quiz
            </button>

            <button
              onClick={() => setActiveTab('tutor')}
              style={{
                flex: 1,
                padding: '0.85rem',
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'tutor' ? '2px solid var(--primary)' : '2px solid transparent',
                color: activeTab === 'tutor' ? '#fff' : 'var(--text-secondary)',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem'
              }}
            >
              <MessageSquare size={16} /> 24/7 AI Tutor
            </button>
          </div>

          {/* Tab Content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem' }}>
            {/* 1. Transcript Tab */}
            {activeTab === 'transcript' && (
              <div>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
                  {currentVariant ? `${currentVariant.persona_name} Spoken Script` : 'Master Teacher Transcript'}
                </h3>
                <div style={{ fontSize: '0.9rem', lineHeight: 1.6, color: '#e2e8f0', whiteSpace: 'pre-wrap' }}>
                  {currentVariant && currentVariant.gen_transcript_text
                    ? currentVariant.gen_transcript_text
                    : lectureDetail?.lecture?.master_transcript || 'No transcript generated yet.'}
                </div>
              </div>
            )}

            {/* 2. Micro-Quiz Tab */}
            {activeTab === 'quiz' && (
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Adaptive Micro-Assessment
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
                  Low-stakes concept check uniquely derived from verified syllabus facts:
                </p>

                {quizData?.questions?.map((q, qIndex) => {
                  const selectedOpt = selectedAnswers[q.id];
                  const isCorrect = selectedOpt === q.correct_index;

                  return (
                    <div key={q.id} style={{ marginBottom: '1.5rem', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#60a5fa' }}>
                          Question {qIndex + 1}
                        </span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          Grounded in {q.grounded_fact_id}
                        </span>
                      </div>
                      <p style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem' }}>{q.question}</p>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                        {q.options.map((opt, oIndex) => {
                          const isPicked = selectedOpt === oIndex;
                          let optBg = 'rgba(255,255,255,0.04)';
                          let optBorder = 'var(--border-color)';

                          if (quizSubmitted) {
                            if (oIndex === q.correct_index) {
                              optBg = 'rgba(16, 185, 129, 0.2)';
                              optBorder = '#10b981';
                            } else if (isPicked && !isCorrect) {
                              optBg = 'rgba(239, 68, 68, 0.2)';
                              optBorder = '#ef4444';
                            }
                          } else if (isPicked) {
                            optBg = 'rgba(59, 130, 246, 0.2)';
                            optBorder = 'var(--primary)';
                          }

                          return (
                            <button
                              key={oIndex}
                              disabled={quizSubmitted}
                              onClick={() => setSelectedAnswers(prev => ({ ...prev, [q.id]: oIndex }))}
                              style={{
                                textAlign: 'left',
                                padding: '0.55rem 0.85rem',
                                background: optBg,
                                border: `1px solid ${optBorder}`,
                                borderRadius: 'var(--radius-sm)',
                                color: '#f8fafc',
                                fontSize: '0.825rem',
                                cursor: quizSubmitted ? 'default' : 'pointer'
                              }}
                            >
                              {opt}
                            </button>
                          );
                        })}
                      </div>

                      {quizSubmitted && (
                        <div style={{ marginTop: '0.6rem', fontSize: '0.75rem', color: isCorrect ? '#34d399' : '#f87171' }}>
                          <strong>{isCorrect ? 'Correct!' : 'Incorrect.'}</strong> {q.explanation}
                        </div>
                      )}
                    </div>
                  );
                })}

                {!quizSubmitted ? (
                  <button
                    onClick={() => setQuizSubmitted(true)}
                    className="btn btn-primary"
                    style={{ width: '100%', padding: '0.65rem' }}
                  >
                    Submit Micro-Quiz
                  </button>
                ) : (
                  <button
                    onClick={() => { setQuizSubmitted(false); setSelectedAnswers({}); }}
                    className="btn btn-secondary"
                    style={{ width: '100%', padding: '0.65rem' }}
                  >
                    Retake Quiz
                  </button>
                )}
              </div>
            )}

            {/* 3. AI Tutor Tab */}
            {activeTab === 'tutor' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
                  {chatMessages.map((msg, i) => (
                    <div
                      key={i}
                      style={{
                        alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                        maxWidth: '85%',
                        background: msg.sender === 'user' ? 'var(--primary)' : 'rgba(255,255,255,0.06)',
                        padding: '0.75rem 1rem',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '0.85rem',
                        color: '#f8fafc',
                        lineHeight: 1.4
                      }}
                    >
                      {msg.text}
                      {msg.facts && (
                        <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: '#60a5fa' }}>
                          Verified syllabus basis: {msg.facts.join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                  {askingTutor && (
                    <div style={{ alignSelf: 'flex-start', background: 'rgba(255,255,255,0.06)', padding: '0.5rem 0.8rem', borderRadius: 'var(--radius-md)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Tutor is thinking...
                    </div>
                  )}
                </div>

                <form onSubmit={handleSendChat} style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    type="text"
                    placeholder="Ask repetitive or basic questions freely..."
                    value={inputMsg}
                    onChange={(e) => setInputMsg(e.target.value)}
                    style={{
                      flex: 1,
                      padding: '0.65rem 0.9rem',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-sm)',
                      color: '#fff',
                      fontSize: '0.85rem'
                    }}
                  />
                  <button type="submit" disabled={askingTutor} className="btn btn-primary" style={{ padding: '0.65rem 1rem' }}>
                    Send
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
