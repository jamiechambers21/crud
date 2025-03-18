from app import db, login
from datetime import datetime
from flask import request
from flask_login import UserMixin, current_user
from hashlib import md5
from typing import Optional
import random
import string
import sqlalchemy as sa
import sqlalchemy.orm as so
from werkzeug.security import generate_password_hash, check_password_hash


# User-Family Association Table
users_families = sa.Table(
    'users_families',
    db.metadata,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('user_id', sa.BigInteger, sa.ForeignKey('users.id'), index=True, nullable=False),
    sa.Column('family_id', sa.BigInteger, sa.ForeignKey('families.id'), index=True, nullable=False),
)

# Family Table
class Family(db.Model):
    __tablename__ = "families"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    code: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True)

    users = so.relationship("User", secondary=users_families, back_populates="families")
    babies = so.relationship("Baby", back_populates="family", cascade="all, delete-orphan")
    recipes = so.relationship("Recipe", back_populates="family", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Family {self.name}>'

    @staticmethod
    def generate_family_code(digits = 32):
        char_set = string.ascii_letters + string.digits
        code = ''.join(random.SystemRandom().choice(char_set) for _ in range(digits))
        return code

    @classmethod
    def create_family(cls, name):
        family = cls(
            name = name,
            code = cls.generate_family_code()
        )
        db.session.add(family)
        db.session.commit()
        return family

    @classmethod
    def get_family_from_code(cls, code):
        return cls.query.filter_by(code=code).first()

    @staticmethod
    def get_user_families_and_family():
        """Fetches the current user, their families, and the selected family."""
        user = User.query.filter_by(id=current_user.id).first_or_404()
        families, family = Family.get_families_for_user(user, request.args.get('family_id', type=int))
        return user, families, family

    @staticmethod
    def get_families_for_user(user, page_family_id=None):
        """Fetch all families for a given user and determine the active family."""
        families = db.session.scalars(
            sa.select(Family).join(users_families).where(users_families.c.user_id == user.id)
        ).all()
        family = next((f for f in families if f.id == page_family_id), families[0] if families else None)
        return families, family


    @staticmethod
    def get_family_data(family, fetch_babies=False, fetch_recipes=False):
        """Fetch babies and recipes for a given family if needed."""
        babies = Baby.query.filter_by(family_id=family.id).all() if family and fetch_babies else []
        recipes = Recipe.query.filter_by(family_id=family.id).all() if family and fetch_recipes else []
        return babies, recipes



# User Table
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    is_admin = db.Column(db.Boolean, default=False) # This is to be site Admin (not sure if the best place, will change later)

    families = so.relationship("Family", secondary=users_families, back_populates="users")

    def __repr__(self):
        return f'<User {self.username}>'

    def avatar(self, size):
            digest = md5(self.email.lower().encode('utf-8')).hexdigest()
            return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def create_user(username, email, password, family, is_admin = False):
        user = User(
            username = username,
            email = email,
            is_admin = is_admin
        )
        user.set_password(password)
        user.families.append(family)
        db.session.add(user)
        db.session.commit()
        return user

    def get_user_by_id(user_id):
        return User.query.get(user_id)

    def check_user_family_association(self, family):
        return db.session.execute(
            sa.select(users_families).where(
                (users_families.c.user_id == self.id) & (users_families.c.family_id == family.id)
            )
        ).first()

    def add_family(self,family):
        self.families.append(family)
        db.session.add(self)
        db.session.commit()

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

    def create_baby(name, date_of_birth, family_id):
        baby = Baby(
            name = name,
            date_of_birth = date_of_birth,
            family_id = family_id
        )
        db.session.add(baby)
        db.session.commit()

# Recipe Table
class Recipe(db.Model):
    __tablename__ = "recipes"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    family_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("families.id"), index=True)
    recipe_name: so.Mapped[str] = so.mapped_column(sa.String(100))
    recipe_ingredients: so.Mapped[str] = so.mapped_column(sa.Text)
    recipe_instructions: so.Mapped[str] = so.mapped_column(sa.Text)
    amount: so.Mapped[int] = so.mapped_column(sa.Integer)

    family = so.relationship("Family", back_populates="recipes")

    def create_recipe(family_id, recipe_name, recipe_ingredients, recipe_instructions, amount=None):
        recipe = Recipe(
            family_id=family_id,
            recipe_name=recipe_name,
            recipe_ingredients=recipe_ingredients,
            recipe_instructions=recipe_instructions,
            amount=amount,
        )
        db.session.add(recipe)
        db.session.commit()

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

    recipe = db.relationship('Recipe', backref='feedings')
    baby = so.relationship("Baby", back_populates="feedings")
    user = so.relationship('User', backref='feedings')

    def create_feeding(baby_id, user_id, timestamp, feeding_type, breast_duration=None, bottle_amount=None, solid_amount=None, recipe_id=None):
        feeding = Feeding(
            baby_id=baby_id,
            user_id=user_id,
            timestamp=timestamp,
            feeding_type=feeding_type,
            breast_duration=breast_duration,
            bottle_amount=bottle_amount,
            solid_amount=solid_amount,
            recipe_id=recipe_id,
        )
        db.session.add(feeding)
        db.session.commit()
        return feeding

    def get_feedings(babies):
        feedings = sorted(
            (feeding for baby in babies for feeding in baby.feedings),
            key=lambda f: f.timestamp,
            reverse=True
        )
        return feedings


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
