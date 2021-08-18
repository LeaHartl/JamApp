from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FloatField, DateField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import ValidationError, DataRequired, InputRequired, Email, EqualTo
from app.models import User, Stake, Entry
from datetime import datetime


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EntryForm(FlaskForm):

    # get stake names from data base for select field.
    def stake_choices():
        stks = [s.stake_id for s in Stake.query.all()]  # .filter_by(name=name).distinct()]
        return stks

    date = DateField('Ablesedatum', format='%Y-%m-%d', default=datetime.now(), validators=[DataRequired()])
    FE = FloatField('Freies Ende', validators=[InputRequired()])
    FE_new = FloatField('Freies Ende Neu', validators=[InputRequired()])
    # who = StringField('Wer gibt die Daten ein?')
    comment = StringField('Kommentar')
    stake_id = SelectField('Pegel Name', choices=stake_choices())
    submit = SubmitField('Speichern')
    # abl_oct = FloatField('Ablation seit Herbst')



class EntrySearchForm(FlaskForm):
    # get stake names from data base for select field.
    def stake_choices():
        stks = [s.stake_id for s in Stake.query.all()]  # .filter_by(name=name).distinct()]
        return stks

    search = SelectField('Suche Pegel:', choices=stake_choices())


class StakeForm(FlaskForm):

    stake_id = StringField('Pegelname', validators=[DataRequired()])
    drilldate = DateField('Bohrdatum', format='%Y-%m-%d', default=datetime.now(), validators=[DataRequired()])
    x = FloatField('Lon', validators=[DataRequired()])
    y = FloatField('Lat', validators=[DataRequired()])
    # who = StringField('Wer gibt die Daten ein?')
    comment = StringField('Kommentar')
    submit = SubmitField('Speichern')

