import os
import sys
from flask import Flask, send_from_directory

# Fix import path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import routes
from routes.api import api_bp

app = Flask(__name__)

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
