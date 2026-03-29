# Sales AI

`Sales AI` is a Flask-based demo app for intelligent sales and revenue operations. It simulates an AI copilot that works on top of CRM-style account and deal data to help teams prioritize prospects, recover risky deals, and flag retention issues early.

The project is built as a lightweight MVP, so it works well as a hackathon demo, portfolio project, or starter template for a more complete RevOps assistant.

## Features

- Prospect scoring based on company fit, buying signals, pain points, and engagement
- Personalized outreach generation for target accounts
- Deal risk analysis using stage velocity, engagement health, competition, and champion changes
- Retention watchlist using product usage, support load, and sentiment signals
- Competitive battlecards for higher-risk opportunities
- Dashboard overview with pipeline and account health metrics
- CSV import for replacing the built-in sample CRM data
- Optional AI generation with Gemini or OpenAI, with fallback output when no API key is configured

## Tech Stack

- Python 3
- Flask
- `python-dotenv`
- OpenAI Python SDK
- Google GenAI SDK

## Project Structure

```text
sales_ai/
|-- app.py                 # Flask app factory and Vercel-ready app object
|-- main.py                # Local development entrypoint
|-- vercel.json            # Vercel framework config
|-- requirements.txt       # Python dependencies
|-- .env.example           # Example environment variables
|-- public/                # Static assets served locally and on Vercel
|-- sample_data/           # Example CRM-style CSV files
|-- sales_ops/
|   |-- ai_client.py       # AI provider selection and text generation
|   |-- data.py            # Built-in demo accounts and deals
|   |-- engine.py          # Revenue operations logic
|   |-- importer.py        # CSV parsing helpers
|   `-- models.py          # Data models
|-- static/                # Legacy static assets
`-- templates/             # Flask HTML templates
```

## Getting Started

### 1. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Then update it with your provider keys if you want real AI-generated responses.

Example:

```env
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash

# Optional alternative provider
# OPENAI_API_KEY=your_openai_key_here
# OPENAI_MODEL=gpt-5.4
```

### 4. Run the app

```powershell
python main.py
```

Open `http://127.0.0.1:5000`.

## AI Provider Behavior

The app checks providers in this order:

1. Gemini
2. OpenAI
3. Built-in fallback content

If neither provider is configured, the application still works and returns deterministic fallback messaging for outreach and recovery play generation.

## API Endpoints

- `GET /`
- `GET /api/overview`
- `GET /api/prospects`
- `GET /api/deals`
- `GET /api/retention`
- `GET /api/competitive`
- `POST /api/generate/outreach/<account_name>`
- `POST /api/generate/recovery/<account_name>`
- `POST /api/import/crm`

The import endpoint expects:

- `accounts_csv`
- `deals_csv`

## Sample Data

The repository includes sample files in:

- `sample_data/accounts.csv`
- `sample_data/deals.csv`

Multi-value CSV fields use the `|` separator.

## Development Notes

- `app.py` uses `load_dotenv()`, so local `.env` values are loaded automatically.
- `main.py` runs the Flask app in debug mode for local development.
- Imported CRM data is stored in memory, so it resets when the app restarts.
- Static assets are served from `public/` so the same setup works locally and on Vercel.

## Deploy On Vercel

This project is configured for Vercel with:

- a top-level Flask `app` object in `app.py`
- a `vercel.json` file using the `flask` framework preset
- static assets in `public/`

To deploy:

1. Push the repository to GitHub.
2. Import the project into Vercel.
3. Add environment variables in the Vercel dashboard if you want AI generation:
   `GEMINI_API_KEY`, `GEMINI_MODEL`, `OPENAI_API_KEY`, `OPENAI_MODEL`
4. Deploy.

Important note:

- Imported CSV data is in-memory only, so it will not persist across deployments or function restarts on Vercel.

## Limitations

- No database persistence
- No authentication
- No background jobs or async processing
- AI output quality depends on the configured provider and model
- CSV import assumes the expected schema is present

## License

Add your preferred license before publishing or distributing the project.
