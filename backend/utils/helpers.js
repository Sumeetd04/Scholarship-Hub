const crypto = require('crypto');

// ── ID Generators ─────────────────────────────────────────────
function generateOTR() {
  const year = new Date().getFullYear();
  const rand = crypto.randomBytes(4).toString('hex').toUpperCase();
  return `OTR-${year}-${rand}`;
}

function generateAppId() {
  const year = new Date().getFullYear();
  const rand = crypto.randomBytes(4).toString('hex').toUpperCase();
  return `NSP-${year}-${rand}`;
}

// ── Date formatter ────────────────────────────────────────────
function formatDate(date) {
  if (!date) return null;
  return new Date(date).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
    timeZone: 'Asia/Kolkata'
  });
}

// ── Pagination helper ─────────────────────────────────────────
function paginate(page = 1, limit = 10) {
  const p      = Math.max(1, parseInt(page));
  const l      = Math.min(100, Math.max(1, parseInt(limit)));
  const offset = (p - 1) * l;
  return { page: p, limit: l, offset };
}

module.exports = { generateOTR, generateAppId, formatDate, paginate };