import os
from werkzeug.security import generate_password_hash

os.environ.setdefault("APP_SKIP_DEFAULT_ADMIN_SEED", "true")

from app import create_app
from app.extensions import db
from backend.app.domain.models.roles import Role
from app.domain.models.user import User

app = create_app("development")
app.config["SKIP_DEFAULT_ADMIN_SEED"] = True
app.app_context().push()

# Ensure the admin role exists.
role = Role.query.filter_by(name="Administrator").first()
if role is None:
    role = Role(name="Administrator", description="System administrator")
    db.session.add(role)
    db.session.flush()

# Make sure existing users point to a real role.
users = User.query.all()
for user in users:
    if user.role_id in (None, 0):
        user.role_id = role.id
    if user.password_hash in (None, "", "admin123"):
        user.set_password("admin123")

# If an old plain-text admin user exists, replace it with a fresh hashed one.
existing_admin = User.query.filter_by(username="admin").first()
if existing_admin is None:
    existing_admin = User(username="admin", is_active=True)
    existing_admin.role_id = role.id
    existing_admin.set_password("admin123")
    db.session.add(existing_admin)

# Remove any duplicate admin rows and keep one clean record.
admin_rows = User.query.filter_by(username="admin").all()
if len(admin_rows) > 1:
    primary = admin_rows[0]
    for duplicate in admin_rows[1:]:
        db.session.delete(duplicate)
    db.session.flush()
    primary.role_id = role.id
    primary.set_password("admin123")

# Ensure the row is active and has a hashed password.
if existing_admin is not None:
    existing_admin.is_active = True
    existing_admin.role_id = role.id
    existing_admin.set_password("admin123")

# Commit the data fix.
db.session.commit()

print("role_id:", existing_admin.role_id if existing_admin else None)
print("password_hash:", existing_admin.password_hash if existing_admin else None)
