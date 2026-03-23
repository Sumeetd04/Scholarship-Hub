/* ============================================================
   script.js  —  UI interactions
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Dropdown menus ─────────────────────────────────────────
  document.querySelectorAll('.nav-item').forEach(item => {
    const trigger  = item.querySelector('span');
    const dropdown = item.querySelector('.dropdown');
    if (!trigger || !dropdown) return;
    trigger.addEventListener('click', e => {
      e.stopPropagation();
      const wasOpen = dropdown.classList.contains('open');
      document.querySelectorAll('.dropdown.open').forEach(d => d.classList.remove('open'));
      if (!wasOpen) dropdown.classList.add('open');
    });
  });
  document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown.open').forEach(d => d.classList.remove('open'));
  });
  document.querySelectorAll('.dropdown').forEach(d => {
    d.addEventListener('click', e => e.stopPropagation());
  });

  // ── Mobile nav hamburger ───────────────────────────────────
  const hamburger = document.getElementById('hamburger');
  const navLinks  = document.querySelector('.nav-links');
  const navRight  = document.querySelector('.nav-right');
  if (hamburger) {
    hamburger.addEventListener('click', () => {
      navLinks?.classList.toggle('mobile-open');
      navRight?.classList.toggle('mobile-open');
      hamburger.classList.toggle('active');
    });
  }

  // ── Carousel ───────────────────────────────────────────────
  const slidesEl = document.getElementById('slides');
  if (slidesEl) {
    let current = 0;
    const dots  = document.querySelectorAll('.dot');
    const total = slidesEl.children.length;
    window.goSlide = n => {
      current = (n + total) % total;
      slidesEl.style.transform = `translateX(-${current * 100}%)`;
      dots.forEach((d, i) => d.classList.toggle('active', i === current));
    };
    window.changeSlide = dir => goSlide(current + dir);
    setInterval(() => goSlide(current + 1), 5000);
  }

  // ── Tracker enter key ──────────────────────────────────────
  const trackerInput = document.getElementById('app-id');
  if (trackerInput) {
    trackerInput.addEventListener('keypress', e => {
      if (e.key === 'Enter') trackApplication();
    });
  }

  // ── Search bar ─────────────────────────────────────────────
  if (typeof initSearch === 'function') initSearch();

  // ── Update nav for logged-in users ─────────────────────────
  if (typeof updateNavForUser === 'function') updateNavForUser();

  // ── Toast slide-in animation ───────────────────────────────
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn { from { opacity:0; transform:translateX(40px); } to { opacity:1; transform:translateX(0); } }

    /* ── Modal styles ── */
    .sh-modal-overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,.55); z-index:10000; align-items:center; justify-content:center; padding:20px; }
    .sh-modal-overlay.open { display:flex; }
    .sh-modal-box { background:#fff; border-radius:20px; padding:36px; max-width:660px; width:100%; max-height:90vh; overflow-y:auto; position:relative; }
    .sh-modal-close { position:absolute; top:16px; right:16px; background:var(--off-white); border:1px solid var(--border); border-radius:8px; width:34px; height:34px; cursor:pointer; font-size:16px; display:flex; align-items:center; justify-content:center; transition:background .2s; }
    .sh-modal-close:hover { background:var(--border); }
    .modal-header-row { display:flex; align-items:flex-start; gap:14px; margin-bottom:20px; }
    .modal-icon { width:50px; height:50px; background:var(--green-light); border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:24px; flex-shrink:0; }
    .modal-title { font-size:18px; color:var(--text-dark); margin-bottom:4px; }
    .modal-sub { font-size:13px; color:var(--text-light); }
    .modal-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:12px; margin-bottom:20px; }
    .modal-cell { background:var(--off-white); border-radius:10px; padding:12px 14px; }
    .modal-cell label { font-size:10px; color:var(--text-light); text-transform:uppercase; letter-spacing:.5px; display:block; }
    .modal-cell p { font-size:14px; font-weight:600; color:var(--text-dark); margin-top:4px; }
    .modal-section { margin-bottom:18px; }
    .modal-section h4 { font-family:'DM Sans',Arial,sans-serif; font-size:13px; font-weight:700; color:var(--text-light); text-transform:uppercase; letter-spacing:.5px; margin-bottom:8px; }
    .modal-section p { font-size:14px; color:var(--text-mid); line-height:1.7; }
    .modal-actions { display:flex; gap:10px; margin-top:24px; padding-top:20px; border-top:1px solid var(--border); }

    /* ── Mobile nav ── */
    @media (max-width: 768px) {
      nav { padding:0 16px; height:60px; flex-wrap:wrap; }
      .nav-links { display:none; width:100%; flex-direction:column; background:white; padding:12px 0; border-top:1px solid var(--border); order:3; }
      .nav-links.mobile-open { display:flex; }
      .nav-right { display:none; width:100%; padding:10px 0 16px; order:4; }
      .nav-right.mobile-open { display:flex; }
      .nav-item > a, .nav-item > span { padding:10px 16px; width:100%; }
      .dropdown { position:static; box-shadow:none; border:none; padding-left:24px; }
      #hamburger { display:flex; }
      .hero .slide { padding:0 24px; }
      .slide h2 { font-size:28px; }
      section { padding:40px 20px; }
      .cards-grid { grid-template-columns:1fr 1fr; }
      .about-grid { grid-template-columns:1fr; }
      .announce-grid { grid-template-columns:1fr; }
      .footer-grid { grid-template-columns:1fr 1fr; gap:24px; }
      .listings-grid { grid-template-columns:1fr; }
      .stats-bar { padding:16px 20px; flex-wrap:wrap; gap:16px; }
      .filter-bar { padding:16px 20px; }
    }
    #hamburger { display:none; flex-direction:column; gap:5px; cursor:pointer; padding:8px; background:none; border:none; }
    #hamburger span { display:block; width:22px; height:2px; background:var(--text-dark); border-radius:2px; transition:all .3s; }
    #hamburger.active span:nth-child(1) { transform:translateY(7px) rotate(45deg); }
    #hamburger.active span:nth-child(2) { opacity:0; }
    #hamburger.active span:nth-child(3) { transform:translateY(-7px) rotate(-45deg); }
  `;
  document.head.appendChild(style);
});
