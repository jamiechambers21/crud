from app import db
from app.models import User, Family, Baby, Feeding, Changing, Sleeping, Note, Recipe
from datetime import datetime
from flask_wtf import FlaskForm
import sqlalchemy as sa
from wtforms import StringField, SelectField, IntegerField, PasswordField, BooleanField, SubmitField, TextAreaField, DateTimeField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Optional


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    family_name = StringField('Family Name', validators=[Optional()])
    family_code = StringField('Family Code (optional)', validators=[Optional()])  # New field for joining an existing family

    username = StringField('Username', validators=[DataRequired()])
    baby_name = StringField('Baby Name', validators=[Optional()])
    baby_dob = DateField('Date of Birth', format='%Y-%m-%d', default=datetime.now)

    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')

class EditFeedingForm(FlaskForm):
    baby_id = SelectField('Baby', coerce=int, validators=[DataRequired()])  # Updated to select baby
    feeding_type = SelectField('Feeding Type', choices=[('breast', 'Breast'), ('bottle', 'Bottle'), ('solids', 'Solids')], validators=[DataRequired()])
    breast_duration = IntegerField('Breastfeeding Duration (minutes)', validators=[Optional()])
    bottle_amount = IntegerField('Bottle Amount (ml)', validators=[Optional()])
    solid_amount = IntegerField('Solid Amount (g)', validators=[Optional()])
    recipe_id = SelectField('Recipe', coerce=int, choices=[], validators=[Optional()])  # Added default empty choices
    timestamp = DateTimeField('Feeding Time', format='%Y-%m-%dT%H:%M', default=datetime.now, validators=[DataRequired()])
    submit = SubmitField('Submit')

class AddBabyForm(FlaskForm):
    baby_name = StringField('Baby Name', validators=[Optional()])
    baby_dob = DateField('Date of Birth', format='%Y-%m-%d', default=datetime.now)
    submit = SubmitField('Submit')
