const jwt = require('jsonwebtoken');
require('dotenv').config();

// ── Any logged-in user ────────────────────────────────────────
function protect(req, res, next) {
  const token = (req.headers['authorization'] || '').split(' ')[1];
  if (!token) {
    return res.status(401).json({ success: false, message: 'No token. Please login.' });
  }
  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET);
    next();
  } catch {
    return res.status(403).json({ success: false, message: 'Invalid or expired token.' });
  }
}

// ── Admin only ────────────────────────────────────────────────
function adminOnly(req, res, next) {
  protect(req, res, () => {
    if (req.user.role !== 'admin') {
      return res.status(403).json({ success: false, message: 'Admin access only.' });
    }
    next();
  });
}

module.exports = { protect, adminOnly };
