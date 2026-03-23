const router          = require('express').Router();
const ctrl            = require('../controllers/adminController');
const { adminOnly }   = require('../middleware/auth');

// All admin routes require admin JWT
router.use(adminOnly);

router.get('/dashboard',                   ctrl.dashboard);

router.get   ('/scholarships',             ctrl.allScholarships);
router.post  ('/scholarships',             ctrl.createScholarship);
router.put   ('/scholarships/:id',         ctrl.updateScholarship);
router.delete('/scholarships/:id',         ctrl.deleteScholarship);

router.get('/applications',                ctrl.allApplications);
router.put('/applications/:id/status',     ctrl.updateApplicationStatus);

router.get   ('/announcements',            ctrl.allAnnouncements);
router.post  ('/announcements',            ctrl.createAnnouncement);
router.put   ('/announcements/:id',        ctrl.updateAnnouncement);
router.delete('/announcements/:id',        ctrl.deleteAnnouncement);

router.get('/messages',                    ctrl.allMessages);
router.put('/messages/:id/read',           ctrl.markMessageRead);

module.exports = router;
