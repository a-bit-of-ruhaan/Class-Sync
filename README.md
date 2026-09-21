# Classync

Classync is an AI-powered study companion built with Streamlit. It gives students one focused place to summarize documents, organize visual notes, discover interesting facts, and learn more about the team behind the project.

## Features

- **Secure account access**
  - Login and account creation flows
  - Display name, username, and email profiles
  - PBKDF2-HMAC-SHA256 password hashing with per-user salts
  - Local SQLite user storage
  - 30-day persistent login sessions that survive browser refreshes
  - Protected application pages with logout support

- **Smart Sum document assistant**
  - Upload PDF, DOCX, and TXT files
  - Extract text with `PyPDF2` and `python-docx`
  - Generate summaries and document-grounded answers with Google Gemini
  - Ask follow-up questions about uploaded content
  - Avoid unsupported answers when information is not present in the document

- **Notes workspace**
  - Upload image-based notes
  - Browse a public album containing notes uploaded by every user
  - Show the uploader name, username, email, and upload time for each image
  - Delete only your own uploaded notes
  - View notes in a simple visual grid

- **Curiosity dashboard**
  - Generate four fresh facts with Google Gemini
  - Explore summarization and notes from the home page
  - View the Classync team and portfolio links

- **Branded interface**
  - Responsive login page
  - Custom logo and visual assets
  - Dark glass-inspired layouts
  - Account sidebar with initials avatar, username, and logout action

## Project Structure

```text
Class Sync/
├── home.py                    # Authenticated home dashboard
├── pages/
│   ├── login.py               # Login and account creation
│   ├── about.py               # Team and portfolio page
│   ├── notes.py               # Image notes workspace
│   └── summarizer.py          # Document upload and Smart Sum chat
├── backend/
│   ├── auth.py                # SQLite authentication and sessions
│   ├── ai_api.py              # Gemini document assistant integration
│   ├── fact.py                # Gemini fact generation
│   └── note_summarizer.py     # PDF and DOCX text extraction
├── database/
│   └── classync.db            # Local SQLite database, created automatically
├── images/
│   ├── logo.png               # Classync logo
│   ├── backg.png              # Shared background artwork
│   ├── note.png               # Notes feature artwork
│   └── summarize.png          # Summarizer feature artwork
├── styles/                    # Page-specific CSS files
├── notes/                     # Per-user uploaded note images
└── README.md
```

## Requirements

- Python 3.10 or newer
- A Google Gemini API key
- Internet access for Gemini requests and hosted font loading

Install the Python packages used by the project:

```bash
pip install streamlit anyio python-dotenv google-genai pydantic PyPDF2 python-docx Pillow
```

## Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

The app also accepts `GOOGLE_API_KEY` as an alias. Do not commit `.env` or expose the API key in source control.

## Running the App

From the project root, run:

```bash
streamlit run home.py
```

Then open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

Unauthenticated visitors are redirected to the login page. After creating an account or signing in, users can access the home dashboard and protected pages.

## Authentication

Authentication is implemented in `backend/auth.py`.

- User records are stored in `database/classync.db`.
- Passwords are never stored as plain text.
- Passwords are derived with PBKDF2-HMAC-SHA256 using 210,000 iterations and a unique salt.
- Existing databases are migrated automatically when the authentication helper connects.
- `require_auth()` protects the home, notes, summarizer, and About pages.
- A random 30-day session token is retained in the app URL while only its SHA-256 hash is stored in SQLite, allowing login to survive browser refreshes.
- Streamlit session state holds the active user profile after the token is restored.

This implementation is suitable for a local or classroom project. A production deployment should add email verification, password reset, rate limiting, secure session management, managed database storage, and a production-grade identity provider.

## Smart Sum Flow

1. A user uploads a PDF, DOCX, or TXT file.
2. The file is converted into text locally.
3. The extracted document is placed into the Gemini request context.
4. The user can request a summary, explanation, or answer to a question.
5. The assistant is instructed to use only the uploaded document and clearly state when information cannot be found.

The Gemini integration requires `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) to be available through `.env`.

## Data and Privacy Notes

- Uploaded note images are saved in username-scoped local directories under `notes/<username>/`.
- The Notes page reads those directories into a public album visible to authenticated users.
- User accounts are saved in the local SQLite database.
- Uploaded document text is held in Streamlit session state while the user works with it.
- Documents and notes are not automatically deleted by the application.
- Review storage and retention requirements before deploying with real personal data.

## Team Portfolio Links

The About page currently includes:

- Ruhaan: portfolio link configured
- Ashish: placeholder link
- Vansh: placeholder link

Replace the placeholder `href` values in `pages/about.py` when the remaining portfolio URLs are ready.

## Troubleshooting

### `GEMINI_API_KEY is not set`

Make sure `.env` exists in the project root and contains a valid key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

The app also accepts `GOOGLE_API_KEY` as a fallback alias. Restart Streamlit after changing environment variables.

### Login redirects back to the login page

The persistent session expires after 30 days or is removed when you log out. Sign in again if the token has expired, and make sure the app can write to `database/classync.db`.

### Uploaded files are not readable

Confirm that the file is a valid PDF, DOCX, or UTF-8 text file. Scanned PDFs may require OCR before their text can be extracted.

### Gemini requests fail

The summarizer and fact generator catch API failures and display an in-app error. Check `GEMINI_API_KEY` or `GOOGLE_API_KEY`, network access, model availability, and account quota.

## Development Notes

Keep secrets in `.env`, avoid committing generated databases or uploaded files, and test authentication and document handling before deploying. The CSS is intentionally page-specific, so changes to one page's visual language should be made in its matching file under `styles/`.

## License

No license has been specified for this project yet.
