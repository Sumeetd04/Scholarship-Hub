const db = require('../config/db');

// GET /api/announcements
exports.getAll = async (req, res) => {
  try {
    const { category } = req.query;
    let query  = 'SELECT * FROM announcements WHERE 1=1';
    let params = [];
    if (category) { query += ' AND category = ?'; params.push(category); }
    query += ' ORDER BY created_at DESC';

    const [rows] = await db.query(query, params);

    // Group by category for frontend convenience
    const grouped = { upcoming: [], current: [], previous: [] };
    rows.forEach(a => { if (grouped[a.category]) grouped[a.category].push(a); });

    res.json({ success: true, announcements: rows, grouped });
  } catch (err) {
    console.error('getAll announcements:', err);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};
