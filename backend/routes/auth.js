const router   = require('express').Router();
const { body } = require('express-validator');
const ctrl     = require('../controllers/authController');
const validate = require('../middleware/validate');
const { protect } = require('../middleware/auth');

router.post('/register',
  [body('full_name').notEmpty(), body('email').isEmail(), body('password').isLength({ min: 6 })],
  validate, ctrl.register
);

router.post('/login',
  [body('email').isEmail(), body('password').notEmpty()],
  validate, ctrl.login
);

router.get('/profile', protect, ctrl.profile);

module.exports = router;
