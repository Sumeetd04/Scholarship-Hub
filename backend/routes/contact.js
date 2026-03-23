const router   = require('express').Router();
const { body } = require('express-validator');
const ctrl     = require('../controllers/contactController');
const validate = require('../middleware/validate');

router.post('/',
  [
    body('first_name').notEmpty().withMessage('First name is required'),
    body('last_name').notEmpty().withMessage('Last name is required'),
    body('email').isEmail().withMessage('Valid email is required'),
    body('query_type').notEmpty().withMessage('Query type is required'),
    body('message').isLength({ min: 10 }).withMessage('Message must be at least 10 characters')
  ],
  validate, ctrl.send
);

module.exports = router;
