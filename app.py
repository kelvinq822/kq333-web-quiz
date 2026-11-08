"""Flask application factory."""
from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request

from config import Config
from services.filestore import Store


def create_app(config_object=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)
    app.json.ensure_ascii = False

    store = Store(app.config["DATA_DIR"])
    app.extensions["store"] = store

    from routes.api import bp as api_bp
    from routes.pages import bp as pages_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def not_found(_err):
        if request.path.startswith("/api/"):
            return jsonify(error="not_found", message="找不到資源"), 404
        return render_template("error.html", code=404, message="找不到頁面"), 404

    @app.errorhandler(500)
    def server_error(_err):
        if request.path.startswith("/api/"):
            return jsonify(error="server_error", message="伺服器錯誤"), 500
        return render_template("error.html", code=500, message="伺服器發生錯誤"), 500

    @app.context_processor
    def inject_globals():
        return {"katex_base": app.config["KATEX_CDN"] % {"version": app.config["KATEX_VERSION"]}}

    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
