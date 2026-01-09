# seed_users_random.py
import string
import secrets
from db import db
from app import app  # import the actual app instance
from models.user import User

# Push app context
app.app_context().push()

def generate_random_username(length=8):
    """Generate a random username of given length."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_random_password(length=12):
    """Generate a random password of given length."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Number of users to create
num_users_to_create = 10

for _ in range(num_users_to_create):
    # Ensure unique username
    while True:
        username = generate_random_username()
        if not User.query.filter_by(username=username).first():
            break

    password = generate_random_password()
    new_user = User(username=username, password=password)  # Remember: hash in production!
    db.session.add(new_user)
    print(f"Added user: {username} / {password}")

db.session.commit()
print(f"Seeding completed: {num_users_to_create} users created.")
