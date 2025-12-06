Intelligent Book Summarization Platform

A streamlined platform that extracts key insights, summaries, and chapter-level understanding from books using modern NLP models.

Overview

This project is an end-to-end system that allows users to upload book files (PDF, DOCX, text), process them, and generate high-quality summaries using transformer-based NLP models.
It includes a Streamlit frontend, a modular backend, database integration, authentication, and a clean project architecture for scalable development.

Features

Upload books in multiple formats (PDF, DOCX, TXT)

Extract raw text using robust parsers

Generate summaries using transformer models (Hugging Face)

User authentication with secure password hashing

SQLite database for storing user data, uploads, and summaries

Clean modular architecture for simple scaling

Streamlit interface for fast UI development

Project Structure
project_root/
├── frontend/           # Streamlit UI pages
├── backend/            # Core business logic
├── utils/              # Helper functions (DB, file handling, auth utilities)
├── models/             # Integration of NLP models
├── data/               # Uploaded files, cache, extracted text
├── config/             # Configuration and logging
├── tests/              # Unit and integration tests
└── README.md

Installation & Setup
1. Clone the repository
git clone <your-repo-url>
cd IntelligentBookSummarizer

2. Create a virtual environment

python -m venv venv
.\venv\Scripts\Activate

3. Install required libraries

pip install streamlit transformers torch huggingface_hub pyPDF2 pdfplumber python-docx bcrypt python-dotenv spacy langdetect

Then generate requirements.txt automatically:

pip freeze > requirements.txt

4. Create .env file

Your .env file is already marked to be ignored by Git.

5. Initialize the database
python utils/database.py

Logging

Logging is preconfigured in config/logging_config.py.
Logs are stored in:

/logs/app.log

This helps with debugging and monitoring app performance.

Tests

Place unit tests and integration tests inside:

Task 2: Database Schema Design & Implementation

This task establishes the database foundation for the Intelligent Book Summarization Platform. It includes schema design, indexing strategy, validation rules, CRUD utilities, and automated tests to ensure the database layer is reliable and consistent.

1. Objective

Create a robust SQLite database schema and implement a database utility module (utils/database.py) that supports user management, book storage, and summarization records.
This database layer will serve as the backbone for upcoming authentication, file upload, and summarization workflows.

2. Deliverables
✔ Database Schema

Three core tables were created:

Users
Field	Type	Notes
user_id	INTEGER PK	Auto-increment
name	TEXT	Required
email	TEXT	Unique, required
password_hash	BLOB	bcrypt hashed
created_at	TEXT	UTC ISO timestamp
role	TEXT	admin or user
Books
Field	Type	Notes
book_id	INTEGER PK	Auto-increment
user_id	INTEGER FK	References Users
title	TEXT	Required
author	TEXT	Optional
chapter	TEXT	Optional
file_path	TEXT	Path to uploaded file
raw_text	TEXT	Extracted text
uploaded_at	TEXT	UTC timestamp
status	TEXT	uploaded / processing / completed / failed
Summaries
Field	Type	Notes
summary_id	INTEGER PK	Auto-increment
book_id	INTEGER FK	References Books
user_id	INTEGER FK	References Users
summary_text	TEXT	Generated summary
summary_length	TEXT	short / medium / long
summary_style	TEXT	paragraphs / bullets
chunk_summaries	TEXT	Stored as JSON
created_at	TEXT	UTC timestamp
processing_time	REAL	Time taken (seconds)
3. Indexing

To improve query performance as data grows:

Users.email → UNIQUE INDEX

Books.user_id → INDEX

Summaries.user_id → INDEX

Summaries.book_id → INDEX

These indexes optimize login, listing summaries, and retrieving user-specific records.

4. Validation & Constraints
Application-level validation

Valid email format

Required fields (name, email, title, summary options)

Password hashing using bcrypt

JSON serialization for chunk summaries

Database-level constraints

UNIQUE(email)

CHECK constraints on role, status, summary_length, summary_style

Foreign keys linking Users → Books → Summaries

5. Database Utilities (utils/database.py)

A complete CRUD layer was implemented with:

Connection & Initialization

connect_db()

init_db()

close_db()

User Operations

create_user()

get_user_by_email()

verify_user_password()

Book Operations

create_book()

update_book_status()

get_book_by_id()

Summary Operations

create_summary()

get_summaries_by_user()

All functions use prepared statements and return Python dictionaries for easy integration.

6. Database Initialization Script

/scripts/init_db.py creates the SQLite file and initializes all tables:

python scripts/init_db.py


This is run once during setup or CI.

7. Automated Tests

A full pytest suite (tests/test_database.py) verifies:

Table creation

Unique email constraint

Password hashing & verification

Book creation + status update

Summary creation + retrieval

JSON chunk parsing

Foreign key relationships

Test result:

5 passed in X.XXs

8. Outcome

Task 2 is complete, and the project now has:

A stable relational schema

Secure user storage

Structured book and summary records

Indexed and optimized queries

Fully tested CRUD operations

Zero warnings or schema issues