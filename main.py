import os
from flask import Flask, send_from_directory
from typing import cast
from flask_cors import CORS

# Import routes (case-sensitive on Linux)
try:
    from Routes.api import api_bp  # type: ignore
except ModuleNotFoundError:
    # Fallback only if the package name casing differs
    from routes.api import api_bp  # type: ignore

# Serve static from `Static/`
app = Flask(__name__, static_folder='Static', static_url_path='')
# Secret key for session cookies (set SECRET_KEY in env for production)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
 
# Enable CORS for API (useful when frontend is on Netlify)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')

# Serve static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_dir = cast(str, app.static_folder or 'Static')
    if path != "" and os.path.exists(os.path.join(static_dir, path)):
        return send_from_directory(static_dir, path)
    else:
        return send_from_directory(static_dir, 'index.html')

if __name__ == '__main__':
    # Ensure the app listens on all interfaces (0.0.0.0) for external access
    app.run(host='0.0.0.0', port=5000, debug=True)
