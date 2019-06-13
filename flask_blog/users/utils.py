import os
from secrets import token_hex
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from flask_blog import mail


def save_image(form_image):
    rnd_img_name = token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)

    pic_name = rnd_img_name + f_ext
    pic_path = os.path.join(
        current_app.root_path, 'static/profilepics', pic_name)

    img_size = [125, 125]

    i = Image.open(form_image)
    i.thumbnail(img_size)
    i.save(pic_path)
    return pic_name


def send_email(user):
    token = user.request_token()
    msg = Message('Password Reset Request', sender='utubebhu1@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{ url_for('users.reset_password', token=token, _external=True) }
If you have not requested for password, just ignore this message and no changes will be done to your account.
    '''
    mail.send(msg)
