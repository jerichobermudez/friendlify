from config import COMMON_PASSWORDS
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from models.user import User

class RegistrationForm(FlaskForm):
    firstname = StringField('Firstname', validators=[DataRequired()])
    lastname = StringField('Lastname', validators=[DataRequired()])
    username = StringField('Username', [
        validators.DataRequired(),
        validators.Length(min=6, max=15, message='Username must be between 6 and 15 characters long.'),
        validators.Regexp('^\w+$', message='Username must not contain special characters or spaces.')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.Length(min=8, message='Password must be at least 8 characters long.'),
        validators.Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
            message='Password must have at least one uppercase letter, one lowercase letter, one number, and one special character.'
        ),
        validators.NoneOf(values=COMMON_PASSWORDS, message='Please choose a stronger password.')
    ])
    confirm_password = PasswordField('Confirm Password', [
        EqualTo('password', message="Password doesn't match.")
    ])
    submit = SubmitField('Register')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already used.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email address already used.')