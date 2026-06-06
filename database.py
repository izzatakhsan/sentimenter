import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables dari .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """
    Mengambil koneksi database PostgreSQL (Supabase).
    """
    if not DATABASE_URL or "YOUR_PASSWORD_HERE" in DATABASE_URL or "YOUR_HOST_HERE" in DATABASE_URL:
        raise ValueError("DATABASE_URL belum dikonfigurasi dengan benar di file .env")
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """
    Menginisialisasi tabel database PostgreSQL jika belum ada.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # 1. Buat tabel users
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                );
            """)
            # 2. Buat tabel analyses
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    filename VARCHAR(255) NOT NULL,
                    text_column VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    positive_count INTEGER DEFAULT 0,
                    neutral_count INTEGER DEFAULT 0,
                    negative_count INTEGER DEFAULT 0,
                    wordcloud_base64 TEXT,
                    results_table_html TEXT,
                    results_csv TEXT
                );
            """)
            # Jalankan migrasi kolom jika tabel sudah ada sebelumnya
            cur.execute("""
                ALTER TABLE analyses ADD COLUMN IF NOT EXISTS results_csv TEXT;
            """)
            conn.commit()
            print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# --- Manajemen Pengguna ---

def create_user(username, password):
    """
    Membuat pengguna baru dengan password yang di-hash.
    Mengembalikan ID pengguna jika sukses, atau None jika username sudah ada.
    """
    conn = None
    try:
        conn = get_db_connection()
        hashed_password = generate_password_hash(password)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id;",
                (username, hashed_password)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
    except psycopg2.errors.UniqueViolation:
        if conn:
            conn.rollback()
        return None
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating user: {e}")
        raise e
    finally:
        if conn:
            conn.close()

def check_user_credentials(username, password):
    """
    Memeriksa kredensial pengguna.
    Mengembalikan dict user jika valid, else None.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
            user = cur.fetchone()
            if user and check_password_hash(user['password_hash'], password):
                return user
            return None
    except Exception as e:
        print(f"Error checking user credentials: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_user_by_id(user_id):
    """
    Mengambil data pengguna berdasarkan ID.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, username FROM users WHERE id = %s;", (user_id,))
            return cur.fetchone()
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

# --- Manajemen Riwayat Analisis ---

def save_analysis(user_id, filename, text_column, positive_count, neutral_count, negative_count, wordcloud_base64, results_table_html, results_csv=None):
    """
    Menyimpan riwayat analisis file ke database Supabase.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO analyses (
                    user_id, filename, text_column, positive_count, neutral_count, negative_count, wordcloud_base64, results_table_html, results_csv
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
                """,
                (user_id, filename, text_column, positive_count, neutral_count, negative_count, wordcloud_base64, results_table_html, results_csv)
            )
            analysis_id = cur.fetchone()[0]
            conn.commit()
            return analysis_id
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error saving analysis: {e}")
        raise e
    finally:
        if conn:
            conn.close()

def get_user_analyses(user_id):
    """
    Mengambil seluruh daftar riwayat analisis milik user (tanpa text besar).
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, filename, text_column, timestamp, positive_count, neutral_count, negative_count
                FROM analyses
                WHERE user_id = %s
                ORDER BY timestamp DESC;
                """,
                (user_id,)
            )
            return cur.fetchall()
    except Exception as e:
        print(f"Error getting user analyses: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_analysis_detail(analysis_id, user_id):
    """
    Mengambil detail lengkap analisis (termasuk wordcloud & tabel html).
    Memastikan data hanya bisa diakses oleh pemiliknya.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM analyses
                WHERE id = %s AND user_id = %s;
                """,
                (analysis_id, user_id)
            )
            return cur.fetchone()
    except Exception as e:
        print(f"Error getting analysis detail: {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_analysis(analysis_id, user_id):
    """
    Menghapus riwayat analisis tertentu milik user.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM analyses WHERE id = %s AND user_id = %s;",
                (analysis_id, user_id)
            )
            conn.commit()
            return True
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error deleting analysis: {e}")
        return False
    finally:
        if conn:
            conn.close()
