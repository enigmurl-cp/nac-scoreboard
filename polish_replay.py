from bs4 import BeautifulSoup
import json
import sys

def parse_time(time_str):
    """Convert H:MM or M:SS style time to seconds."""
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        h, m = int(parts[0]), int(parts[1])
        return h * 3600 + m * 60
    return None

def parse_standings(html_file):
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Extract problem letters from the header row
    header = soup.find("div", class_="grid1")
    problem_letters = []
    if header:
        header_cells = header.find_all("div", class_="result-cell--header")
        for cell in header_cells:
            letter = cell.contents[0].strip() if cell.contents else ""
            problem_letters.append(letter.upper())

    teams = []

    # Each team is in a div.grid1 that contains a div.grid3
    for grid1 in soup.find_all("div", class_="grid1"):
        grid3 = grid1.find("div", class_="grid3")
        if not grid3:
            continue

        # Skip header row
        if grid3.find("div", class_="result-cell--header"):
            continue

        # Team name
        name_div = grid3.find("div", class_="contestant__name")
        if not name_div:
            continue
        team_name = name_div.contents[0].strip()

        # Result cells (inside div.results)
        results_div = grid3.find("div", class_="results")
        if not results_div:
            continue

        result_cells = results_div.find_all("div", class_="result-cell", recursive=False)

        submissions = {}
        for idx, cell in enumerate(result_cells):
            classes = cell.get("class", [])
            if "result-cell--OK" not in classes:
                continue

            prob_letter = problem_letters[idx] if idx < len(problem_letters) else chr(ord("A") + idx)

            time_span = cell.find("span", class_="result-cell__time")
            if not time_span:
                continue

            time_sec = parse_time(time_span.text)
            if time_sec is None:
                continue

            bombs_span = cell.find("span", class_="result-cell__bombs")
            wrong = int(bombs_span.text.strip().replace("+", "")) if bombs_span else 0
            tries = wrong + 1

            is_first = "first-solve-badge" in classes

            submissions[prob_letter] = {
                "time": time_sec,
                "tries": tries,
                "first": is_first
            }

        teams.append({
            "name": team_name,
            "university": team_name,
            "submissions": submissions
        })

    return {
        "name": "EUC 2026",
        "duration": 5 * 3600,
        "freeze": 4 * 3600,
        "problems": problem_letters if problem_letters else [chr(ord("A") + i) for i in range(11)],
        "teams": teams
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python polish_replay.py <standings.html> <output.json>")
        sys.exit(1)

    data = parse_standings(sys.argv[1])

    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(data['teams'])} teams, {len(data['problems'])} problems to {sys.argv[2]}")
