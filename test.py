import os
os.environ['DATABASE_URL'] = 'sqlite://'

from app import db, app
from app.models import User, Family, Baby, users_families
from app.routes import generate_code
from datetime import datetime

def add_user(family_name, username, email, family_code=None, is_admin=False, baby_name=None, baby_date_of_birth=None):
    with app.app_context():
        # Create or fetch the family
        family = Family.query.filter_by(code=family_code).first()
        if not family:
            family_code = generate_code()
            family = Family(name=family_name, code=family_code)
            db.session.add(family)
            db.session.commit()

        # Create the user
        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(username)
        db.session.add(user)
        db.session.commit()

        # Associate user with family
        user.families.append(family)
        db.session.commit()

        # Create the baby profile
        if baby_name and baby_date_of_birth:
            baby = Baby(name=baby_name, date_of_birth=datetime.strptime(baby_date_of_birth, "%Y-%m-%d").date(), family_id=family.id)
            db.session.add(baby)
            db.session.commit()

        print("User successfully added!")

        return db.session.get(User, user.id)

def get_family_code(user_id):
    with app.app_context():
        # Query the users_families table directly
        user_fam_search = db.session.execute(
            users_families.select().where(users_families.c.user_id == user_id)
        ).first()
        family_id = user_fam_search.family_id  # Extract family_id

        family = Family.query.filter_by(id=family_id).first()

        return family.code

if __name__ == "__main__":

    user1 = add_user(family_name = "Chambers",
            username = "jamie",
            email = "jamiechambers21@gmail.com",
            is_admin = True,
            baby_name  ="Leo",
            baby_date_of_birth = "2024-07-14")

    add_user(family_name = None,
            family_code = get_family_code(user1.id),
            username = "raquel",
            email = "raquel@gmail.com"
            )

    user2 = add_user(family_name = "Callaghan",
            username = "paul",
            email = "paul@gmail.com",
            baby_name  ="Noah",
            baby_date_of_birth = "2024-01-12")
