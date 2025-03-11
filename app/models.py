from app import db, login
from datetime import datetime
from flask_login import UserMixin
from hashlib import md5
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from werkzeug.security import generate_password_hash, check_password_hash

# Family Table
class Family(db.Model):
    __tablename__ = "families"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    code: so.Mapped[str] = so.mapped_column(sa.String(100))#, unique=True)

    users = so.relationship("User", back_populates="family", cascade="all, delete-orphan")
    babies = so.relationship("Baby", back_populates="family", cascade="all, delete-orphan")
    recipes = so.relationship("Recipe", back_populates="family", cascade="all, delete-orphan")

# User Table
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    family_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("families.id"), index=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    is_admin = db.Column(db.Boolean, default=False)

    family = so.relationship("Family", back_populates="users")

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

# Baby Table
class Baby(db.Model):
    __tablename__ = "babies"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    family_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("families.id"), index=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    date_of_birth: so.Mapped[datetime] = so.mapped_column(sa.Date)

    family = so.relationship("Family", back_populates="babies")
    feedings = so.relationship("Feeding", back_populates="baby", cascade="all, delete-orphan")
    changings = so.relationship("Changing", back_populates="baby", cascade="all, delete-orphan")
    sleepings = so.relationship("Sleeping", back_populates="baby", cascade="all, delete-orphan")
    notes = so.relationship("Note", back_populates="baby", cascade="all, delete-orphan")

# Recipe Table
class Recipe(db.Model):
    __tablename__ = "recipes"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    family_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("families.id"), index=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    ingredients: so.Mapped[str] = so.mapped_column(sa.Text)
    instructions: so.Mapped[str] = so.mapped_column(sa.Text)
    amount: so.Mapped[int] = so.mapped_column(sa.Integer)

    family = so.relationship("Family", back_populates="recipes")

# Feeding Table
class Feeding(db.Model):
    __tablename__ = "feedings"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    baby_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("babies.id"), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("users.id"), index=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=sa.func.current_timestamp())
    feeding_type: so.Mapped[str] = so.mapped_column(sa.String(20))
    breast_duration: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer)
    bottle_amount: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer)
    solid_amount: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer)
    recipe_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("recipes.id"), nullable=True)

    baby = so.relationship("Baby", back_populates="feedings")
    user = so.relationship('User', backref='feedings')


# Changing Table
class Changing(db.Model):
    __tablename__ = "changings"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    baby_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("babies.id"), index=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=sa.func.current_timestamp())
    wet_nappy: so.Mapped[bool] = so.mapped_column(sa.Boolean)
    poop_amount: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer)

    baby = so.relationship("Baby", back_populates="changings")

# Sleeping Table
class Sleeping(db.Model):
    __tablename__ = "sleepings"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    baby_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("babies.id"), index=True)
    start_timestamp: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=sa.func.current_timestamp())
    end_timestamp: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime)

    baby = so.relationship("Baby", back_populates="sleepings")

# Notes Table
class Note(db.Model):
    __tablename__ = "notes"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    baby_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("babies.id"), index=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=sa.func.current_timestamp())
    extra: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    feeding_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("feedings.id"), nullable=True)
    changing_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("changings.id"), nullable=True)
    sleeping_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("sleepings.id"), nullable=True)

    baby = so.relationship("Baby", back_populates="notes")

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))
