import { useState, useEffect, useRef } from 'react';
import {
    ArrowLeft,
    ArrowRight,
    Building2,
    MapPin,
    Clock,
    Send,
    Download,
    RefreshCw,
    FileText,
    Briefcase,
    Edit3,
} from 'lucide-react';
import StepProgress from '../components/StepProgress';
import JdPreview from '../components/JdPreview';
import * as api from '../services/api';
import './RecruiterPage.css';

export default function RecruiterPage() {
    // ── wizard state ──
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // ── data across steps ──
    const [roles, setRoles] = useState([]);
    const [selectedRole, setSelectedRole] = useState(null);
    const [jdData, setJdData] = useState({});

    const [questions, setQuestions] = useState([]);
    const [answers, setAnswers] = useState({});

    const [profile, setProfile] = useState(null);

    // Step 4 — Choose Title
    const [suggestedRoles, setSuggestedRoles] = useState([]);
    const [chosenRole, setChosenRole] = useState('');
    const [customRole, setCustomRole] = useState('');
    const [showCustomInput, setShowCustomInput] = useState(false);
    const [roleChatHistory, setRoleChatHistory] = useState([]);
    const [roleChatInput, setRoleChatInput] = useState('');

    const [draftJd, setDraftJd] = useState('');
    const [finalJd, setFinalJd] = useState('');

    const [chatHistory, setChatHistory] = useState([]);
    const [chatInput, setChatInput] = useState('');
    const [sessionId] = useState(() => Date.now().toString());

    // ── helpers ──
    const handleError = (err) => {
        console.error(err);
        setError(err.message || 'Something went wrong');
        setLoading(false);
    };

    // ═══════════════════════════════════
    // STEP 1 — Select Role
    // ═══════════════════════════════════
    const rolesLoadedRef = useRef(false);

    useEffect(() => {
        if (rolesLoadedRef.current) return;
        rolesLoadedRef.current = true;

        async function fetchRoles() {
            setLoading(true);
            setError('');
            try {
                const data = await api.fetchRoles();
                setRoles(data || []);
            } catch (err) {
                console.error(err);
                setError(err.message || 'Failed to load roles');
            }
            setLoading(false);
        }

        fetchRoles();
    }, []);

    const selectRole = (role) => {
        setSelectedRole(role.role);
        setJdData(role);
    };

    // ═══════════════════════════════════
    // STEP 2 — Clarify
    // ═══════════════════════════════════
    const loadQuestions = async () => {
        setStep(2);
        if (questions.length) return;
        setLoading(true);
        setError('');
        try {
            const res = await api.clarifyJd(jdData);
            setQuestions(res.questions || []);
        } catch (err) {
            handleError(err);
        }
        setLoading(false);
    };

    const toggleAnswer = (qIdx, option) => {
        setAnswers((prev) => {
            const current = prev[qIdx] || [];
            const next = current.includes(option)
                ? current.filter((o) => o !== option)
                : [...current, option];
            return { ...prev, [qIdx]: next };
        });
    };

    // ═══════════════════════════════════
    // STEP 3 — Profile
    // ═══════════════════════════════════
    const loadProfile = async () => {
        setStep(3);
        if (profile) return;
        setLoading(true);
        setError('');
        try {
            const formatted = questions.map((q, i) => ({
                id: q.id,
                question: q.question,
                answer: answers[i] || [],
                target_section: q.target_section || '',
            }));
            const res = await api.buildProfile({
                form_data: jdData,
                answers: formatted,
            });
            setProfile(res.profile);
        } catch (err) {
            handleError(err);
        }
        setLoading(false);
    };

    // ═══════════════════════════════════
    // STEP 4 — Choose Title
    // ═══════════════════════════════════
    const loadSuggestions = async () => {
        setStep(4);
        if (suggestedRoles.length > 0) return;
        setLoading(true);
        setError('');
        try {
            const res = await api.suggestRoles(profile);
            setSuggestedRoles(res.suggestions || []);
            // Auto-select the first (original) role
            if (res.suggestions && res.suggestions.length > 0) {
                setChosenRole(res.suggestions[0]);
            }
        } catch (err) {
            handleError(err);
            // Fallback: use original role from profile
            const fallback = profile?.role || selectedRole || 'Unknown Role';
            setSuggestedRoles([fallback]);
            setChosenRole(fallback);
        }
        setLoading(false);
    };

    const confirmTitle = () => {
        const finalTitle = showCustomInput && customRole.trim()
            ? customRole.trim()
            : chosenRole;
        setChosenRole(finalTitle);
        generateDraft(finalTitle);
    };

    const refineRoles = async () => {
        if (!roleChatInput.trim()) return;
        setLoading(true);
        try {
            const res = await api.suggestRoles(profile, roleChatInput.trim());
            setSuggestedRoles(res.suggestions || []);
            setRoleChatHistory(prev => [
                ...prev,
                { type: 'user', text: roleChatInput.trim() },
                { type: 'system', text: `Generated ${res.suggestions.length} new titles.` }
            ]);
            setRoleChatInput('');
        } catch (err) {
            handleError(err);
        }
        setLoading(false);
    };

    // ═══════════════════════════════════
    // STEP 5 — Draft JD
    // ═══════════════════════════════════
    const generateDraft = async (roleOverride) => {
        setStep(5);
        if (draftJd) return;
        setLoading(true);
        setError('');
        try {
            const usedRole = roleOverride || chosenRole || selectedRole;
            const updatedFormData = { ...jdData, role: usedRole };
            const updatedProfile = { ...profile, role: usedRole };
            const res = await api.generateJd({
                form_data: updatedFormData,
                profile: updatedProfile,
            });
            setDraftJd(res.jd);
            setFinalJd(res.jd);
        } catch (err) {
            handleError(err);
        }
        setLoading(false);
    };

    // ═══════════════════════════════════
    // STEP 6 — Refine
    // ═══════════════════════════════════
    const applyRefinement = async () => {
        if (!chatInput.trim()) return;
        setLoading(true);
        setError('');
        try {
            const res = await api.refineJd({
                jd: finalJd,
                instruction: chatInput.trim(),
                role: chosenRole || selectedRole,
                session_id: sessionId,
            });
            setFinalJd(res.jd);
            setChatHistory((prev) => [
                ...prev,
                { instruction: chatInput.trim(), version: prev.length + 1 },
            ]);
            setChatInput('');
        } catch (err) {
            handleError(err);
        }
        setLoading(false);
    };

    // ═══════════════════════════════════
    // STEP 7 — Export
    // ═══════════════════════════════════
    const downloadDocx = async () => {
        setLoading(true);
        setError('');
        try {
            const usedRole = chosenRole || selectedRole || 'Job_Description';
            const blob = await api.exportDocx(finalJd, usedRole);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${usedRole.replace(/\s/g, '_')}_JD.docx`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (err) {
            handleError(err);
        }
        setLoading(false);
    };

    const startOver = () => {
        setStep(1);
        setSelectedRole(null);
        setJdData({});
        setQuestions([]);
        setAnswers({});
        setProfile(null);
        setSuggestedRoles([]);
        setChosenRole('');
        setCustomRole('');
        setShowCustomInput(false);
        setRoleChatHistory([]);
        setRoleChatInput('');
        setDraftJd('');
        setFinalJd('');
        setChatHistory([]);
        setChatInput('');
        setError('');
    };

    // ═══════════════════════════════════
    // RENDER
    // ═══════════════════════════════════
    return (
        <div className="recruiter-page">
            {/* Page Header */}
            <div className="page-header animate-fade-in">
                <div className="flex items-center gap-sm">
                    <FileText size={20} style={{ color: 'var(--accent-primary)' }} />
                    <h1>JD Generator</h1>
                </div>
                <p>Create professional job descriptions in 7 easy steps</p>
            </div>

            <StepProgress current={step} />

            {error && (
                <div className="alert alert-error mb-lg">
                    ⚠️ {error}
                    <button className="btn btn-ghost text-sm" onClick={() => setError('')}>
                        Dismiss
                    </button>
                </div>
            )}

            {/* ── STEP 1 ── */}
            {step === 1 && (
                <div className="step-content animate-fade-in-up">
                    <div className="card">
                        <h3 className="section-heading">Select a Job Role</h3>

                        {loading ? (
                            <div className="loading-overlay">
                                <div className="spinner" />
                                <span>Loading roles…</span>
                            </div>
                        ) : roles.length === 0 ? (
                            <div className="alert alert-warning">
                                No roles found. Make sure the backend is running.
                            </div>
                        ) : (
                            <>
                                <select
                                    className="select"
                                    value={selectedRole || ''}
                                    onChange={(e) => {
                                        const r = roles.find((r) => r.role === e.target.value);
                                        if (r) selectRole(r);
                                    }}
                                    id="role-select"
                                >
                                    <option value="" disabled>
                                        Choose a role…
                                    </option>
                                    {roles.map((r, i) => (
                                        <option key={i} value={r.role}>
                                            {r.role}
                                        </option>
                                    ))}
                                </select>

                                {selectedRole && (
                                    <div className="role-info mt-md">
                                        <div className="role-chip">
                                            <Building2 size={12} />
                                            {jdData.department || '—'}
                                        </div>
                                        <div className="role-chip">
                                            <MapPin size={12} />
                                            {jdData.location || '—'}
                                        </div>
                                        <div className="role-chip">
                                            <Clock size={12} />
                                            {jdData.experience || '—'}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>

                    <div className="step-nav">
                        <div />
                        <button
                            className="btn btn-primary"
                            disabled={!selectedRole}
                            onClick={loadQuestions}
                        >
                            Continue <ArrowRight size={14} />
                        </button>
                    </div>
                </div>
            )}

            {/* ── STEP 2 ── */}
            {step === 2 && (
                <div className="step-content animate-fade-in-up">
                    <div className="card">
                        <h3 className="section-heading">
                            Clarifying Questions — {jdData.department || ''} Head Perspective
                        </h3>
                        <p className="text-muted text-sm mb-md">
                            As the Head of <strong>{jdData.department}</strong>, answer
                            these questions about the <strong>{selectedRole}</strong> role.
                        </p>

                        {loading ? (
                            <div className="loading-overlay">
                                <div className="spinner" />
                                <span>Generating clarifying questions…</span>
                            </div>
                        ) : questions.length === 0 ? (
                            <div className="alert alert-success">
                                ✅ No clarifying questions needed — all info is available.
                            </div>
                        ) : (
                            questions.map((q, idx) => (
                                <div key={idx} className="question-block">
                                    <p className="question-text">
                                        <strong>Q{idx + 1}.</strong> {q.question}
                                    </p>
                                    <div className="options-group">
                                        {(q.options || []).map((opt, oi) => {
                                            const selected = (answers[idx] || []).includes(opt);
                                            return (
                                                <button
                                                    key={oi}
                                                    className={`option-btn ${selected ? 'selected' : ''}`}
                                                    onClick={() => toggleAnswer(idx, opt)}
                                                >
                                                    {opt}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    <div className="step-nav">
                        <button
                            className="btn btn-secondary"
                            onClick={() => setStep(1)}
                        >
                            <ArrowLeft size={14} /> Back
                        </button>
                        <button
                            className="btn btn-primary"
                            onClick={loadProfile}
                            disabled={loading}
                        >
                            Build Profile <ArrowRight size={14} />
                        </button>
                    </div>
                </div>
            )}

            {/* ── STEP 3 ── */}
            {step === 3 && (
                <div className="step-content animate-fade-in-up">
                    {loading ? (
                        <div className="loading-overlay">
                            <div className="spinner" />
                            <span>Building ideal candidate profile…</span>
                        </div>
                    ) : profile ? (
                        <>
                            <div className="profile-hero">
                                <div className="profile-hero-title">
                                    🎯 Ideal Candidate Profile
                                </div>
                                <div className="profile-hero-sub">
                                    {profile.role || selectedRole} —{' '}
                                    {profile.department || jdData.department} Department
                                </div>
                            </div>

                            {profile.profile_summary && (
                                <div className="alert alert-info mb-lg">
                                    {profile.profile_summary}
                                </div>
                            )}

                            <div className="grid grid-2">
                                <div className="card">
                                    <h3 className="section-heading">💡 Core Competencies</h3>
                                    <div className="chip-group">
                                        {(profile.core_competencies || []).map((c, i) => (
                                            <span key={i} className="chip">{c}</span>
                                        ))}
                                    </div>
                                    <h3 className="section-heading mt-lg">🛠️ Must-Have Skills</h3>
                                    <ul className="skill-list">
                                        {(profile.must_have_skills_refined || []).map((s, i) => (
                                            <li key={i}>{s}</li>
                                        ))}
                                    </ul>
                                </div>

                                <div className="card">
                                    <h3 className="section-heading">🧠 Behavioral Traits</h3>
                                    <div className="chip-group">
                                        {(profile.behavioral_traits || []).map((t, i) => (
                                            <span key={i} className="chip">{t}</span>
                                        ))}
                                    </div>
                                    <h3 className="section-heading mt-lg">✨ Nice-to-Have</h3>
                                    <ul className="skill-list">
                                        {(profile.nice_to_have_skills || []).map((s, i) => (
                                            <li key={i}>{s}</li>
                                        ))}
                                    </ul>
                                </div>
                            </div>

                            {(profile.success_metrics || []).length > 0 && (
                                <div className="card mt-lg">
                                    <h3 className="section-heading">📊 Success Metrics</h3>
                                    <ul className="skill-list">
                                        {profile.success_metrics.map((m, i) => (
                                            <li key={i}>{m}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {profile.team_context && (
                                <div className="alert alert-info mt-md">
                                    <strong>👥 Team Context:</strong> {profile.team_context}
                                </div>
                            )}
                        </>
                    ) : null}

                    <div className="step-nav">
                        <button
                            className="btn btn-secondary"
                            onClick={() => {
                                setProfile(null);
                                setStep(2);
                            }}
                        >
                            <ArrowLeft size={14} /> Back
                        </button>
                        <button
                            className="btn btn-primary"
                            onClick={loadSuggestions}
                            disabled={loading || !profile}
                        >
                            Choose Role Title <ArrowRight size={14} />
                        </button>
                    </div>
                </div>
            )}

            {/* ── STEP 4 — Choose Title ── */}
            {step === 4 && (
                <div className="step-content animate-fade-in-up">
                    {loading ? (
                        <div className="loading-overlay">
                            <div className="spinner" />
                            <span>Generating role title suggestions…</span>
                        </div>
                    ) : (
                        <>
                            <div className="card mb-lg">
                                <h3 className="section-heading">
                                    <Briefcase size={16} /> Choose a Job Title
                                </h3>
                                <p className="text-muted text-sm mb-md">
                                    Select a suggested title or type your own. This title will be
                                    used throughout the Job Description.
                                </p>

                                <div className="role-suggestion-grid">
                                    {suggestedRoles.map((role, i) => (
                                        <button
                                            key={i}
                                            className={`role-suggestion-card ${!showCustomInput && chosenRole === role ? 'selected' : ''
                                                }`}
                                            onClick={() => {
                                                setChosenRole(role);
                                                setShowCustomInput(false);
                                            }}
                                        >
                                            <span className="role-suggestion-icon">
                                                {i === 0 ? '⭐' : '💼'}
                                            </span>
                                            <span className="role-suggestion-label">
                                                {role}
                                            </span>
                                            {i === 0 && (
                                                <span className="role-badge">Original</span>
                                            )}
                                        </button>
                                    ))}

                                    <button
                                        className={`role-suggestion-card custom-card ${showCustomInput ? 'selected' : ''
                                            }`}
                                        onClick={() => setShowCustomInput(true)}
                                    >
                                        <span className="role-suggestion-icon"><Edit3 size={16} /></span>
                                        <span className="role-suggestion-label">Custom Title</span>
                                    </button>
                                </div>

                                {showCustomInput && (
                                    <div className="custom-role-input mt-md">
                                        <input
                                            className="input"
                                            placeholder="Enter your custom job title…"
                                            value={customRole}
                                            onChange={(e) => setCustomRole(e.target.value)}
                                            autoFocus
                                            id="custom-role-input"
                                        />
                                    </div>
                                )}
                            </div>

                            {/* Role Chat Interface */}
                            <div className="card mb-lg" style={{ background: 'var(--slate-50)', border: '1px dashed var(--border-default)' }}>
                                <div className="section-heading mb-sm">
                                    <span style={{ fontSize: '0.8rem' }}>🤔 Discuss & Refine Titles</span>
                                </div>

                                <div className="chat-history simple-chat" style={{ maxHeight: '150px', marginBottom: '8px' }}>
                                    {roleChatHistory.map((msg, i) => (
                                        <div key={i} className={`chat-bubble ${msg.type === 'user' ? 'user' : 'system'}`} style={{ fontSize: '0.75rem', padding: '6px 10px' }}>
                                            {msg.type === 'user' ? '👤' : '🤖'} {msg.text}
                                        </div>
                                    ))}
                                    {roleChatHistory.length === 0 && (
                                        <p className="text-muted text-xs">Target a specific style? Just ask AI below.</p>
                                    )}
                                </div>

                                <div className="chat-input-row">
                                    <input
                                        className="input chat-text-input"
                                        placeholder="e.g. Make them more creative / professional / concise..."
                                        value={roleChatInput}
                                        onChange={(e) => setRoleChatInput(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && refineRoles()}
                                        disabled={loading}
                                        style={{ fontSize: '0.813rem' }}
                                    />
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        onClick={refineRoles}
                                        disabled={loading || !roleChatInput.trim()}
                                    >
                                        <Send size={12} />
                                    </button>
                                </div>
                            </div>

                            <div className="alert alert-info mb-lg">
                                ✏️ Selected title: <strong>{showCustomInput && customRole.trim() ? customRole.trim() : chosenRole}</strong>
                            </div>
                        </>
                    )}

                    <div className="step-nav">
                        <button
                            className="btn btn-secondary"
                            onClick={() => {
                                setSuggestedRoles([]);
                                setChosenRole('');
                                setStep(3);
                            }}
                        >
                            <ArrowLeft size={14} /> Back to Profile
                        </button>
                        <button
                            className="btn btn-primary"
                            onClick={confirmTitle}
                            disabled={loading || (!chosenRole && !(showCustomInput && customRole.trim()))}
                        >
                            Generate JD <ArrowRight size={14} />
                        </button>
                    </div>
                </div>
            )}

            {/* ── STEP 5 — Draft JD ── */}
            {step === 5 && (
                <div className="step-content animate-fade-in-up">
                    {loading ? (
                        <div className="loading-overlay">
                            <div className="spinner" />
                            <span>Generating Job Description…</span>
                        </div>
                    ) : (
                        <>
                            <div className="alert alert-success mb-lg">
                                ✅ Draft JD generated! Review it below, then proceed to refine.
                            </div>
                            <JdPreview markdown={finalJd} />
                        </>
                    )}

                    <div className="step-nav">
                        <button
                            className="btn btn-secondary"
                            onClick={() => {
                                setDraftJd('');
                                setFinalJd('');
                                setStep(4);
                            }}
                        >
                            <ArrowLeft size={14} /> Back to Title
                        </button>
                        <button
                            className="btn btn-primary"
                            onClick={() => setStep(6)}
                            disabled={loading || !finalJd}
                        >
                            Refine with Chat <ArrowRight size={14} />
                        </button>
                    </div>
                </div>
            )}

            {/* ── STEP 6 — Refine ── */}
            {step === 6 && (
                <div className="step-content animate-fade-in-up">
                    <div className="card">
                        <h3 className="section-heading">💬 Refine Your JD</h3>
                        <p className="text-muted text-sm mb-md">
                            Type an instruction and click <strong>Apply</strong>. Each time
                            you apply, a new version is generated. Click <strong>Finalize</strong>{' '}
                            when you're happy.
                        </p>

                        <div className="chat-history">
                            {chatHistory.map((entry, i) => (
                                <div key={i} className="chat-pair">
                                    <div className="chat-bubble user">
                                        💬 <strong>You:</strong> {entry.instruction}
                                    </div>
                                    <div className="chat-bubble system">
                                        ✅ Applied — version {entry.version}
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="chat-input-row">
                            <input
                                className="input chat-text-input"
                                placeholder="e.g. Make it more concise / Add Python requirement"
                                value={chatInput}
                                onChange={(e) => setChatInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && applyRefinement()}
                                disabled={loading}
                                id="refine-input"
                            />
                            <button
                                className="btn btn-primary"
                                onClick={applyRefinement}
                                disabled={loading || !chatInput.trim()}
                            >
                                <Send size={14} /> Apply
                            </button>
                        </div>
                    </div>

                    <details className="jd-details mt-lg" open>
                        <summary>📄 Current JD Preview</summary>
                        <div className="jd-details-body">
                            <JdPreview markdown={finalJd} />
                        </div>
                    </details>

                    <div className="step-nav">
                        <button
                            className="btn btn-secondary"
                            onClick={() => setStep(5)}
                        >
                            <ArrowLeft size={14} /> Back to Draft
                        </button>
                        <button
                            className="btn btn-primary"
                            onClick={() => setStep(7)}
                        >
                            Finalize & Export <ArrowRight size={14} />
                        </button>
                    </div>
                </div>
            )}

            {/* ── STEP 7 — Export ── */}
            {step === 7 && (
                <div className="step-content animate-fade-in-up">
                    <div className="alert alert-success mb-lg">
                        🎉 Your Job Description is ready!
                    </div>

                    <JdPreview markdown={finalJd} />

                    <details className="jd-details mt-lg">
                        <summary>✏️ Manual Edit (optional)</summary>
                        <div className="jd-details-body">
                            <textarea
                                className="textarea"
                                rows={12}
                                value={finalJd}
                                onChange={(e) => setFinalJd(e.target.value)}
                            />
                        </div>
                    </details>

                    <hr className="divider" />

                    <h3 className="section-heading">📥 Download your JD</h3>
                    <button
                        className="btn btn-primary btn-block btn-lg"
                        onClick={downloadDocx}
                        disabled={loading}
                        id="download-docx-btn"
                    >
                        {loading ? (
                            <>
                                <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                                Generating DOCX…
                            </>
                        ) : (
                            <>
                                <Download size={14} /> Download as DOCX
                            </>
                        )}
                    </button>

                    {chatHistory.length > 0 && (
                        <p className="text-muted text-sm mt-md text-center">
                            💾 {chatHistory.length} refinement(s) applied
                        </p>
                    )}

                    <hr className="divider" />

                    <button
                        className="btn btn-secondary btn-block"
                        onClick={startOver}
                    >
                        <RefreshCw size={14} /> Create Another JD
                    </button>
                </div>
            )}
        </div>
    );
}
