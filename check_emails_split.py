#!/usr/bin/env python3
"""
check_emails_split.py

Reads INPUT_FILE (CSV), validates emails (syntax + MX check), and writes two CSVs:
 - GOOD_FILE : rows that passed both syntax and MX checks
 - BAD_FILE  : rows that failed either check (or had an error)

Outputs keep all original columns and append:
 ["Invalid Email", "syntax_ok", "mx_ok", "status"]

Requires: dnspython
    pip install dnspython
"""

import csv
import re
import dns.resolver
import concurrent.futures
import threading
import time
import sys

# ==================== CONFIG ====================
INPUT_FILE = "emails.csv"           # input CSV (must have header)
GOOD_FILE = "emails_good.csv"       # rows that are fully valid
BAD_FILE = "emails_bad.csv"         # rows with any check failure
THREADS = 50                        # number of worker threads for MX checks
MAX_IN_FLIGHT = 1000                # max pending futures to limit memory usage
DNS_TIMEOUT = 5.0                   # seconds per DNS resolve
PROGRESS_EVERY = 10000              # log progress every N processed rows
# =================================================

# Domains to skip MX check for (treat as mx_ok=True)
SKIP_MX_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "live.com", "icloud.com", "msn.com", "protonmail.com", "gmx.com",
    "yandex.com", "mail.com", "zoho.com"
}

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

# thread-safe cache for domain MX checks
domain_cache = {}
cache_lock = threading.Lock()

# increase CSV field size limit a bit (avoid errors on huge fields)
try:
    csv.field_size_limit(2**20)
except Exception:
    pass


def is_valid_syntax(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))


def has_mx_record(domain: str) -> bool:
    """Thread-safe cached MX check with timeout."""
    # normalize domain
    domain = domain.strip().lower().rstrip(".")
    with cache_lock:
        if domain in domain_cache:
            return domain_cache[domain]

    try:
        # Using lifetime to limit total DNS time
        dns.resolver.resolve(domain, "MX", lifetime=DNS_TIMEOUT)
        ok = True
    except Exception:
        ok = False

    with cache_lock:
        domain_cache[domain] = ok
    return ok


def process_row(row, row_num):
    """
    Input:
      row: list (CSV row)
    Returns:
      list: original row + [Invalid Email, syntax_ok, mx_ok, status]
    Guarantees: never raises (catches exceptions and returns an error status)
    """
    # Defensive: if row is too short, pad so index 1 exists
    if len(row) <= 1:
        email = ""
    else:
        email = (row[1] or "").strip()

    # Default outputs
    invalid_email_col = ""
    syntax_ok = False
    mx_ok = False
    status = "Missing Email" if not email else "Invalid Syntax"

    try:
        if not email:
            # Missing or blank email
            return row + [invalid_email_col, False, False, status]

        # Syntax check
        syntax_ok = is_valid_syntax(email)
        if not syntax_ok:
            # As requested: write the email into the "Invalid Email" column
            invalid_email_col = email
            status = "Invalid Syntax"
            return row + [invalid_email_col, False, False, status]

        # Domain / MX check
        domain = email.split("@")[-1].lower().strip()
        if domain in SKIP_MX_DOMAINS:
            mx_ok = True
        else:
            mx_ok = has_mx_record(domain)

        status = "Valid" if (syntax_ok and mx_ok) else "Invalid Domain"
        return row + [invalid_email_col, syntax_ok, mx_ok, status]

    except Exception as exc:
        # Catch-all: don't let worker crash the pipeline. Include the email if available.
        invalid_email_col = email if not syntax_ok else ""
        status = f"Error: {type(exc).__name__}"
        return row + [invalid_email_col, syntax_ok, mx_ok, status]


def main():
    start_time = time.time()
    processed = 0
    submitted = 0

    # Open files. Use utf-8-sig for input to handle BOM if present.
    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as infile, \
         open(GOOD_FILE, "w", newline="", encoding="utf-8") as goodfile, \
         open(BAD_FILE, "w", newline="", encoding="utf-8") as badfile:

        reader = csv.reader(infile)
        # Read header (and preserve it). If no header exists, this still uses first row as header.
        try:
            header = next(reader)
        except StopIteration:
            print("Input file is empty.", file=sys.stderr)
            return

        # New header
        new_header = header + ["Invalid Email", "syntax_ok", "mx_ok", "status"]

        good_writer = csv.writer(goodfile)
        bad_writer = csv.writer(badfile)
        good_writer.writerow(new_header)
        bad_writer.writerow(new_header)

        # Thread pool for checks
        with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
            in_flight = set()

            for row_num, row in enumerate(reader, start=2):  # start=2 to account for header row
                future = executor.submit(process_row, row, row_num)
                in_flight.add(future)
                submitted += 1

                # If too many in-flight futures, wait for some to finish and write them out
                if len(in_flight) >= MAX_IN_FLIGHT:
                    done, not_done = concurrent.futures.wait(
                        in_flight, return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    for fut in done:
                        try:
                            out_row = fut.result()
                        except Exception as e:
                            # Shouldn't happen because process_row handles exceptions,
                            # but be defensive: create a minimal error row
                            out_row = [""] * len(header) + ["", False, False, f"FutureError: {e}"]

                        # Decide which file
                        status = out_row[-1]
                        if status == "Valid":
                            good_writer.writerow(out_row)
                        else:
                            bad_writer.writerow(out_row)

                        processed += 1

                    # continue with not_done set
                    in_flight = not_done

                    # occasional progress print
                    if processed % PROGRESS_EVERY < len(done):
                        print(f"[{time.strftime('%H:%M:%S')}] Submitted: {submitted}, Processed: {processed}")

            # All rows submitted. Now drain remaining futures.
            if in_flight:
                for fut in concurrent.futures.as_completed(in_flight):
                    try:
                        out_row = fut.result()
                    except Exception as e:
                        out_row = [""] * len(header) + ["", False, False, f"FutureError: {e}"]
                    status = out_row[-1]
                    if status == "Valid":
                        good_writer.writerow(out_row)
                    else:
                        bad_writer.writerow(out_row)
                    processed += 1

    elapsed = time.time() - start_time
    print("Done.")
    print(f" Input:  {INPUT_FILE}")
    print(f" Good:   {GOOD_FILE}   (passed both checks)")
    print(f" Bad:    {BAD_FILE}   (invalid syntax, invalid domain, or errors)")
    print(f" Submitted rows: {submitted}, Processed rows: {processed}")
    print(f" Time elapsed: {elapsed:.1f}s")
    print(f" Domain cache size: {len(domain_cache)}")


if __name__ == "__main__":
    main()
