from flask import Flask
from flask import render_template
from flask import session
import flask.ext.login as flask_login
import datetime 

app = Flask(__name__)

app.config['DEBUG'] = True
app.secret_key = 'herebesecretkey'
app.before_request(lambda: setattr(session, 'permanent', True))  
app.permanent_session_lifetime = datetime.timedelta(days=160)  

