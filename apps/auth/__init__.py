from flask import Blueprint

bp = Blueprint('auth', __name__)

from apps.auth import routes
