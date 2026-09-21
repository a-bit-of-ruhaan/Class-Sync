# Class Sync

Class Sync is a Streamlit-based study companion designed for students who want a cleaner way to manage notes, summarize documents, and explore learning content. The app combines secure user accounts, AI-powered document analysis, and a shared notes gallery in one local classroom-friendly workspace.

## Overview

The project includes:

- A login and sign-up flow with secure local account storage
- A protected dashboard for authenticated users
- A document summarizer powered by Google Gemini
- A notes gallery for uploaded study images
- A quick facts section that surfaces interesting learning prompts
- A small team/about page for the project creators

## Features

### Secure authentication

- User registration and login with email, name, and username
- Password hashing using PBKDF2-HMAC-SHA256 with a unique per-user salt
- SQLite storage in the local database folder
- Session persistence for 30 days using hashed browser tokens
- Protected pages that redirect unauthenticated users to the login screen

### Smart Sum document assistant

- Upload PDF, DOCX, or TXT files
- Extract text from supported document types
- Ask questions about the uploaded file
- Generate summaries based only on the document content
- Avoid answering questions when the information is not present in the upload

### Notes workspace

- Upload image-based notes tied to the active user
- View a shared public album of notes from all users
- See uploader metadata such as name, username, and upload time
- Delete only your own uploaded notes

### Curiosity and home dashboard

- Display a collection of quick facts on the home screen
- Generate fresh AI-powered facts using Gemini
- Navigate to the notes, summarizer, and about pages from the app dashboard

## Tech stack

- Python
- Streamlit
- SQLite
- Google Gemini API via google-genai
- PyPDF2 for PDF extraction
- python-docx for DOCX extraction
- Pillow for image handling
- python-dotenv for local environment variables
- Pydantic for structured fact responses

## Project structure

```text
Class Sync/
├── home.py                   # Authenticated landing page/dashboard
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
├── backend/
│   ├── ai_api.py            # Gemini integration for document Q&A and summaries
│   ├── auth.py              # Authentication, session handling, SQLite logic
│   ├── config.py            # API key resolution from environment variables
│   ├── fact.py              # Gemini fact generation logic
│   └── note_summarizer.py   # PDF/DOCX text extraction helpers
├── database/
│   └── classync.db          # Local SQLite database, created when the app runs
├── images/
│   ├── backg.png            # Background image used across pages
│   ├── logo.png             # Brand/logo asset
│   ├── note.png             # Notes feature artwork
│   └── summarize.png        # Summarizer feature artwork
├── notes/
│   └── <username>/          # User-uploaded note images
├── pages/
│   ├── about.py             # Team/about page
│   ├── login.py             # Login and account creation page
│   ├── notes.py             # Notes gallery and uploads
│   └── summarizer.py        # Document summarizer page
├── styles/
│   ├── about.css
│   ├── home.css
│   ├── login.css
│   ├── notes.css
│   └── summarizer.css
├── tests/
│   ├── __init__.py
│   ├── test_ai_config.py
│   └── test_fact_parsing.py
└── .env                     # Local environment secrets (not committed)
```

## Prerequisites

- Python 3.10+
- A valid Google Gemini API key
- Access to the internet for Gemini requests

## Quick start

1. Clone the project.
2. Open a terminal in the project root.
3. Create and activate a virtual environment if desired.
4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the project root with your Gemini key:

```env
GEMINI_API_KEY=your_api_key_here
```

The app also supports `GOOGLE_API_KEY` as a fallback alias. For better quota isolation, copy `.env.example` and add dedicated `SUMMARIZER_API_KEY`, `QUIZ_API_KEY`, and `FACTS_API_KEY` values. Each feature prefers its dedicated key and falls back to the existing Gemini key until you add one.

6. Start the app:

```bash
streamlit run home.py
```

7. Open the local Streamlit URL (typically `http://localhost:8501`).

## Using the app

### Login and account creation

- Visit the login page when the app starts.
- Create a new account or sign in with an existing one.
- Authenticated users are directed to the main dashboard.

### Dashboard

From the home dashboard, users can navigate to:

- Summarizer
- Notes
- About/Team

### Smart Sum workflow

1. Upload a PDF, DOCX, or TXT file.
2. The app extracts readable text.
3. Generate a summary or ask a document-related question.
4. The model responds based only on the uploaded content.

### Notes gallery

- Upload note images from the notes page.
- Files are stored under a user-specific folder in `notes/`.
- The gallery displays each uploaded image with basic metadata.

## Environment and storage notes

- Secrets are expected in a local `.env` file and should not be committed.
- The app stores user accounts and login sessions in `database/classync.db`.
- Images uploaded to the notes system are stored in the project folders under `notes/<username>/`.
- The app uses hashed session tokens, not raw session IDs, for safer persistence.

## Running tests

This project includes a small set of tests for config and fact parsing. To run them:

```bash
pytest
```

## Troubleshooting

### `No API key found`

Check that your `.env` file exists and includes one of the supported keys:

```env
GEMINI_API_KEY=your_api_key_here
```

### App redirects to login

- Make sure the user has created an account or signed in.
- Confirm that the SQLite database is writable.
- Verify that the app can create and update files in the project directory.

### Files fail to extract

- PDF files should be readable text PDFs or OCR-processed versions.
- DOCX files should be valid Word documents.
- TXT files should be UTF-8 encoded if possible.

## Project status

This is a local study-application prototype designed for classroom or personal use. It is not a production-grade deployment setup and should be reviewed before use with real personal or institutional data.

## License

No license has been specified for this project yet.
