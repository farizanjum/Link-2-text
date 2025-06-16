from main import app
import vercel_wsgi

def handler(event, context):
    return vercel_wsgi.handle_wsgi(app, event, context)
