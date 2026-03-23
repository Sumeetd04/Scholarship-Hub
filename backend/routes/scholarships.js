const router = require('express').Router();
const ctrl   = require('../controllers/scholarshipController');

router.get('/',    ctrl.getAll);
router.get('/:id', ctrl.getOne);

module.exports = router;
