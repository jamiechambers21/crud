from app import app, db
from app.forms import LoginForm, RegistrationForm, EditFeedingForm, AddBabyForm, AddFamilyForm, AddRecipeForm
from app.models import User, Family, Baby, Feeding, Changing, Sleeping, Note, Recipe, users_families
from collections import defaultdict
from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from urllib.parse import urlsplit

@app.route('/')
@login_required
def index():
    # # Get the last 7 days
    # today = datetime.now().date()
    # start_date = today - timedelta(days=6)  # Show last 7 days including today

    # # Query feedings for the last week
    # feedings = Feeding.query.join(Baby).filter(
    # Baby.family_id == current_user.family_id,
    # Feeding.timestamp >= start_date).all()

    # # Count feedings per day
    # feeding_counts = defaultdict(int)
    # for feeding in feedings:
    #     day = feeding.timestamp.date()
    #     feeding_counts[day] += 1

    # # Ensure all days are present (0 if no feedings)
    # labels = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    # data = [feeding_counts[datetime.strptime(day, '%Y-%m-%d').date()] for day in labels]

    return render_template('index.html', title="Home")#, labels=labels, data=data)

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
            family = Family.get_family_from_code(form.family_code.data)
            if not family:
                flash('Invalid family code.', 'error')
                return render_template('register.html', title='Register', form=form)
        else:  # Otherwise, create a new family and baby profile

            family = Family.create_family(name = form.family_name.data)
            Baby.create_baby(name=form.baby_name.data, date_of_birth=form.baby_dob.data, family_id=family.id)

        # Create a new user and associate with the family
        _ = User.create_user(username=form.username.data, email=form.email.data, password = form.password.data, family=family)

        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user, families, family = Family.get_user_families_and_family()
    babies, _ = Family.get_family_data(family, fetch_babies=True, fetch_recipes=False)

    # Collect feedings for all babies in the selected family
    feedings = Feeding.get_feedings(babies)

    return render_template('user.html', user=user, families=families, family=family, feedings=feedings)


@app.route('/add_feeding', methods=['GET', 'POST'])
@login_required
def add_feeding():
    _, families, family = Family.get_user_families_and_family()
    babies, recipes = Family.get_family_data(family, fetch_babies=True, fetch_recipes=True)

    form = EditFeedingForm(babies=babies, recipes=recipes)

    if form.validate_on_submit():
        Feeding.create_feeding(
            baby_id=form.baby_id.data,
            user_id=current_user.id,
            timestamp=form.timestamp.data,
            feeding_type=form.feeding_type.data,
            breast_duration=form.breast_duration.data,
            bottle_amount=form.bottle_amount.data,
            solid_amount=form.solid_amount.data,
            recipe_id=form.recipe_id.data,
        )

        flash('Your feeding information has been saved.')
        return redirect(url_for('add_feeding'))

    return render_template('add_feeding.html', title='Add Feeding', families=families, family=family, recipes=recipes, form=form)

@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = AddRecipeForm()
    _, families, family = Family.get_user_families_and_family()
    _, recipes = Family.get_family_data(family, fetch_babies=False, fetch_recipes=True)

    if form.validate_on_submit():
        Recipe.create_recipe(
            family_id=family.id,
            recipe_name=form.recipe_name.data,
            recipe_ingredients=form.recipe_ingredients.data,
            recipe_instructions=form.recipe_instructions.data,
            amount=form.amount.data
        )

        flash('Recipe added successfully!')
        return redirect(url_for('index'))
    return render_template('add_recipe.html', title='Add Recipe', families=families, family=family, recipes=recipes, form=form)

@app.route('/add_baby', methods=['GET', 'POST'])
@login_required
def add_baby():
    form = AddBabyForm()
    _, families, family = Family.get_user_families_and_family()

    if form.validate_on_submit():
        Baby.create_baby(
            name=form.baby_name.data,
            date_of_birth=form.baby_dob.data,
            family_id=family.id
        )
        flash('Baby added successfully!')
        return redirect(url_for('index'))
    return render_template('add_baby.html', title='Add Baby', families=families, family=family, form=form)

@app.route('/add_family', methods=['GET', 'POST'])
@login_required
def add_family():
    form = AddFamilyForm()
    if form.validate_on_submit():
        if form.family_code.data:  # If a family code is provided, join the existing family
            family = Family.get_family_from_code(form.family_code.data)
            if not family:
                flash('Invalid family code.', 'error')
                return render_template('register.html', title='Register', form=form)
        else:
            flash("You must enter a valid family code.", "error")
            return render_template('add_family.html', title='Add Family', form=form)

        # Associate the user with the family (many-to-many)
        user = User.get_user_by_id(current_user.id)

        # Check if the association already exists
        existing_association = user.check_user_family_association(family)
        if existing_association:
            flash("You're already part of this family!", "info")
            return redirect(url_for('index'))

        # Manually insert into the association table
        user.add_family(family)

        flash('Family added successfully!')
        return redirect(url_for('index'))

    return render_template('add_family.html', title='Add Family', form=form)

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
    users_fams = db.session.execute(sa.select(users_families)).fetchall()
    users = User.query.all()
    families = Family.query.all()
    babies = Baby.query.all()
    recipes = Recipe.query.all()
    feedings = Feeding.query.order_by(Feeding.timestamp.desc()).all()
    # changes = Change.query.order_by(Change.timestamp.desc()).all()
    # sleeps = Sleep.query.order_by(Sleep.timestamp.desc()).all()

    return render_template('admin.html', users_families=users_fams, users=users, families=families, babies=babies, recipes=recipes, feedings=feedings)# , changes=changes, sleeps=sleeps)
