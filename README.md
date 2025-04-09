# Website Logo Scraper

A Python tool for automatically scraping and extracting logo images from websites.

## Features

- Extracts logo images from websites using various detection methods
- Processes multiple websites concurrently to improve efficiency
- Uses intelligent heuristics to identify the most likely logo candidate
- Provides comprehensive logging and progress tracking
- Randomized delays and user agents to avoid rate limiting

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The script requires an input CSV file with a column named `website` containing the URLs to scrape.

### Basic Usage

```bash
python logo_scraper.py --input websites.csv --output logos.csv
```

### Command-line Arguments

- `--input`, `-i`: Input CSV file with websites (default: `websites.csv`)
- `--output`, `-o`: Output CSV file for logo URLs (default: `logos.csv`)
- `--workers`, `-w`: Number of worker threads (default: `5`)
- `--delay`, `-d`: Delay between requests in seconds (default: `1.0`)
- `--timeout`, `-t`: Request timeout in seconds (default: `10`)

### Example

```bash
python logo_scraper.py --input companies.csv --output company_logos.csv --workers 10 --delay 2 --timeout 15
```

## Input Format

The input CSV file should contain a column named `website` with the URLs to scrape:

```csv
website
example.com
google.com
github.com
```

## Output Format

The script outputs a CSV file with the following columns:

- `website`: The original website URL
- `logo_url`: The URL of the extracted logo (if found)
- `status`: The status of the extraction (`success`, `no logo found`, or an error message)

## How It Works

The logo scraper uses multiple methods to identify logo images:

1. Looks for images with "logo" in their URL, class name, ID, or alt text
2. Checks for images positioned in header elements or as home page links
3. Examines SVG elements with "logo" in their class names
4. Checks for meta tags with OpenGraph images
5. Looks for favicon and apple-touch-icon links

For each website, the script:

1. Sends an HTTP request with a random user agent
2. Parses the HTML content
3. Applies logo detection heuristics
4. Scores potential logo candidates
5. Returns the highest-scoring logo URL

## License

MIT
