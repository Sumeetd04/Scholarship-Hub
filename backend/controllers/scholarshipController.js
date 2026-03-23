const db = require('../config/db');
const { paginate } = require('../utils/helpers');

// GET /api/scholarships
exports.getAll = async (req, res) => {
  const { type, status, category, level, search, page, limit } = req.query;
  const { page: p, limit: l, offset } = paginate(page, limit);

  let where  = 'WHERE 1=1';
  let params = [];

  if (type)     { where += ' AND type = ?';                                                       params.push(type); }
  if (status)   { where += ' AND status = ?';                                                     params.push(status); }
  if (category) { where += ' AND category LIKE ?';                                                params.push(`%${category}%`); }
  if (level)    { where += ' AND level LIKE ?';                                                   params.push(`%${level}%`); }
  if (search)   { where += ' AND (title LIKE ? OR description LIKE ? OR provider LIKE ?)';        params.push(`%${search}%`, `%${search}%`, `%${search}%`); }

  try {
    const [[{ total }]] = await db.query(`SELECT COUNT(*) AS total FROM scholarships ${where}`, params);
    const [rows]        = await db.query(`SELECT * FROM scholarships ${where} ORDER BY created_at DESC LIMIT ? OFFSET ?`, [...params, l, offset]);
    res.json({ success: true, total, page: p, limit: l, totalPages: Math.ceil(total / l), scholarships: rows });
  } catch (err) {
    console.error('getAll scholarships:', err);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// GET /api/scholarships/:id
exports.getOne = async (req, res) => {
  try {
    const [rows] = await db.query('SELECT * FROM scholarships WHERE id = ?', [req.params.id]);
    if (!rows.length) return res.status(404).json({ success: false, message: 'Scholarship not found.' });
    res.json({ success: true, scholarship: rows[0] });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};
