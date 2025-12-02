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
	
	# Find all table rows
	rows = soup.find_all("tr")
	if not rows:
		print("ERROR: No rows found.")
		sys.exit(1)
	
	teams = []
	problems_count = None
	
	for row in rows:
		cells = row.find_all("td")
		if not cells or len(cells) < 6:
			continue
		
		# Skip header rows
		if cells[0].text.strip() == "Rank" or not cells[0].text.strip().isdigit():
			continue
		
		# Column structure:
		# 0 = rank
		# 1 = team name (e.g. "41 University of Illinois Urbana-Champaign")
		# 2 = solved
		# 3 = penalty
		# Problem cells start at index 4
		
		try:
			rank = int(cells[0].text.strip())
		except:
			continue
			
		team_text = cells[1].text.strip()
		# Extract university name (remove leading number if present)
		team_parts = team_text.split(None, 1)
		if len(team_parts) >= 2 and team_parts[0].isdigit():
			university = team_parts[1]
		else:
			university = team_text
		
		solved = int(cells[2].text.strip())
		penalty = int(cells[3].text.strip())
		
		# Problem cells start at index 4
		problem_cells = cells[4:]
		
		# Detect number of problems (excluding the last summary column if present)
		if problems_count is None:
			# Check if last cell looks like a summary (e.g., "17/12")
			last_cell = problem_cells[-1].text.strip()
			if "/" in last_cell and last_cell.count("/") == 1:
				problems_count = len(problem_cells) - 1
			else:
				problems_count = len(problem_cells)
		
		submissions = {}
		
		for idx in range(problems_count):
			pc = problem_cells[idx]
			prob_letter = chr(ord("A") + idx)
			
			cell_text = pc.text.strip()
			cell_classes = pc.get("class", [])
			
			# Skip if empty or marked as "no"
			if not cell_text or cell_text == "--" or "no" in cell_classes:
				continue
			
			# Only process "yes" cells
			if "yes" not in cell_classes:
				continue
			
			# Parse format: "tries/penalty" (e.g., "1/73" or "2/199")
			match = re.match(r"(\d+)/(\d+)", cell_text)
			if not match:
				continue
			
			tries = int(match.group(1))
			time_min = int(match.group(2))
			time_sec = min_to_sec(time_min)
			
			submissions[prob_letter] = {
				"time": time_sec,
				"tries": tries,
				"first": False  # Can't determine from this format
			}
		
		teams.append({
			"name": university,
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
