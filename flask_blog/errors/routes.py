from flask import Blueprint, render_template

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(404)
def err404(error):
    return render_template('errors/err404.html', title='Page not found!'), 404
