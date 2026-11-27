# Nusa Mete

Dashboard jambu mete Nusa Tenggara Timur 2022-2025 (Streamlit + Neon).

Jalankan di komputer:

    python -m venv .venv
    .venv\Scripts\activate        (Windows)   |   source .venv/bin/activate (Mac/Linux)
    pip install -r requirements.txt
    streamlit run app.py

Tanpa file `.streamlit/secrets.toml`, aplikasi membaca `data/jambu_mete_pusat.csv`.
Untuk memakai Neon, salin `.streamlit/secrets.toml.example` menjadi `secrets.toml`
lalu isi connection string db_PUSAT_JAMBU_METE. Jangan unggah secrets.toml ke GitHub.
