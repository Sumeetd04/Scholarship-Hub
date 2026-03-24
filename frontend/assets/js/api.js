/* ============================================================
   api.js  —  All communication between frontend and backend
   ============================================================ */

// ── Smart API base: works on localhost AND any deployed server ─
const API_BASE = (() => {
  const h = window.location.hostname;
  if (h === '127.0.0.1' || h === 'localhost' || h === '') {
    return 'http://localhost:5000/api';
  }
  return window.location.origin + '/api';
})();

// ── Auth helpers ──────────────────────────────────────────────
const Auth = {
  save:      (token, user) => { localStorage.setItem('sh_token', token); localStorage.setItem('sh_user', JSON.stringify(user)); },
  token:     ()            => localStorage.getItem('sh_token'),
  user:      ()            => JSON.parse(localStorage.getItem('sh_user') || 'null'),
  logout:    ()            => { localStorage.removeItem('sh_token'); localStorage.removeItem('sh_user'); window.location.href = _root() + 'pages/login.html'; },
  isLoggedIn:()            => !!localStorage.getItem('sh_token'),
  isAdmin:   ()            => { const u = Auth.user(); return u && u.role === 'admin'; }
};

function _root() {
  const p = window.location.pathname;
  return p.includes('/pages/') ? '../' : './';
}

// ── Generic fetch wrapper ─────────────────────────────────────
async function apiFetch(path, options = {}) {
  const token = Auth.token();
  try {
    const res = await fetch(API_BASE + path, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(options.headers || {})
      }
    });
    return await res.json();
  } catch (err) {
    console.error('apiFetch error:', err);
    return { success: false, message: 'Could not reach the server. Please make sure the backend is running.' };
  }
}

// ── Load scholarships into a grid ─────────────────────────────
async function loadScholarships(type, containerSelector) {
  const container = document.querySelector(containerSelector);
  if (!container) return;
  container.innerHTML = '<div class="loading">Loading scholarships...</div>';

  const data = await apiFetch(`/scholarships?type=${type}&limit=20`);

  // Server not reachable
  if (!data.success && data.message && data.message.toLowerCase().includes('reach')) {
    container.innerHTML = `
      <div style="text-align:center;padding:60px 20px;color:var(--text-light)">
        <div style="font-size:52px;margin-bottom:16px">&#128268;</div>
        <h3 style="font-size:18px;color:var(--text-dark);margin-bottom:10px">Backend server is offline</h3>
        <p style="font-size:14px;margin-bottom:18px">Start the server to see scholarships:</p>
        <code style="background:var(--off-white);border:1px solid var(--border);padding:10px 20px;border-radius:8px;font-size:13px;display:inline-block">
          cd backend &amp;amp;&amp;amp; npm run dev
        </code>
      </div>`;
    const hdr = document.querySelector('.listings-header h3');
    if (hdr) hdr.textContent = 'Server offline';
    return;
  }

  if (!data.success || !data.scholarships || !data.scholarships.length) {
    container.innerHTML = `
      <div style="text-align:center;padding:60px 20px;color:var(--text-light)">
        <div style="font-size:52px;margin-bottom:16px">&#128218;</div>
        <h3 style="font-size:18px;color:var(--text-dark);margin-bottom:10px">No scholarships found</h3>
        <p style="font-size:14px">No ${type} scholarships available right now.</p>
      </div>`;
    const hdr = document.querySelector('.listings-header h3');
    if (hdr) hdr.textContent = '0 Scholarships';
    return;
  }

  const hdr = document.querySelector('.listings-header h3');
  if (hdr) hdr.textContent = `Showing ${data.scholarships.length} of ${data.total} Scholarships`;
  container.innerHTML = data.scholarships.map(s => _scholarshipCard(s)).join('');
}

