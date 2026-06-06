from flask import Flask, render_template, request, url_for, flash, redirect, session, g, Response, send_file
from model import predict_sentiment, analyze_sentiment_from_file, get_sentiment_counts, generate_wordcloud_base64
import os
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import database
import functools

# Load environment variables dari .env
load_dotenv()

# Konfigurasi folder upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'gantidenganyangaman')

# Batasi ukuran unggahan berkas maksimal 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Konfigurasi keamanan Cookie Sesi
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Inisialisasi CSRF Protection
csrf = CSRFProtect(app)

# Inisialisasi Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Pastikan folder upload ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inisialisasi Database PostgreSQL
try:
    database.init_db()
except Exception as e:
    print(f"WARNING: Database initialization failed: {e}")

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def load_logged_in_user():
    """Memuat data user yang sedang login ke flask.g."""
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        try:
            g.user = database.get_user_by_id(user_id)
        except Exception as e:
            print(f"Error loading user: {e}")
            g.user = None
            session.pop('user_id', None)

def login_required(view):
    """Decorator untuk memastikan user harus login untuk mengakses route ini."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Silakan masuk terlebih dahulu untuk mengakses halaman ini.', 'danger')
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

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
@limiter.limit("20 per minute")
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
                os.remove(file_path)

                # Dapatkan teks CSV hasil analisis
                results_csv_str = df.to_csv(index=False)

                # Bersihkan file temp lama dari session jika ada
                if 'temp_csv_file' in session:
                    old_temp_path = os.path.join(app.config['UPLOAD_FOLDER'], session['temp_csv_file'])
                    if os.path.exists(old_temp_path):
                        try:
                            os.remove(old_temp_path)
                        except Exception:
                            pass

                # Simpan berkas CSV hasil secara sementara untuk diunduh
                temp_filename = f"temp_{uuid.uuid4()}.csv"
                temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
                try:
                    with open(temp_file_path, "w", encoding="utf-8") as f:
                        f.write(results_csv_str)
                    session['temp_csv_file'] = temp_filename
                    session['temp_original_filename'] = file.filename
                except Exception as e:
                    print(f"Gagal menulis file CSV sementara: {e}")

                # Simpan ke Supabase jika user login
                if g.user:
                    try:
                        database.save_analysis(
                            user_id=g.user['id'],
                            filename=file.filename,
                            text_column=text_column,
                            positive_count=sentiment_counts.get('Positif', 0),
                            neutral_count=sentiment_counts.get('Netral', 0),
                            negative_count=sentiment_counts.get('Negatif', 0),
                            wordcloud_base64=wordcloud,
                            results_table_html=results_table,
                            results_csv=results_csv_str
                        )
                        flash('Analisis selesai dan riwayat berhasil disimpan ke akun Anda.', 'success')
                    except Exception as e:
                        flash(f'Analisis selesai, tetapi gagal menyimpan riwayat: {e}', 'warning')
                else:
                    flash('Analisis selesai. Masuk untuk menyimpan riwayat analisis Anda di masa mendatang.', 'info')
            else:
                flash('Format file tidak diizinkan. Gunakan .csv atau .xlsx', 'danger')
                return redirect(url_for('analysis'))
            
    return render_template('analysis.html', 
                           prediction=prediction_result, 
                           text=input_text,
                           sentiment_counts=sentiment_counts, 
                           results_table=results_table,
                           wordcloud=wordcloud)

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    """Menangani pendaftaran akun baru."""
    if g.user:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not password:
            flash('Username dan password tidak boleh kosong.', 'danger')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Konfirmasi password tidak cocok.', 'danger')
            return redirect(url_for('register'))
            
        try:
            user_id = database.create_user(username, password)
            if user_id:
                flash('Pendaftaran berhasil! Silakan masuk.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Username sudah digunakan. Pilih username lain.', 'danger')
        except Exception as e:
            flash(f'Terjadi kesalahan saat pendaftaran: {e}', 'danger')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Menangani proses masuk pengguna."""
    if g.user:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        try:
            user = database.check_user_credentials(username, password)
            if user:
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash(f'Selamat datang kembali, {user["username"]}!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Username atau password salah.', 'danger')
        except Exception as e:
            flash(f'Gagal menghubungkan ke database: {e}', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Menangani proses keluar pengguna."""
    session.clear()
    flash('Anda telah keluar.', 'success')
    return redirect(url_for('home'))

@app.route('/history')
@login_required
def history():
    """Menampilkan daftar riwayat analisis milik user."""
    try:
        analyses = database.get_user_analyses(g.user['id'])
        return render_template('history.html', analyses=analyses)
    except Exception as e:
        flash(f'Gagal memuat riwayat analisis: {e}', 'danger')
        return render_template('history.html', analyses=[])

@app.route('/history/<int:analysis_id>')
@login_required
def history_detail(analysis_id):
    """Menampilkan detail visualisasi hasil analisis dari riwayat."""
    try:
        analysis = database.get_analysis_detail(analysis_id, g.user['id'])
        if not analysis:
            flash('Riwayat analisis tidak ditemukan atau Anda tidak memiliki akses.', 'danger')
            return redirect(url_for('history'))
        return render_template('history_detail.html', analysis=analysis)
    except Exception as e:
        flash(f'Gagal memuat detail riwayat: {e}', 'danger')
        return redirect(url_for('history'))

@app.route('/history/<int:analysis_id>/delete', methods=['POST'])
@login_required
def delete_history(analysis_id):
    """Menghapus data riwayat analisis tertentu."""
    try:
        success = database.delete_analysis(analysis_id, g.user['id'])
        if success:
            flash('Riwayat analisis berhasil dihapus.', 'success')
        else:
            flash('Gagal menghapus riwayat analisis.', 'danger')
    except Exception as e:
        flash(f'Terjadi kesalahan: {e}', 'danger')
    return redirect(url_for('history'))

@app.route('/download_temp')
def download_temp():
    """Mengunduh berkas analisis sementara untuk pengguna (guest/tamu)."""
    temp_file = session.get('temp_csv_file')
    if not temp_file:
        flash("Tidak ada data analisis sementara untuk diunduh.", "danger")
        return redirect(url_for('analysis'))
        
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_file)
    if not os.path.exists(file_path):
        flash("Berkas analisis tidak ditemukan atau sudah kedaluwarsa.", "danger")
        return redirect(url_for('analysis'))
        
    original_filename = session.get('temp_original_filename', 'hasil_analisis.csv')
    # Ubah ekstensi file asli ke .csv untuk diunduh
    download_name = os.path.splitext(original_filename)[0] + "_analisis.csv"
    
    return send_file(file_path, as_attachment=True, download_name=download_name, mimetype='text/csv')

@app.route('/history/<int:analysis_id>/download')
@login_required
def download_history_csv(analysis_id):
    """Mengunduh berkas CSV hasil analisis dari database Supabase (pengguna login)."""
    try:
        analysis = database.get_analysis_detail(analysis_id, g.user['id'])
        if not analysis or not analysis.get('results_csv'):
            flash("Data analisis tidak ditemukan atau tidak dapat diunduh.", "danger")
            return redirect(url_for('history'))
            
        download_name = os.path.splitext(analysis['filename'])[0] + "_analisis.csv"
        
        return Response(
            analysis['results_csv'],
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={download_name}"}
        )
    except Exception as e:
        flash(f"Gagal mengunduh berkas: {e}", "danger")
        return redirect(url_for('history'))

@app.route('/about')
def about():
    """Merender halaman about."""
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)