import bcrypt

password = "admin"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(f"Password: {password}")
print(f"Hash: {hashed.decode('utf-8')}")

