# Classync

Classync is a local Streamlit study and learning community app. It combines document-based AI study tools with note sharing, profiles, messaging, games, and lightweight moderation.

## Features

- Account creation and login with salted PBKDF2-HMAC-SHA256 password hashing
- Persistent sessions backed by hashed browser tokens
- AI document assistant for PDF, DOCX, and TXT files
- Summary, study guide, flashcard, practice quiz, and simple explanation modes
- Document-grounded questions and answers through Google Gemini
- Image note uploads with titles, tags, categories, search, likes, saves, and study plans
- Community discovery, profiles, avatars, mate requests, direct chat, and group study chats
- AI-generated quiz games with local scoring and leaderboards
- Developer console for admin accounts, user bans, note moderation, and activity logs
- Home dashboard with generated study facts

## Technology

- Python 3.10+
- Streamlit
- SQLite
- Google Gemini through `google-genai`
- PyPDF2 and `python-docx` for document extraction
- Pillow for image handling
- `python-dotenv` for local configuration
- Pydantic for structured AI responses

## Setup

From the project root, create a virtual environment and install the dependencies:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Create a local `.env` file. Do not commit it or share its values:

```env
GEMINI_API_KEY=your_gemini_api_key
```

The app also accepts `GOOGLE_API_KEY` as a fallback name. Feature-specific keys can be set when separate quotas are needed:

```env
SUMMARIZER_API_KEY=your_key
QUIZ_API_KEY=your_key
FACTS_API_KEY=your_key
ADMIN_EMAILS=admin@example.com
```

Each feature-specific key takes priority over the shared key. `ADMIN_EMAILS` is a comma-separated list of email addresses allowed to open the Developer page.

## Run the app

```bash
streamlit run home.py
```

Open the local URL shown by Streamlit, usually `http://localhost:8501`. New users can create an account from the login page. The app creates its SQLite database and storage directories as needed.

## Main pages

| Page | Purpose |
| --- | --- |
| Home | Dashboard, metrics, and study facts |
| Notes | Upload, organize, search, like, save, and plan study work |
| Summarize | Analyze documents and chat about their contents |
| Explore | Browse community notes and learner profiles |
| Search | Find discoverable users |
| Games | Create and play AI-generated quizzes |
| Profile | Edit profile details, manage mates, and view uploads |
| Chat | Message accepted mates and use group study chats |
| Developer | Admin-only moderation and activity tools |
| About | Project team information |

## Project structure

```text
Class Sync/
├── home.py                 # Streamlit entry point and dashboard
├── backend/                # Authentication, AI, chat, games, study, and UI logic
├── pages/                  # Streamlit pages
├── database/               # SQLite database created at runtime
├── notes/                  # User-uploaded notes and metadata
├── images/                 # App artwork and branding
├── styles/                 # Page-specific CSS
├── tests/                  # pytest test suite
├── requirements.txt        # Runtime and test dependencies
└── README.md
```

## Data and security notes

- Secrets belong in `.env`, which should remain local and untracked.
- User accounts, sessions, social relationships, chats, games, and moderation data are stored in `database/classync.db`.
- Uploaded notes and profile photos are stored under `notes/<username>/`.
- Uploaded files are local application data; review the storage and privacy model before deploying publicly.
- The app is a local prototype and is not configured as a production deployment.

## Tests

Run the test suite from the project root:

```bash
pytest
```

## Troubleshooting

### `No API key found`

Ensure `.env` exists in the project root and contains `GEMINI_API_KEY`, `GOOGLE_API_KEY`, or the relevant feature-specific key.

### The app redirects to login

Create an account or sign in, and confirm that the project can write to `database/` and `notes/`.

### A document cannot be read

Use a text-based PDF, a valid DOCX file, or a UTF-8 TXT file. Scanned PDFs may require OCR before upload.

## License

No license has been specified for this project.
