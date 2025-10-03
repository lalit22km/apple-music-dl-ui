from flask import Flask

app = Flask(__name__)

from app import routes  # import your routes after app is created
