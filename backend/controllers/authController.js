const bcrypt = require('bcryptjs');
const jwt    = require('jsonwebtoken');
const db     = require('../config/db');
const { generateOTR } = require('../utils/helpers');
require('dotenv').config();

function signToken(payload) {
  return jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: process.env.JWT_EXPIRES_IN });
}

// POST /api/auth/register
exports.register = async (req, res) => {
  const { full_name, email, password, mobile, aadhaar_no } = req.body;
  try {
    const [existing] = await db.query('SELECT id FROM users WHERE email = ?', [email]);
    if (existing.length) {
      return res.status(409).json({ success: false, message: 'Email already registered.' });
    }
    const hashed    = await bcrypt.hash(password, 10);
    const otr       = generateOTR();
    const [result]  = await db.query(
      'INSERT INTO users (full_name, email, password, mobile, aadhaar_no, otr_number) VALUES (?,?,?,?,?,?)',
      [full_name, email, hashed, mobile || null, aadhaar_no || null, otr]
    );
    const token = signToken({ id: result.insertId, email, role: 'student' });
    res.status(201).json({
      success: true,
      message: 'Registration successful!',
      token,
      user: { id: result.insertId, full_name, email, otr_number: otr, role: 'student' }
    });
  } catch (err) {
    console.error('register:', err);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// POST /api/auth/login
exports.login = async (req, res) => {
  const { email, password } = req.body;
  try {
    const [rows] = await db.query('SELECT * FROM users WHERE email = ?', [email]);
    if (!rows.length || !(await bcrypt.compare(password, rows[0].password))) {
      return res.status(401).json({ success: false, message: 'Invalid email or password.' });
    }
    const user  = rows[0];
    const token = signToken({ id: user.id, email: user.email, role: user.role });
    res.json({
      success: true,
      message: 'Login successful!',
      token,
      user: { id: user.id, full_name: user.full_name, email: user.email, otr_number: user.otr_number, role: user.role }
    });
  } catch (err) {
    console.error('login:', err);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// GET /api/auth/profile
exports.profile = async (req, res) => {
  try {
    const [rows] = await db.query(
      'SELECT id, full_name, email, mobile, aadhaar_no, otr_number, role, created_at FROM users WHERE id = ?',
      [req.user.id]
    );
    if (!rows.length) return res.status(404).json({ success: false, message: 'User not found.' });
    res.json({ success: true, user: rows[0] });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};
