from database import db

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
