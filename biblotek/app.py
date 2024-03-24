from flask import Flask, render_template, request, redirect, url_for
from isbnlib import canonical, meta
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired
import mysql.connector
import os

class NameForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    surname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired()])
    access_level = IntegerField('Access level', validators=[DataRequired()])
    submit = SubmitField('Submit')

app = Flask(__name__)

# In-memory storage for books and patrons
books = []
patrons = []
next_patron_id = 1  # Initialize the unique identifier for patrons

app.config['SECRET_KEY'] = os.urandom(32)
app.config['MYSQL_HOST'] = 'xi.hostup.se'
app.config['MYSQL_USER'] = 'syhod_biblioteksskaparna'
app.config['MYSQL_PASSWORD'] = 'Franklins2024'
app.config['MYSQL_DB'] = 'syhod_library'
app.config['CHARSET']='utf8mb4'

class Book:
    def __init__(self, title, author, isbn, year, publisher, checked_out=False):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.year = year
        self.publisher = publisher
        self.checked_out = checked_out

class Patron:
    def __init__(self, name):
        global next_patron_id
        self.id = next_patron_id
        next_patron_id += 1
        self.name = name

@app.route('/')
def index():
    return render_template('index.html', books=books, patrons=patrons)

@app.route('/add_book', methods=['POST'])
def add_book():

    isbn = canonical(request.form['isbn'])
    data = meta(isbn, service='default')
    author = data['Authors']
    title = data['Title']
    year = data['Year']
    publisher = data['Publisher']

    new_book = Book(title=title, author=author, isbn=isbn, year=year, publisher=publisher)
    books.append(new_book)

    return redirect(url_for('index'))

@app.route('/add_patron', methods=['GET', 'POST'])
def addpatron():
    # Connect to MySQL database
    try:
        conn  = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            charset = app.config['CHARSET']
            )
        cursor = conn.cursor()
        form = NameForm()
        if form.validate_on_submit():
            first_name = form.first_name.data
            surname = form.surname.data
            email = form.email.data
            access_level = form.access_level.data
            insert_query = "INSERT INTO Patron (first_name, surname, email, accesslevel) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (first_name, surname, email, access_level))
            conn.commit()
            flash('Name successfully added to the database!', 'success')
        return render_template('addpatron.html', form=form)

    except mysql.connector.Error as err:    
        return f"Error: {err}"

    finally:
        # Close connection
        cursor.close()
        conn.close()

@app.route('/readpatrons')
def readpatrons():
    # Connect to MySQL database
    try:
        conn  = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            charset = app.config['CHARSET']
            )
        #conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()

        # Example query
        cursor.execute("SELECT * FROM `Patron`")
        data = cursor.fetchall()
        return render_template('readpatrons.html', data=data)        

    except mysql.connector.Error as err:
        return f"Error: {err}"

    finally:
        # Close connection
        cursor.close()
        conn.close()

@app.route('/check_out', methods=['POST'])
def check_out():
    patron_id = int(request.form['patron_id'])
    isbn = request.form['isbn']

    for book in books:
        if book.isbn == isbn and not book.checked_out:
            book.checked_out = True
            return redirect(url_for('index'))

    return "Book not available for checkout or invalid ISBN."

@app.route('/return_book', methods=['POST'])
def return_book():
    patron_id = int(request.form['patron_id'])
    isbn = request.form['isbn']

    for book in books:
        if book.isbn == isbn and book.checked_out:
            book.checked_out = False
            return redirect(url_for('index'))

    return "Book not checked out or invalid ISBN."

if __name__ == '__main__':
    app.run(debug=True)
