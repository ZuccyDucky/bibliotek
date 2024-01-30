from flask import Flask, render_template, request, redirect, url_for
from isbnlib import canonical, meta

app = Flask(__name__)

# In-memory storage for books and patrons
books = []
patrons = []
next_patron_id = 1  # Initialize the unique identifier for patrons

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

@app.route('/add_patron', methods=['POST'])
def add_patron():
    name = request.form['name']

    new_patron = Patron(name=name)
    patrons.append(new_patron)

    return redirect(url_for('index'))

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
