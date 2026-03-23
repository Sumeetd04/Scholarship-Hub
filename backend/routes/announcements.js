const router = require('express').Router();
const ctrl   = require('../controllers/announcementController');

router.get('/', ctrl.getAll);

module.exports = router;
