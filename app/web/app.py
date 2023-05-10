import math
from flask_mail import Mail
from config import DB_HOST, DB_PORT, DB_DATABASE, DB_USERNAME, DB_PASSWORD, SECRET_KEY, TOKEN, ACTIVATION_EXPIRATION
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask_restful import Resource, Api
from flask_socketio import SocketIO, emit
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from sqlalchemy.orm import joinedload
from database import db
from models.user import User
from mail_config import mail
from routes.auth import login, register, activate, logout

from serializers import AlchemyEncoder

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

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    attachments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    user = db.relationship('User')
    likes = db.relationship('Like', backref='posts', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='posts', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'attachments': self.attachments,
            'user': self.user.to_dict(),
            'comments': [comment.to_dict() for comment in self.comments]
        }

class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User')

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment = db.Column(db.Text)
    typing = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    
    user = db.relationship('User')

    def __repr__(self):
        return f"Comment('{self.user_id}', '{self.comment}', '{self.typing}')"
    

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'comment': self.comment,
            'user': self.user.to_dict()
        }

class Message(db.Model):
    __tablename__ = 'messages'

    user_id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

class Friend(db.Model):
    __tablename__ = 'friends'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

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

@app.route('/')
def home():
    if 'id' in session and session['loggedIn'] == True:
        user = User.query.filter_by(id=session['id']).first()

        return render_template('index.html', user=user)
    else:
        return redirect(url_for('login'))

@app.route('/get-posts/<int:page>', methods=['GET'])
def get_new_post(page):
    max_comments=10
    per_page = 5  # Number of posts to load per page
    offset = (page - 1) * per_page
    user = User.query.filter_by(id=session['id']).first()

    logged_in_user_posts = db.session.query(Post).options(
        joinedload(Post.comments).joinedload(Comment.user)
    ).join(User).filter(Post.user_id == session['id']).all()

    friend_posts = db.session.query(Post).options(
        joinedload(Post.comments).joinedload(Comment.user)
    ).join(User).join(Friend,
    (User.id == Friend.friend_id) |
    (User.id == Friend.user_id)).filter(
    Friend.user_id == session['id']).all()

    all_posts = db.session.query(Post).filter(
        Post.id.in_([post.id for post in logged_in_user_posts + friend_posts])
    ).distinct().order_by(Post.id.desc()).offset(offset).limit(per_page).all()

    has_more = len(all_posts) <= per_page

    for post in all_posts:
        post.comments.sort(key=lambda c: c.id, reverse=False)
        post.comments = post.comments[:max_comments]

    rendered_template = render_template('get_posts.html', user=user, posts=all_posts)
    return jsonify(html=rendered_template, has_more=has_more, last_page=len(all_posts))

@socketio.on('new_post')
def handle_new_post(data):
    if data['content'] != '':
        new_post = Post(user_id=session['id'], content=data['content'])
        db.session.add(new_post)
        db.session.commit()

        user = User.query.filter_by(id=new_post.user_id).first()
        data['post_id'] = new_post.id
        data['user_id'] = user.id
        data['username'] = user.username
        data['firstname'] = user.firstname
        data['lastname'] = user.lastname
        data['profile'] = url_for('static', filename='files/' + user.username + '/' + user.image)

    emit('new_post', data, broadcast=True)

@socketio.on('new_comment')
def handle_new_comment(data):
    new_comment = Comment(post_id=data['post_id'], user_id=session['id'], comment=data['comment'])
    db.session.add(new_comment)
    db.session.commit()

    user = User.query.filter_by(id=new_comment.user_id).first()
    data['user_id'] = user.id
    data['username'] = user.username
    data['firstname'] = user.firstname
    data['profile'] = url_for('static', filename='files/' + user.username + '/' + user.image)

    emit('new_comment', data, broadcast=True)
    emit('typing_status', {'user_id': '', 'name': '', 'comment': '', 'post_id': data['post_id'], 'typing': False}, broadcast=True)

@socketio.on('typing')
def on_typing(data):
    user_id = data['user_id']
    postId = data['post_id']
    user = User.query.filter_by(id=user_id).first()
    comment = Comment.query.filter_by(user_id=user_id).first()
    comment.typing = True
    db.session.commit()

    emit('typing_status', {'user_id': user_id, 'name': user.firstname, 'comment': data['comment'], 'post_id': postId, 'typing': True}, broadcast=True)

@socketio.on('stop_typing')
def on_stop_typing(data):
    user_id = data['user_id']
    postId = data['post_id']
    user = User.query.filter_by(id=user_id).first()
    comment = Comment.query.filter_by(user_id=user_id).first()
    comment.typing = False
    db.session.commit()

    emit('typing_status', {'user_id': user_id, 'name': user.firstname, 'comment': data['comment'], 'post_id': postId, 'typing': False}, broadcast=True)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    socketio.run(app)
