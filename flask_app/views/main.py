from flask import render_template, request, redirect, Blueprint, url_for, flash

from .forms import ClusterSelectionForm

from ..build_feed import build_feed

main_blueprint = Blueprint("main", __name__, template_folder="templates")


@main_blueprint.route("/")
def index():
    form = ClusterSelectionForm(request.form)
    feed = build_feed("Python")
    if form.validate_on_submit():
        return render_template("index.html", form=form, feed=feed)
    return render_template("index.html", form=form, feed=feed)


@main_blueprint.route("/about/")
def about():
    return render_template("about.html")
