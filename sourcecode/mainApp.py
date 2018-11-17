import sqlite3
import bcrypt
import os
import os.path
import random
from array import *
from flask import Flask, render_template, redirect, request, session, url_for

app = Flask(__name__)

userData = 'data/users.db'
urlData = 'data/urls.db'

app.secret_key = 'asdfghjkkl;;' 


def checkLogged():
	try:
		if session['logged'] == True:
			return True
		return False
	except:
		return False

@app.route('/')
def home():
	return render_template('home.html', logged=checkLogged())

@app.route('/', methods=['POST'])
def home_post():
	link = None
	conn = sqlite3.connect(urlData)
	cursor = conn.cursor()
	chars = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','0','1','2','3','4','5','6','7','8','9','$','_','-','!'] 
	while (link == None):
		temp = ""
		for x in range(6):
			temp += chars[random.randint(0,39)]		

		cursor.execute(""" SELECT compressed
				   FROM userURLs
				   WHERE compressed=?""",
			       (temp,))
		result = cursor.fetchone()
		if not result:
			link = temp

	original = request.form['rawURL']
	cursor.execute("INSERT INTO userURLs VALUES (?, ?, ?, ?)",(link, original, session['user'], 0))	
	conn.commit()

	return render_template('home.html', logged=checkLogged(), link=link) 

@app.route('/signup')
def signup():
	return render_template('signup.html', logged=checkLogged())

@app.route('/signup', methods=['POST'])
def signup_post():
	error = None
	username = request.form['username']
	password = request.form['password']
	password2 = request.form['password2']
	
	if password != password2:
		error = "Passwords did not match!"
		return render_template('signup.html', logged=checkLogged(), error=error)
	else:
		conn = sqlite3.connect(userData)
		cursor = conn.cursor()
		cursor.execute(""" SELECT username
				   FROM login
				   WHERE username=?
				   COLLATE NOCASE""",
			       (username,))
		result = cursor.fetchone()
		if result:
			error = "Account using input Username aready exists!"
			return render_template('signup.html', logged=checkLogged(), error=error)
		else:
			hash = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
			cursor.execute("INSERT INTO login VALUES (?, ?)", (username, hash))
			conn.commit()
			return redirect('login')

@app.route('/login')
def login():
	return render_template('login.html', logged=checkLogged())

@app.route('/login', methods=['POST'])
def login_post():
	error = None
	username = request.form['username']
	password = request.form['password']
	
	conn = sqlite3.connect(userData)
	cursor = conn.cursor()
	cursor.execute(""" SELECT username
			   FROM login
			   WHERE username=?""",
		       (username,))
	result = cursor.fetchone()
	if result:
		cursor.execute(""" SELECT password
				    FROM login
				    WHERE username=?""",
			        (username,))

		readPW = cursor.fetchone()[0].encode('utf8')
		
		if readPW == bcrypt.hashpw(password.encode('utf8'), readPW):
			session['user'] = username
			session['logged'] = True
			return redirect('/')
				
	error = "Invalid Login details!"
	return render_template('login.html', logged=checkLogged(), error=error)	


@app.route('/logout')
def logout():
	session['user'] = None
	session['logged'] = False
	return redirect('/')

@app.route('/mylinks')
def mylinks():
	if not session['logged']:
		return redirect('/login')
	else:
		conn = sqlite3.connect(urlData)
		cursor = conn.cursor()
		cursor.execute(""" SELECT * 
				   FROM userURLs
  				   """
			       )
		rows = cursor.fetchall()
		myURLs = []
		total = 0
		for row in rows:
			temp = []
			temp.append(row[0])
			temp.append(row[1])
			temp.append(row[3])
			myURLs.append(temp)
			total+=1
		if total == 0:
			return render_template('mylinks.html', logged=checkLogged())
		else:	
			return render_template('mylinks.html', logged=checkLogged(),myURLs=myURLs,total=total)

@app.route('/myaccount')
def myaccount():
	if not session['logged']:
		return redirect('/login')
	else:
		return render_template('myaccount.html', logged=checkLogged())

@app.route('/url/<url>')
def url(url):
	conn = sqlite3.connect(urlData)
	cursor = conn.cursor()
	cursor.execute(""" SELECT original
			   FROM userURLs
			   WHERE compressed=?
			   COLLATE NOCASE""",
		       (url,))

	result = cursor.fetchone()
	
	if result:
		cursor.execute(""" SELECT clicks
				   FROM userURLs
				   WHERE compressed=?
				   COLLATE NOCASE""",
			       (url,))
		clicks = cursor.fetchone()[0]
		clicks += 1
		cursor.execute(""" UPDATE userURLs
				   SET clicks=?
				   WHERE compressed=?
				   COLLATE NOCASE""",
                               (clicks,url,))
		conn.commit()
		return redirect(result[0])		
	else:
		return render_template('errorPage.html', logged=checkLogged())


@app.route('/del/<url>')
def delurl(url):
	logged = checkLogged()
	if logged:
		conn=sqlite3.connect(urlData)
		cursor = conn.cursor()
		cursor.execute(""" SELECT owner
				   FROM userURLs
				   WHERE compressed=?
				   COLLATE NOCASE""",
			       (url,))
		result = cursor.fetchone()

		if result:
			if result[0] == session['user']:
				cursor = conn.cursor()
				cursor.execute(""" DELETE FROM userURLs
                        	                   WHERE compressed=?
                        	                   COLLATE NOCASE""",
                        	               (url,))
				conn.commit()
	return redirect('/mylinks')

@app.route('/changepw')
def changepw():
	logged = checkLogged()
	if logged:
		return render_template('changepw.html', logged=checkLogged())
	else:
		return redirect('/login')

@app.route('/changepw', methods=['POST'])
def changepw_post():	
	error = None
	password = request.form['password']
	newPassword = request.form['newpassword']
	newPassword2 = request.form['newpassword2']

	if newPassword != newPassword2:
		error = "New Passwords did not match!"
		return render_template('changepw.html', logged=checkLogged(), error=error)
	else:
		conn = sqlite3.connect(userData)
		cursor = conn.cursor()
		cursor.execute(""" SELECT password
				   FROM login
				   WHERE username=?""",
			       (session['user'],))
			
		readPW = cursor.fetchone()[0].encode('utf8')

		if readPW == bcrypt.hashpw(password.encode('utf8'), readPW):
				cursor = conn.cursor()
				hash = bcrypt.hashpw(newPassword.encode('utf8'), bcrypt.gensalt())
				cursor.execute(""" UPDATE login
						   SET password=?
						   WHERE username=?""",
					       (hash, session['user'],))
				conn.commit()
				return redirect('/')
		else:
			error = "Incorrect current password!"
			return render_template('changepw.html', logged=checkLogged(), error=error)
		

@app.route('/delaccount')
def delaccount():
	logged = checkLogged()
	if logged:
		return render_template('delaccount.html', logged=checkLogged())
	else:
		return redirect('/login')

@app.route('/delaccount', methods=['POST'])
def delaccount_post():
	conn = sqlite3.connect(urlData)
	cursor = conn.cursor()
	cursor.execute(""" DELETE FROM userURLs
			   WHERE owner=?""",
		       (session['user'],))
	conn.commit()

	conn = sqlite3.connect(userData)
	cursor = conn.cursor()
	cursor.execute(""" DELETE FROM login
			   WHERE username=?""",
		       (session['user'],))
     	conn.commit()
	
	return redirect('/logout')

@app.errorhandler(404)
def noPage(e):
	return render_template('errorPage.html', logged=checkLogged()),404
