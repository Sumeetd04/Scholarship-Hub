const router      = require('express').Router();
const { body }    = require('express-validator');
const ctrl        = require('../controllers/applicationController');
const { protect } = require('../middleware/auth');
const validate    = require('../middleware/validate');

const submitValidation = [
  body('scholarship_id').notEmpty().withMessage('Scholarship is required.'),
  body('full_name').notEmpty().withMessage('Full name is required.'),
  body('email').isEmail().withMessage('Valid email is required.'),
  body('mobile').isMobilePhone('en-IN').withMessage('Valid 10-digit mobile number is required.'),
  body('aadhaar_no').isLength({ min: 12, max: 12 }).isNumeric().withMessage('Aadhaar must be 12 digits.'),
  body('dob').isDate().withMessage('Valid date of birth is required.'),
  body('gender').isIn(['male', 'female', 'other']).withMessage('Invalid gender value.'),
  body('percentage').isFloat({ min: 0, max: 100 }).withMessage('Percentage must be between 0 and 100.'),
  body('family_income').isNumeric().withMessage('Family income must be a number.'),
  body('bank_account').notEmpty().withMessage('Bank account number is required.'),
  body('ifsc_code')
    .matches(/^[A-Z]{4}0[A-Z0-9]{6}$/)
    .withMessage('Invalid IFSC code format.'),
  body('college_name').notEmpty().withMessage('College name is required.'),
  body('course').notEmpty().withMessage('Course is required.'),
  body('academic_year').notEmpty().withMessage('Academic year is required.'),
];

router.get('/my',             protect, ctrl.getMine);
router.get('/track/:app_id',           ctrl.track);
router.post('/',              protect, submitValidation, validate, ctrl.submit);

module.exports = router;