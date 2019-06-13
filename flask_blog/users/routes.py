from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from flask_blog.users.forms import RegistrationForm, LoginForm, UpdateForm, RequestResetForm, ResetPasswordForm
from flask_login import login_user, current_user, logout_user, login_required
from flask_blog import db, bcrypt
from flask_blog.users.models import User
from flask_blog.posts.models import Post
from flask_blog.users.utils import *

users = Blueprint('users', __name__)


@users.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        flash(f'Account has been created successfully. You can login now!', 'success')
        return redirect(url_for('users.login'))

    return render_template('register.html', title='Register', form=form)


@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_val = request.args.get('next')
            return redirect(next_val) if next_val else redirect(url_for('main.home'))
        else:
            flash(f'Login unsuccessful. Please check username and password!', 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route('/account', methods=['GET', 'POST'])
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
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    image_file = url_for(
        'static', filename='profilepics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@users.route('/posts/<string:username>')
def user_posts(username):
    user = User.query\
        .filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)
    posts = Post.query\
        .filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('myposts.html', posts=posts, username=user.username)


@users.route('/reset_password', methods=['GET', 'POST'])
def request_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_email(user)
        flash('An email has been sent to the registered email id.\n'
              + 'Please check the email for more details. ', 'info')
        return redirect(url_for('users.login'))
    return render_template('request_reset_pwd.html', form=form, title='Request Password Reset')


@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

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
        return redirect(url_for('users.login'))
    return render_template('reset_pwd.html', form=form, title='Request Password Reset')
