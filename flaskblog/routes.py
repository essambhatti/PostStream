from flask import render_template,url_for,flash,redirect,request,abort
from flaskblog.models import User, Posts, Comment, Trend, MessageRequest, Messages,  post_trend
from flaskblog.forms import RegistrationForm,LoginForm,UpdateAccountForm,PostForm,EmptyForm,CommentForm, ResetPasswordForm, MessageForm
from flaskblog import app,db, bcrypt
from flask_login import login_user,current_user,logout_user,login_required
from sqlalchemy import or_
import secrets
import os
from PIL import Image
import random
from datetime import datetime, timedelta
from flask_mail import Message
from flaskblog.__init__ import mail 
from itsdangerous import URLSafeTimedSerializer
from flaskblog.moderations import is_content_inappropriate, is_nsfw_image, is_nsfw_video
from sqlalchemy.exc import IntegrityError
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from . import socketio

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _ , f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path =  os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    resize = (50, 50)
    i = Image.open(form_picture)
    i.thumbnail(resize)
    i.save(picture_path)

    return picture_fn

def send_confirmation_email(user):
    token = user.get_token()  # assuming your model has this method
    msg = Message('Confirm Your Email',
                  sender='your_email@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To confirm your email, visit the following link:
{url_for('confirm_email', token=token, _external=True)}

If you did not make this request, please ignore this email.
'''
    mail.send(msg)

def save_attachment(file):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(file.filename)
    attachment_fn = random_hex + f_ext
    attachment_path = os.path.join(app.root_path, 'static/post_attachments', attachment_fn)

    # Check if it's an image
    if f_ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        output_size = (600, 400)  # Adjust width x height as needed
        i = Image.open(file)
        i.thumbnail(output_size)  # Maintain aspect ratio
        i.save(attachment_path)
    else:
        file.save(attachment_path)  # Save as-is for videos/docs

    return attachment_fn, attachment_path

#home route
@app.route("/")
@app.route("/home")
def home():
    form=EmptyForm()
    repost = EmptyForm()
    all_posts = Posts.query.all()
    viral_posts = [post for post in all_posts if (post.like_count or 0) >= 10 or len(post.comments) >= 5]
    new_posts = [post for post in all_posts if post.date_posted > datetime.utcnow() - timedelta(days=7)]
    viral_ids = set(post.id for post in viral_posts)
    mixed_posts = viral_posts + [post for post in new_posts if post.id not in viral_ids]
    random.shuffle(mixed_posts)
    if len(mixed_posts) < 10:
        extra_posts = [post for post in all_posts if post.id not in [p.id for p in mixed_posts]]
        random.shuffle(extra_posts)
        mixed_posts += extra_posts[:10 - len(mixed_posts)]
    return render_template("home.html", posts=mixed_posts, form=form, repost=repost)

#about route
@app.route("/about")
def about():
    return render_template("about.html",title="about")



@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        send_confirmation_email(user)

        # Generate token
        token = user.get_token()

        # You can now send this token via email for verification
        print(f"Verification link: {url_for('confirm_email', token=token, _external=True)}")

        flash("Account created! Please check your email to confirm.", 'success')
        return redirect(url_for('login'))
    return render_template("register.html", title="Register", form=form)

@app.route("/confirm_email/<token>")
def confirm_email(token):
    email = User.verify_token(token)
    if email is None:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('register'))

    user = User.query.filter_by(email=email).first()
    if user:
        user.is_confirmed = True  # ✅ Mark user as confirmed
        db.session.commit()
        flash('Email confirmed. You can now log in.', 'success')
        return redirect(url_for('login'))

    flash('Account not found.', 'danger')
    return redirect(url_for('register'))

@app.route("/resend_confirmation", methods=["POST"])
def resend_confirmation():
    email = request.form.get("email")
    user = User.query.filter_by(email=email).first()

    if user:
        if user.is_confirmed:
            flash("Your email is already confirmed. You can log in.", "info")
            return redirect(url_for('login'))
        
        send_confirmation_email(user)  # reuse your existing function
        flash("A new confirmation email has been sent!", "success")
    else:
        flash("No account found with that email.", "danger")
    
    return redirect(url_for('login'))




#login route
@app.route("/login" , methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if not user.is_confirmed:
                flash("Please confirm your email before logging in.", "warning")
                return redirect(url_for('login'))

            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                flash('You have been logged in!', 'success')
                return redirect(url_for('home'))
        else:
            flash('login unsuccessful! please check email and password', 'danger')
    return render_template("login.html", title="login" ,form=form)

#logout route
@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

#account info route
@app.route('/account', methods=['GET','POST'])
@login_required
def account():
    form=UpdateAccountForm()
    repost = EmptyForm()
    
    if form.validate_on_submit():
        email_changed = current_user.email != form.email.data

        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.about = form.about.data

        if email_changed:
            current_user.email = form.email.data
            current_user.is_confirmed = False
            db.session.commit()

            send_confirmation_email(current_user)
            logout_user()  
            flash('Email updated. Please verify your new email to log in.', 'info')
            return redirect(url_for('login'))

        db.session.commit()
        flash('Your account info has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method =='GET':
        form.username.data=current_user.username
        form.email.data=current_user.email
        form.about.data=current_user.about

    posts = Posts.query.filter_by(author=current_user).order_by(Posts.date_posted.desc()).all()

    image_file=url_for("static" , filename="profile_pics/"+ current_user.image_file)
    return render_template('account.html', title="Account", image_file=image_file, form=form , posts=posts, repost = repost )

#create post route
@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        trend_txt = form.trends.data if form.content.data else None
        if trend_txt:
            if is_content_inappropriate(title) or is_content_inappropriate(content) or is_content_inappropriate(trend_txt) :
                flash("Your post contains inappropriate content. Please modify it.", "danger")
                return redirect(url_for("new_post"))
        elif is_content_inappropriate(title) or is_content_inappropriate(content):
            flash("Your post contains inappropriate content. Please modify it.", "danger")
            return redirect(url_for("new_post"))
        attachment_filename = None
        if form.attachment.data:
            attachment_filename, attachment_path = save_attachment(form.attachment.data)
            ext = os.path.splitext(attachment_filename)[1].lower()
            
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                if is_nsfw_image(attachment_path):
                    flash("Your image contains inappropriate content.", "danger")
                    return redirect(url_for("new_post"))
            elif ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv']:
                if is_nsfw_video(attachment_path):
                    flash("Your video contains inappropriate content.", "danger")
                    return redirect(url_for("new_post"))
            

        post = Posts(title=form.title.data, content=form.content.data,
                    author=current_user, attachment=attachment_filename)
        trend_names = list(set(t.strip().lower() for t in form.trends.data.split(',') if t.strip()))

        for name in trend_names:
            trend = Trend.query.filter_by(name=name).first()
            if not trend:
                trend = Trend(name=name)
                db.session.add(trend)  # Add to session so it has an ID
                db.session.flush()     # Flush so it can be used in the relationship

            if trend not in post.trends:
                post.trends.append(trend)

        db.session.add(post)
        db.session.commit()
        flash('The post is created and published!', 'success')
        return redirect(url_for('home'))
    return render_template('new_post.html',title='New Post', legend = 'New Post', form=form, post=None)

#single post route
@app.route('/post/<int:post_id>' , methods=['GET', 'POST'])
def post(post_id):
    post = Posts.query.get_or_404(post_id)
    form=EmptyForm()
    delete_comment=EmptyForm()
    comment_form= CommentForm()
    repost = EmptyForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please login to commenr', 'danger')
            return redirect(url_for('login'))
        comment=Comment(content=comment_form.content.data, user_id=current_user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('post', post_id=post.id))
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.date_posted.desc()).all()
    return render_template('post.html', title=post.title, post=post, form=form,comment_form=comment_form,comments=comments,delete_comment=delete_comment, repost=repost)

#update post route
@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def updatepost(post_id):
    post = Posts.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    form = PostForm()

    if form.validate_on_submit():
        attachment_file = None
        if form.attachment.data:
            attachment_file = save_attachment(form.attachment.data)
        post.title = form.title.data
        post.content = form.content.data
        post.attachment = attachment_file


        post.trends.clear()

  
        trend_names = [t.strip().lower() for t in form.trends.data.split(',') if t.strip()]
        for name in trend_names:
            trend = Trend.query.filter_by(name=name).first()
            if not trend:
                trend = Trend(name=name)
                db.session.add(trend)  
            post.trends.append(trend)  
        db.session.commit()
        flash('Your Post has been Updated!', 'success')
        return redirect(url_for('post', post_id=post.id))

    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.attachment.data = post.attachment
        form.trends.data = ', '.join([trend.name for trend in post.trends]) 

    return render_template('new_post.html', title="Update Post", form=form, legend="Update Post", post=post)

#delete post route
@app.route('/post/<int:post_id>/delete', methods= ['POST'])
@login_required
def deletepost(post_id):
    post= Posts.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your Post has been Deleted!', 'success')
    return redirect(url_for('home'))


    
#like route
@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like(post_id):
    post=Posts.query.get_or_404(post_id)
    if current_user.has_liked_post(post):
        current_user.unlike_post(post)
    elif not current_user.has_liked_post(post):
        current_user.like_post(post)
    db.session.add(post)
    db.session.commit()
    return redirect(request.referrer)



@app.route('/comment/<int:comment_id>/update', methods= ['GET', 'POST'])
@login_required
def update_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user != current_user:
        abort(403)
    form = CommentForm()
    if form.validate_on_submit():
        comment.content=form.content.data
        db.session.commit()
        flash('Your Comment has been Updated!', 'success')
        return redirect(url_for('post', post_id=comment.post_id))
    elif request.method== 'GET':
        form.content.data = comment.content
       
    return render_template('update_comment.html', title="Update Comment", form = form)

@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user != current_user:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment has been deleted.", "success")
    return redirect(url_for('post', post_id=comment.post_id))


@app.route("/user/<string:username>")
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Posts.query.filter_by(author=user).order_by(Posts.date_posted.desc()).all()
    form = EmptyForm()
    repost = EmptyForm()
    return render_template("user.html", posts=posts, form=form, user=user, repost=repost)


# repost route
@app.route('/repost/<int:post_id>', methods=['POST'])
@login_required
def repost(post_id):
    original = Posts.query.get_or_404(post_id)
    repost  = Posts(title= f'{original.title}', content= original.content, user_id=  current_user.id, original_post_id = original.id)
    db.session.add(repost)
    db.session.commit()
    flash("Post has been reposted !", "success")
    return redirect(url_for('home'))

# Top trends route

@app.route('/trends')
def trends():
    filter_option = request.args.get('filter', 'all') 

    now = datetime.utcnow()
    if filter_option == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_option == '7days':
        start_date = now - timedelta(days=7)
    elif filter_option == '30days':
        start_date = now - timedelta(days=30)
    else:
        start_date = None

    # Query trends with post count
    if start_date:
        # Filter posts by date
        trends_with_count = (
            db.session.query(Trend, db.func.count(Posts.id).label('post_count'))
            .join(Trend.posts)
            .filter(Posts.date_posted >= start_date)
            .group_by(Trend.id)
            .order_by(db.desc('post_count'))
            .all()
        )
    else:

        trends_with_count = (
            db.session.query(Trend, db.func.count(Posts.id).label('post_count'))
            .join(Trend.posts)
            .group_by(Trend.id)
            .order_by(db.desc('post_count'))
            .all()
        )

    return render_template('trends.html', trends_with_count=trends_with_count, filter=filter_option)

# trending posts
@app.route("/trend/<string:name>")
def trend_posts(name):
    trend = Trend.query.filter_by(name=name).first_or_404()
    posts = Posts.query.join(post_trend).join(Trend).filter(Trend.name == name).order_by(Posts.date_posted.desc()).all()
    form=EmptyForm()
    repost = EmptyForm()
    return render_template("trend_posts.html", trend=trend, posts=posts, form=form, repost=repost)

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)

    for post in user.posts:
        db.session.delete(post)

    logout_user()
    db.session.delete(user)
    db.session.commit()
    
    flash('Your account has been permanently deleted.', 'info')
    return redirect(url_for('home'))

@app.route('/reset_password', methods=['POST', 'GET'])
@login_required
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
    #    db.session.delete(current_user.password)
       hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
       current_user.password = hashed_pw
       db.session.commit()
       flash('Your password has been changed','success')
       return redirect(url_for('account'))
    return render_template("reset_password.html", form=form)


@app.route('/search_results')
@login_required
def search_results():
    form = EmptyForm()
    repost = EmptyForm()
    query = request.args.get('query', '')
    filter_by = request.args.get('filter', 'posts')

    posts = Posts.query.filter(
    or_(
        Posts.title.ilike(f"%{query}%"),
        Posts.title.ilike(f"{query}%"),
        Posts.title.ilike(f"%{query}")
    )
).all() if filter_by == 'posts' else []

    trends = []
    if filter_by == 'trends':
        # Get all trends matching query
        trends = Trend.query.filter(or_(
        Trend.name.ilike(f"%{query}%"),
        Trend.name.ilike(f"{query}%"),
        Trend.name.ilike(f"%{query}")
    )
).all()

    users = User.query.filter(
    or_(
        User.username.ilike(f"{query}%"),
        User.username.ilike(f"%{query}"),
        User.username.ilike(f"%{query}%")
    )
).all() if filter_by == 'users' else []

    return render_template(
        'results.html',
        query=query,
        posts=posts,
        users=users,
        filter_by=filter_by,
        form=form,
        repost=repost,
        trends=trends
    )


@app.route('/send_request/<int:receiver_id>')
@login_required
def send_request(receiver_id):
    receiver = User.query.get(receiver_id) 
    existing = MessageRequest.query.filter_by(sender_id=current_user.id, receiver_id=receiver_id).first()
    if not existing:
        req = MessageRequest(sender_id=current_user.id, receiver_id=receiver_id)
        db.session.add(req)
        db.session.commit()
        flash("Message request sent!", "success")
        return redirect(url_for("user_posts", username=receiver.username))
    flash("You have already sent the request", "danger")
    return redirect(url_for("user_posts", username=receiver.username))



@app.route('/accept_request/<int:request_id>')
@login_required
def accept_request(request_id):
    req = MessageRequest.query.get_or_404(request_id)
    if req.receiver_id != current_user.id:
        abort(403)
    req.is_accepted = True
    db.session.commit()
    flash("Message request accepted!", "success")
    return redirect(url_for("chat", user_id=req.sender_id))


@app.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    messages = Messages.query.filter(
        ((Messages.sender_id == current_user.id) & (Messages.receiver_id == user_id)) |
        ((Messages.sender_id == user_id) & (Messages.receiver_id == current_user.id))
    ).order_by(Messages.timestamp.asc()).all()
    
    return render_template('chat.html', user_id=user_id, messages=messages, current_user=current_user)
@socketio.on('join')
def handle_join(room):
    join_room(room)


@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    msg = data['msg']
    user = data['user']
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']

    # Save message to DB
    new_message = Messages(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=msg
    )
    db.session.add(new_message)
    db.session.commit()

    # Broadcast to room
    send({'msg': msg, 'user': user}, to=room)

@app.route('/messages_dashboard')
@login_required
def messages_dashboard():
    # All accepted chat requests
    accepted_requests = MessageRequest.query.filter(
        ((MessageRequest.sender_id == current_user.id) | (MessageRequest.receiver_id == current_user.id)) &
        (MessageRequest.is_accepted == True)
    ).all()

    # All pending incoming requests
    pending_requests = MessageRequest.query.filter_by(receiver_id=current_user.id, is_accepted=False).all()

    return render_template('messages_dashboard.html', accepted_requests=accepted_requests, pending_requests=pending_requests)
