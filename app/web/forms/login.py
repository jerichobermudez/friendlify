from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators

class LoginForm(FlaskForm):
    username = StringField('Username',[validators.DataRequired()])
    password = StringField('Password',[validators.DataRequired()])
    submit = SubmitField('Login')