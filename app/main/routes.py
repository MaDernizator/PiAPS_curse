from app.api.address_controller import address_bp
from app.api.resident_controller import resident_bp
from app.api.invitation_controller import invitation_bp
from app.api.notification_controller import notification_bp
from app.api.log_controller import log_bp
from app.auth.auth_controller import auth_bp
from app.web.views import web_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(address_bp, url_prefix="/api/addresses")
    app.register_blueprint(resident_bp, url_prefix="/api/residents")
    app.register_blueprint(invitation_bp, url_prefix="/api/invitations")
    app.register_blueprint(notification_bp, url_prefix="/api/notifications")
    app.register_blueprint(log_bp, url_prefix="/api/logs")
    app.register_blueprint(web_bp)
