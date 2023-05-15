from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email',[
        validators.DataRequired(),
        validators.Email()
    ])
    submit = SubmitField('Reset Password')