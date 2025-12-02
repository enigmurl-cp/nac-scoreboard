import requests
from bs4 import BeautifulSoup
import json
import re
import sys

def min_to_sec(min_str):
    if not min_str or min_str == "-" or "min" not in min_str:
        return None
    m = int(min_str.replace("min","").strip())
    return m * 60

def parse_kattis_standings(url):
    print(f"Fetching {url} ...")
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", class_="standings-table")
    if not table:
        print("ERROR: Could not find standings table.")
        sys.exit(1)

    rows = table.find("tbody").find_all("tr")

    problems_count = None
    teams = []

    for row in rows:
        cells = row.find_all("td")

        if not cells:
            continue

        rank = int(cells[0].text.strip())
        team_name = cells[1].get_text(" ", strip=True)
        university = team_name  # Kattis doesn't include clean affiliation
        solved = int(cells[3].text.strip())
        penalty = int(cells[4].text.strip())

        # the problem columns start at index 5
        problem_cells = cells[5:]

        if problems_count is None:
            problems_count = len(problem_cells)

        submissions = {}

        for idx, pc in enumerate(problem_cells):
            prob_letter = chr(ord("A") + idx)

            span = pc.find("span")
            if not span:
                continue

            # Check if solved
            is_solved = "solved" in span.get("class", []) or "first" in span.get("class", [])

            if not is_solved:
                continue

            # Tries
            tries_el = pc.find("span", class_="standings-table-result-cell-primary")
            time_el = pc.find("span", class_="standings-table-result-cell-time")

            if not tries_el or not time_el:
                continue

            tries = int(tries_el.text.strip())
            timestr = time_el.text.strip()
            time_sec = min_to_sec(timestr)

            if time_sec is None:
                continue  # invalid / ---

            is_first = "first" in span.get("class", [])

            submissions[prob_letter] = {
                "tries": tries,
                "time": time_sec,
                "first": is_first
            }

        teams.append({
            "name": team_name,
            "university": university,
            "submissions": submissions
        })

    problems = [chr(ord("A") + i) for i in range(problems_count)]

    result = {
        "duration": 5 * 3600,   # Kattis NAC uses 5 hr contest
        "freeze": 4 * 3600,   # Kattis NAC uses 5 hr contest
        "problems": problems,
        "teams": teams
    }

    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python kattis_to_replay_json.py <kattis-standings-url> <output.json>")
        sys.exit(1)

    url = sys.argv[1]
    out = sys.argv[2]

    data = parse_kattis_standings(url)

    with open(out, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved replay JSON to {out}")
