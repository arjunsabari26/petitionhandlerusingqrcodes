import os
import socket
import string
import random
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import qrcode
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secure_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///petition.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['QR_FOLDER'] = os.path.join('static', 'qrcodes')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default='user')
    petitions = db.relationship('Petition', backref='author', lazy=True)

class Petition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    petition_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    query_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='Submitted') 
    response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class QRCodeDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_type = db.Column(db.String(50), unique=True, nullable=False)
    file_path = db.Column(db.String(255), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def generate_petition_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@app.route('/')
def home():
    qrcodes = QRCodeDB.query.all()
    return render_template('home.html', qrcodes=qrcodes)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email address already exists. Please login.', 'danger')
            return redirect(url_for('signup'))
            
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        role = 'user'
        if email.endswith('@admin.com'):
            role = 'admin'
        user = User(name=name, email=email, password=hashed_pw, role=role)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            if user.role == 'admin':
                return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    login_user_role = current_user.role if current_user.is_authenticated else None
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    petitions = Petition.query.filter_by(email=current_user.email).order_by(Petition.created_at.desc()).all()
    unread_count = sum(1 for p in petitions if p.status != 'Submitted' and not p.is_read)
    return render_template('dashboard.html', petitions=petitions, unread_count=unread_count)

@app.route('/mark_read/<int:id>')
@login_required
def mark_read(id):
    petition = db.session.get(Petition, id)
    if petition and petition.email == current_user.email:
        petition.is_read = True
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    query_type_prefill = request.args.get('type', '')
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        query_type = request.form.get('query_type')
        description = request.form.get('description')
        
        file = request.files.get('file')
        file_path = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            file_path = unique_filename
            
        petition_id = generate_petition_id()
        user_id = current_user.id if current_user.is_authenticated else None
        
        petition = Petition(
            petition_id=petition_id,
            user_id=user_id,
            name=name,
            email=email,
            phone=phone,
            query_type=query_type,
            description=description,
            file_path=file_path
        )
        db.session.add(petition)
        db.session.commit()
        
        flash(f'Petition submitted successfully! Your tracking ID is {petition_id}', 'success')
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('track', petition_id=petition_id))
        
    return render_template('submit_petition.html', query_type_prefill=query_type_prefill)

@app.route('/track', methods=['GET', 'POST'])
def track():
    petition = None
    if request.method == 'POST':
        pid = request.form.get('petition_id')
        petition = Petition.query.filter_by(petition_id=pid).first()
        if not petition:
            flash('Petition not found with that ID.', 'danger')
    elif request.args.get('petition_id'):
        pid = request.args.get('petition_id')
        petition = Petition.query.filter_by(petition_id=pid).first()
    return render_template('status_tracker.html', petition=petition)

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access Denied: Admins Only.', 'danger')
        return redirect(url_for('dashboard'))
    
    petitions = Petition.query.order_by(Petition.created_at.desc()).all()
    qrcodes = QRCodeDB.query.all()
    return render_template('admin_dashboard.html', petitions=petitions, qrcodes=qrcodes)

@app.route('/admin/update/<int:id>', methods=['POST'])
@login_required
def admin_update(id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))
        
    petition = db.session.get(Petition, id)
    if petition:
        old_status = petition.status
        petition.status = request.form.get('status')
        petition.response = request.form.get('response')
        if old_status != petition.status or request.form.get('response'):
            petition.is_read = False # reset read status so user gets notified
        db.session.commit()
        flash('Petition updated successfully.', 'success')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/generate_qr', methods=['POST'])
@login_required
def generate_qr():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
        
    query_type = request.form.get('query_type')
    if query_type:
        exist = QRCodeDB.query.filter_by(query_type=query_type).first()
        if exist:
            flash(f'QR Code for {query_type} already exists!', 'warning')
            return redirect(url_for('admin_dashboard'))
            
        ip = get_local_ip()
        url = f"http://{ip}:5000/submit?type={query_type.replace(' ', '%20')}"
        
        img = qrcode.make(url)
        filename = f"{query_type.replace(' ', '_').lower()}_qr.png"
        filepath = os.path.join(app.config['QR_FOLDER'], filename)
        img.save(filepath)
        
        qr_record = QRCodeDB(query_type=query_type, file_path=filename)
        db.session.add(qr_record)
        db.session.commit()
        flash(f'QR Code generated for {query_type}. Pointing to: {url}', 'success')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/help')
def help():
    return render_template('help.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not QRCodeDB.query.first():
            types = ['Maintenance', 'IT Support', 'General Enquiry']
            ip = get_local_ip()
            for query_type in types:
                url = f"http://{ip}:5000/submit?type={query_type.replace(' ', '%20')}"
                img = qrcode.make(url)
                filename = f"{query_type.replace(' ', '_').lower()}_qr.png"
                filepath = os.path.join(app.config['QR_FOLDER'], filename)
                img.save(filepath)
                qr_record = QRCodeDB(query_type=query_type, file_path=filename)
                db.session.add(qr_record)
            db.session.commit()
            print("Seeded default QR codes.")
    app.run(host='0.0.0.0', port=5000, debug=True)
