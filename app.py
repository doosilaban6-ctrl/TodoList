from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "ini_rahasia_banget"

# Config SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todolist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Model Task
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Buat decorator login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Silakan login dulu ya!", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Username sudah dipakai!", "danger")
            else:
                new_user = User(username=username, password=password)
                db.session.add(new_user)
                db.session.commit()
                flash("Registrasi berhasil! Silakan login.", "success")
                return redirect(url_for('login'))
        else:
            flash("Username dan password harus diisi!", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login berhasil!", "success")
            return redirect(url_for('index'))
        else:
            flash("Username atau password salah!", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Kamu sudah logout.", "info")
    return redirect(url_for('login'))

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_id = session['user_id']
    if request.method == "POST":
        task_text = request.form.get("task")
        if task_text:
            new_task = Task(task=task_text, user_id=user_id)
            db.session.add(new_task)
            db.session.commit()
        return redirect(url_for("index"))
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
    return render_template("index.html", tasks=tasks)

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        flash("Kamu tidak boleh mengedit tugas ini.", "danger")
        return redirect(url_for('index'))

    if request.method == "POST":
        new_task = request.form.get("task")
        if new_task:
            task.task = new_task
            db.session.commit()
            return redirect(url_for('index'))
    return render_template("edit.html", task=task)

@app.route("/delete/<int:task_id>")
@login_required
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        flash("Kamu tidak boleh menghapus tugas ini.", "danger")
        return redirect(url_for('index'))

    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # buat database dan tabel jika belum ada
    app.run(debug=True,port=5001)

