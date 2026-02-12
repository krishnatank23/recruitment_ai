const API_BASE = '';

async function request(url, options = {}) {
    const res = await fetch(`${API_BASE}${url}`, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`API Error ${res.status}: ${text}`);
    }

    return res.json();
}

export async function fetchRoles() {
    return request('/jd/jd/roles');
}

export async function clarifyJd(formData) {
    return request('/jd/jd/clarify', {
        method: 'POST',
        body: JSON.stringify(formData),
    });
}

export async function buildProfile(payload) {
    return request('/jd/jd/profile', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function generateJd(payload) {
    return request('/jd/jd/generate', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function refineJd(payload) {
    return request('/jd/jd/refine', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function exportDocx(jdText, role) {
    const res = await fetch(`${API_BASE}/jd/jd/export-docx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jd: jdText, role }),
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Export Error ${res.status}: ${text}`);
    }

    return res.blob();
}

export async function runPipeline(formData) {
    const res = await fetch(`${API_BASE}/pipeline/run_pipeline`, {
        method: 'POST',
        body: formData, // FormData — no Content-Type header, browser sets boundary
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Pipeline Error ${res.status}: ${text}`);
    }

    return res.json();
}

// ── CV Analysis Pipeline ──

export async function buildPersonas(profile) {
    return request('/cv/personas', {
        method: 'POST',
        body: JSON.stringify({ profile }),
    });
}

export async function evaluateCVs(resumeFile, personas) {
    const formData = new FormData();
    formData.append('resumes', resumeFile);
    formData.append('personas', JSON.stringify(personas));

    const res = await fetch(`${API_BASE}/cv/evaluate`, {
        method: 'POST',
        body: formData,
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`CV Evaluate Error ${res.status}: ${text}`);
    }

    return res.json();
}

export async function rankCandidates(evaluations, topN = 10) {
    return request('/cv/rank', {
        method: 'POST',
        body: JSON.stringify({ evaluations, top_n: topN }),
    });
}

export async function runFullCVPipeline(resumeFile, profile, topN = 10) {
    const formData = new FormData();
    formData.append('resumes', resumeFile);
    formData.append('profile', JSON.stringify(profile));
    formData.append('top_n', topN.toString());

    const res = await fetch(`${API_BASE}/cv/full`, {
        method: 'POST',
        body: formData,
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`CV Pipeline Error ${res.status}: ${text}`);
    }

    return res.json();
}

