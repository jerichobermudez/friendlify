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
    # if 'id' in session and session['loggedIn'] == True:
        user = User.query.filter_by(id=session['id']).first()

        return render_template('home/index.html', user=user)
    # else:
    #     return redirect(url_for('login'))

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
        post.total_comments = len(post.comments)
        post.comments.sort(key=lambda c: c.id, reverse=True)
        post.comments = post.comments[:max_comments][::-1]

    # Serialize the posts to a JSON-serializable format
    serialized_posts = []
    for post in all_posts:
        serialized_post = {
            'id': post.id,
        }
        serialized_posts.append(serialized_post)

    rendered_template = render_template('home/get-posts.html', user=user, posts=all_posts)
    return jsonify(html=rendered_template, has_more=has_more, last_page=len(all_posts), posts=serialized_posts)

# Get Post Comments
def get_post_comments(post_id, page):
    per_page = COMMENTS_PER_POST
    offset = (page - 1) * per_page

    comments = db.session.query(Comment).join(User).options(
        joinedload(Comment.user)
    ).filter(Comment.post_id == post_id).order_by(Comment.id.desc()).offset(offset).limit(per_page).all()

    has_more = len(comments) >= per_page

    for comment in comments:
        comments.sort(key=lambda c: c.id, reverse=True)
        comments = comments[:per_page][::-1]

    # return render_template('home/get_comments.html', comments=comments)
    rendered_template = render_template('home/get-comments.html', comments=comments)
    return jsonify(html=rendered_template, has_more=has_more, last_page=len(comments))

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
        data['display_name'] = user.display_name if user.display_name else user.firstname + ' ' + user.lastname
        data['profile'] = url_for('static', filename='files/' + user.username + '/' + user.image)

        emit('new_comment', data, broadcast=True)
        emit('typing_status', {'user_id': '', 'name': '', 'comment': '', 'post_id': data['post_id'], 'typing': False}, broadcast=True)

# Dictionary to store users typing comments per post
typing_users = {}
# On Typing - Comment
def on_typing(data):
    user_id = data['user_id']
    postId = data['post_id']

    user = User.query.filter_by(id=user_id).first()
    display_name=user.display_name if user.display_name else user.firstname

    comment = Comment.query.filter_by(user_id=user_id).first()
    comment.typing = True
    db.session.commit()

    # Store the users typing status
    if postId in typing_users:
        typing_users[postId].add(display_name)
    else:
        typing_users[postId] = {display_name}

    emit('typing_status', {'user_id': user_id, 'name': display_name, 'users': list(typing_users[postId]), 'comment': data['comment'], 'post_id': postId, 'typing': True}, broadcast=True)

# Stop Typing - Comment
def on_stop_typing(data):
    user_id = data['user_id']
    postId = data['post_id']
    user = User.query.filter_by(id=user_id).first()
    display_name=user.display_name if user.display_name else user.firstname

    comment = Comment.query.filter_by(user_id=user_id).first()
    comment.typing = False
    db.session.commit()

    if data['comment'] == '':
    # Remove the user's typing status from the dictionary
        if postId in typing_users and display_name in typing_users[postId]:
            typing_users[postId].remove(display_name)

    emit('typing_status', {'user_id': user_id, 'name': display_name, 'users': list(typing_users[postId]), 'comment': data['comment'], 'post_id': postId, 'typing': False}, broadcast=True)
