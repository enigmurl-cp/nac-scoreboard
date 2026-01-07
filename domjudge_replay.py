import json
import requests
from bs4 import BeautifulSoup
import sys
import re

def min_to_sec(m):
	return int(float(m) * 60)

def parse_domjudge(url):
	print(f"Fetching {url} ...")
	f = open("inner.html")
	html = f.read()
	soup = BeautifulSoup(html, "html.parser")

	# DOMjudge scoreboard rows
	rows = soup.find_all("tr")
	if not rows:
		print("ERROR: No DOMjudge rows found.")
		sys.exit(1)

	teams = []
	problems_count = None

	for row in rows:
		if not row.get("id") or not row["id"].startswith("team:") or "mobile" in row["id"]:
			continue
		cells = row.find_all("td")

		if not cells:
			continue

		# Column structure:
		# 0 = rank
		# 1 = heart
		# 2 = affiliation logo
		# 3 = team name cell
		# 4 = solved
		# 5 = penalty
		#
		# Problem cells start at index 6
		rank = int(cells[0].text.strip())
		solved = int(cells[4].text.strip())
		penalty = int(cells[5].text.strip())

		# Team name inside <td class="scoretn ...">
		team_td = cells[3]
		team_name = team_td.get_text(" ", strip=True)
		if "Division" in team_name:
			team_name = team_name[team_name.index("Division") + len("Division"):]

		# Use team name as university (DOMjudge doesn't necessarily include cleaned affiliation)
		university = team_name

		# Problem cells:
		problem_cells = cells[6:]

		if problems_count is None:
			problems_count = len(problem_cells)

		submissions = {}

		for idx, pc in enumerate(problem_cells):
			prob_letter = chr(ord("A") + idx)

			div = pc.find("div")
			if not div:
				continue

			classes = div.get("class", [])

			# Skip incorrect cells
			if "score_incorrect" in classes:
				continue

			# Only accept `score_correct`
			if "score_correct" not in classes and "score_first" not in classes:
				continue

			# Has time + tries inside
			time_text = div.contents[0].strip()

			# Empty or non-number → skip
			if not time_text.isdigit():
				continue

			time_min = int(time_text)
			time_sec = min_to_sec(time_min)

			# Find tries in <span>… "2 tries"
			span = div.find("span")
			tries = None
			if span:
				m = re.search(r"(\d+)\s+tr", span.text.strip())
				if m:
					tries = int(m.group(1))

			if tries is None:
				continue

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
		"duration": 5 * 3600,  # NAC and most DOMjudge ICPCs are 5h
		"freeze": 4 * 3600,  # NAC and most DOMjudge ICPCs are 5h
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
