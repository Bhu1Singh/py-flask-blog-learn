from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class AddNewPost(FlaskForm):
    title = StringField('Title', validators=[
                        DataRequired(), Length(min=2, max=50)])
    content = TextAreaField('Content', validators=[
                            DataRequired(), Length(min=2, max=1000)])

    submit = SubmitField('Save')
