const nodemailer = require('nodemailer');
require('dotenv').config();

const transporter = nodemailer.createTransport({
  host:   process.env.EMAIL_HOST,
  port:   process.env.EMAIL_PORT,
  secure: false,
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS
  }
});

// ── Reusable HTML email wrapper ───────────────────────────────
function emailWrapper(body) {
  return `
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px">
      <div style="background:#1a7a4a;padding:20px 24px;border-radius:10px 10px 0 0;text-align:center">
        <h1 style="color:white;margin:0;font-size:20px">🎓 Scholarship Hub</h1>
      </div>
      <div style="background:#f8faf9;padding:28px;border-radius:0 0 10px 10px;border:1px solid #d0e8da">
        ${body}
        <p style="color:#6a8e78;font-size:12px;margin-top:28px;border-top:1px solid #d0e8da;padding-top:16px">
          This is an automated message from Scholarship Hub. Please do not reply directly.<br>
          For support: 0120-6619540 · helpdesk@nsp.gov.in
        </p>
      </div>
    </div>`;
}

// ── Send contact confirmation ─────────────────────────────────
async function sendContactConfirmation({ to, name, queryType, message, appRef }) {
  await transporter.sendMail({
    from:    process.env.EMAIL_FROM,
    to,
    subject: 'We received your message — Scholarship Hub',
    html: emailWrapper(`
      <p style="font-size:16px;color:#1a2e22">Dear <strong>${name}</strong>,</p>
      <p style="color:#3a5a47;line-height:1.7">
        Thank you for contacting us. We received your message about
        <strong>"${queryType}"</strong> and will reply within <strong>2 working days</strong>.
      </p>
      <div style="background:white;border:1px solid #d0e8da;border-radius:8px;padding:16px;margin:20px 0">
        <p style="margin:0;font-size:12px;color:#6a8e78;text-transform:uppercase">Your Message</p>
        <p style="margin:8px 0 0;color:#1a2e22">${message}</p>
      </div>
      ${appRef ? `<p style="color:#3a5a47">Reference ID: <strong>${appRef}</strong></p>` : ''}
    `)
  });
}

// ── Notify admin of new contact message ───────────────────────
async function notifyAdmin({ name, email, mobile, queryType, message, appRef }) {
  await transporter.sendMail({
    from:    process.env.EMAIL_FROM,
    to:      process.env.ADMIN_EMAIL,
    subject: `📬 New Contact: ${queryType} — ${name}`,
    html: emailWrapper(`
      <h3 style="color:#1a2e22">New Contact Message</h3>
      <table style="width:100%;font-size:14px;border-collapse:collapse">
        <tr><td style="padding:6px 0;color:#6a8e78;width:130px">Name</td><td style="color:#1a2e22"><strong>${name}</strong></td></tr>
        <tr><td style="padding:6px 0;color:#6a8e78">Email</td><td style="color:#1a5a9a">${email}</td></tr>
        <tr><td style="padding:6px 0;color:#6a8e78">Mobile</td><td style="color:#1a2e22">${mobile || 'Not provided'}</td></tr>
        <tr><td style="padding:6px 0;color:#6a8e78">App Ref</td><td style="color:#1a2e22">${appRef || 'Not provided'}</td></tr>
        <tr><td style="padding:6px 0;color:#6a8e78">Query Type</td><td style="color:#1a2e22">${queryType}</td></tr>
      </table>
      <div style="background:white;border:1px solid #d0e8da;border-radius:8px;padding:16px;margin:20px 0">
        <p style="margin:0;font-size:12px;color:#6a8e78;text-transform:uppercase">Message</p>
        <p style="margin:8px 0 0;color:#1a2e22">${message}</p>
      </div>
    `)
  });
}

module.exports = { sendContactConfirmation, notifyAdmin };
