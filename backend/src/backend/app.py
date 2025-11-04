"""Flask application factory with SocketIO support."""

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from .config import Config

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*")


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize configuration
    config_class.init_app(app)
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": config_class.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Content-Disposition"],
            "supports_credentials": True
        }
    })
    
    # Initialize SocketIO with the app
    socketio.init_app(app, 
                     cors_allowed_origins=config_class.CORS_ORIGINS,
                     async_mode='threading',
                     logger=config_class.DEBUG,
                     engineio_logger=config_class.DEBUG)
    
    # Initialize database
    from .db import init_db
    init_db(app)
    
    # Register blueprints
    from .api import auth_bp, documents_bp, conversations_bp, settings_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(conversations_bp, url_prefix='/api/conversations')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    
    # Register WebSocket events
    from .api import websocket
    
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return {'status': 'ok'}, 200
    
    return app


def run_app():
    """Run the application with SocketIO."""
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5001, debug=app.config['DEBUG'])


if __name__ == '__main__':
    run_app()

