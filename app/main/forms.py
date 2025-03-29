from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length


class ContactForm(FlaskForm):
    """Form for the contact page."""

    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    subject = StringField(
        "Subject", validators=[DataRequired(), Length(min=2, max=100)]
    )
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=10)])
    submit = SubmitField("Send Message")


class SearchForm(FlaskForm):
    """Form for searching."""

    query = StringField("Search", validators=[DataRequired()])
    category = SelectField(
        "Category",
        choices=[
            ("all", "All Categories"),
            ("transactions", "Transactions"),
            ("posts", "Posts"),
        ],
    )
    submit = SubmitField("Search")
