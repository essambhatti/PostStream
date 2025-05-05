from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired,Length,Email,EqualTo,ValidationError
from flask_wtf.file import FileAllowed
import email_validator
from flaskblog.models import User,Posts,Trend
from flask_login import current_user



class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        
        if user:
            raise ValidationError('Username is taken, Try another one!')
        
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        
        if user:
            raise ValidationError('Account with this email already exists!')

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(),Email()])
    password = PasswordField('passwprd', validators=[DataRequired()])
    remember=BooleanField('Remember me')
    submit = SubmitField("Login" )



class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField("Update Profile Picture", validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    about = StringField('About', validators=[Length(max=499)])
    submit = SubmitField('Update')


    def validate_username(self, username):
        if username.data!=current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username is taken, Try another one!')
        
    def validate_email(self, email):
        if email.data!=current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Account with this email already exists!')
            
class PostForm(FlaskForm):
    title=StringField("Title", validators=[DataRequired(), Length(max=50)])
    content=TextAreaField('Content', validators=[DataRequired()])
    attachment = FileField("Attachment", validators=[FileAllowed(['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mpeg',
                   'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg', 'webp'])])
    trends = StringField('Trends (comma-separated)')
    publish = SubmitField('Publish')




class EmptyForm(FlaskForm):
    pass

    
class CommentForm(FlaskForm):
    content = TextAreaField('Add a comment..', validators=[DataRequired()])
    submit = SubmitField("Post comment.. ", validators=[DataRequired()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit  = SubmitField('Reset Password')


class MessageForm(FlaskForm):
    content = TextAreaField('Send a message...', validators=[DataRequired()])
    send = SubmitField("Send", validators=[DataRequired()])