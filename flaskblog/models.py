from datetime import datetime
from flaskblog import db, login_manager
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm')

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=expiration)
    except:
        return False
    return email

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
likes = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True)
)
post_trend = db.Table('post_trend',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('trend_id', db.Integer, db.ForeignKey('trend.id'), primary_key=True)
)

class User(db.Model,UserMixin):
    id = db.Column( db.Integer, primary_key=True )
    username = db.Column( db.String(20), nullable=False, unique=True)
    email = db.Column( db.String(120), nullable=False, unique=True)
    about = db.Column( db.String(500), nullable=True, default = ' ')
    image_file = db.Column( db.String(20), nullable=False, default='default.jpg')
    password = db.Column( db.String(60), nullable=False)
    is_confirmed = db.Column(db.Boolean, default=False)
    posts = db.relationship( 'Posts', backref='author', lazy=True ,  cascade="all, delete")
    liked = db.relationship('Posts', secondary=likes,backref=db.backref('likers', lazy='dynamic'), lazy='dynamic')

        # Add this method to generate a token
    def get_token(self, expires_sec=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.email, salt='email-confirm')

    # Add this method to verify a token
    @staticmethod
    def verify_token(token, expires_sec=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt='email-confirm', max_age=expires_sec)
        except:
            return None
        return email

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"
    
    def like_post(self, post):
        if not self.has_liked_post(post):
            self.liked.append(post)

    def unlike_post(self, post):
        if self.has_liked_post(post):
            self.liked.remove(post)

    def has_liked_post(self, post):
        return self.liked.filter(likes.c.post_id == post.id).count() > 0

    
class Posts(db.Model):
    id = db.Column( db.Integer, primary_key=True )
    title = db.Column( db.String(100), nullable=False)
    date_posted = db.Column( db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column( db.Text, nullable=False)
    attachment = db.Column( db.String(20))
    user_id = db.Column( db.Integer, db.ForeignKey('user.id'), nullable=False)
    trends = db.relationship('Trend', secondary=post_trend, back_populates='posts',passive_deletes=True)
    comments = db.relationship('Comment', backref='parent_post', lazy=True, cascade="all, delete-orphan")
    original_post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    original_post = db.relationship('Posts', remote_side=[id], backref='reposts')

    
    def __repr__(self):
        return f"User('{self.title}', '{self.date_posted}')"
    @property
    def like_count(self):
        return self.likers.count()
    



class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    user = db.relationship('User', backref='comments', lazy=True)




class Trend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    posts = db.relationship('Posts', secondary=post_trend, back_populates='trends')





class MessageRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_accepted = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])


class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

class BlockedUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blocked_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    blocker = db.relationship('User', foreign_keys=[blocker_id])
    blocked = db.relationship('User', foreign_keys=[blocked_id])