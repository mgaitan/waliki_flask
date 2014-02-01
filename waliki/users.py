import os
import json


"""
    User classes & helpers
    ~~~~~~~~~~~~~~~~~~~~~~
"""


class UserManager(object):
    """A very simple user Manager, that saves it's data as json."""
    def __init__(self, path, app):
    	self.app = app
        self.file = os.path.join(path, 'users.json')

    def read(self):
        if not os.path.exists(self.file):
            return {}
        with open(self.file) as f:
            data = json.loads(f.read())
        return data

    def write(self, data):
        with open(self.file, 'w') as f:
            f.write(json.dumps(data, indent=2))

    def add_user(self, name, password, full_name, email,
                 active=True, roles=[], authentication_method=None):
        users = self.read()
        if users.get(name):
            return False
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        new_user = {
            'active': active,
            'roles': roles,
            'authentication_method': authentication_method,
            'authenticated': False,
            'full_name': full_name,
            'email': email
        }
        new_user['password'] = self.app.make_password(authentication_method,
                                                 	  password)
        users[name] = new_user
        self.write(users)
        userdata = users.get(name)
        return User(self, name, userdata)

    def get_user(self, name):
        users = self.read()
        userdata = users.get(name)
        if not userdata:
            return None
        return User(self, name, userdata)

    def delete_user(self, name):
        users = self.read()
        if not users.pop(name, False):
            return False
        self.write(users)
        return True

    def update(self, name, userdata):
        data = self.read()
        data[name] = userdata
        self.write(data)


class User(object):
    def __init__(self, manager, name, data):
        self.manager = manager
        self.name = name
        self.data = data

    def get(self, option):
        return self.data.get(option)

    def set(self, option, value):
        self.data[option] = value
        self.save()

    def save(self):
        self.manager.update(self.name, self.data)

    def is_authenticated(self):
        return self.data.get('authenticated')

    def is_active(self):
        return self.data.get('active')

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.name

    def check_password(self, password):
        """Return True, return False, or raise NotImplementedError if the
        authentication_method is missing or unknown."""
        authentication_method = self.data.get('authentication_method', None)
        user_password = self.get('password')
        return app.check_password(authentication_method,
                                  user_password, password)


def get_default_authentication_method():
    return app.config.get('DEFAULT_AUTHENTICATION_METHOD', 'hash')


def make_salted_hash(password, salt=None):
        if not salt:
            salt = os.urandom(64)
        d = hashlib.sha512()
        d.update(salt[:32])
        d.update(password)
        d.update(salt[32:])
        return binascii.hexlify(salt) + d.hexdigest()


def make_password(authmethod, password):

    if authmethod == "hash":
        return make_salted_hash(password)
    elif authmethod == "cleartext":
        return password


def check_password(authmethod, upassword, password):

    def check_hashed_password(password, salted_hash):
        salt = binascii.unhexlify(salted_hash[:128])
        return make_salted_hash(password, salt) == salted_hash

    if authmethod == "hash":
        return check_hashed_password(password, upassword)
    elif authmethod == "cleartext":
        return password == upassword
    return False