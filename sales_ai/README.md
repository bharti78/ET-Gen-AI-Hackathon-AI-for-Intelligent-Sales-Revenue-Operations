# Sales AI

`Sales AI` is a Flask-based demo app for intelligent sales and revenue operations. It simulates an AI copilot that works on top of CRM-style account and deal data to help teams prioritize prospects, recover risky deals, and flag retention issues early.

The project is built as a lightweight MVP, so it runs well as a hackathon demo, portfolio project, or starter template for a more complete RevOps assistant.

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
|-- app.py                 # Flask app factory and routes
|-- main.py                # Local development entrypoint
|-- requirements.txt       # Python dependencies
|-- .env.example           # Example environment variables
|-- sample_data/           # Example CRM-style CSV files
|-- sales_ops/
|   |-- ai_client.py       # AI provider selection and text generation
|   |-- data.py            # Built-in demo accounts and deals
|   |-- engine.py          # Revenue operations logic
|   |-- importer.py        # CSV parsing helpers
|   `-- models.py          # Data models
|-- static/                # CSS assets
`-- templates/             # Flask HTML templates
```

## What the App Does

The app loads account and deal records, calculates operational signals, and exposes them through a simple dashboard and API.

Core workflows include:

1. Prospecting: ranks accounts by fit and recommends a multi-touch outreach sequence.
2. Deal inspection: highlights at-risk deals and suggests recovery actions.
3. Retention monitoring: identifies customers showing churn or adoption risk.
4. Competitive support: generates battlecard-style positioning for risky opportunities.

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

Then update it with your preferred provider keys if you want real AI-generated responses.

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

Open:

```text
http://127.0.0.1:5000
```

## AI Provider Behavior

The app checks providers in this order:

1. Gemini
2. OpenAI
3. Built-in fallback content

If `GEMINI_API_KEY` is set, Gemini is used first.

If Gemini is not configured and `OPENAI_API_KEY` is set, OpenAI is used.

If neither provider is available, the application still works and returns deterministic fallback messaging for outreach and recovery play generation.

## API Endpoints

### Read endpoints

- `GET /`
- `GET /api/overview`
- `GET /api/prospects`
- `GET /api/deals`
- `GET /api/retention`
- `GET /api/competitive`

### Generation endpoints

- `POST /api/generate/outreach/<account_name>`
- `POST /api/generate/recovery/<account_name>`

### Import endpoint

- `POST /api/import/crm`

The import endpoint expects both uploaded files:

- `accounts_csv`
- `deals_csv`

## Sample Data

The repository includes sample data in:

- `sample_data/accounts.csv`
- `sample_data/deals.csv`

You can use those files directly in the import flow or as a template for your own CRM exports.

## CSV Import Notes

The importer expects structured columns for account, contact, engagement, and deal metadata. Multi-value fields are split using the `|` character.

Examples:

- `tech_stack`: `Salesforce|HubSpot|Snowflake`
- `pain_points`: `slow lead routing|poor forecast visibility`
- `stakeholders`: `CRO|Procurement|Sales Director`

## Development Notes

- `app.py` uses `load_dotenv()`, so local `.env` values are loaded automatically.
- `main.py` runs the Flask app in debug mode for local development.
- The current implementation stores data in memory, so imported CRM data resets when the app restarts.

## Use Cases

- Hackathon demo for AI in sales operations
- Prototype for a RevOps copilot
- Starter project for CRM insight automation
- Demo app for AI-generated sales messaging and pipeline intelligence

## Limitations

- No database persistence
- No authentication
- No background jobs or async processing
- AI output quality depends on the configured provider and model
- CSV import assumes the expected schema is present

## License

Add your preferred license before publishing or distributing the project.
