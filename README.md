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