import datetime

from flask_blog import db
from flask import render_template, request, url_for, flash, redirect, request, abort, Blueprint
from flask_blog.posts.forms import AddNewPost
from flask_blog.posts.models import Post
from flask_login import current_user, login_required

posts = Blueprint('posts', __name__)


@posts.route('/posts/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = AddNewPost()

    if form.validate_on_submit():
        post = Post(title=form.title.data, date_posted=datetime.datetime.today(),
                    content=form.content.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Post has been submitted successfully!', 'success')
        return redirect(url_for('main.home'))

    return render_template('new_post.html', title='Add Post', form=form, legend='Add New Post')


@posts.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title='Post', posts=[post])


@posts.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
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
        return redirect(url_for('posts.post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('new_post.html', title='Update Post', form=form, legend='Update Post')


@posts.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if (post.author != current_user):
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted successfully!', 'success')
    return redirect(url_for('main.home'))
