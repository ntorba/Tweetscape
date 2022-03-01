from flask_app.models import User, Match
from flask_app.extensions import db


def login(client, email, password):
    return client.post(
        "/login", data=dict(email=email, password=password), follow_redirects=True
    )


def logout(client):
    return client.get("/logout", follow_redirects=True)


def add_user(role, email, password):
    user = User(role=role, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return user


def add_match(user, form_data):
    match = Match(leader_id=user.id, **form_data)
    db.session.add(match)
    db.session.commit()
    return match
