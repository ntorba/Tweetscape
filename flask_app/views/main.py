from flask import render_template, request, redirect, Blueprint, url_for, flash

from .forms import ClusterSelectionForm

from ..build_feed import FeedDB, url_get_host

main_blueprint = Blueprint("main", __name__, template_folder="templates")

db = FeedDB("db/test_db2.json")


@main_blueprint.route("/", methods=["GET", "POST"])
def index():
    form = ClusterSelectionForm(request.form)
    if form.validate_on_submit():
        external_url_feed = db.get_external_url_feed(form.data["cluster"])
        return render_template(
            "index.html", form=form, feed=external_url_feed, url_get_host=url_get_host
        )
    external_url_feed = db.get_external_url_feed("Ethereum")
    return render_template(
        "index.html", form=form, feed=external_url_feed, url_get_host=url_get_host
    )


@main_blueprint.route("/about/")
def about():
    return render_template("about.html")
