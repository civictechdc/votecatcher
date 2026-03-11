# Votecatcher User Guide

## Overview

Votecatcher automates petition signature verification using LLM-based OCR and fuzzy matching. It reduces manual verification from hours to minutes by extracting handwritten text from scanned petitions and matching it against official voter registration lists.

## Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- OR: Python 3.12+ and Node.js 20+ for local development
- At least one LLM provider API key (OpenAI, Gemini, or Mistral)

### Running with Docker Compose

```bash
# Clone the repository
git clone https://github.com/your-org/votecatcher.git
cd votecatcher

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...
# MISTRAL_API_KEY=...

# Start all services
docker-compose up -d

# Access the application
open http://localhost:5173
```

### Running Locally (Development)

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your settings
uv sync
uv run fastapi dev

# Frontend (in another terminal)
cd frontend-svelt
cp .env.example .env
bun install
bun run dev

# Access the application
open http://localhost:5173
```

## Core Workflow

### 1. Create a Campaign

A campaign represents an election effort (e.g., "DC Mayor 2024").

1. Navigate to **Campaigns** in the sidebar
2. Click **Create Campaign**
3. Enter campaign name and year
4. Click **Create**

### 2. Upload Voter Registration List

Upload the official voter registration data for your region.

1. Navigate to **Upload** → **Voter List**
2. Select your campaign
3. Upload a CSV or Excel file with voter data
4. Required columns: `first_name`, `last_name`, `address`, `zipcode` (optional: `ward`, `precinct`)
5. Click **Upload**

**Supported formats:**
- CSV (comma-separated)
- Excel (.xlsx, .xls)

**Maximum file size:** 50MB

### 3. Upload Petition Scans

Upload scanned petition PDFs. The system will automatically crop individual signatures.

1. Navigate to **Upload** → **Petitions**
2. Select your campaign
3. Upload one or more PDF files
4. The system pre-crops each signature entry
5. Click **Upload**

**Note:** For the DC region preset, the system uses predefined crop coordinates.

### 4. Run OCR and Matching

Create a matching job to process your petitions.

1. Navigate to **Jobs**
2. Click **Create Job**
3. Select your campaign and petition scans
4. Choose an OCR provider (OpenAI, Gemini, or Mistral)
5. Click **Start Job**

The job will:
1. Submit images to the OCR provider (batch API)
2. Poll for completion
3. Run fuzzy matching against the voter list
4. Generate confidence-scored results

**Progress tracking:** Watch real-time status updates on the Jobs page.

### 5. Review Results

Review and verify matched signatures.

1. Navigate to **Results**
2. Filter by confidence level:
   - **HIGH** (≥85%): Very likely correct match
   - **MEDIUM** (60-84%): Needs review
   - **LOW** (<60%): Likely incorrect, manual verification needed
3. Compare OCR-extracted text with registered voter data
4. Export results to CSV for further analysis

### 6. Export and Report

Export your verified results for reporting.

1. On the Results page, click **Export CSV**
2. The file includes:
   - OCR-extracted name and address
   - Matched voter record
   - Confidence score
   - Petition page and row numbers

## Features

### Confidence Scoring

The system calculates match confidence using fuzzy string matching:

| Score | Level | Interpretation |
|-------|-------|----------------|
| ≥85%  | HIGH  | Very likely correct - minimal review needed |
| 60-84%| MEDIUM| Needs review - possible correct match |
| <60%  | LOW   | Likely incorrect - manual verification required |

**Note:** Confidence thresholds can be calibrated based on your specific use case.

### Session Management

Save your workspace state for later:

1. Navigate to **Sessions**
2. Click **Save Session**
3. Enter a name and description
4. Later, click **Load** to restore your workspace

**Export session:** Download a ZIP file with all data for backup or sharing.

### Demo Mode

Try the system with sample data:

1. Navigate to **Demo** in the sidebar
2. Click **Load DC Petition Demo**
3. The system loads a pre-baked session with sample petitions and results
4. Explore the full workflow without uploading your own data

**Reset demo:** Click **Reset Demo** to clear all data and start fresh.

## Keyboard Navigation

Votecatcher is fully keyboard-accessible:

| Action | Shortcut |
|--------|----------|
| Navigate sidebar | Tab / Shift+Tab |
| Activate link/button | Enter / Space |
| Close modal | Escape |
| Navigate tables | Arrow keys |

## Troubleshooting

### OCR Accuracy Issues

If OCR results are poor:
- Ensure petition scans are high resolution (300 DPI minimum)
- Check that handwriting is legible
- Try a different OCR provider
- Adjust lighting/contrast on scanned images

### Matching Performance

If matching is slow:
- Ensure database indexes are created
- Check that voter list has region/zipcode filters
- Consider splitting large voter lists by region

### API Errors

Common API issues:
- **401 Unauthorized:** Check your API key is correct
- **429 Rate Limited:** Wait and retry, or upgrade your API plan
- **500 Server Error:** Check backend logs for details

### Database Issues

If you encounter database errors:
```bash
# Reset database (development only!)
cd backend
uv run alembic downgrade base
uv run alembic upgrade head
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./votecatcher.db` |
| `OPENAI_API_KEY` | OpenAI API key | Required for OpenAI OCR |
| `GEMINI_API_KEY` | Google Gemini API key | Required for Gemini OCR |
| `MISTRAL_API_KEY` | Mistral API key | Required for Mistral OCR |
| `DEMO_MODE` | Enable demo features | `false` |
| `DEMO_RESET` | Allow demo data reset | `false` |

### Feature Flags

| Flag | Description |
|------|-------------|
| `demo_mode` | Enable demo mode features |
| `demo_reset` | Allow resetting demo data |
| `load_prebaked_results` | Skip OCR/matching, load pre-computed results |
| `debug_logging` | Enable verbose logging |

## Support

- **Documentation:** [docs/](../docs/)
- **Issues:** [GitHub Issues](https://github.com/your-org/votecatcher/issues)
- **API Reference:** [http://localhost:8000/docs](http://localhost:8000/docs) (when running locally)

## License

MIT License - see [LICENSE](../LICENSE) for details.