function _scholarshipCard(s) {
  return `
    <div class="s-card">
      <div class="s-card-top">
        <div class="s-flag">${_typeIcon(s.type)}</div>
        <div class="s-info">
          <h4>${_esc(s.title)}</h4>
          <p class="s-sub">${_esc(s.provider)} · ${_esc(s.level || 'All Levels')}</p>
        </div>
        <span class="s-badge ${_badgeClass(s.status)}">${_badgeLabel(s.status)}</span>
      </div>
      <p class="s-desc">${_esc(s.description || '')}</p>
      <div class="s-meta">
        <span>💰 ${_esc(s.amount || 'See details')}</span>
        ${s.deadline ? `<span>📅 Deadline: ${_fmtDate(s.deadline)}</span>` : ''}
        ${s.category ? `<span>👥 ${_esc(s.category)}</span>` : ''}
      </div>
      <div class="s-actions">
        <a href="${_esc(s.apply_link || 'https://scholarships.gov.in')}" target="_blank" class="btn-card">Apply Now &rarr;</a>
        <button class="btn-card-outline" onclick="openScholarshipModal(${JSON.stringify(s).replace(/"/g,'&quot;')})">View Details</button>
      </div>
    </div>`;
}

// ── Scholarship detail modal ──────────────────────────────────
function openScholarshipModal(s) {
  let modal = document.getElementById('sh-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'sh-modal';
    modal.className = 'sh-modal-overlay';
    modal.innerHTML = `<div class="sh-modal-box">
      <button class="sh-modal-close" onclick="closeScholarshipModal()">✕</button>
      <div id="sh-modal-body"></div>
    </div>`;
    modal.addEventListener('click', e => { if (e.target === modal) closeScholarshipModal(); });
    document.body.appendChild(modal);
  }
  document.getElementById('sh-modal-body').innerHTML = `
    <div class="modal-header-row">
      <div class="modal-icon">${_typeIcon(s.type)}</div>
      <div>
        <h3 class="modal-title">${_esc(s.title)}</h3>
        <p class="modal-sub">${_esc(s.provider)} ${s.country ? '· ' + _esc(s.country) : ''}</p>
      </div>
      <span class="s-badge ${_badgeClass(s.status)}">${_badgeLabel(s.status)}</span>
    </div>
    <div class="modal-grid">
      ${s.amount   ? `<div class="modal-cell"><label>Amount</label><p>${_esc(s.amount)}</p></div>` : ''}
      ${s.level    ? `<div class="modal-cell"><label>Level</label><p>${_esc(s.level)}</p></div>` : ''}
      ${s.category ? `<div class="modal-cell"><label>Category</label><p>${_esc(s.category)}</p></div>` : ''}
      ${s.deadline ? `<div class="modal-cell"><label>Deadline</label><p>${_fmtDate(s.deadline)}</p></div>` : ''}
      ${s.field    ? `<div class="modal-cell"><label>Field</label><p>${_esc(s.field)}</p></div>` : ''}
    </div>
    ${s.description ? `<div class="modal-section"><h4>About</h4><p>${_esc(s.description)}</p></div>` : ''}
    ${s.eligibility ? `<div class="modal-section"><h4>Eligibility</h4><p>${_esc(s.eligibility)}</p></div>` : ''}
    <div class="modal-actions">
      <a href="${_esc(s.apply_link || 'https://scholarships.gov.in')}" target="_blank" class="btn-card" style="display:inline-block;padding:12px 28px;font-size:14px">Apply Now &rarr;</a>
      <button class="btn-card-outline" onclick="closeScholarshipModal()" style="padding:12px 20px;font-size:14px">Close</button>
    </div>`;
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeScholarshipModal() {
  const modal = document.getElementById('sh-modal');
  if (modal) { modal.classList.remove('open'); document.body.style.overflow = ''; }
}

// ── Track application ─────────────────────────────────────────
async function trackApplication() {
  const input  = document.getElementById('app-id');
  const result = document.getElementById('status-result');
  if (!input || !result) return;
  const val = input.value.trim();
  if (!val) { showToast('Please enter an Application ID or OTR Number.', 'error'); return; }
  result.innerHTML = '<div class="loading">Searching…</div>';
  result.classList.add('show');
  const data = await apiFetch(`/applications/track/${encodeURIComponent(val)}`);
  if (!data.success) {
    result.innerHTML = `<div class="status-card" style="text-align:center;color:#c0392b;padding:32px">❌ ${_esc(data.message)}</div>`;
    return;
  }
  const a     = data.application;
  const steps = ['submitted','verified','sanctioned','disbursed','complete'];
  const cur   = steps.indexOf(a.status);
  result.innerHTML = `
    <div class="status-card">
      <div class="status-top">
        <div>
          <div class="status-name">${_esc(a.full_name)}</div>
          <div class="status-id">App ID: ${_esc(a.app_id)} &nbsp;·&nbsp; ${_esc(a.scholarship_title)}</div>
        </div>
        <span class="status-badge ${_statusBadge(a.status)}">${_statusLabel(a.status)}</span>
      </div>
      <div class="progress-steps">
        ${steps.map((s,i) => `
          <div class="step ${i < cur ? 'done' : i === cur ? 'active' : ''}">
            <div class="step-circle">${i < cur ? '✓' : i+1}</div>
            <div class="step-label">${_cap(s)}</div>
          </div>`).join('')}
      </div>
      <div class="status-info-grid">
        <div class="info-cell"><label>Scholarship</label><p>${_esc(a.scholarship_title)}</p></div>
        <div class="info-cell"><label>Amount</label><p>${a.amount_sanctioned ? '₹'+Number(a.amount_sanctioned).toLocaleString('en-IN') : a.amount || 'Pending'}</p></div>
        <div class="info-cell"><label>Academic Year</label><p>${_esc(a.academic_year)}</p></div>
        <div class="info-cell"><label>Applied On</label><p>${_fmtDate(a.created_at)}</p></div>
        <div class="info-cell"><label>Type</label><p>${_cap(a.app_type)}</p></div>
        <div class="info-cell"><label>Last Updated</label><p>${_fmtDate(a.updated_at)}</p></div>
        ${a.rejection_reason ? `<div class="info-cell" style="grid-column:1/-1"><label>Rejection Reason</label><p style="color:#c0392b">${_esc(a.rejection_reason)}</p></div>` : ''}
      </div>
    </div>`;
  result.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ── Load announcements ────────────────────────────────────────
async function loadAnnouncements() {
  const data = await apiFetch('/announcements');
  if (!data.success) return;
  const { grouped } = data;
  _renderCol('col-upcoming', grouped.upcoming, false);
  _renderCol('col-current',  grouped.current,  true);
  _renderCol('col-previous', grouped.previous, false);
}

function _renderCol(cls, items, isCurrent) {
  const col = document.querySelector('.' + cls);
  if (!col) return;
  const header = col.querySelector('h3');
  col.innerHTML = '';
  if (header) col.appendChild(header);
  if (!items || !items.length) {
    col.innerHTML += '<p style="color:var(--text-light);font-size:13px;padding:8px 0">No announcements yet.</p>';
    return;
  }
  items.forEach(a => {
    const el = document.createElement('div');
    el.className = isCurrent ? 'current-item' : 'announce-item';
    el.innerHTML = isCurrent
      ? `<h4>${_esc(a.title)}</h4><p>${_esc(a.content)}</p>
         ${a.link ? `<a href="${_esc(a.link)}" target="_blank">${_esc(a.link_text||'Learn More')} ↗</a>` : ''}`
      : `${a.is_new ? '<span class="announce-new">New</span>' : ''}
         <p><strong>${_esc(a.title)}</strong> — ${_esc(a.content)}</p>
         ${a.link ? `<a href="${_esc(a.link)}" target="_blank" style="color:var(--green);font-weight:600;font-size:13px">${_esc(a.link_text||'View')} ↗</a>` : ''}
         <div class="announce-date">📅 ${_fmtDate(a.created_at)}</div>`;
    col.appendChild(el);
  });
}

// ── Submit contact form ───────────────────────────────────────
async function submitContactForm() {
  const g = id => document.getElementById(id)?.value?.trim() || '';
  const req = {
    first_name: g('fname'), last_name: g('lname'), email: g('email'),
    mobile: g('phone'), app_ref: g('app-ref'), query_type: g('query-type'), message: g('message')
  };
  if (!req.first_name || !req.last_name || !req.email || !req.query_type || !req.message) {
    showToast('Please fill in all required fields marked with *', 'error'); return;
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(req.email)) {
    showToast('Please enter a valid email address.', 'error'); return;
  }
  const btn = document.querySelector('.btn-submit');
  if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }
  const data = await apiFetch('/contact', { method: 'POST', body: JSON.stringify(req) });
  if (data.success) {
    document.getElementById('success-msg')?.classList.add('show');
    if (btn) { btn.textContent = '✓ Message Sent'; btn.style.background = '#2ea06a'; }
  } else {
    showToast(data.message || 'Something went wrong. Please try again.', 'error');
    if (btn) { btn.disabled = false; btn.textContent = 'Send Message →'; }
  }
}

// ── Update navbar for logged-in user ─────────────────────────
function updateNavForUser() {
  const applyBtn = document.querySelector('.btn-apply');
  if (!applyBtn) return;
  if (!Auth.isLoggedIn()) {
    applyBtn.href = _root() + 'pages/login.html';
    applyBtn.textContent = 'Login / Register';
    return;
  }
  const user = Auth.user();
  applyBtn.outerHTML = `
    <div class="nav-item" style="position:relative">
      <span style="cursor:pointer;display:flex;align-items:center;gap:6px;padding:8px 14px;background:var(--green-light);color:var(--green);border-radius:8px;font-size:14px;font-weight:600"
            onclick="this.nextElementSibling.classList.toggle('open')">
        👤 ${_esc(user.full_name.split(' ')[0])} <span style="font-size:10px">▾</span>
      </span>
      <div class="dropdown">
        <a href="${_root()}pages/dashboard.html">My Applications</a>
        ${Auth.isAdmin() ? `<a href="${_root()}pages/admin.html">⚙️ Admin Panel</a>` : ''}
        <a href="#" onclick="Auth.logout()" style="color:#c0392b">Logout</a>
      </div>
    </div>`;
}

// ── Search ────────────────────────────────────────────────────
function initSearch() {
  const inputs = document.querySelectorAll('.nav-search input');
  inputs.forEach(input => {
    input.addEventListener('keypress', e => {
      if (e.key === 'Enter') {
        const q = input.value.trim();
        if (q) window.location.href = _root() + 'pages/search.html?q=' + encodeURIComponent(q);
      }
    });
    const btn = input.closest('.nav-search')?.querySelector('.nav-search-icon');
    if (btn) btn.style.cursor = 'pointer';
    if (btn) btn.addEventListener('click', () => {
      const q = input.value.trim();
      if (q) window.location.href = _root() + 'pages/search.html?q=' + encodeURIComponent(q);
    });
  });
}

// ── Toast notification ────────────────────────────────────────
function showToast(msg, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position:fixed;top:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  const colors = { success:'#1a7a4a', error:'#c0392b', info:'#1a5a9a', warning:'#a07a0e' };
  toast.style.cssText = `background:${colors[type]||colors.info};color:white;padding:12px 20px;border-radius:10px;font-size:14px;font-weight:500;max-width:320px;box-shadow:0 4px 20px rgba(0,0,0,.2);animation:slideIn .3s ease;`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity='0'; toast.style.transition='opacity .3s'; setTimeout(()=>toast.remove(),300); }, 3500);
}

// ── Helpers ───────────────────────────────────────────────────
function _esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function _typeIcon(t)   { return {international:'🌐',national:'🇮🇳',state:'🏛️',private:'🏢'}[t]||'🎓'; }
function _badgeClass(s) { return {open:'badge-open',closing_soon:'badge-closing',upcoming:'badge-upcoming',closed:'badge-closing'}[s]||'badge-open'; }
function _badgeLabel(s) { return {open:'Open',closing_soon:'Closing Soon',upcoming:'Upcoming',closed:'Closed'}[s]||s; }
function _statusBadge(s){ return {submitted:'badge-review',verified:'badge-review',sanctioned:'badge-pending',disbursed:'badge-approved',complete:'badge-approved',rejected:'badge-closing'}[s]||'badge-review'; }
function _statusLabel(s){ return {submitted:'⏳ Submitted',verified:'✓ Verified',sanctioned:'✅ Sanctioned',disbursed:'💰 Disbursed',complete:'🎉 Complete',rejected:'❌ Rejected'}[s]||s; }
function _cap(str)      { return str ? str.charAt(0).toUpperCase()+str.slice(1) : ''; }
function _fmtDate(d)    { return d ? new Date(d).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'}) : '—'; }
