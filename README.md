Intelligent Book Summarization Platform

A modular platform that extracts text from books, preprocesses it, and generates high-quality summaries using modern NLP models. It includes a Streamlit UI, backend services, authentication, a structured database, and a clean architecture ready for scaling.

🚀 Features

Upload books in PDF, DOCX, TXT

Robust text extraction with fallbacks

Transformer-based summaries (Hugging Face)

User authentication with bcrypt hashing

SQLite storage for users, uploads, and summaries

Streamlit-based dashboard and navigation

Modular backend: extraction, preprocessing, summarization, auth

Full test suite with pytest

📁 Project Structure
project_root/
│── frontend/        # Streamlit UI pages
│── backend/         # Core logic (auth, extraction, preprocessing)
│── utils/           # DB utilities, validators, helpers
│── models/          # NLP model integration
│── data/            # Uploads, cache, extracted text
│── config/          # Logging and configuration
│── tests/           # Unit & integration tests
└── README.md

⚙️ Installation
git clone <repo-url>
cd IntelligentBookSummarizer

python -m venv venv
.\venv\Scripts\activate

pip install -r requirements.txt
# or generate fresh:
pip freeze > requirements.txt


Create a .env file for secrets.

Initialize the database:

python utils/database.py

📌 Task Breakdown
Task 2 – Database Schema & Utilities

Built a reliable SQLite schema with tables for Users, Books, and Summaries.
Includes indexing, validation rules, foreign keys, and a full CRUD utility module.

create_user, get_user_by_email

create_book, update_book_status

create_summary, get_summaries_by_user

All DB tests passed successfully.

Task 3 – Authentication UI (Frontend)

Streamlit-based registration and login pages with full client-side validation.

Name, Email, Password, Confirm Password

Regex and strength validation

Login with optional “Remember me”

Clear error messages and navigation

Run:

streamlit run frontend/auth.py

Task 4 – Authentication Backend & Sessions

Secure backend for login and registration.

bcrypt password hashing

Safe login verification

Session state handling (login/logout)

Expiry, rate limits & clean error messages

All auth tests passed

Task 5 – File Upload Interface

Upload TXT, PDF, DOCX with validation, preview, and history.

Size, format, corruption checks

Metadata: title, author, chapter

Preview content (text / pages / paragraphs)

File history with actions

Saves files to data/uploads/

Run:

streamlit run frontend/upload.py

Task 6 – Text Extraction (Backend)

Extracts clean text from multiple formats with fallbacks and error handling.

TXT encoding handling

PDF via PyPDF → pdfplumber fallback

DOCX paragraph extraction

Scanned PDF detection

Word/character stats

Saves extracted text to DB

Task 7 – User Dashboard

Main navigation hub for authenticated users.

Header with user name

Sidebar: Dashboard, Upload, Books, Summaries, Settings

Quick stats and recent activity

Clean routing and session-aware pages

Admin-only options

Task 8 – Text Preprocessing Pipeline

Prepares extracted text for summarization.

Cleanup & normalization

spaCy-based sentence segmentation

Language detection

Word, sentence, reading-time stats

Chunking by sentence ranges

Returns cleaned text + structured chunks

🧪 Testing

All database and backend modules include pytest coverage.
Example:

pytest -q

📄 Logging

Logs stored in:

logs/app.log
