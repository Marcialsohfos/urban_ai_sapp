from app import app
from flask import Flask
import os

# Vercel nécessite une variable application
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    application.run(host="0.0.0.0", port=port)