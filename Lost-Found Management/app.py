from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request, session
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
import random
import os
from datetime import datetime, timezone, timedelta
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer as Serializer, SignatureExpired
from flask_mail import Mail, Message
from models import db, User, PasswordResetToken, Item, Category, Notification, ItemStatusEnum
app = Flask(__name__)

app.config['SECRET_KEY'] = 'd6b5f6a4d1c1e3c9b7d9d2f1e8b9c0a4e5d6f7a8b9c0d1e2f3a4b5c6d7e8f9g0h'
import os
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'lost_found.db')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = '_____@gmail.com'
app.config['MAIL_PASSWORD'] = 'passeward'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db.init_app(app)
mail = Mail(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def send_otp_reg(email, otp):
    msg = Message('Email Confirmation OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = f'''
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #004085; text-align: centre;">LOST-FOUND Management Team</h2>
        <p>Welcome!</p>
        <p>Thank you for signing up! Please confirm your college email ID.</p>
        <p style="font-size: 18px; color: #007bff;"><strong>Your OTP code is: {otp}</strong></p>
        <p style="color: #6c757d;">If you did not request this, please ignore this email.</p>
        <hr>
        <p style="font-size: 12px; color: #6c757d;">This is an automated message, please do not reply.</p>
    </div>
    '''
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        flash('Failed to send OTP. Please try again later.', category='danger')

def send_otp_forget_pass(email, otp):
    msg = Message('Password Reset OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = f'''
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #004085;  text-align: centre;">LOST-FOUND Management Team</h2>
        <p>You have requested a password reset.</p>
        <p style="font-size: 18px; color: #007bff;"><strong>Your OTP code is: {otp}</strong></p>
        <p style="color: #6c757d;">If you did not request this, please secure your account immediately.</p>
        <hr>
        <p style="font-size: 12px; color: #6c757d;">This is an automated message, please do not reply.</p>
    </div>
    '''
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        flash('Failed to send OTP. Please try again later.', category='danger')


def generate_otp():
    return f"{random.randint(100000, 999999)}"

EXPIRATION_TIME = 600

def generate_token(data, expiration=EXPIRATION_TIME):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps(data).decode('utf-8')

def verify_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None
    return data


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        roll_number = request.form.get('roll_number')
        batch = request.form.get('batch')
        course = request.form.get('course')
        branch = request.form.get('branch')

        if not email.endswith('.edu'):
            flash('Email must end with .edu domain.', category='danger')
            return redirect(url_for('register'))

        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(
                char.isalpha() for char in password):
            flash('Password must be at least 8 characters long and contain both letters and digits.', category='danger')
            return redirect(url_for('register'))

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already registered.', category='danger')
            return redirect(url_for('register'))

        otp = generate_otp()  # Ensure this function is defined to generate an OTP
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        session['temp_user'] = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': hashed_password,
            'roll_number': roll_number,
            'batch': batch,
            'course': course,
            'branch': branch,
            'otp': otp,
            'otp_generated_at': datetime.utcnow().replace(tzinfo=None)
        }

        send_otp_reg(email, otp)  # Ensure this function is defined to send an OTP
        flash('An OTP has been sent to your email. Please verify to complete registration.', category='info')
        return redirect(url_for('verify_registration'))

    return render_template('register.html')


# Route for verifying registration
@app.route('/verify_registration', methods=['GET', 'POST'])
def verify_registration():
    if request.method == 'POST':
        otp = request.form.get('otp')
        temp_user = session.get('temp_user')

        if temp_user:
            # Convert both to timezone-aware datetimes for comparison
            otp_generated_at = temp_user.get('otp_generated_at').astimezone(timezone.utc)
            otp_age = datetime.now(timezone.utc) - otp_generated_at

            if otp_age.total_seconds() > 600:  # 10 minutes in seconds
                flash('OTP has expired. Please request a new one.', category='danger')
                return redirect(url_for('register'))

            if temp_user['otp'] == otp:
                new_user = User(
                    email=temp_user['email'],
                    first_name=temp_user['first_name'],
                    last_name=temp_user['last_name'],
                    password=temp_user['password'],
                    roll_number=temp_user['roll_number'],
                    batch=temp_user['batch'],
                    course=temp_user['course'],
                    branch=temp_user['branch'],
                    is_verified=True
                )
                db.session.add(new_user)
                db.session.commit()
                session.pop('temp_user', None)
                flash('Your account has been created successfully!', category='success')
                return redirect(url_for('login'))
            else:
                flash('Invalid OTP. Please try again.', category='danger')

    return render_template('verify_registration.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            if user.is_verified:
                login_user(user)
                flash('Login successful!', category='success')
                return redirect(url_for('home_page'))
            else:
                flash('Please verify your email before logging in.', category='danger')
        else:
            flash('Login failed. Check your credentials.', category='danger')
    return render_template('login.html')


# Route for user logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', category='info')
    return redirect(url_for('login'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            otp = generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            reset_token = PasswordResetToken(user_id=user.id, otp=otp, expires_at=expires_at)
            db.session.add(reset_token)
            db.session.commit()
            send_otp_forget_pass(email, otp)
            session['reset_email'] = email  # Store email in session
            flash('An OTP has been sent to your email for password reset.', category='info')
            return redirect(url_for('verify_reset_password'))
        else:
            flash('Email not registered.', category='danger')

    return render_template('forgot_password.html')

# Route for verifying password reset
@app.route('/verify_reset_password', methods=['GET', 'POST'])
def verify_reset_password():
    email = session.get('reset_email')  # Retrieve email from session
    if not email:
        flash('No email found in session. Please try again.', category='danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        otp = request.form.get('otp')
        user = User.query.filter_by(email=email).first()
        if user:
            reset_token = PasswordResetToken.query.filter_by(user_id=user.id, otp=otp).first()
            if reset_token and reset_token.expires_at > datetime.utcnow():
                session['reset_user'] = user.id
                db.session.delete(reset_token)
                db.session.commit()
                flash('OTP verified. You can now reset your password.', category='success')
                return redirect(url_for('reset_password'))
            else:
                flash('Invalid or expired OTP. Please try again.', category='danger')
        else:
            flash('Email not registered.', category='danger')

    return render_template('verify_reset_password.html', email=email)

# Route for resetting password
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        password = request.form.get('password')
        user_id = session.get('reset_user')

        # Check if the password is None
        if password is None or len(password) < 8 or not any(char.isdigit() for char in password) or not any(
                char.isalpha() for char in password):
            flash('Password must be at least 8 characters long and contain both letters and digits.', category='danger')
            return redirect(url_for('reset_password'))

        if user_id:
            user = User.query.get(user_id)
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')
            db.session.commit()
            session.pop('reset_user', None)
            flash('Your password has been reset successfully!', category='success')
            return redirect(url_for('login'))
        else:
            flash('No user session found. Please try again.', category='danger')

    return render_template('reset_password.html')



@app.route('/')
def home_page():
    # Get search and category parameters from the request
    search_term = request.args.get('search', '')
    category_id = request.args.get('category', '')

    # Build the query with filters
    query = Item.query

    if search_term:
        query = query.filter(
            (Item.name.ilike(f'%{search_term}%')) |
            (Item.description.ilike(f'%{search_term}%'))
        )

    if category_id:
        query = query.filter(Item.category_id == category_id)

    items = query.all()
    categories = Category.query.all()

    return render_template('home.html', items=items, categories=categories)


@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category_id = request.form.get('category')
        status = request.form.get('status')
        date = request.form.get('date')
        location = request.form.get('location')
        image = request.files.get('image')

        # Handle image upload if any
        image_filename = 'default.jpg'
        if image and image.filename:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)

        new_item = Item(
            name=name,
            description=description,
            category_id=category_id,
            status=status,
            date=date,
            image_file=image_filename,
            user_id=current_user.id
        )
        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for('home_page'))

    categories = Category.query.all()
    return render_template('add_item.html', categories=categories)


@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)

    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.category_id = request.form['category']
        item.status = request.form['status']
        item.date = request.form['date']
        image_file = request.files['image_file']

        if image_file:
            image_filename = secure_filename(image_file.filename)
            image_file.save(f'static/images/{image_filename}')
            item.image_file = image_filename

        db.session.commit()
        flash('Item updated successfully.', 'success')
        return redirect(url_for('home_page'))

    categories = Category.query.all()
    return render_template('edit_item.html', item=item, categories=categories)


@app.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully.', 'success')
    return redirect(url_for('home_page'))

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item_detail.html', item=item)


@app.route('/notifications')
@login_required
def view_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).all()
    return render_template('notifications.html', notifications=notifications)


@app.route('/profile')
@login_required
def view_profile():
    courses = {
        'BTECH': 'Btech',
        'BARCH': 'Barch',
        'MTECH': 'Mtech',
        'MSC': 'Msc',
        'PHD': 'PHD'
    }
    branches = {
        'CSE': 'CSE',
        'ECE': 'ECE',
        'EEE': 'EEE',
        'ICE': 'ICE',
        'Chem': 'Chem',
        'Civil': 'Civil',
        'MECH': 'MECH',
        'Prod': 'Prod',
        'Other': 'Other'
    }
    return render_template('profile.html', courses=courses, branches=branches)



@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.roll_number = request.form['roll_number']
        user.batch = request.form['batch']
        user.course = request.form['course']
        user.branch = request.form['branch']

        # Handle image upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/images', filename)
                file.save(file_path)
                user.profile_pic = filename

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('view_profile'))

    return render_template('edit_profile.html')

def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


if __name__ == '__main__':
    app.run(debug=True)
