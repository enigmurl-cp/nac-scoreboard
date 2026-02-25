
import json
from bs4 import BeautifulSoup
import sys
import re

CONTEST_DURATION = 300 * 60
FREEZE_TIME = 240 * 60

def parse_naipc_2016_from_file(path):
    html = open(path, "r", encoding="utf-8").read()
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", id="standings")
    if not table:
        raise RuntimeError("standings table not found")

    # ---- extract problems from SECOND header row ----
    thead = table.find("thead")
    header_rows = thead.find_all("tr")
    # if len(header_rows) < 2:
    #     raise RuntimeError("unexpected header structure")

    problem_headers = header_rows[0].find_all("th")
    problems = [th.get_text(strip=True) for th in problem_headers]

    teams = []

    tbody = table.find("tbody")
    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 4 + len(problems):
            continue

        # ---- team info ----
        team_cell = cells[1]
        parts = list(team_cell.stripped_strings)
        team_name = parts[0]
        university = parts[1] if len(parts) > 1 else team_name

        submissions = {}

        # ---- problem cells ----
        prob_cells = cells[4 : 4 + len(problems)]

        for prob, cell in zip(problems, prob_cells):
            text = cell.get_text(strip=True)

            if not text or text == ".":
                continue

            # formats: "+2 123", "+ 45", "+0 7"
            m = re.match(r"\+(\d*)\s*(\d+)", text)
            if not m:
                continue

            wrong = int(m.group(1)) if m.group(1) else 0
            tries = wrong + 1
            time_minutes = int(m.group(2))

            submissions[prob] = {
                "time": time_minutes * 60,
                "tries": tries
            }

        teams.append({
            "name": team_name,
            "university": university,
            "submissions": submissions
        })

    return {
        "name": "NAIPC 2016",
        "duration": CONTEST_DURATION,
        "freeze": FREEZE_TIME,
        "problems": problems,
        "teams": teams
    }

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python naipc2016.py naipc16.txt out.json")
        sys.exit(1)

    data = parse_naipc_2016_from_file(sys.argv[1])

    with open(sys.argv[2], "w") as f:
        json.dump(data, f, indent=2)

    print("done")
