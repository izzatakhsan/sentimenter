# Gunakan Python 3.9 sebagai dasar
FROM python:3.9

# Set working directory
WORKDIR /code

# Copy requirements.txt ke dalam container
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Buat user baru 'user' dengan ID 1000 (Syarat keamanan Hugging Face)
RUN useradd -m -u 1000 user

# Ganti user ke 'user'
USER user

# Set environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Pre-download & cache model IndoBERT di dalam container agar space startup instan
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; AutoTokenizer.from_pretrained('crypter70/IndoBERT-Sentiment-Analysis'); AutoModelForSequenceClassification.from_pretrained('crypter70/IndoBERT-Sentiment-Analysis')"

# Pindah ke direktori kerja user
WORKDIR $HOME/app

# Copy semua file proyek ke dalam container dengan izin user yang benar
COPY --chown=user . $HOME/app

# Buat folder uploads agar tidak error saat upload file
RUN mkdir -p $HOME/app/uploads

# Jalankan aplikasi menggunakan Gunicorn pada port 7860
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]
