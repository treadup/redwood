import hashlib

# Calculates the password hash

password="henrik"
salt = "123456789"
m = hashlib.sha256()
m.update(salt.encode('utf-8'))
m.update(password.encode('utf-8'))
password_hash = m.hexdigest()

print(password_hash)
