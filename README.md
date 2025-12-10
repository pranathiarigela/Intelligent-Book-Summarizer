Intelligent Book Summarization Platform

A lightweight and efficient platform that allows users to upload books, extract text, preprocess it, and generate summaries. The system includes secure authentication, database-backed storage, search and filter features, and a clean Streamlit interface.

Features

1. Project Setup & Environment

Python virtual environment with all required dependencies

Streamlit for frontend

SQLAlchemy ORM for database handling

PDF and text processing libraries (PyPDF2, pdfplumber)

Organized project structure with separate backend, frontend, models, and utils modules

Git initialized for version control


2. Database Design

SQLite database with the following tables:

Users: user_id, username, email, password_hash, role, timestamps

Books: book_id, user_id, title, author, extracted_text, upload_date, file_type

Summaries: summary_id, book_id, summary_text, summary_length, generation_date, model_used


ORM models created using SQLAlchemy


3. User Authentication & Authorization

Secure registration and login

Password hashing using bcrypt/werkzeug

Session tracking and session timeout

Role-based access:

Admin: Access all books and summaries

User: Access only their content


Logout support


4. File Upload & Text Input

Upload support for .txt and .pdf files (max 10MB)

PDF multi-page extraction

Validation for corrupted files and text inputs

Metadata storage (title, author, chapter)

Extracted text stored in database


5. UI & Dashboard

Streamlit-based UI

Landing page with project intro and auth forms

Dashboard for uploaded books and summaries

Clean layout working on both desktop and mobile

Basic styling and responsive design


6. Text Preprocessing Pipeline

Cleaning and normalization

Handling special characters, spacing, formatting

Optional removal of citations, footnotes, page numbers

Language detection with langdetect

Automatic chunking of long text into 1000–1500 word segments with overlap


7. Search & Filter Features

Search books by title, author, or upload date

Filters for:

Newest or oldest

Alphabetical sorting

Summary status (summarized or not)


Pagination for large datasets

Clear result display with options to view, summarize, or delete entries


Tech Stack

Frontend: Streamlit

Backend: Python

Database: SQLite

ORM: SQLAlchemy

Text Parsing: PyPDF2, pdfplumber

Language Detection: langdetect

Version Control: Git and GitHub


Project Structure

project_root/
│
├── frontend/        # Streamlit pages (login, dashboard, upload, etc.)
├── backend/         # Auth logic, file handling, text processing
├── models/          # SQLAlchemy ORM models
├── utils/           # Helpers (database, validation, etc.)
├── data/            # Uploaded files and extracted text
├── config/          # Configurations
└── tests/           # Unit tests

How to Run

# Create environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the app
streamlit run app.py