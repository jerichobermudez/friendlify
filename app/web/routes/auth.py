import os
# import secrets
import shutil
from config import ACTIVATION_EXPIRATION, SECRET_KEY, TOKEN
from database import db
from enums.UserStatus import UserStatus
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import render_template, request, flash, session, redirect, url_for, jsonify
from forms.registration import RegistrationForm
from forms.login import LoginForm
from forms.forgot_password import ForgotPasswordForm
from forms.reset_password import ResetPasswordForm
from models.user import User
from components.mail_helper import sendMail

token_serializer = URLSafeTimedSerializer(SECRET_KEY)

def login():
    if 'id' in session and session['loggedIn'] == True:
        return redirect(url_for('home'))

    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data

            user = User.query.filter(
                (User.username == username) | (User.email == username),
                User.status != UserStatus.DEFAULT.value,
                User.deleted == 0
            ).first()

            if user and user.check_password_hash(password):
                session['loggedIn'] = True
                session['id'] = user.id
                session['username'] = user.username

                return redirect(url_for('home'))
            else:
                flash('Invalid login credentials.', 'error')

    return render_template('auth/login.html', form=form)

def register():
    form = RegistrationForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            token = token_serializer.dumps(form.username.data, salt=TOKEN)
            user = User(
                firstname=form.firstname.data,
                lastname=form.lastname.data,
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                token=token
            )

            source_file='static/files/default.png'
            upload_path = 'static/files/' + user.username
            os.makedirs(upload_path, exist_ok=True)
            # Add write access to the directory
            os.chmod(upload_path, 0o777)
            shutil.copy(source_file, upload_path)

            db.session.add(user)
            db.session.commit()

            # Generate activation link with the token
            activation_link = url_for('activate', token=token, _external=True)
            html = render_template('mail/activation.html', link=activation_link)
            sendMail('Account Activation', '', 'admin@friendlify.com', [form.email.data], html)

            flash('Registration success!', 'success')
            return redirect(url_for('register'))
        else:
            flash('An error has occurred.', 'error')

    return render_template('auth/register.html', form=form)

def activate(token):
    try:
        username = token_serializer.loads(token, salt=TOKEN, max_age=ACTIVATION_EXPIRATION)
        user = User.query.filter(
            User.username == username,
            User.token == token,
            User.status == UserStatus.DEFAULT.value
        ).first()

        if not user:
            return redirect(url_for('login'))

        user.status = UserStatus.ACTIVATED.value
        user.token = None
        db.session.commit()

        return render_template('auth/activated.html')
    except SignatureExpired:
        return render_template('error/404.html')
    except BadSignature:
        return render_template('error/404.html')

def forgotPassword():
    form = ForgotPasswordForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter(
                User.email == form.email.data,
                User.status != UserStatus.DEFAULT.value
            ).first()

            if user:
                token = token_serializer.dumps(user.username, salt=TOKEN)

                user.status = UserStatus.RESET_PASSWORD.value
                user.token = token
                db.session.commit()
                
                # Generate activation link with the token
                activation_link = url_for('resetPassword', token=token, _external=True)
                html = render_template('mail/reset-password.html', name=user.firstname, link=activation_link)
                sendMail('Reset Password', '', 'admin@friendlify.com', [user.email], html)

            flash('Reset Password Success!', 'success')
            return redirect(url_for('forgotPassword'))
        else:
            flash('An error has occurred.', 'error')

    return render_template('auth/forgot-password.html', form=form)

def resetPassword(token):
    try:
        username = token_serializer.loads(token, salt=TOKEN, max_age=ACTIVATION_EXPIRATION)
        user = User.query.filter(
            User.username == username,
            User.token == token,
            User.status == UserStatus.RESET_PASSWORD.value
        ).first()

        if not user:
            return redirect(url_for('login'))

        form = ResetPasswordForm()

        if request.method == 'POST':
            if form.validate_on_submit():
                user.update_password(form.password.data)
                user.status = UserStatus.ACTIVATED.value
                user.token = None
                db.session.commit()
                
                flash('Reset Password Success!', 'success')
                return redirect(url_for('login'))
            else:
                flash('An error has occurred.', 'error')
                
        return render_template('auth/reset-password.html', token=token, form=form)
    except SignatureExpired:
        return render_template('error/404.html')
    except BadSignature:
        return render_template('error/404.html')

def logout():
    # Remove session data, this will log the user out
   session.pop('loggedIn', None)
   session.pop('id', None)
   session.pop('userfirstname', None)

   return redirect(url_for('login'))