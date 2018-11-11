import sqlite3
import bcrypt
import os
import os.path
from functools import wraps
from flask import Flask, render_template, redirect, request, session, url_for

app = Flask(__name__)

userData = 'data/users.db'
urlData = 'data/urls.db'

app.secret_key = 'asdfghjkkl;;' 


def checkLogged():
	print session['logged']
	if session['logged'] == True:
		return True
	return False

@app.route('/')
def home():
	return render_template('home.html', logged=checkLogged())

@app.route('/signup')
def signup():
	return render_template('signup.html', logged=checkLogged())

@app.route('/signup', methods=['POST'])
def signup_post():
	error = None
	email = request.form['email']
	password = request.form['password']
	password2 = request.form['password2']
	
	if password != password2:
		error = "Passwords did not match!"
		return render_template('signup.html', logged=checkLogged(), error=error)
	else:
		conn = sqlite3.connect(userData)
		cursor = conn.cursor()
		cursor.execute(""" SELECT email
				   FROM login
				   WHERE email=?""",
			       (email,))
		result = cursor.fetchone()
		if result:
			error = "Account using input Email aready exists!"
			return render_template('signup.html', logged=checkLogged(), error=error)
		else:
			hash = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
			cursor.execute("INSERT INTO login VALUES (?, ?)", (email, hash))
			conn.commit()
			return redirect('login')

@app.route('/login')
def login():
	return render_template('login.html', logged=checkLogged())

@app.route('/login', methods=['POST'])
def login_post():
	error = None
	email = request.form['email']
	password = request.form['password']
	
	conn = sqlite3.connect(userData)
	cursor = conn.cursor()
	cursor.execute(""" SELECT email
			   FROM login
			   WHERE email=?""",
		       (email,))
	result = cursor.fetchone()
	if result:
		cursor.execute(""" SELECT password
				    FROM login
				    WHERE email=?""",
			        (email,))

		readPW = cursor.fetchone()[0].encode('utf8')
		
		if readPW == bcrypt.hashpw(password.encode('utf8'), readPW):
			session['user'] = email
			session['logged'] = True
			return redirect('/')			
		else:
			error = "Incorrect Password"
			return render_template('login.html', logged=checkLogged(), error=error) 
	else:
		error = "No account of EMAIL exists!"
		return render_template('login.html', logged=checkLogged(), error=error)	


@app.route('/logout')
def logout():
	session['user'] = None
	session['logged'] = False
	return redirect('/')

@app.route('/mylinks')
def mylinks():
	if not session['logged']:
		return redirect('/signup')
	else:
		return session['user']
