import os
from database import db
from dotenv import load_dotenv
from flask_mail import Mail
from flask import Flask, render_template, session, redirect, request, url_for
from flask_restful import Api
from flask_socketio import SocketIO
from mail_config import mail
from routes.auth import login, register, activate, forgotPassword, resetPassword, logout
from routes.home import home, get_post, get_post_comments, handle_new_post, handle_new_comment, on_typing, on_stop_typing

app = Flask(__name__)
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')
app.token = os.getenv('TOKEN')

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail()

api = Api(app)
db.init_app(app)
mail.init_app(app)
socketio = SocketIO(app)

@app.before_request
def before_request():
    authRoutes = ['login', 'register', 'activate', 'forgotPassword', 'resetPassword']
    sessionRoutes = ['home']
    if 'id' not in session:
        if request.endpoint in sessionRoutes:
            return redirect(url_for('login'))
    
    if 'id' in session:
        if request.endpoint in authRoutes:
            return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

# Login
app.route('/login', methods=['GET', 'POST'])(login)
# Register
app.route('/register', methods=['GET', 'POST'])(register)
# Activate
app.route('/activate/<token>')(activate)
# Forgot Password
app.route('/forgot-password', methods=['GET', 'POST'])(forgotPassword)
# Reset Password
app.route('/reset-password/<token>', methods=['GET', 'POST'])(resetPassword)
# Logout
app.route('/logout')(logout)

# Homepage
app.route('/')(home)
# Get User posts
app.route('/get-posts/<int:page>', methods=['GET'])(get_post)
# Get Post Comments
app.route('/get-comments/<int:post_id>/<int:page>', methods=['GET'])(get_post_comments)
# Handle New Post - Realtime
socketio.on('new_post')(handle_new_post)
# Handle New Comment - Realtime
socketio.on('new_comment')(handle_new_comment)
# Check typing on Comment - Realtime
socketio.on('typing')(on_typing)
# Check stop typing on Comment - Realtime
socketio.on('stop_typing')(on_stop_typing)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    socketio.run(app)
