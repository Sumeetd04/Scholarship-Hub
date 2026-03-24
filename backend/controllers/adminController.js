const db = require('../config/db');
const { paginate } = require('../utils/helpers');

// GET /api/admin/dashboard
exports.dashboard = async (req, res) => {
  try {
    const [[{ total_scholarships }]] = await db.query('SELECT COUNT(*) AS total_scholarships FROM scholarships');
    const [[{ total_applications }]] = await db.query('SELECT COUNT(*) AS total_applications FROM applications');
    const [[{ total_users }]]        = await db.query('SELECT COUNT(*) AS total_users FROM users WHERE role="student"');
    const [[{ disbursed }]]          = await db.query('SELECT COUNT(*) AS disbursed FROM applications WHERE status="disbursed"');
    const [[{ new_messages }]]       = await db.query('SELECT COUNT(*) AS new_messages FROM contact_messages WHERE status="new"');
    const [recent]                   = await db.query(
      `SELECT a.app_id, a.full_name, a.status, a.created_at, s.title AS scholarship
       FROM applications a JOIN scholarships s ON a.scholarship_id=s.id
       ORDER BY a.created_at DESC LIMIT 5`
    );
    res.json({ success: true, stats: { total_scholarships, total_applications, total_users, disbursed, new_messages }, recent });
  } catch (err) {
    console.error('dashboard:', err);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// ── Scholarships ──────────────────────────────────────────────
exports.allScholarships = async (req, res) => {
  try {
    const [rows] = await db.query('SELECT * FROM scholarships ORDER BY created_at DESC');
    res.json({ success: true, scholarships: rows });
  } catch (err) { res.status(500).json({ success: false, message: 'Server error.' }); }
};

exports.createScholarship = async (req, res) => {
  const { title, type, provider, country, level, field, category, amount,
          description, eligibility, deadline, apply_link, status } = req.body;
  if (!title || !type || !provider) {
    return res.status(400).json({ success: false, message: 'title, type and provider are required.' });
  }
  try {
    const [r] = await db.query(
      `INSERT INTO scholarships (title,type,provider,country,level,field,category,amount,
        description,eligibility,deadline,apply_link,status,created_by)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
      [title, type, provider, country, level, field, category, amount,
       description, eligibility, deadline, apply_link, status || 'open', req.user.id]
    );
    res.status(201).json({ success: true, message: 'Scholarship created!', id: r.insertId });
  } catch (err) { res.status(500).json({ success: false, message: 'Server error.' }); }
};

exports.updateScholarship = async (req, res) => {
  const { title, type, provider, country, level, field, category, amount,
          description, eligibility, deadline, apply_link, status } = req.body;

  if (!title || !type || !provider) {
    return res.status(400).json({ success: false, message: 'title, type and provider are required.' });
  }

  try {
    const [result] = await db.query(
      `UPDATE scholarships SET title=?,type=?,provider=?,country=?,level=?,field=?,
        category=?,amount=?,description=?,eligibility=?,deadline=?,apply_link=?,status=?
       WHERE id=?`,
      [title, type, provider, country, level, field, category, amount,
       description, eligibility, deadline, apply_link, status, req.params.id]
    );

    if (result.affectedRows === 0) {
      return res.status(404).json({ success: false, message: 'Scholarship not found.' });
    }

    res.json({ success: true, message: 'Scholarship updated!' });
  } catch (err) {
    console.error('updateScholarship:', err);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};

exports.deleteScholarship = async (req, res) => {
  try {
    const [apps] = await db.query(
      'SELECT COUNT(*) AS total FROM applications WHERE scholarship_id = ? AND status NOT IN ("rejected","complete")',
      [req.params.id]
    );
    if (apps[0].total > 0) {
      return res.status(400).json({
        success: false,
        message: `Cannot delete — this scholarship has ${apps[0].total} active application(s). Close or reject them first.`
      });
    }
    await db.query('DELETE FROM scholarships WHERE id=?', [req.params.id]);
    res.json({ success: true, message: 'Scholarship deleted.' });
  } catch (err) {
    console.error('deleteScholarship:', err);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// ── Applications ──────────────────────────────────────────────
exports.allApplications = async (req, res) => {
  const { status, page, limit } = req.query;
  const { page: p, limit: l, offset } = paginate(page, limit);
  let where = 'WHERE 1=1'; let params = [];
  if (status) { where += ' AND a.status=?'; params.push(status); }
  try {
    const [rows] = await db.query(
      `SELECT a.*, s.title AS scholarship_title FROM applications a
       JOIN scholarships s ON a.scholarship_id=s.id ${where}
       ORDER BY a.created_at DESC LIMIT ? OFFSET ?`,
      [...params, l, offset]
    );
    res.json({ success: true, applications: rows });
  } catch (err) { res.status(500).json({ success: false, message: 'Server error.' }); }
};

exports.updateApplicationStatus = async (req, res) => {
  const { status, amount_sanctioned, rejection_reason } = req.body;
  const valid = ['submitted','verified','sanctioned','disbursed','complete','rejected'];
  if (!valid.includes(status)) {
    return res.status(400).json({ success: false, message: 'Invalid status value.' });
  }
  try {
    let q = 'UPDATE applications SET status=?'; let p = [status];
    if (amount_sanctioned)  { q += ',amount_sanctioned=?'; p.push(amount_sanctioned); }
    if (status === 'disbursed') { q += ',disbursed_at=NOW()'; }
    if (rejection_reason)   { q += ',rejection_reason=?';  p.push(rejection_reason); }
    q += ' WHERE id=?'; p.push(req.params.id);
    await db.query(q, p);
    res.json({ success: true, message: `Status updated to "${status}".` });
  } catch (err) { res.status(500).json({ success: false, message: 'Server error.' }); }
};

// ── Announcements ─────────────────────────────────────────────
exports.allAnnouncements = async (req, res) => {
  try {
    const [rows] = await db.query('SELECT * FROM announcements ORDER BY created_at DESC');
    res.json({ success: true, announcements: rows });
  } catch (err) { res.status(500).json({ success: false, message: 'Server error.' }); }
};

exports.createAnnouncement = async (req, res) => {
  const { title, content, category, is_new, link, link_text } = req.body;
  if (!title || !content) return res.status(400).json({ success: false, message: 'title and content are required.' });
  try {
    await db.query(
      'INSERT INTO announcements (title,content,category,is_new,link,link_text,created_by) VALUES (?,?,?,?,?,?,?)',
      [title, content, category || 'current', is_new !== false, link || null, link_text || null, req.user.id]
    );
    res.status(201).json({ success: true, message: 'Announcement created!' });
  } catch (err) { res.status(500).json({ success: false, message: 'Server error.' }); }
};

exports.updateAnnouncement = async (req, res) => {
  const { title, content, category, is_new, link, link_text } = req.body;
  try {
    await db.query(
      'UPDATE announcements SET title=?,content=?,category=?,is_new=?,link=?,link_text=? WHERE id=?',
      [title, content, category, is_new, link, link_text, req.params.id]
    );
    res.json({ success: true, message: 'Announcement updated!' });
  } catch (err) { res.status(500).json({ success: false, message: 'Server error.' }); }
};

exports.deleteAnnouncement = async (req, res) => {
  try {
    await db.query('DELETE FROM announcements WHERE id=?', [req.params.id]);
    res.json({ success: true, message: 'Announcement deleted.' });
  } catch (err) { res.status(500).json({ success: false, message: 'Server error.' }); }
};

// ── Messages ──────────────────────────────────────────────────
exports.allMessages = async (req, res) => {
  try {
    const [rows] = await db.query('SELECT * FROM contact_messages ORDER BY created_at DESC');
    res.json({ success: true, messages: rows });
  } catch (err) { res.status(500).json({ success: false, message: 'Server error.' }); }
};

exports.markMessageRead = async (req, res) => {
  try {
    await db.query('UPDATE contact_messages SET status="read" WHERE id=?', [req.params.id]);
    res.json({ success: true, message: 'Marked as read.' });
  } catch (err) { res.status(500).json({ success: false, message: 'Server error.' }); }
};
