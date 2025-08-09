import os
from flask import Flask, send_from_directory
from flask_cors import CORS

# Import routes (case-sensitive on Linux)
from Routes.api import api_bp

# Serve static from `Static/`
app = Flask(__name__, static_folder='Static', static_url_path='')
 
# Enable CORS for API (useful when frontend is on Netlify)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')

# Serve static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Ensure the app listens on all interfaces (0.0.0.0) for external access
    app.run(host='0.0.0.0', port=5000, debug=True)
