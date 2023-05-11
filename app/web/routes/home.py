from config import POST_PER_PAGE, COMMENTS_PER_POST
from database import db
from flask import redirect, render_template, session, url_for, jsonify
from models.friend import Friend
from models.post import Post
from models.user import User
from models.like import Like
from models.comment import Comment
from flask_socketio import emit
from sqlalchemy.orm import joinedload

# Homepage
def home():
    if 'id' in session and session['loggedIn'] == True:
        user = User.query.filter_by(id=session['id']).first()

        return render_template('index.html', user=user)
    else:
        return redirect(url_for('login'))

# Get Posts
def get_post(page):
    max_comments = COMMENTS_PER_POST
    per_page = POST_PER_PAGE
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

# Submit Post
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

# Submit Comment
def handle_new_comment(data):
    if data['comment'] != '':
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

# On Typing - Comment
def on_typing(data):
    user_id = data['user_id']
    postId = data['post_id']
    user = User.query.filter_by(id=user_id).first()
    comment = Comment.query.filter_by(user_id=user_id).first()
    comment.typing = True
    db.session.commit()

    emit('typing_status', {'user_id': user_id, 'name': user.firstname, 'comment': data['comment'], 'post_id': postId, 'typing': True}, broadcast=True)

# Stop Typing - Comment
def on_stop_typing(data):
    user_id = data['user_id']
    postId = data['post_id']
    user = User.query.filter_by(id=user_id).first()
    comment = Comment.query.filter_by(user_id=user_id).first()
    comment.typing = False
    db.session.commit()

    emit('typing_status', {'user_id': user_id, 'name': user.firstname, 'comment': data['comment'], 'post_id': postId, 'typing': False}, broadcast=True)
