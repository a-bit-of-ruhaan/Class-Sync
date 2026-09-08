# Classync

Classync is an AI-powered study companion built with Streamlit. It gives students one focused place to summarize documents, organize visual notes, discover interesting facts, and learn more about the team behind the project.

## Features

- **Secure account access**
  - Login and account creation flows
  - Display name, username, and email profiles
  - PBKDF2-HMAC-SHA256 password hashing with per-user salts
  - Local SQLite user storage
  - Protected application pages with logout support

- **Smart Sum document assistant**
  - Upload PDF, DOCX, and TXT files
  - Extract text with `PyPDF2` and `python-docx`
  - Generate summaries and document-grounded answers with Google Gemini
  - Ask follow-up questions about uploaded content
  - Avoid unsupported answers when information is not present in the document

- **Notes workspace**
  - Upload image-based notes
  - Browse previously uploaded notes
  - View notes in a simple visual grid

- **Curiosity dashboard**
  - Generate four fresh facts with Gemini
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
├── notes/                     # Uploaded note images
└── README.md
```

## Requirements

- Python 3.10 or newer
- A Google Gemini API key
- Internet access for Gemini requests and hosted font loading

Install the Python packages used by the project:

```bash
pip install streamlit google-genai python-dotenv PyPDF2 python-docx pydantic anyio
```

## Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Do not commit `.env` or expose the API key in source control.

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
- Streamlit session state tracks the signed-in user during the active session.

This implementation is suitable for a local or classroom project. A production deployment should add email verification, password reset, rate limiting, secure session management, managed database storage, and a production-grade identity provider.

## Smart Sum Flow

1. A user uploads a PDF, DOCX, or TXT file.
2. The file is converted into text locally.
3. The extracted document is placed into the Gemini request context.
4. The user can request a summary, explanation, or answer to a question.
5. The assistant is instructed to use only the uploaded document and clearly state when information cannot be found.

The Gemini integration requires `GEMINI_API_KEY` to be available through `.env`.

## Data and Privacy Notes

- Uploaded note images are saved in the local `notes/` directory.
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

Restart Streamlit after changing environment variables.

### Login redirects back to the login page

The application uses Streamlit session state. Confirm that the app is running as one Streamlit process and that the browser session has not been reset.

### Uploaded files are not readable

Confirm that the file is a valid PDF, DOCX, or UTF-8 text file. Scanned PDFs may require OCR before their text can be extracted.

## Development Notes

Keep secrets in `.env`, avoid committing generated databases or uploaded files, and test authentication and document handling before deploying. The CSS is intentionally page-specific, so changes to one page's visual language should be made in its matching file under `styles/`.

## License

No license has been specified for this project yet.
