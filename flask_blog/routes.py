import os
import datetime
from secrets import token_hex
from PIL import Image

from flask import render_template, url_for, flash, redirect, request, abort
from flask_blog.models import User, Post
from flask_blog.forms import RegistrationForm, LoginForm, UpdateForm, AddNewPost, RequestResetForm, ResetPasswordForm
from flask_blog import app, db, bcrypt, mail
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


@app.route('/')
@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(
        Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts, title='Home')


@app.route('/about',)
def about():
    return render_template('about.html', title='About')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        flash(f'Account has been created successfully. You can login now!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_val = request.args.get('next')
            return redirect(next_val) if next_val else redirect(url_for('home'))
        else:
            flash(f'Login unsuccessful. Please check username and password!', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_image(form_image):
    rnd_img_name = token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)

    pic_name = rnd_img_name + f_ext
    pic_path = os.path.join(
        app.root_path, 'static/profilepics', pic_name)

    img_size = [125, 125]

    i = Image.open(form_image)
    i.thumbnail(img_size)
    i.save(pic_path)
    return pic_name


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data

        if form.image.data:
            image_file = save_image(form.image.data)
            current_user.image_file = image_file

        db.session.commit()

        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    image_file = url_for(
        'static', filename='profilepics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route('/posts/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = AddNewPost()

    if form.validate_on_submit():
        post = Post(title=form.title.data, date_posted=datetime.datetime.today(),
                    content=form.content.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Post has been submitted successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('new_post.html', title='Add Post', form=form, legend='Add New Post')


@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title='Post', posts=[post])


@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)

    if (post.author != current_user):
        abort(403)

    form = AddNewPost()

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post has been updated successfully!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('new_post.html', title='Update Post', form=form, legend='Update Post')


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if (post.author != current_user):
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted successfully!', 'success')
    return redirect(url_for('home'))


@app.route('/posts/<string:username>')
def user_posts(username):
    user = User.query\
        .filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)
    posts = Post.query\
        .filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('myposts.html', posts=posts, username=user.username)


def send_email(user):
    token = user.request_token()
    msg = Message('Password Reset Request', sender='utubebhu1@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{ url_for('reset_password', token=token, _external=True) }
If you have not requested for password, just ignore this message and no changes will be done to your account.
    '''
    mail.send(msg)


@app.route('/reset_password', methods=['GET', 'POST'])
def request_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_email(user)
        flash('An email has been sent to the registered email id.\n'
              + 'Please check the email for more details. ', 'info')
        return redirect(url_for('login'))
    return render_template('request_reset_pwd.html', form=form, title='Request Password Reset')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    user = User.verify_token(token)

    if user is None:
        flash('The token has expired. Please request again', 'warning')
        return redirect(url_for('request_password'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.password = hashed_pw
        db.session.commit()

        flash(f'Password has been updated successfully. You can login now!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_pwd.html', form=form, title='Request Password Reset')
