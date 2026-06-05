from flask import Flask, render_template, request, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from model import predict_sentiment, analyze_sentiment_from_file, get_sentiment_counts, generate_wordcloud_base64
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timezone
from flask import send_from_directory
from urllib.parse import urlparse

# Konfigurasi folder upload
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'gantidenganyangaman' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class AnalysisHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    result_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Pastikan folder upload ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

with app.app_context():
    db.create_all()

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username sudah digunakan.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Akun berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('home')
            return redirect(next_page)
        else:
            flash('Login gagal. Periksa username dan password Anda.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/history')
@login_required
def history():
    analyses = AnalysisHistory.query.filter_by(user_id=current_user.id).order_by(AnalysisHistory.created_at.desc()).all()
    return render_template('history.html', analyses=analyses)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['RESULTS_FOLDER'], filename, as_attachment=True)

@app.route('/')
def home():
    """Merender halaman home."""
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    """
    Merender halaman dashboard dengan data visualisasi IKN dan Whoosh.
    """
    # Data Hardcoded sesuai permintaan
    dashboard_data = {
        'ikn': {
            'title': 'Sentimen Masyarakat terhadap IKN',
            'counts': {'Positif': 633, 'Netral': 387, 'Negatif': 452},
            'image': 'ikn.png' # Pastikan file ini ada di static/images/
        },
        'whoosh': {
            'title': 'Sentimen Masyarakat terhadap Whoosh',
            'counts': {'Positif': 1122, 'Netral': 4270, 'Negatif': 2108},
            'image': 'whoosh.png' # Pastikan file ini ada di static/images/
        }
    }
    
    return render_template('dashboard.html', dashboard_data=dashboard_data)

@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    """
    Merender halaman analisis. Menangani analisis teks tunggal DAN upload file.
    """
    prediction_result = None
    input_text = "" 
    results_table = None
    wordcloud = None 
    sentiment_counts = None 

    if request.method == 'POST':
        if 'text_input' in request.form:
            input_text = request.form.get('text_input', '')
            if input_text:
                prediction_result = predict_sentiment(input_text)
        
        elif 'file' in request.files:
            file = request.files['file']
            text_column = request.form.get('text_column')

            if file.filename == '':
                flash('Tidak ada file yang dipilih', 'danger')
                return redirect(url_for('analysis'))
            
            if not text_column:
                flash('Nama kolom teks tidak boleh kosong', 'danger')
                return redirect(url_for('analysis'))

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                df, error = analyze_sentiment_from_file(file_path, text_column)

                if error:
                    flash(error, 'danger')
                    os.remove(file_path) 
                    return redirect(url_for('analysis'))

                sentiment_counts = get_sentiment_counts(df)
                wordcloud = generate_wordcloud_base64(df, text_column)
                results_table = df.to_html(classes='table table-striped table-hover', index=False, border=0)

                # Simpan file hasil analisis
                result_filename = f"analisis_{uuid.uuid4().hex}.csv"
                result_filepath = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
                df.to_csv(result_filepath, index=False)

                # Simpan riwayat jika user login
                if current_user.is_authenticated:
                    new_history = AnalysisHistory(
                        user_id=current_user.id,
                        original_filename=file.filename,
                        result_filename=result_filename
                    )
                    db.session.add(new_history)
                    db.session.commit()

                os.remove(file_path)

                return render_template('analysis.html',
                                       prediction=prediction_result,
                                       text=input_text,
                                       sentiment_counts=sentiment_counts,
                                       results_table=results_table,
                                       wordcloud=wordcloud,
                                       result_filename=result_filename)
            else:
                flash('Format file tidak diizinkan. Gunakan .csv atau .xlsx', 'danger')
                return redirect(url_for('analysis'))
            
    return render_template('analysis.html', 
                           prediction=prediction_result, 
                           text=input_text,
                           sentiment_counts=sentiment_counts, 
                           results_table=results_table,
                           wordcloud=wordcloud)

@app.route('/about')
def about():
    """Merender halaman about."""
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)