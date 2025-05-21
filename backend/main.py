import json
from scraper import scrape_user

with open("frontend/users.json") as f:
    users = json.load(f)

global_has_changes = False

for i, user in enumerate(users):
    if i > 0 and not global_has_changes:
        print("⏭ No changes for first user — skipping remaining users.")
        break

    has_changes = scrape_user(user, i)

    if i == 0:
        global_has_changes = has_changes
