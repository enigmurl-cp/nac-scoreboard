"""
Converts a BOCA HTML scoreboard to the replay JSON format.

Usage:
    python parse_boca.py <input.html> <output.json>

Notes:
- BOCA encodes problem results as colored balloon images.
  A solved problem cell contains an <img> tag (the balloon color).
  An attempted-but-unsolved cell contains only a text like "3/-" (tries/time with no time).
- The score format in each cell is: tries/time_in_minutes  e.g. "2/124" means 2 tries, accepted at minute 124.
  Cells with time "-" are failed attempts (no accepted solution).
- Each team appears multiple times (once per region group they belong to).
  We keep only rows with class "sitegroup1" which is the overall PdA ranking.
- Contest: ICPC Latin America Championship 2026
  Duration: 5 hours (18000 seconds)
  Freeze:   4 hours (14400 seconds)  — last hour frozen
"""

from bs4 import BeautifulSoup
import json
import sys
import re


DURATION = 18000   # 5 hours in seconds
FREEZE   = 14400   # 4 hours in seconds (freeze starts at 4h, last 1h frozen)


def parse_boca_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # Find the score table
    table = soup.find("table", id="myscoretable")
    if not table:
        raise ValueError("Could not find score table with id='myscoretable'")

    # Determine problem letters from header row
    header_row = table.find("tr")
    header_cells = header_row.find_all("td")
    # Header cells: #, User/Site, Name, A, B, C, ..., Total
    # Find the problem columns: cells between index 3 and last (Total)
    problems = []
    for cell in header_cells[3:-1]:
        letter = cell.get_text(strip=True).replace('\xa0', '').strip()
        if letter:
            problems.append(letter)

    seen_team_ids = set()
    teams = []

    all_rows = table.find("tbody").find_all("tr")

    for row in all_rows:
        # Only process rows in the overall ranking (sitegroup1)
        classes = row.get("class", [])
        if "sitegroup1" not in classes:
            continue

        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        # Team identifier: the link text inside the site cell (cell index 1)
        site_cell = cells[1]
        link = site_cell.find("a")
        team_id = link.get_text(strip=True) if link else site_cell.get_text(strip=True)
        team_id = team_id.strip()

        if team_id in seen_team_ids:
            continue
        seen_team_ids.add(team_id)

        # Team name: cell index 2 — grab text nodes before any <br> or <b> tag
        name_cell = cells[2]
        from bs4 import NavigableString
        raw_name = ""
        for content in name_cell.contents:
            if isinstance(content, NavigableString):
                raw_name += str(content)
            else:
                # Stop at the first tag (br, b, etc.)
                break
        team_name = raw_name.strip()
        if not team_name:
            # Fallback: first line of text
            team_name = name_cell.get_text(" ", strip=True).split("\n")[0].strip()

        # Parse university from brackets: e.g. "[UFMG] ooga booga" -> "UFMG"
        university = team_name
        m = re.match(r'\[([^\]]+)\]', team_name)
        if m:
            university = m.group(1)

        # Problem cells: indices 3 to 3+len(problems)-1
        submissions = {}
        prob_cells = cells[3 : 3 + len(problems)]

        for i, pc in enumerate(prob_cells):
            prob_letter = problems[i]

            # Check if there's a balloon image (= accepted)
            img = pc.find("img")
            text = pc.get_text(strip=True).replace('\xa0', '').strip()

            # Parse the "tries/time" text, e.g. "2/124" or "3/-"
            match = re.search(r'(\d+)/(-|\d+)', text)
            if not match:
                continue  # empty cell, no attempt

            tries = int(match.group(1))
            time_str = match.group(2)

            if img is None or time_str == "-":
                # Attempted but not solved (no balloon, or time is "-")
                continue

            time_min = int(time_str)
            time_sec = time_min * 60

            submissions[prob_letter] = {
                "tries": tries,
                "time": time_sec,
                "first": False   # BOCA HTML doesn't distinguish first-solve; set False
            }

        teams.append({
            "name": team_name,
            "university": university,
            "submissions": submissions
        })

    return {
        "name": "ICPC Latin America Championship 2026",
        "duration": DURATION,
        "freeze": FREEZE,
        "problems": problems,
        "teams": teams
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python parse_boca.py <input.html> <output.json>")
        sys.exit(1)

    html_path = sys.argv[1]
    out_path  = sys.argv[2]

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    data = parse_boca_html(html)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Parsed {len(data['teams'])} teams, {len(data['problems'])} problems.")
    print(f"Saved to {out_path}")
