from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from datetime import datetime, timedelta
import qrcode
import io
import logging
import os
from dotenv import load_dotenv
from functools import wraps
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///idpay.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    pin = db.Column(db.String(4), nullable=False)
    barcode = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Float, default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50), nullable=False)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)

class Ticket(db.Model):
    ticket_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issue_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Open')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def authorized(user_id):
    return str(user_id) == str(session.get('user_id'))

# Initialize DB
with app.app_context():
    db.create_all()

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        barcode = request.form['barcode']
        pin = request.form.get('pin', '')

        user = User.query.filter_by(email=email, barcode=barcode).first()
        if user and user.password == password and user.pin == pin:
            session['user_id'] = user.id
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            name=request.form['name'],
            email=request.form['email'],
            mobile=request.form['mobile'],
            password=request.form['password'],
            pin=request.form['pin'],
            barcode=request.form['barcode']
        )
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/home')
@login_required
def home():
    user_id = session['user_id']
    user = User.query.get(user_id)
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date_time.desc()).limit(10).all()
    return render_template('home.html', name=user.name, balance=user.balance, transactions=transactions, user_id=user_id)

@app.route('/get_balance', methods=['POST'])
def get_balance():
    user_id = request.json['user_id']
    if not authorized(user_id):
        return jsonify({'status': 'error'}), 401
    user = User.query.get(user_id)
    return jsonify({'status': 'success', 'balance': user.balance})

@app.route('/get_latest_transactions', methods=['POST'])
def get_latest_transactions():
    user_id = request.json['user_id']
    if not authorized(user_id):
        return jsonify({'status': 'error'}), 401
    txns = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date_time.desc()).limit(10).all()
    return jsonify({'status': 'success', 'transactions': [{'type': t.type, 'date_time': t.date_time.strftime('%d %b %Y, %H:%M'), 'amount': t.amount, 'method': t.method} for t in txns]})

@app.route('/get_dashboard_data', methods=['POST'])
def get_dashboard_data():
    user_id = request.json['user_id']
    if not authorized(user_id):
        return jsonify({'status': 'error'}), 401
    user = User.query.get(user_id)
    txns = Transaction.query.filter_by(user_id=user_id).all()
    recent = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date_time.desc()).limit(10).all()
    recent_list = [{'type': r.type, 'date_time': r.date_time.strftime('%d %b %Y, %H:%M'), 'amount': r.amount, 'method': r.method, 'id': r.id} for r in recent]
    total_credited = sum(t.amount for t in txns if t.type == 'Top Up')
    tx_count = len(txns)
    points = tx_count * 10
    return jsonify({
        'status': 'success',
        'balance': user.balance,
        'total_credited': total_credited,
        'transaction_count': tx_count,
        'reward_points': points,
        'recent_transactions': recent_list,
        'all_transactions': [{'type': t.type, 'date_time': t.date_time.strftime('%d %b %Y, %H:%M'), 'amount': t.amount, 'method': t.method, 'id': t.id} for t in txns]
    })

@app.route('/top_up_wallet', methods=['POST'])
def top_up_wallet():
    data = request.json
    user_id = data['user_id']
    if not authorized(user_id):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    amount = float(data['amount'])
    method = data['method']
    user = User.query.get(user_id)
    user.balance += amount
    txn = Transaction(user_id=user_id, type='Top Up', amount=amount, method=method)
    db.session.add(txn)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/reset_pin', methods=['POST'])
def reset_pin():
    data = request.json
    user_id = data['user_id']
    if not authorized(user_id):
        return jsonify({'status': 'error'}), 401
    user = User.query.get(user_id)
    if user.pin == data['current_pin']:
        user.pin = data['new_pin']
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Invalid current PIN'})

@app.route('/get_ticket_history', methods=['POST'])
def get_ticket_history():
    user_id = request.json['user_id']
    if not authorized(user_id):
        return jsonify({'status': 'error'}), 401
    tickets = Ticket.query.filter_by(user_id=user_id).all()
    return jsonify({'status': 'success', 'tickets': [{'ticket_id': t.ticket_id, 'issue_type': t.issue_type, 'description': t.description, 'date': t.date.strftime('%d %b %Y'), 'status': t.status} for t in tickets]})

@app.route('/raise_ticket', methods=['POST'])
def raise_ticket():
    data = request.json
    user_id = data['user_id']
    if not authorized(user_id):
        return jsonify({'status': 'error'}), 401
    ticket = Ticket(user_id=user_id, issue_type=data['issue_type'], description=data['description'])
    db.session.add(ticket)
    db.session.commit()
    return jsonify({'status': 'success', 'ticket_id': ticket.ticket_id})

@app.route('/get_rewards', methods=['POST'])
def get_rewards():
    user_id = request.json['user_id']
    if not authorized(user_id):
        return jsonify({'status': 'error'}), 401
    tx_count = Transaction.query.filter_by(user_id=user_id).count()
    return jsonify({'status': 'success', 'points': tx_count * 10, 'transaction_count': tx_count})

@app.route('/redeem_voucher', methods=['POST'])
def redeem_voucher():
    user_id = request.json['user_id']
    if not authorized(user_id):
        return jsonify({'status': 'error'}), 401
    return jsonify({'status': 'success', 'voucher_code': secrets.token_hex(5).upper()})

@app.route('/chat_support', methods=['POST'])
def chat_support():
    user_id = request.json['user_id']
    message = request.json['message'].lower()
    if not authorized(user_id):
        return jsonify({'status': 'error'}), 401
    responses = {
        'hi': 'Hello! How can I help?',
        'balance': 'Your current balance is ₹0.00 (check dashboard)',
        'help': 'Try: balance, transactions, tickets, rewards',
        'transactions': 'View transactions in sidebar.',
        'tickets': 'Raise tickets under Support.',
        'rewards': 'Earn 10 pts per transaction!'
    }
    user = User.query.get(user_id)
    response = responses[message] or "Try 'help' for commands."
    return jsonify({'status': 'success', 'response': response})

@app.route('/request_callback', methods=['POST'])
def request_callback():
    return jsonify({'status': 'success'})

@app.route('/send_support_email', methods=['POST'])
def send_support_email():
    return jsonify({'status': 'success'})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, port=5023)
d e f   p r e d i c t ( ) :   p a s s  
 a p i _ e n d p o i n t   =   ' / p r e d i c t '  
 #   D a s h b o a r d   r o u t e  
 UPI/QR topup routes
