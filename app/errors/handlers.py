from flask import jsonify, render_template, request

def register_error_handlers(app):
    def wants_json_response():
        return request.path.startswith(
            "/api") or request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html

    @app.errorhandler(404)
    def not_found_error(error):
        if wants_json_response():
            return jsonify({"error": "Not found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        if wants_json_response():
            return jsonify({"error": "Forbidden"}), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def internal_error(error):
        if wants_json_response():
            return jsonify({"error": "Internal server error"}), 500
        return render_template("errors/500.html"), 500
