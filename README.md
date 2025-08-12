# Bulk Email Validator

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)
![Contributions](https://img.shields.io/badge/contributions-welcome-orange)

Bulk Email Validator is a **high-performance, multi-threaded** Python script to validate large lists of email addresses from a CSV file.

It checks:
- ✅ **Syntax** — ensures emails follow the correct format.
- ✅ **MX Records** — ensures the email domain can receive mail.
- ✅ **Popular Free Domains** (Gmail, Yahoo, etc.) are automatically marked as MX-valid without DNS checks.

## ✨ Features

- ✅ **Syntax validation** using a robust regex pattern.
- 📬 **MX record lookup** to confirm if domains can receive mail.
- 🚀 **Multi-threaded** processing with adjustable worker count.
- 🛡 **Domain cache** to avoid duplicate lookups.
- ⏭ **Skip MX checks** for popular free email providers (Gmail, Yahoo, Outlook, etc.).
- 📂 **Keeps all original CSV columns** and appends:
  - `Invalid Email` → original email (only for invalid syntax)
  - `syntax_ok` → True/False
  - `mx_ok` → True/False
  - `status` → Valid, Invalid Syntax, Invalid Domain, or Error
- 📤 **Two output CSVs**:
  - `emails_good.csv` — fully valid entries
  - `emails_bad.csv` — failed syntax, domain, or DNS checks
- 💾 **Streams output** for memory efficiency with large datasets (400K+ rows supported).

## 📂 Example Input CSV

| Name       | Email                | Record Label | First Name | Last Name | Phone     | Company | Address line 1 | Address line 2 | City    | State / County | Zipcode / Postcode | Country / Region |
|------------|----------------------|--------------|------------|-----------|-----------|---------|----------------|----------------|---------|----------------|--------------------|------------------|
| John Doe   | john@example.com      | A1           | John       | Doe       | 123456789 | ABC Inc | Street 1       | Apt 2          | NY      | NY State       | 12345              | USA              |
| Jane Smith | jane@fake-domain.tld  | B2           | Jane       | Smith     | 987654321 | XYZ LLC | Street 2       | Suite 3        | LA      | California     | 90001              | USA              |

---

## 📂 Example Output (emails_good.csv)

| Name       | Email                | Record Label | First Name | Last Name | Phone     | Company | Address line 1 | Address line 2 | City    | State / County | Zipcode / Postcode | Country / Region | Invalid Email | syntax_ok | mx_ok | status |
|------------|----------------------|--------------|------------|-----------|-----------|---------|----------------|----------------|---------|----------------|--------------------|------------------|---------------|-----------|-------|--------|
| John Doe   | john@example.com      | A1           | John       | Doe       | 123456789 | ABC Inc | Street 1       | Apt 2          | NY      | NY State       | 12345              | USA              |               | True      | True  | Valid  |

---

## 📂 Example Output (emails_bad.csv)

| Name       | Email                | Record Label | First Name | Last Name | Phone     | Company | Address line 1 | Address line 2 | City    | State / County | Zipcode / Postcode | Country / Region | Invalid Email       | syntax_ok | mx_ok | status         |
|------------|----------------------|--------------|------------|-----------|-----------|---------|----------------|----------------|---------|----------------|--------------------|------------------|---------------------|-----------|-------|----------------|
| Jane Smith | jane@fake-domain.tld  | B2           | Jane       | Smith     | 987654321 | XYZ LLC | Street 2       | Suite 3        | LA      | California     | 90001              | USA              |                     | True      | False | Invalid Domain |
| Foo Bar    | foo@invalid_email     | C3           | Foo        | Bar       | 555555555 | TestCo  | Test Street    |                | Miami   | Florida        | 33101              | USA              | foo@invalid_email   | False     | False | Invalid Syntax |

---

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

After processing, the script will create:
- ✅ `emails_good.csv` — contains fully valid emails
- ❌ `emails_bad.csv` — contains invalid syntax, invalid domains, or errors


## ⚡ Performance Tips
- Increase THREADS for faster MX lookups on good network connections.
- Keep THREADS lower if your DNS provider throttles requests.
- Large files (400K+ rows) are processed line-by-line — low memory usage.
- Common free email providers are whitelisted from MX checks to save time.

## 📝 Notes
- This script does not send emails — it only validates format and domain availability.
- MX record check verifies if the domain has mail servers, not if the specific mailbox exists.
- For full deliverability testing, use an SMTP handshake check (slower and riskier).

# 🤝 Contributing
Pull requests are welcome!
If you’d like to add new features (e.g., SMTP check, API integration for verification), fork the repo and submit a PR.

## ⭐ Support
If you find this project useful, please give it a ⭐ on GitHub — it helps others find it too!

## License
This project is licensed under the MIT License.
