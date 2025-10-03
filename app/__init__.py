from flask import Flask

app = Flask(__name__)

# Import routes after app is created
from . import routes
