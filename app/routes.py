from app import app, db
from app.forms import LoginForm, RegistrationForm, EditFeedingForm, AddBabyForm
from app.models import User, Family, Baby, Feeding, Changing, Sleeping, Note, Recipe
from collections import defaultdict
from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from urllib.parse import urlsplit

def generate_code():
    import random
    import string
    N = 32
    char_set = string.ascii_letters + string.digits
    code = ''.join(random.SystemRandom().choice(char_set) for _ in range(N))
    return code

@app.route('/')
@login_required
def index():
    # Get the last 7 days
    today = datetime.now().date()
    start_date = today - timedelta(days=6)  # Show last 7 days including today

    # Query feedings for the last week
    feedings = Feeding.query.join(Baby).filter(
    Baby.family_id == current_user.family_id,
    Feeding.timestamp >= start_date).all()

    # Count feedings per day
    feeding_counts = defaultdict(int)
    for feeding in feedings:
        day = feeding.timestamp.date()
        feeding_counts[day] += 1

    # Ensure all days are present (0 if no feedings)
    labels = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    data = [feeding_counts[datetime.strptime(day, '%Y-%m-%d').date()] for day in labels]

    return render_template('index.html', title="Home", labels=labels, data=data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.family_code.data:  # If a family code is provided, join the existing family
            family = Family.query.filter_by(code=form.family_code.data).first()
            if not family:
                flash('Invalid family code.', 'error')
                return render_template('register.html', title='Register', form=form)
        else:  # Otherwise, create a new family and baby profile
            code = generate_code()
            family = Family(name=form.family_name.data, code=code)
            db.session.add(family)
            db.session.commit()

        # Create a new user and associate with the family
        user = User(username=form.username.data, email=form.email.data, family_id=family.id)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Only create a baby if a new family is created
        if not form.family_code.data:
            baby = Baby(name=form.baby_name.data, date_of_birth=form.baby_dob.data, family_id=family.id)
            db.session.add(baby)
            db.session.commit()

        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    family = Family.query.filter_by(id=user.family_id).first_or_404()
    babies = Baby.query.filter_by(family_id=user.family_id).all()

    feedings = []
    for baby in babies:
        feedings.extend(baby.feedings)
    feedings.sort(key=lambda f: f.timestamp, reverse=True)
    return render_template('user.html', user=user, feedings=feedings, family=family)


@app.route('/add_feeding', methods=['GET', 'POST'])
@login_required
def add_feeding():
    form = EditFeedingForm()
    babies = Baby.query.filter_by(family_id=current_user.family_id).all()
    form.baby_id.choices = [(baby.id, baby.name) for baby in babies]
    form.recipe_id.choices = []

    if form.validate_on_submit():
        timestamp = request.form.get('timestamp')
        try:
            timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M')
        except ValueError:
            timestamp = datetime.now()

        feeding = Feeding(
            baby_id=form.baby_id.data,
            user_id=current_user.id,
            feeding_type=form.feeding_type.data,
            breast_duration=form.breast_duration.data or None,
            bottle_amount=form.bottle_amount.data or None,
            solid_amount=form.solid_amount.data or None,
            timestamp=timestamp
        )
        db.session.add(feeding)
        db.session.commit()

        flash('Your feeding information has been saved.')
        return redirect(url_for('add_feeding'))

    return render_template('add_feeding.html', title='Add Feeding', form=form)

@app.route('/add_baby', methods=['GET', 'POST'])
@login_required
def add_baby():
    form = AddBabyForm()  # Assumes you have created a BabyForm with baby_name and baby_dob fields
    if form.validate_on_submit():
        baby = Baby(
            name=form.baby_name.data,
            date_of_birth=form.baby_dob.data,
            family_id=current_user.family_id  # Associate the baby with the current user's family
        )
        db.session.add(baby)
        db.session.commit()
        flash('Baby added successfully!')
        return redirect(url_for('index'))
    return render_template('add_baby.html', title='Add Baby', form=form)


def admin_required(func):
    """Decorator to restrict access to admins only."""
    from functools import wraps
    from flask import abort

    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return func(*args, **kwargs)

    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.all()
    families = Family.query.all()
    babies = Baby.query.all()
    feedings = Feeding.query.order_by(Feeding.timestamp.desc()).all()
    # changes = Change.query.order_by(Change.timestamp.desc()).all()
    # sleeps = Sleep.query.order_by(Sleep.timestamp.desc()).all()

    return render_template('admin.html', users=users, families=families, babies=babies, feedings=feedings)# , changes=changes, sleeps=sleeps)
