const express   = require('express');
const cors      = require('cors');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const app = express();

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, max: 10,
  message: { success: false, message: 'Too many attempts. Try again in 15 minutes.' },
  standardHeaders: true, legacyHeaders: false
});

const contactLimiter = rateLimit({
  windowMs: 10 * 60 * 1000, max: 5,
  message: { success: false, message: 'Too many messages sent. Please wait 10 minutes before trying again.' },
  standardHeaders: true, legacyHeaders: false
});

const generalLimiter = rateLimit({ windowMs: 60 * 1000, max: 120 });

// Accept all localhost ports + deployed URL
app.use(cors({
  origin: (origin, cb) => {
    if (!origin) return cb(null, true);
    if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin)) return cb(null, true);
    if (origin === process.env.FRONTEND_URL) return cb(null, true);
    cb(new Error('CORS: origin not allowed'));
  },
  methods: ['GET','POST','PUT','DELETE','OPTIONS'],
  allowedHeaders: ['Content-Type','Authorization'],
  credentials: true
}));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(generalLimiter);

app.use('/api/auth',          authLimiter, require('./routes/auth'));
app.use('/api/scholarships',  require('./routes/scholarships'));
app.use('/api/applications',  require('./routes/applications'));
app.use('/api/announcements', require('./routes/announcements'));
app.use('/api/contact',       contactLimiter, require('./routes/contact'));
app.use('/api/admin',         require('./routes/admin'));

app.get('/', (req, res) => res.json({ status: 'running', message: 'Scholarship Hub API v1.0' }));
app.use((req, res) => res.status(404).json({ success: false, message: 'Route not found.' }));
app.use((err, req, res, next) => { console.error(err.stack); res.status(500).json({ success: false, message: 'Server error.' }); });

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`\n🚀  Server running  →  http://localhost:${PORT}`);
  console.log(`📋  Health check   →  http://localhost:${PORT}/`);
  console.log(`⚙️   Admin login    →  POST /api/auth/login\n`);
});
