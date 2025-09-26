# pythonlodz.org

Repo for keeping the source code of our official website

## Roadmap

- Upcoming event on main page
- CFP page with form https://forms.gle/HzXsBTu9DFi4mUAx8
- How to find us tutorial page (https://www.youtube.com/watch?v=Eeyk2EG6Xto)
- Own meetup signups (without third-party pages like meetup.com)

## How to run the website locally

1. [Install Hugo](https://gohugo.io/installation/).
2. Clone this repository.
3. On new clone and when there are submodule updates:

   ```
   git submodule update --init --depth 1
   ```

4. Run the Hugo development server:

   ```
   cd page
   hugo server
   ```

5. Open http://127.0.0.1:1313.

## Python Łódź Meetup Management CLI

This repository includes a Python CLI tool (`pyldz`) for managing meetup data and generating Hugo content from Google Sheets.

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Sheets API credentials (`.client_secret.json`)

### Installation

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Set up Google Sheets API credentials:

   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Google Sheets API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials file as `.client_secret.json` in the project root

3. Configure environment variables in `.env`:
   ```bash
   GOOGLE_SHEETS__SHEET_ID=your_google_sheets_id_here
   ```

### Usage

The CLI provides two main commands:

#### 1. Dry Run - Preview Meetup Data

Display meetup data from Google Sheets without generating any files:

```bash
uv run pyldz dry-run
```

This command will:

- Fetch all enabled meetups from Google Sheets
- Display meetup information including talks, speakers, and sponsors
- Show language information for English talks
- Useful for verifying data before generating Hugo content

#### 2. Fill Hugo - Generate Hugo Content

Generate Hugo markdown files for meetups:

```bash
# Generate to default directory (page/)
uv run pyldz fill-hugo

# Generate to custom directory
uv run pyldz fill-hugo --output-dir /path/to/hugo/site
```

This command will:

- Fetch meetup data from Google Sheets
- Generate markdown files in `content/spotkania/{meetup_id}/index.md`
- Create featured images using Hugo templates
- Include frontmatter with meetup metadata
- Generate content sections for talks, speakers, and sponsors

#### Command Help

Get help for any command:

```bash
# General help
uv run pyldz --help

# Command-specific help
uv run pyldz dry-run --help
uv run pyldz fill-hugo --help
```

### Development

#### Running Tests

```bash
# Run all tests
uv run pytest

# Run CLI tests only
uv run pytest tests/test_cli.py

# Run with verbose output
uv run pytest -v
```

#### Code Quality

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type checking
uv run mypy src/
```

### Project Structure

```
├── src/pyldz/           # Python source code
│   ├── main.py          # CLI entry point with typer commands
│   ├── config.py        # Configuration management
│   ├── meetup.py        # Meetup data models and Google Sheets integration
│   └── hugo_generator.py # Hugo content generation
├── tests/               # Test suite
├── page/                # Hugo site files
│   ├── content/         # Hugo content
│   ├── layouts/         # Hugo templates
│   └── assets/          # Static assets
└── pyproject.toml       # Project configuration
```

### Featured Images

The CLI generates featured images for meetups using the Hugo template located at:
`page/layouts/partials/infographic-image-duo.html`

These images are automatically created when running the `fill-hugo` command and saved as `featured.png` in each meetup's directory.

### Optional Fields

The meetup data supports optional fields:

- `feedback_url`: URL for meetup feedback (optional)
- `livestream_id`: ID for livestream integration (optional)

When these fields are provided in the Google Sheets data, they will be included in the generated Hugo content.
