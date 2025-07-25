from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-default-secret-key')

# ======================
# PostgreSQL Configuration
# ======================
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable not set")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ======================
# Models
# ======================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(300), nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)

# ======================
# Routes
# ======================

@app.route('/')
def home():
    return render_template('index.html', username=session.get('username'))

@app.route('/about')
def about():
    return render_template('about.html', username=session.get('username'))

@app.route('/gallery')
def gallery():
    return render_template('gallery.html', username=session.get('username'))

@app.route('/quotes', methods=['GET', 'POST'])
def quotes():
    if request.method == 'POST':
        author = request.form['author']
        content = request.form['quote']
        new_quote = Quote(author=author, content=content)
        db.session.add(new_quote)
        db.session.commit()
        return redirect(url_for('quotes'))

    quotes = Quote.query.all()
    return render_template('quotes.html', quotes=quotes, username=session.get('username'))

@app.route('/events', methods=['GET', 'POST'])
def events():
    if request.method == 'POST':
        title = request.form['title']
        details = request.form['details']
        new_event = Event(title=title, details=details)
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('events'))

    events = Event.query.order_by(Event.id.desc()).all()
    return render_template('events.html', events=events, username=session.get('username'))

# ========== Auth ==========

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists"
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            return "Invalid credentials"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# ========== Chat ==========

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form['content']
        username = session['username']
        new_msg = Message(username=username, content=content)
        db.session.add(new_msg)
        db.session.commit()
        return redirect(url_for('chat'))

    messages = Message.query.order_by(Message.id.asc()).all()
    return render_template('chat.html', messages=messages, username=session['username'])

@app.route('/get_messages')
def get_messages():
    messages = Message.query.order_by(Message.id.asc()).all()
    return jsonify([
        {"username": msg.username, "content": msg.content}
        for msg in messages
    ])

# ======================
# Run the app
# ======================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    with app.app_context():
        # Drop only the 'quote' table if it exists
        try:
            Quote.__table__.drop(db.engine)
            print("✅ Dropped old 'quote' table.")
        except Exception as e:
            print(f"⚠️ Could not drop 'quote' table: {e}")

        # Recreate all tables
        db.create_all()
        print("✅ All tables created successfully.")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
