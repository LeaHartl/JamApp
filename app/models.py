from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    #entries = db.relationship('Entry', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Stake(db.Model):
    __tablename__ = 'stakes'
    id = db.Column(db.Integer, primary_key=True, index=True)
    stake_id = db.Column(db.String, db.ForeignKey('entries.stake_id'))
    # stake_id = db.Column(db.String, db.ForeignKey('entries.stake_id'))
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    drilldate = db.Column(db.DateTime)
    comment = db.Column(db.String)
    who = db.Column(db.String)
    abl_since_drilled = db.Column(db.Float)

    # def __getitem__(self, key):
    #     print("Inside `__getitem__` method!", self, key)
    #     return self.__dict__[key]


class Entry(db.Model):
    __tablename__ = 'entries'
    id = db.Column(db.Integer, primary_key=True, index=True)
    stake_id = db.Column(db.String,  db.ForeignKey('stakes.stake_id'))
    date = db.Column(db.DateTime)
    FE = db.Column(db.Float)
    FE_new = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    comment = db.Column(db.String)
    who = db.Column(db.String)
    abl_since_last = db.Column(db.Float)
    abl_since_oct = db.Column(db.Float)
