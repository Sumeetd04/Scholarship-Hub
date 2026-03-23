const db     = require('../config/db');
const mailer = require('../utils/mailer');

// POST /api/contact
exports.send = async (req, res) => {
  const { first_name, last_name, email, mobile, app_ref, query_type, message } = req.body;
  try {
    // Save to DB
    await db.query(
      'INSERT INTO contact_messages (first_name,last_name,email,mobile,app_ref,query_type,message) VALUES (?,?,?,?,?,?,?)',
      [first_name, last_name, email, mobile || null, app_ref || null, query_type, message]
    );

    // Send emails (non-blocking — don't fail the request if email fails)
    const name = `${first_name} ${last_name}`;
    mailer.sendContactConfirmation({ to: email, name, queryType: query_type, message, appRef: app_ref }).catch(console.error);
    mailer.notifyAdmin({ name, email, mobile, queryType: query_type, message, appRef: app_ref }).catch(console.error);

    res.json({ success: true, message: 'Message sent! We will reply within 2 working days.' });
  } catch (err) {
    console.error('contact send:', err);
    res.status(500).json({ success: false, message: 'Server error. Please try again.' });
  }
};
