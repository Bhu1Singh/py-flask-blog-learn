import os
from secrets import token_hex
from PIL import Image

from flask import render_template, url_for, flash, redirect, request
from flask_blog.models import User, Post
from flask_blog.forms import RegistrationForm, LoginForm, UpdateForm
from flask_blog import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required


posts = [
    {
        'author': 'Bhuwan Singh',
        'title': 'First Blog Post',
        'content': 'Content for the first post',
        'date_posted': '10-Apr-2019'
    },
    {
        'author': 'Priyanka Bhatt',
        'title': 'Second Blog Post',
        'content': 'Content for the second post',
        'date_posted': '11-Apr-2019'
    }
]


@app.route('/')
@app.route('/home')
def home():
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


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data

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
