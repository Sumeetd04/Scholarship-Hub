-- Fix UTF-8 charset on all tables
ALTER DATABASE scholarship_hub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE users          CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE scholarships   CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE applications   CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE announcements  CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE contact_messages CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Delete old broken data (??? characters)
DELETE FROM announcements;
DELETE FROM scholarships WHERE created_by = 1;

-- Re-insert scholarships with correct UTF-8
INSERT INTO scholarships (title, type, provider, country, level, category, amount, description, deadline, status, created_by) VALUES
('Fulbright-Nehru Research Fellowship',  'international', 'US Embassy India',           'USA',   'PhD / Post-Doctoral', 'General / Merit', 'Full Funding',     'Prestigious award for Indian scholars to undertake research in the USA.',                                    '2025-07-15', 'open',         1),
('Chevening Scholarship',                'international', 'UK Government',               'UK',    'Postgraduate',        'General / Merit', 'Full Funding',     'UK government scholarship for a one-year master\'s degree at any UK university.',                           '2025-11-04', 'open',         1),
('Post-Matric Scholarship for SC',       'national',      'Ministry of Social Justice',  'India', 'Post-Matric',         'SC',              'Up to ₹75,000/yr', 'Financial support for SC students in post-matric education.',                                               '2025-10-31', 'open',         1),
('Pre-Matric Scholarship for Minority',  'national',      'Ministry of Minority Affairs','India', 'Class 1-10',          'Minority',        'Up to ₹1,100/yr',  'Financial support for minority students in Class 1 to 10.',                                                 '2025-09-30', 'open',         1),
('Maharashtra State OBC Scholarship',    'state',         'Maharashtra Government',      'India', 'Post-Matric',         'OBC',             'Up to ₹25,000/yr', 'State scholarship for OBC students domiciled in Maharashtra.',                                              '2025-11-30', 'open',         1),
('Tata Capital Pankh Scholarship',       'private',       'Tata Capital CSR',            'India', 'Class 11 to UG',      'Need-based',      'Up to ₹10,000/yr', 'Supports underprivileged meritorious students from Class 11 to UG.',                                        '2025-08-31', 'open',         1),
('Reliance Foundation Scholarship',      'private',       'Reliance Foundation',         'India', 'Undergraduate',       'Merit + Need',    '₹2,00,000/yr',    'For UG students in STEM or humanities at top Indian universities.',                                          '2025-09-15', 'open',         1);

-- Re-insert announcements with correct UTF-8
INSERT INTO announcements (title, content, category, is_new, link, link_text, created_by) VALUES
('Applications Open for AY 2024-25',  'Fresh & Renewal scholarship applications are now open. OTR registration is also open for all students.', 'current',  TRUE,  'https://scholarships.gov.in', 'Apply Now',         1),
('OTR Mandatory from AY 2024-25',     'OTR is now required for all NSP scholarships. Generate using Aadhaar or EID.',                          'current',  TRUE,  NULL,                          NULL,                1),
('SC/ST Applications — Chhattisgarh', 'Applications for SC, ST, OBC students outside Chhattisgarh open 15/03/2024 to 04/04/2024.',            'upcoming', TRUE,  NULL,                          NULL,                1),
('NSP OTR App on Google Play',        'NSP OTR App now available on Google Play Store for easy mobile registration.',                          'upcoming', FALSE, NULL,                          NULL,                1),
('Civil Services Incentive — AP',     '₹1 Lakh incentive for UPSC Preliminary qualifiers from economically weaker sections of Andhra Pradesh.','previous', FALSE, 'https://jcsp.apcfss.in',     'Print Application', 1);

SELECT 'Done! UTF-8 fix applied successfully.' AS status;
