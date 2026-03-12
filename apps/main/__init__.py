from flask import Blueprint

bp = Blueprint('main', __name__)

from apps.main import routes
