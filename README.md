Intelligent Book Summarizer

An end-to-end web application that allows users to upload books and generate high-quality summaries using NLP techniques. The system is designed with scalability, modularity, and resource efficiency in mind, combining a Flask backend, Streamlit frontend, and robust database management.

📌 Project Overview

The Intelligent Book Summarizer enables users to:

Upload books in PDF, DOCX, or TXT formats

Extract and preprocess large textual content

Generate summaries using a safe, CPU-efficient NLP pipeline

Store, manage, and version multiple summaries per book

View summaries with metadata such as model used, length, and creation time

The platform also includes authentication, role-based access control, and admin analytics.

🚀 Key Features
User Features

Secure user registration and login

Upload and manage books

Generate summaries for uploaded books

View multiple summary versions for the same book

Edit or delete summaries

Generate summaries from pasted text

Admin Features

View all summaries in the system

Manage user-generated content

Analytics dashboard:

Total summaries generated

Average summary length

Most active users

🧠 Summarization Pipeline

Text Extraction: PDF, DOCX, TXT parsers

Preprocessing:

Cleaning and normalization

Intelligent chunking for large texts

Summarization:

Extractive summarization (TextRank-based)

Resource-safe for CPU-only systems

Post-Processing:

Sentence deduplication

Length control

Improved readability and flow

Keyword extraction

This design avoids heavy transformer inference on local machines, ensuring stability and performance.

🛠️ Tech Stack
Backend

Python

Flask

Flask-SQLAlchemy

SQLite

NLTK

Sumy (TextRank)

Frontend

Streamlit

Other Tools

Werkzeug (security utilities)

SQLAlchemy ORM

Git & GitHub for version control

📂 Project Structure
IntelligentBookSummarizer/
│
├── backend/
│   ├── app.py
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── db_models.py
│   ├── file_utils.py
│   ├── hash_utils.py
│   ├── text_preprocessing.py
│   ├── models/
│   │   └── summarizer.py
│   └── utils/
│       └── summary_postprocess.py
│
├── frontend/
│   ├── app.py
│   └── pages/
│
├── requirements.txt
├── README.md
└── .gitignore

⚙️ How to Run the Project
1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

2. Install dependencies
pip install -r requirements.txt

3. Run the backend
python -m backend.app

4. Run the frontend
streamlit run frontend/app.py

🗄️ Database Notes

Uses SQLite for simplicity

Supports:

Multiple summaries per book

Versioning of summaries

User-to-book relationships

If schema changes are made, delete the .db file and restart the backend to reinitialize tables
