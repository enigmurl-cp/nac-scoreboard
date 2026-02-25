import json
import requests
from bs4 import BeautifulSoup
import sys
import re

def min_to_sec(m):
    return int(float(m) * 60)

def parse_domjudge(url):
    print(f"Fetching {url} ...")
    with open("inner.html") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    rows = soup.find_all("tr", attrs={"data-team-id": True})
    if not rows:
        print("ERROR: No DOMjudge rows found.")
        sys.exit(1)

    teams = []
    problems_count = None

    for row in rows:
        print(f"Processing row with team-id={row.get('data-team-id')} ...")

        # Rank
        rank_td = row.find("td", class_="scorepl")
        if not rank_td:
            continue
        rank_text = rank_td.get_text(strip=True)
        if not rank_text.isdigit():
            continue
        rank = int(rank_text)

        # Team name
        team_td = row.find("td", class_="scoretn")
        if not team_td:
            continue
        team_name = team_td.get_text(" ", strip=True)
        if "Pre-qualified" in team_name:
            team_name = team_name[team_name.index("Pre-qualified") + len("Pre-qualified"):].strip()

        university = team_name

        # Problem cells (NEW: explicit selector)
        problem_cells = row.find_all("td", class_="score_cell")

        if problems_count is None:
            problems_count = len(problem_cells)

        submissions = {}

        for idx, pc in enumerate(problem_cells):
            prob_letter = chr(ord("A") + idx)

            div = pc.find("div")
            if not div:
                continue

            classes = div.get("class", [])

            # Skip incorrect-only cells
            if "score_incorrect" in classes:
                continue

            # Accept correct / first solve
            if "score_correct" not in classes and "score_first" not in classes:
                continue

            # Time (minutes)
            time_text = div.contents[0].strip()
            if not time_text.isdigit():
                continue

            time_sec = min_to_sec(time_text)

            # Tries
            span = div.find("span")
            if not span:
                continue

            m = re.search(r"(\d+)\s+tr", span.get_text(strip=True))
            if not m:
                continue

            tries = int(m.group(1))
            is_first = "score_first" in classes

            submissions[prob_letter] = {
                "time": time_sec,
                "tries": tries,
                "first": is_first
            }

        teams.append({
            "name": team_name,
            "university": university,
            "submissions": submissions
        })

    problems = [chr(ord("A") + i) for i in range(problems_count)]

    return {
        "duration": 5 * 3600,
        "freeze": 4 * 3600,
        "problems": problems,
        "teams": teams
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python domjudge_to_replay_json.py <domjudge-scoreboard-url> <output.json>")
        sys.exit(1)

    url = sys.argv[1]
    outfile = sys.argv[2]

    data = parse_domjudge(url)

    with open(outfile, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved replay JSON to {outfile}")
