# lunch2confluence

`lunch2confluence` is a small Python automation project that fetches lunch menus from selected restaurants and publishes them to a Confluence Cloud page.

The project was originally built around restaurants in Vienna's 1st district, but the structure is generic enough to add other restaurants later.

## Features

- Fetch lunch menus from restaurant websites
- Support multiple source types:
  - HTML pages
  - PDF menus
  - Future: image/OCR menus
- Normalize all restaurant menus into one shared data model
- Generate a readable Confluence page
- Publish automatically via the Confluence Cloud REST API
- Run locally or through GitHub Actions
- Use GitHub Secrets for Confluence credentials
- Continue publishing even if one restaurant fails

## Current Restaurants

Currently supported:

- WRENKH
- Wienerin

Planned / possible:

- Sparky's
- Other nearby restaurants

## Important Files

### `src/main.py`

Local preview entry point.

Use this when you want to generate the lunch menu output locally without updating Confluence.

```bash
python -m src.main
```

This creates:

```text
lunch_menus.html
```

This command does **not** update Confluence.

### `src/publish.py`

Publishing entry point.

Use this when you want to update Confluence.

```bash
python -m src.publish
```

GitHub Actions also uses this command.

### `src/menu_builder.py`

Shared logic for:

- deciding which restaurants are enabled
- running restaurant parsers safely
- collecting errors
- building the final Confluence page content

### `src/restaurants/registry.py`

Central place where active restaurants are registered.

If a parser is not listed here, it will not be used.

### `src/restaurants/_template.py`

Template for adding new restaurant parsers.

Copy this file when creating a new parser.

### `src/formatter.py`

Formats normalized restaurant menu data into Confluence-friendly HTML.

### `src/confluence_client.py`

Handles reading and updating the Confluence page through the Confluence Cloud REST API.

## Requirements

- Python 3.13 recommended
- Confluence Cloud page
- Atlassian API token
- GitHub repository secrets if running via GitHub Actions

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/AllUsernamesWereGone/lunch2confluence.git
cd lunch2confluence
```

### 2. Create a virtual environment

On Windows Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Run local preview

```bash
python -m src.main
```

This should generate:

```text
lunch_menus.html
```

This command does not update Confluence.

## Confluence Setup

### 1. Create a Confluence test page

Create a page in Confluence, for example:

```text
Lunch Tests
```

Restrict the page if needed.

### 2. Find the page ID

A Confluence page URL usually looks like this:

```text
https://your-company.atlassian.net/wiki/spaces/SPACE/pages/123456789/Page+Title
```

The page ID is:

```text
123456789
```

### 3. Create an Atlassian API token

Create an API token in your Atlassian account settings.

You will need:

```text
CONFLUENCE_BASE_URL
CONFLUENCE_EMAIL
CONFLUENCE_API_TOKEN
CONFLUENCE_PAGE_ID
```

Example base URL:

```text
https://your-company.atlassian.net/wiki
```

## Environment Variables

Create a local `.env` file in the project root.

```env
CONFLUENCE_BASE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_EMAIL=your.email@company.com
CONFLUENCE_API_TOKEN=your-api-token
CONFLUENCE_PAGE_ID=123456789
```

Never commit `.env`.

The repository should only contain `.env.example`.

## `.env.example`

Example:

```env
CONFLUENCE_BASE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_EMAIL=your.email@company.com
CONFLUENCE_API_TOKEN=your-api-token-here
CONFLUENCE_PAGE_ID=123456789
ENABLED_RESTAURANTS=wienerin,wrenkh
```

## Publishing Locally

After creating `.env`, run:

```bash
python -m src.publish
```

This will:

1. Fetch the restaurant menus
2. Format the Confluence page
3. Update the configured Confluence page

## GitHub Actions Setup

The project can publish automatically through GitHub Actions.

### Required Repository Secrets

In GitHub:

```text
Repository
→ Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

Create these secrets:

```text
CONFLUENCE_BASE_URL
CONFLUENCE_EMAIL
CONFLUENCE_API_TOKEN
CONFLUENCE_PAGE_ID
```

Optional:

```text
ENABLED_RESTAURANTS
```

Example:

```text
ENABLED_RESTAURANTS=wienerin,wrenkh
```

If `ENABLED_RESTAURANTS` is not set, all registered restaurants are enabled by default.

## GitHub Actions Workflow

The workflow file is located at:

```text
.github/workflows/daily.yml
```

The workflow can be triggered manually or on a schedule.

Manual trigger:

```text
GitHub → Actions → Publish Lunch Menus → Run workflow
```

Scheduled trigger example:

```yaml
schedule:
  - cron: "0 8 * * 1-5"
```

This runs Monday to Friday at 08:00 UTC.

Note: GitHub Actions cron schedules use UTC, not local Vienna time.


## Enabling / Disabling Restaurants

Restaurants are controlled through:

```text
src/restaurants/registry.py
```

Example:

```python
AVAILABLE_RESTAURANTS = {
    "wrenkh": {
        "display_name": "WRENKH",
        "parser": parse_wrenkh_menu,
    },
    "wienerin": {
        "display_name": "Wienerin",
        "parser": parse_wienerin_menu,
    },
}
```

You can also restrict which restaurants run using the environment variable:

```env
ENABLED_RESTAURANTS=wienerin,wrenkh
```

This is useful if one restaurant is temporarily broken or unreachable from GitHub Actions.

Example GitHub Actions setting:

```yaml
env:
  ENABLED_RESTAURANTS: wienerin
```

## Data Model

The shared data model is defined in:

```text
src/models.py
```

High-level structure:

```text
RestaurantMenu
├── Restaurant
├── menu_type
├── week_range_text
├── price_text
├── serving_time
├── current_day
├── days
│   ├── MO
│   ├── DI
│   ├── MI
│   ├── DO
│   └── FR
└── meta
```

Each menu item supports:

```text
name
description
price
tags
```

## Running Tests

Install test dependencies from `requirements.txt`, then run:

```bash
python -m pytest
```

Note:

Some tests may access live restaurant websites. If a restaurant website is down or blocks GitHub-hosted runners, live tests may fail even if the code is correct.


## License

```text
MIT License
```
