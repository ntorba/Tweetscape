# project/user/forms.py


from flask_wtf import FlaskForm
from wtforms import (
    SelectField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo


class ClusterSelectionForm(FlaskForm):
    cluster = SelectField("Select Cluster", choices=["Ethereum", "Python", "Bitcoin"])
