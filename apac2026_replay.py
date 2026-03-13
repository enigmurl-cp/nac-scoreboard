#!/usr/bin/env python3
"""
Parser for the 2026 ICPC Asia Pacific Championship scoreboard.
Reads the HTML from the livesite and converts it to the replay JSON format.

Usage:
    python apac2026_parser.py <input.html> <output.json>

The input HTML can be obtained by:
    - Saving the page source of https://icpcapac.firebaseapp.com/standings/
    - Or fetching it with: curl -o inner.html https://icpcapac.firebaseapp.com/standings/
"""

import sys
import json
import re
from bs4 import BeautifulSoup


def hhmm_to_sec(time_str):
    """Convert 'H:MM' or 'HH:MM' time string to seconds."""
    time_str = time_str.strip()
    if not time_str or time_str == "-":
        return None
    parts = time_str.split(":")
    if len(parts) != 2:
        return None
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        return (hours * 60 + minutes) * 60
    except ValueError:
        return None


def parse_apac_standings(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    # --- Extract problem letters from the legend row ---
    legend = soup.find("div", class_="team-row legend")
    if not legend:
        print("ERROR: Could not find legend row.", file=sys.stderr)
        sys.exit(1)

    problem_divs = legend.find("div", class_="team-problems")
    problems = []
    for prob_col in problem_divs.find_all("div", class_="team-col team-problem"):
        span = prob_col.find("span")
        if span:
            letter = span.get_text(strip=True)
            if letter:
                problems.append(letter)

    print(f"Found {len(problems)} problems: {problems}", file=sys.stderr)

    # --- Extract team rows ---
    # Team rows are inside standings-teams sections, each wrapped in a div[data-key]
    teams = []

    team_wrappers = soup.find_all("div", attrs={"data-key": True})
    for wrapper in team_wrappers:
        team_row = wrapper.find("div", class_="team-row")
        if not team_row:
            continue

        # Team name is inside div.team-col.team-name > a > span.team-generic-col-content > span[title]
        name_col = team_row.find("div", class_="team-col team-name")
        if not name_col:
            continue
        team_name_span = name_col.find("span", title=True)
        team_name = team_name_span["title"] if team_name_span else name_col.get_text(" ", strip=True)

        # University name
        univ_span = name_col.find("span", class_="university-name")
        university = univ_span["title"] if univ_span and univ_span.has_attr("title") else team_name

        # Problem cells
        problems_div = team_row.find("div", class_="team-problems")
        if not problems_div:
            continue

        prob_cols = problems_div.find_all("div", class_="team-col team-problem")

        submissions = {}
        for idx, pc in enumerate(prob_cols):
            if idx >= len(problems):
                break
            prob_letter = problems[idx]

            # Determine status from background class
            bg_div = pc.find("div", class_=lambda c: c and "team-colored-col-bg" in c)
            if not bg_div:
                continue

            classes = bg_div.get("class", [])
            is_first = "bg-solved-first" in classes
            is_solved = is_first or "bg-solved" in classes

            if not is_solved:
                continue  # unattempted or only wrong submissions — skip

            # Extract time from the fg div
            fg_div = pc.find("div", class_="team-colored-col-fg")
            if not fg_div:
                continue

            fg_spans = fg_div.find_all("span", recursive=False)
            if not fg_spans:
                continue

            # The first span contains "H:MM\n" then possibly a <small>
            time_text = fg_spans[0].get_text(separator="\n").split("\n")[0].strip()
            time_sec = hhmm_to_sec(time_text)
            if time_sec is None:
                continue

            # Extract penalty tries from the <small> tag, e.g. "(+3)"
            penalty = 0
            small = fg_spans[0].find("small")
            if small:
                small_text = small.get_text(strip=True)
                match = re.search(r'\(\+(\d+)\)', small_text)
                if match:
                    penalty = int(match.group(1))

            tries = 1 + penalty  # 1 successful + N failed before

            submissions[prob_letter] = {
                "time": time_sec,
                "tries": tries,
                "first": is_first,
            }

        teams.append({
            "name": team_name,
            "university": university,
            "submissions": submissions,
        })

    print(f"Parsed {len(teams)} teams.", file=sys.stderr)

    result = {
        "name": "APAC 2026",
        "duration": 5 * 3600,   # 5-hour contest
        "freeze": 4 * 3600,     # freeze at 4 hours (typical ICPC)
        "problems": problems,
        "teams": teams,
    }
    return result


def main():
    if len(sys.argv) != 3:
        print("Usage: python apac2026_parser.py <input.html> <output.json>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    print(f"Reading {input_path} ...", file=sys.stderr)
    with open(input_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    data = parse_apac_standings(html_content)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved replay JSON to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
