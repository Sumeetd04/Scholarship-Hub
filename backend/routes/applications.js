const router      = require('express').Router();
const ctrl        = require('../controllers/applicationController');
const { protect } = require('../middleware/auth');

router.get('/my',          protect, ctrl.getMine);
router.get('/track/:app_id',        ctrl.track);
router.post('/',           protect, ctrl.submit);

module.exports = router;
