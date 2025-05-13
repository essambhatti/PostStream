from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO, emit, join_room, leave_room


mail = Mail()
app=Flask(__name__)
csrf = CSRFProtect(app)  
app.config['SECRET_KEY'] = 'abcd'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///site.db'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'essambhatti@gmail.com'
app.config['MAIL_PASSWORD'] = 'ygrgafmxoypvhfop'  # use Gmail App Password
mail.init_app(app)
db=SQLAlchemy(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)
login_manager=LoginManager(app)
login_manager.login_view='login'
login_manager.login_message_category='info'
socketio.init_app(app)




from flaskblog import routes