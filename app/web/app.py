from config import DB_HOST, DB_PORT, DB_DATABASE, DB_USERNAME, DB_PASSWORD, SECRET_KEY, TOKEN
from database import db
from flask_mail import Mail
from flask import Flask, render_template
from flask_restful import Api
from flask_socketio import SocketIO
from mail_config import mail
from routes.auth import login, register, activate, logout
from routes.home import home, get_post, handle_new_post, handle_new_comment, on_typing

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = SECRET_KEY
app.token = TOKEN

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465 #465 - if SSL=True | 587 - if TLS=True
app.config['MAIL_USERNAME'] = 'jerichoramosbermudez@gmail.com'
app.config['MAIL_PASSWORD'] = 'qflozdvylkobugca'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail()

api = Api(app)
db.init_app(app)
mail.init_app(app)
socketio = SocketIO(app)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

# Login
app.route('/login', methods=['GET', 'POST'])(login)
# Register
app.route('/register', methods=['GET', 'POST'])(register)
# Activate
app.route('/activate/<token>')(activate)
# Logout
app.route('/logout')(logout)

# Homepage
app.route('/')(home)
# Get User posts
app.route('/get-posts/<int:page>', methods=['GET'])(get_post)
# Handle New Post - Realtime
socketio.on('new_post')(handle_new_post)
# Handle New Comment - Realtime
socketio.on('new_comment')(handle_new_comment)
# Check typing on Comment - Realtime
socketio.on('typing')(on_typing)
# Check stop typing on Comment - Realtime
socketio.on('stop_typing')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    socketio.run(app)
