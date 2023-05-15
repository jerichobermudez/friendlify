from config import COMMON_PASSWORDS
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, validators
from wtforms.validators import EqualTo

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.Length(min=8, message='Password must be at least 8 characters long.'),
        validators.Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
            message='Password must have at least one uppercase letter, one lowercase letter, one number, and one special character.'
        ),
        EqualTo('confirm_password', message="Password doesn't match."),
        validators.NoneOf(values=COMMON_PASSWORDS, message='Please choose a stronger password.')
    ])
    confirm_password = PasswordField('Confirm Password', [
        EqualTo('password', message="Password doesn't match."),
        validators.DataRequired(),
    ])
    submit = SubmitField('Reset Password')