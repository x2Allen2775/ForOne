import React, { useState, useEffect } from 'react';
import { Upload, Video, FileText, CheckCircle, Clock, AlertTriangle, BookOpen, User, Play, Sparkles } from 'lucide-react';

export default function TeacherStudio({ onSelectLectureForStudent, onOpenFailsafeModal }) {
  const [lectures, setLectures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Form state
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [instructor, setInstructor] = useState('Prof. Vance');
  const [file, setFile] = useState(null);

  // Selected lecture for fact preview
  const [inspectLecture, setInspectLecture] = useState(null);
  const [inspectFacts, setInspectFacts] = useState([]);

  useEffect(() => {
    fetchLectures();
  }, []);

  const fetchLectures = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://127.0.0.1:8000/api/lectures');
      const data = await res.json();
      setLectures(data.lectures || []);
    } catch (err) {
      console.error('Failed to fetch lectures:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !title || !subject) {
      alert('Please fill out all fields and select a video file.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('subject', subject);
    formData.append('instructor', instructor);

    setUploading(true);
    setUploadProgress(20);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/lectures/upload', {
        method: 'POST',
        body: formData,
      });
      setUploadProgress(70);
      const data = await res.json();
      setUploadProgress(100);

      setTimeout(() => {
        setUploading(false);
        setTitle('');
        setSubject('');
        setFile(null);
        fetchLectures();
      }, 1000);
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Upload failed. Please check backend server.');
      setUploading(false);
    }
  };

  const handleInspect = async (lec) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/lectures/${lec.id}`);
      const data = await res.json();
      setInspectLecture(data.lecture);
      setInspectFacts(data.facts || []);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1280px', margin: '0 auto' }}>
      {/* Hero Header */}
      <div style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 800, marginBottom: '0.5rem', background: 'linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Teacher Studio & Lecture Repository
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>
            Upload raw master classroom lectures. The AI platform automatically transcribes, extracts granular syllabus facts, and feeds the multi-persona personalization engine.
          </p>
        </div>
        <button
          onClick={fetchLectures}
          className="btn btn-secondary"
          style={{ padding: '0.6rem 1.2rem' }}
        >
          Refresh Catalog
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
        {/* Upload Form Card */}
        <div className="glass-panel" style={{ padding: '1.75rem', height: 'fit-content' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.25rem' }}>
            <Upload size={22} color="var(--primary)" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Upload Master Lecture</h2>
          </div>

          <form onSubmit={handleUpload}>
            <div style={{ marginBottom: '1.2rem' }}>
              <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                Lecture Title
              </label>
              <input
                type="text"
                placeholder="e.g. Binary Search & Time Complexity"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{ width: '100%', padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', color: '#fff', fontSize: '0.9rem' }}
              />
            </div>

            <div style={{ marginBottom: '1.2rem' }}>
              <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                Subject / Department
              </label>
              <input
                type="text"
                placeholder="e.g. Computer Science / Algorithms"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                style={{ width: '100%', padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', color: '#fff', fontSize: '0.9rem' }}
              />
            </div>

            <div style={{ marginBottom: '1.2rem' }}>
              <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                Instructor Name
              </label>
              <input
                type="text"
                placeholder="e.g. Prof. Alan Vance"
                value={instructor}
                onChange={(e) => setInstructor(e.target.value)}
                style={{ width: '100%', padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', color: '#fff', fontSize: '0.9rem' }}
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                Master Lecture Video (MP4 / WebM)
              </label>
              <div
                style={{
                  border: '2px dashed var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.5rem',
                  textAlign: 'center',
                  background: 'rgba(255,255,255,0.02)',
                  cursor: 'pointer'
                }}
                onClick={() => document.getElementById('file-upload-input').click()}
              >
                <Video size={32} color="var(--text-muted)" style={{ margin: '0 auto 0.5rem auto' }} />
                <p style={{ fontSize: '0.85rem', color: file ? 'var(--success)' : 'var(--text-secondary)' }}>
                  {file ? file.name : 'Click to select or drop video file'}
                </p>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Supports MP4, WebM up to 500MB</span>
                <input
                  id="file-upload-input"
                  type="file"
                  accept="video/mp4,video/webm"
                  style={{ display: 'none' }}
                  onChange={(e) => setFile(e.target.files[0])}
                />
              </div>
            </div>

            {uploading && (
              <div style={{ marginBottom: '1.2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                  <span>Processing & Extracting Audio...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${uploadProgress}%`, height: '100%', background: 'var(--primary)', transition: 'width 0.3s' }} />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={uploading}
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.75rem' }}
            >
              {uploading ? 'Processing Video...' : 'Upload & Process Lecture'}
            </button>
          </form>
        </div>

        {/* Master Lecture List */}
        <div>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BookOpen size={20} color="var(--primary)" />
            Master Lecture Catalog ({lectures.length})
          </h2>

          {loading ? (
            <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              Loading lecture catalog...
            </div>
          ) : lectures.length === 0 ? (
            <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No master lectures found. Upload a video above to begin!
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {lectures.map((lec) => (
                <div
                  key={lec.id}
                  className="glass-panel"
                  style={{
                    padding: '1.4rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.3rem' }}>
                        <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>{lec.title}</h3>
                        <span className={`badge ${lec.status === 'ready' ? 'badge-approved' : 'badge-warning'}`}>
                          {lec.status === 'ready' ? 'Ready for Personalization' : lec.status}
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: '1.25rem', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                          <BookOpen size={14} /> {lec.subject}
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                          <User size={14} /> {lec.instructor}
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                          <Clock size={14} /> {lec.duration_seconds ? `${Math.round(lec.duration_seconds)}s` : 'Processing'}
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: '#60a5fa' }}>
                          <CheckCircle size={14} /> {lec.facts_count || 10} Syllabus Facts Extracted
                        </span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => handleInspect(lec)}
                        className="btn btn-secondary"
                        style={{ padding: '0.5rem 0.9rem', fontSize: '0.8rem' }}
                      >
                        <FileText size={15} /> Fact Graph
                      </button>
                      <button
                        onClick={() => onSelectLectureForStudent(lec.id)}
                        className="btn btn-primary"
                        style={{ padding: '0.5rem 0.9rem', fontSize: '0.8rem' }}
                      >
                        <Sparkles size={15} /> Personalize Lecture
                      </button>
                    </div>
                  </div>

                  {/* Transcript preview excerpt */}
                  {lec.master_transcript && (
                    <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.05)', fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      "{lec.master_transcript.slice(0, 180)}..."
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Fact Graph Modal Preview */}
      {inspectLecture && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '850px', maxHeight: '85vh', overflowY: 'auto', padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div>
                <span className="badge badge-primary" style={{ marginBottom: '0.4rem' }}>FAILSAFE MASTER KNOWLEDGE BASE</span>
                <h3 style={{ fontSize: '1.4rem', fontWeight: 800 }}>{inspectLecture.title}</h3>
              </div>
              <button onClick={() => setInspectLecture(null)} className="btn btn-secondary">Close</button>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              The following {inspectFacts.length} granular factual propositions, formulas, and conditions were extracted from the master lecture. Every student persona video must strictly incorporate these details to pass the Failsafe Quality Gate:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {inspectFacts.map((fact) => (
                <div key={fact.id || fact.fact_id} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '0.9rem', display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                  <span style={{ background: 'rgba(59,130,246,0.2)', color: '#60a5fa', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 700, fontSize: '0.75rem' }}>
                    {fact.fact_id}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: fact.criticality === 'critical' ? '#f87171' : '#94a3b8', fontWeight: 700 }}>
                        {fact.category} • {fact.criticality}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Timestamp ~{fact.timestamp_hint}</span>
                    </div>
                    <p style={{ fontSize: '0.9rem', color: '#f8fafc', lineHeight: 1.4 }}>{fact.statement}</p>
                    {fact.keywords && (
                      <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.4rem', flexWrap: 'wrap' }}>
                        {fact.keywords.split(',').map((kw, i) => (
                          <span key={i} style={{ background: 'rgba(255,255,255,0.05)', padding: '0.15rem 0.45rem', borderRadius: '3px', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
