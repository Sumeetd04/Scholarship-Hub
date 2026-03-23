const db = require('../config/db');
const { generateAppId } = require('../utils/helpers');

// POST /api/applications  — submit new application
exports.submit = async (req, res) => {
  const {
    scholarship_id, full_name, email, mobile, aadhaar_no, dob,
    gender, category, state, college_name, course, academic_year,
    percentage, family_income, bank_account, ifsc_code, bank_name, app_type
  } = req.body;

  try {
    const [dup] = await db.query(
      'SELECT id FROM applications WHERE user_id=? AND scholarship_id=? AND academic_year=?',
      [req.user.id, scholarship_id, academic_year]
    );
    if (dup.length) {
      return res.status(409).json({ success: false, message: 'You already applied for this scholarship this year.' });
    }

    const app_id = generateAppId();
    await db.query(
      `INSERT INTO applications
        (app_id,user_id,scholarship_id,full_name,email,mobile,aadhaar_no,dob,
         gender,category,state,college_name,course,academic_year,percentage,
         family_income,bank_account,ifsc_code,bank_name,app_type)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
      [app_id, req.user.id, scholarship_id, full_name, email || req.user.email,
       mobile, aadhaar_no, dob, gender, category, state, college_name,
       course, academic_year, percentage, family_income, bank_account, ifsc_code, bank_name, app_type]
    );
    res.status(201).json({ success: true, message: 'Application submitted!', app_id });
  } catch (err) {
    console.error('submit application:', err);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// GET /api/applications/my  — logged-in student's applications
exports.getMine = async (req, res) => {
  try {
    const [rows] = await db.query(
      `SELECT a.*, s.title AS scholarship_title, s.type AS scholarship_type
       FROM applications a JOIN scholarships s ON a.scholarship_id = s.id
       WHERE a.user_id = ? ORDER BY a.created_at DESC`,
      [req.user.id]
    );
    res.json({ success: true, applications: rows });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// GET /api/applications/track/:app_id  — public tracker
exports.track = async (req, res) => {
  try {
    const [rows] = await db.query(
      `SELECT a.app_id, a.full_name, a.status, a.app_type, a.academic_year,
              a.amount_sanctioned, a.created_at, a.updated_at, a.disbursed_at,
              a.rejection_reason, a.college_name, a.course,
              s.title AS scholarship_title, s.type AS scholarship_type, s.amount
       FROM applications a JOIN scholarships s ON a.scholarship_id = s.id
       WHERE a.app_id = ?`,
      [req.params.app_id]
    );
    if (!rows.length) {
      return res.status(404).json({ success: false, message: 'Application not found. Please check your ID.' });
    }
    res.json({ success: true, application: rows[0] });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};
