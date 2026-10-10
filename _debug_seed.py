"""Quick debug: check seed data for duplicate emails and count totals."""
import re
from collections import Counter

with open("database/seed.py", encoding="utf-8") as f:
    src = f.read()

parts = src.split("creators_raw = [")
after_creators = parts[1].split("]", 1)[0]
creator_emails = re.findall(r'email="([^"]+)"', after_creators)

brands_part = src.split("brands_raw = [")[1].split("]", 1)[0]
brand_emails = re.findall(r'email="([^"]+)"', brands_part)

print("Creator count:", len(creator_emails))
print("Brand count:", len(brand_emails))
print("Creator emails:")
for i, e in enumerate(creator_emails):
    print(f"  [{i}] {e}")
print("Brand emails:")
for i, e in enumerate(brand_emails):
    print(f"  [{i}] {e}")
all_emails = creator_emails + brand_emails
dupes = [(e, c) for e, c in Counter(all_emails).items() if c > 1]
print("Duplicates:", dupes)
