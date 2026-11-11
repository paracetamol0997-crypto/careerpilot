"""Flask application factory and entry point for CareerPilot AI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from flask import Flask

from careerpilot.config import Config
from careerpilot.db import init_db
from careerpilot.routes.api import api_bp
from careerpilot.routes.pages import pages_bp


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure the CareerPilot Flask application."""
    load_dotenv()

    base_dir = Path(__file__).resolve().parent
    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "public" / "static"),
        static_url_path="/static",
    )

    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    Path(app.config["INSTANCE_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

    init_db(Path(app.config["DATABASE_PATH"]))

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
