-- ============================================================
--  SCHOLARSHIP HUB — MySQL Schema
--  Run: mysql -u root -p < backend/database/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS scholarship_hub;
USE scholarship_hub;

-- ── USERS ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  full_name   VARCHAR(150) NOT NULL,
  email       VARCHAR(150) NOT NULL UNIQUE,
  password    VARCHAR(255) NOT NULL,
  mobile      VARCHAR(15),
  aadhaar_no  VARCHAR(12),
  otr_number  VARCHAR(50)  UNIQUE,
  role        ENUM('student','admin') DEFAULT 'student',
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ── SCHOLARSHIPS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scholarships (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  title       VARCHAR(255)  NOT NULL,
  type        ENUM('international','national','state','private') NOT NULL,
  provider    VARCHAR(200)  NOT NULL,
  country     VARCHAR(100)  DEFAULT 'India',
  level       VARCHAR(100),
  field       VARCHAR(150),
  category    VARCHAR(100),
  amount      VARCHAR(100),
  description TEXT,
  eligibility TEXT,
  deadline    DATE,
  apply_link  VARCHAR(500),
  status      ENUM('open','closing_soon','upcoming','closed') DEFAULT 'open',
  created_by  INT,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ── APPLICATIONS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS applications (
  id                INT AUTO_INCREMENT PRIMARY KEY,
  app_id            VARCHAR(50)    NOT NULL UNIQUE,
  user_id           INT            NOT NULL,
  scholarship_id    INT ,
  full_name         VARCHAR(150)   NOT NULL,
  email             VARCHAR(150)   NOT NULL,
  mobile            VARCHAR(15),
  aadhaar_no        VARCHAR(12),
  dob               DATE,
  gender            ENUM('male','female','other'),
  category          VARCHAR(50),
  state             VARCHAR(100),
  college_name      VARCHAR(200),
  course            VARCHAR(150),
  academic_year     VARCHAR(20),
  percentage        DECIMAL(5,2),
  family_income     DECIMAL(12,2),
  bank_account      VARCHAR(20),
  ifsc_code         VARCHAR(11),
  bank_name         VARCHAR(100),
  app_type          ENUM('fresh','renewal') DEFAULT 'fresh',
  status            ENUM('submitted','verified','sanctioned','disbursed','complete','rejected') DEFAULT 'submitted',
  rejection_reason  VARCHAR(500),
  amount_sanctioned DECIMAL(12,2),
  disbursed_at      TIMESTAMP NULL,
  created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id)        REFERENCES users(id)        ON DELETE CASCADE,
  FOREIGN KEY (scholarship_id) REFERENCES scholarships(id) ON DELETE SET NULL
);

-- ── ANNOUNCEMENTS ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS announcements (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  title       VARCHAR(255) NOT NULL,
  content     TEXT         NOT NULL,
  category    ENUM('upcoming','current','previous') DEFAULT 'current',
  is_new      BOOLEAN DEFAULT TRUE,
  link        VARCHAR(500),
  link_text   VARCHAR(100),
  created_by  INT,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ── CONTACT MESSAGES ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contact_messages (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  first_name  VARCHAR(100)  NOT NULL,
  last_name   VARCHAR(100)  NOT NULL,
  email       VARCHAR(150)  NOT NULL,
  mobile      VARCHAR(15),
  app_ref     VARCHAR(50),
  query_type  VARCHAR(100)  NOT NULL,
  message     TEXT          NOT NULL,
  status      ENUM('new','read','replied') DEFAULT 'new',
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
--  SEED DATA
-- ============================================================

-- Admin (password = Admin@123)
INSERT INTO users (full_name, email, password, role) VALUES
('Admin User', 'admin@scholarshiphub.com',
 '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin');

-- Sample scholarships
INSERT INTO scholarships (title, type, provider, country, level, category, amount, description, deadline, status, created_by) VALUES
('Fulbright-Nehru Research Fellowship',  'international', 'US Embassy India',          'USA',    'PhD / Post-Doctoral', 'General / Merit', 'Full Funding',    'Prestigious award for Indian scholars to undertake research in the USA.',            '2025-07-15', 'open',         1),
('Chevening Scholarship',                'international', 'UK Government',              'UK',     'Postgraduate',        'General / Merit', 'Full Funding',    'UK government scholarship for a one-year master\'s degree at any UK university.',    '2025-11-04', 'open',         1),
('Post-Matric Scholarship for SC',       'national',      'Ministry of Social Justice', 'India',  'Post-Matric',         'SC',              'Up to ₹75,000/yr','Financial support for SC students in post-matric education.',                       '2025-10-31', 'open',         1),
('Pre-Matric Scholarship for Minority',  'national',      'Ministry of Minority Affairs','India', 'Class 1–10',          'Minority',        'Up to ₹1,100/yr', 'Financial support for minority students in Class 1–10.',                            '2025-09-30', 'open',         1),
('Maharashtra State OBC Scholarship',    'state',         'Maharashtra Government',     'India',  'Post-Matric',         'OBC',             'Up to ₹25,000/yr','State scholarship for OBC students domiciled in Maharashtra.',                      '2025-11-30', 'open',         1),
('Tata Capital Pankh Scholarship',       'private',       'Tata Capital CSR',           'India',  'Class 11 to UG',      'Need-based',      'Up to ₹10,000/yr','Supports underprivileged meritorious students from Class 11 to UG.',               '2025-08-31', 'open',         1),
('Reliance Foundation Scholarship',      'private',       'Reliance Foundation',        'India',  'Undergraduate',       'Merit + Need',    '₹2,00,000/yr',   'For UG students in STEM or humanities at top Indian universities.',                 '2025-09-15', 'open',         1);

-- Sample announcements
INSERT INTO announcements (title, content, category, is_new, link, link_text, created_by) VALUES
('Applications Open for AY 2024-25',  'Fresh & Renewal scholarship applications are now open. OTR registration is also open for all students.', 'current',  TRUE,  'https://scholarships.gov.in', 'Apply Now',         1),
('OTR Mandatory from AY 2024-25',     'OTR is now required for all NSP scholarships. Generate using Aadhaar or EID.',                          'current',  TRUE,  NULL,                          NULL,                1),
('SC/ST Applications — Chhattisgarh', 'Applications for SC, ST, OBC students outside Chhattisgarh open 15/03/2024 to 04/04/2024.',            'upcoming', TRUE,  NULL,                          NULL,                1),
('NSP OTR App on Google Play',        'NSP OTR App now available on Google Play Store for easy mobile registration.',                          'upcoming', FALSE, NULL,                          NULL,                1),
('Civil Services Incentive — AP',     '₹1 Lakh incentive for UPSC Preliminary qualifiers from economically weaker sections of Andhra Pradesh.','previous', FALSE, 'https://jcsp.apcfss.in',     'Print Application', 1);
