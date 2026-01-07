import json
import requests
from bs4 import BeautifulSoup
import sys
import re

CONTEST_DURATION = 300  # minutes (5 hours)
FREEZE_TIME = 240       # minutes (4 hours)

def parse_nerc(url):
    print(f"Fetching {url} ...")
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if not table:
        raise RuntimeError("No scoreboard table found")

    rows = table.find_all("tr", class_=re.compile("^row"))
    if not rows:
        raise RuntimeError("No team rows found")

    # ------------------------------------
    # Infer problem count
    # ------------------------------------
    first_cells = rows[0].find_all("td")
    PROBLEM_START = 2
    PROBLEM_END = len(first_cells) - 3
    problem_count = PROBLEM_END - PROBLEM_START
    problems = [chr(ord("A") + i) for i in range(problem_count)]

    teams = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < PROBLEM_END:
            continue

        # ------------------------------------
        # Team name / university
        # ------------------------------------
        raw_team = cells[1].get_text(" ", strip=True)

        if ":" in raw_team:
            team_name = raw_team
            university, _ = raw_team.split(":", 1)
            university = university.strip()
        else:
            team_name = raw_team
            university = raw_team

        submissions = {}

        # ------------------------------------
        # Parse problems
        # ------------------------------------
        for i, prob in enumerate(problems):
            cell = cells[PROBLEM_START + i]
            text = cell.get_text(" ", strip=True)

            if text == ".":
                continue

            i_tag = cell.find("i")
            if not i_tag:
                continue

            # -------- tries --------
            # "+", "+1", "+2", ...
            m = re.match(r"\+(\d*)", i_tag.contents[0].strip())
            if not m:
                continue

            wrong = int(m.group(1)) if m.group(1) else 0
            tries = wrong + 1

            # -------- time (minutes only) --------
            s_tag = cell.find("s")
            if not s_tag:
                continue

            tm = re.search(r"(\d+):(\d+)", s_tag.text)
            if not tm:
                continue

            time_minutes = int(tm.group(1))
            time_seconds = int(tm.group(2))

            is_first = "first-to-solve" in i_tag.get("class", [])

            submissions[prob] = {
                "time": time_minutes * 60 + time_seconds,
                "tries": tries,
                **({"first": True} if is_first else {})
            }

        teams.append({
            "name": team_name,
            "university": university,
            "logo": "",
            "submissions": submissions
        })

    return {
        "name": "NERC 2024",
        "duration": CONTEST_DURATION * 60,
        "freeze": FREEZE_TIME * 60,
        "problems": problems,
        "teams": teams
    }

# ----------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python nerc_to_replay_json.py <url> <output.json>")
        sys.exit(1)

    url = sys.argv[1]
    outfile = sys.argv[2]

    data = parse_nerc(url)

    with open(outfile, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved replay JSON to {outfile}")
