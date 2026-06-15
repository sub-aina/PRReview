def login(username, password):
    query = f"SELECT * FROM users WHERE username={username}"
    user = db.execute(query)
    if user and user.password == password:
        return True
