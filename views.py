from flask import render_template, request, session, g, redirect, url_for
from app import app
import flask.ext.login as flask_login
import flask
import sqlite3
import hashlib
import mediabase
from flask import g
import send_email

DATABASE = 'main.db'

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

def get_db():
	"""Return database object"""
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = sqlite3.connect(DATABASE)
	return db

@app.teardown_appcontext
def close_connection(exception):
	"""Close database connection"""
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()

def query_db(query, args=(), one=False):
	"""Perform database query and return result"""
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv
		
def insert_db(query):
	conn = get_db()
	cur = conn.cursor()
	cur.execute(query)
	conn.commit()

class User(flask_login.UserMixin):
	email = ""
	mb_username = ""
	mb_password = ""

@login_manager.user_loader
def user_loader(username):
	if not query_db('select * from users where username=\'%s\'' % username, one=True):
		return

	user = User()
	user.id = username
	
	return user


@login_manager.request_loader
def request_loader(request):
	username = request.form.get('username')
	
	if not query_db('select * from users where username=\'%s\'' % username, one=True):
		return

	user = User()
	user.id = username

	password = query_db('select password from users where username=\'%s\'' % username, one=True)[0]
	user.is_authenticated = True

	return user

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return redirect(url_for('index')) 
	
	if 'username' in flask.request.form:
		username = flask.request.form['username']
		try:
			password = query_db('select password from users where username=\'%s\'' % username, one=True)[0]
		except:
			
			return redirect(url_for('login_error')) 
	if 'password' in flask.request.form and flask.request.form['password'] == password:
		user = User()
		user.id = username
		flask_login.login_user(user)
		return redirect(url_for('index')) 
	else:
		return redirect(url_for('login_error')) 

@app.route('/login_error')
def login_error():
	options = {}
	options['error'] = "Login error. Check your login/password."
	return render_template('login_error.html', **options)
	
@app.route('/logout')
def logout():
	flask_login.logout_user()
	return redirect(url_for('index')) 

@app.route('/')
def index():
	#return redirect(url_for('scrape')) 
	return render_template('index.html')

@app.route('/help')
@flask_login.login_required
def help():
	return render_template('help.html')

@app.route('/scrape', methods=['GET', 'POST'])
@flask_login.login_required
def scrape():
	options = {}
					
	if flask.request.method == 'POST':
		artist = flask.request.form['artist']
		song = flask.request.form['song']
		elements = [x for x in flask.request.form if flask.request.form[x] == 'on']
		threshold = flask.request.form['threshold']
		try:
			threshold = int(threshold)
		except:
			threshold = 1
		daysnum = flask.request.form['daysnum']
		
		if not artist or not song:
			options["error"] = "Specify search query"
			return render_template('scrape.html', **options)
		
		if not elements:
			options["error"] = "Select charts to scrape"
			return render_template('scrape.html', **options)
		
		insert_db('INSERT OR IGNORE INTO artist_select_options (option) VALUES ("%s")' % artist)
		insert_db('INSERT OR IGNORE INTO song_select_options (option) VALUES ("%s")' % song)
							
		mdb_data = mediabase.scrape(elements, daysnum, threshold)
		search_results = mediabase.get_search_results(mdb_data, artist, song)
		results = mediabase.process_search_result(search_results, threshold)
		email_data = mediabase.make_email_body(results)
		session["email_content"] = email_data
		
		options["results"] = results
		options["email"] = email_data
	
	try:
		options["artist_select_options"] = [x[0] for x in query_db('select * from artist_select_options')]
		options["song_select_options"] = [x[0] for x in query_db('select * from song_select_options')]
		options["email_select_options"] = [x[0] for x in query_db('select * from email_select_options')]
	except:
		pass
	
	return render_template('scrape.html', **options)

@app.route('/mail', methods=['POST'])
@flask_login.login_required
def mail():
	options = {}
	if 'email_content' in session:
		content = session["email_content"]
	print content
	if content:
		print content
		email = flask.request.form['mail']
		if not send_email.mail(content, email):
			options["error"] = "Failed to send message"
		else:
			options["success"] = "Message sent successfully"

		insert_db('INSERT OR IGNORE INTO email_select_options (option) VALUES ("%s")' % email)
	try:
		options["artist_select_options"] = [x[0] for x in query_db('select * from artist_select_options')]
		options["song_select_options"] = [x[0] for x in query_db('select * from song_select_options')]
		options["email_select_options"] = [x[0] for x in query_db('select * from email_select_options')]
	except:
		pass
		
	return render_template('scrape.html', **options)