from app import create_app
from backend.app.domain.models.roles import Role
from app.domain.models.users import User

app = create_app('development')
app.config['SKIP_DEFAULT_ADMIN_SEED'] = True
app.app_context().push()

user = User.query.filter_by(username='admin').first()
role = Role.query.filter_by(name='Administrator').first()
print('admin_exists', user is not None)
print('role_id', user.role_id if user else None)
print('role_name', user.role if user else None)
print('hash_prefix', user.password_hash[:20] if user else None)
