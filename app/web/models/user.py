# from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    firstname = db.Column(db.String(120), unique=True, nullable=False)
    lastname = db.Column(db.String(120), unique=True, nullable=False)
    display_name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    birthday = db.Column(db.Date, nullable=True)
    image = db.Column(db.String(80), nullable=True, default='default.png')
    token = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(120), nullable=True, default=0)
    deleted = db.Column(db.Boolean, default=False)


    friends = db.relationship(
        'User',
        secondary='friends',
        primaryjoin='User.id == friends.c.user_id',
        secondaryjoin='User.id == friends.c.friend_id',
        backref=db.backref('friend_of', lazy='dynamic'),
        lazy='dynamic')
    
    def __init__(self, firstname, lastname, username, email, password, token):
        self.firstname = firstname
        self.lastname = lastname
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)
        self.token = token

    def check_password_hash(self, password):
        return check_password_hash(self.password, password)
    
    def update_password(self, new_password):
        self.password = generate_password_hash(new_password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'email': self.email,
            'password': self.password,
            'token': self.token,
            'status': self.status,
        }
