import csv
import re
import dns.resolver
from concurrent.futures import ThreadPoolExecutor, as_completed

# === CONFIG ===
INPUT_FILE = "master-list-all.csv"
OUTPUT_FILE = "master-list-all_checked.csv"
THREADS = 50  # Adjust depending on your internet speed & DNS server limits

# Popular domains to skip MX check for
SKIP_MX_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "live.com", "icloud.com", "msn.com", "protonmail.com", "gmx.com",
    "yandex.com", "mail.com", "zoho.com"
}

# Regex for basic email syntax validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Cache for already checked domains
domain_cache = {}

def is_valid_syntax(email):
    return EMAIL_REGEX.match(email) is not None

def has_mx_record(domain):
    """Check if domain has MX record (cached)."""
    if domain in domain_cache:
        return domain_cache[domain]
    try:
        dns.resolver.resolve(domain, 'MX')
        domain_cache[domain] = True
    except:
        domain_cache[domain] = False
    return domain_cache[domain]

def process_row(row):
    """Process a single CSV row and return updated row with results."""
    email = row[1].strip()  # Email is in 2nd column
    syntax_ok = is_valid_syntax(email)

    if not syntax_ok:
        return row + [email, False, False, "Invalid Syntax"]

    domain = email.split("@")[-1].lower()

    # Skip MX check for common free email domains
    if domain in SKIP_MX_DOMAINS:
        mx_ok = True
    else:
        mx_ok = has_mx_record(domain)

    status = "Valid" if (syntax_ok and mx_ok) else "Invalid Domain"
    return row + ["", syntax_ok, mx_ok, status]

def process_file():
    results = []
    
    with open(INPUT_FILE, newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        header = next(reader)

        # Append our new columns
        new_header = header + ["Invalid Email", "syntax_ok", "mx_ok", "status"]
        results.append(new_header)

        # Use multithreading for faster domain checks
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = {executor.submit(process_row, row): row for row in reader}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    row = futures[future]
                    results.append(row + [row[1], False, False, f"Error: {e}"])

    # Save results
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerows(results)

    print(f"✅ Done! Processed file saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_file()
