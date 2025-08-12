# Bulk Email Validator

Bulk Email Validator is a **high-performance, multi-threaded** Python script to validate large lists of email addresses from a CSV file.

It checks:
- ✅ **Syntax** — ensures emails follow the correct format.
- ✅ **MX Records** — ensures the email domain can receive mail.
- ✅ **Popular Free Domains** (Gmail, Yahoo, etc.) are automatically marked as MX-valid without DNS checks.

## Features
- **Multi-threaded processing** — Handles large files (400K+ records) quickly.
- **Keeps all original CSV fields** — Adds `syntax_ok`, `mx_ok`, and `status` columns.
- **Splits results** — Saves `valid_results.csv` and `invalid_results.csv`.

## CSV Format
Your CSV should have the following headers:
```
Name,Email,Record Label,First Name,Last Name,Phone,Company,Address line 1,Address line 2,City,State / County,Zipcode / Postcode,Country / Region
```

## Installation
```bash
git clone https://github.com/yourusername/bulk-email-validator.git
cd bulk-email-validator
pip install -r requirements.txt
```

## Usage
```bash
python check_emails_split.py yourfile.csv
```

The script will create:
- `valid_results.csv` — all checks passed
- `invalid_results.csv` — one or more checks failed

## License
This project is licensed under the MIT License.
