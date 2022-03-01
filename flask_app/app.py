import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, flash

from .extensions import cors, turbo

BASE_DIR = Path(__file__).parent.parent


def create_app(deploy_mode="Development", settings_override={}):
    load_dotenv()
    deploy_mode = (
        deploy_mode
        if deploy_mode is not None
        else os.environ.get("DEPLOY_MODE", "Development")
    )
    app = Flask(__name__, static_folder="../frontend/build", static_url_path="/static/")

    config_module = f"config.{deploy_mode}Config"
    print(f"running with {config_module} config")
    app.config.from_object(config_module)
    app.config["CORS_HEADERS"] = "Content-Type"
    app.config["Access-Control-Allow-Origin"] = "*"
    app.config.update(
        {
            "WEBPACK_LOADER": {
                "MANIFEST_FILE": os.path.join(BASE_DIR, "frontend/build/manifest.json"),
            }
        }
    )
    app.config.update(settings_override)

    cors.init_app(app)
    turbo.init_app(app)

    from webpack_boilerplate.config import setup_jinja2_ext

    setup_jinja2_ext(app)
    from .views import (
        main_blueprint,
    )

    app.register_blueprint(main_blueprint)

    @app.cli.command("webpack_init")
    def webpack_init():
        from cookiecutter.main import cookiecutter
        import webpack_boilerplate

        pkg_path = os.path.dirname(webpack_boilerplate.__file__)
        cookiecutter(pkg_path, directory="frontend_template")

    return app
