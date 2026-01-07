import { useEffect, useState, useRef } from "react";
import "./App.css";
import contestData from "./assets/nac2024.json";

// Convert seconds → HH:MM:SS
function formatTime(sec) {
  // const h = String(Math.floor(sec / 3600)).padStart(2, "0");
  // const m = String(Math.floor((sec % 3600) / 60)).padStart(2, "0");
  // const s = String(sec % 60).padStart(2, "0");
  return `${sec / 60}`;
}

// Convert seconds → HH:MM:SS for header
function formatTimeLeft(sec) {
  const h = String(Math.floor(sec / 3600)).padStart(2, "0");
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, "0");
  return `${h}:${m}`;
}

export default function App() {
  const [currentTime, setCurrentTime] = useState(0);  // contest clock in seconds
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef(null);

  const startTimestampRef = useRef(null);
  const startTimeValueRef = useRef(0);


  const sortedSubsRef = useRef([]);

  // ——————————————————————————————————
  // Preprocess submissions once
  // ——————————————————————————————————
  useEffect(() => {
    const allSubs = [];
    for (const team of contestData.teams) {
      for (const p of contestData.problems) {
        const info = team.submissions[p];
        if (info) {
          allSubs.push({
            team: team.name,
            problem: p,
            time: info.time,
            tries: info.tries,
            first: info.first || false
          });
        }
      }
    }

    allSubs.sort((a, b) => a.time - b.time);
    sortedSubsRef.current = allSubs;
  }, []);

  // ——————————————————————————————————
  // Warn on tab close if replay is active
  // ——————————————————————————————————
  useEffect(() => {
    const handler = (e) => {
      if (isRunning) {
        e.preventDefault();
        e.returnValue = "There are unsaved changes.";
        return "There are unsaved changes.";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isRunning]);

  const duration = contestData.duration;
  const timeLeft = Math.max(0, duration - currentTime);

  // Build revealed submissions based on current time
  const revealed = sortedSubsRef.current.filter((s) => s.time <= Math.min(currentTime, contestData.freeze));

  // ——————————————————————————————————
  // Compute teams from revealed submissions
  // ——————————————————————————————————
  function computeTeams() {
    const teams = contestData.teams.map((t) => ({
      name: t.name,
      university: t.university,
      submissions: {},
      solved: 0,
      penalty: 0
    }));

    for (const s of revealed) {
      const team = teams.find((x) => x.name === s.team);
      if (!team.submissions[s.problem]) {
        team.submissions[s.problem] = {
          time: s.time,
          tries: s.tries,
          first: s.first
        };
        team.solved++;
        team.penalty += s.time + (s.tries - 1) * 20 * 60;
      }
    }

    teams.sort((a, b) => {
      if (b.solved !== a.solved) return b.solved - a.solved;
      if (a.penalty - b.penalty) return a.penalty - b.penalty;
      return a.name.localeCompare(b.name);
    });

    return teams;
  }

  const teams = computeTeams();

  // ——————————————————————————————————
  // Start replay: advance contest clock
  // ——————————————————————————————————
  function startReplay() {
    if (isRunning) return;

    setIsRunning(true);

    // When play starts, remember real clock time + contest time offset
    startTimestampRef.current = Date.now();
    startTimeValueRef.current = currentTime;

    const delay = 1000;

    intervalRef.current = setInterval(() => {
      const now = Date.now();
      const elapsed = (now - startTimestampRef.current) / 1000;

      const newTime = startTimeValueRef.current + elapsed;

      if (newTime >= duration) {
        clearInterval(intervalRef.current);
        setIsRunning(false);
        setCurrentTime(duration);
        return;
      }

      setCurrentTime(Math.round(newTime));
    }, delay);
  }

  // ——————————————————————————————————
  // Manual seek (changes contest time)
  // ——————————————————————————————————
  function manualSeek(sec) {
    setCurrentTime(sec);
  }

  return (
    <div className="page">
      <div className="headerBar">

        <button disabled={isRunning} onClick={startReplay} className="startBtn">
          Start Replay
        </button>

        <div className="timeLeftBox">
          Time Left:{" "}
          <span className="timeLeft">{formatTimeLeft(timeLeft)}</span>
        </div>

        <div className="seekBox">
          Seek:
          <input
            type="range"
            min="0"
            max={duration}
            value={currentTime}
            onChange={(e) => manualSeek(parseInt(e.target.value))}
            disabled={isRunning}
            step="1"
          />
        </div>

      </div>

      <h1 className="title">{contestData.name} Scoreboard {currentTime > contestData.freeze ? "(FROZEN)" : ""} </h1>

      <table className="scoreboard">
        <thead>
          <tr>
            <th className="rankCol">Rank</th>
            <th className="teamCol">Team</th>
            <th className="scoreCol">Score</th>
            {contestData.problems.map((p) => (
              <th key={p} className="probHeader">{p}</th>
            ))}
          </tr>
        </thead>

        <tbody>
          {teams.map((team, idx) => (
            <tr key={team.name}>
              <td className="rankCol">{idx + 1}</td>

              <td className="teamCol">
                <div className="teamName">{team.name}</div>
                {/* <div className="teamUniv">{team.university}</div>*/}
              </td>

              <td className="scoreCol">
                <span className="solvedCount">{team.solved}</span>
                <span className="penaltyTime">{formatTime(team.penalty)}</span>
              </td>

              {contestData.problems.map((p) => {
                const info = team.submissions[p];
                if (!info) return <td key={p} className="emptyCell"></td>;

                return (
                  <td
                    key={p}
                    className={`solvedCell ${info.first ? "firstSolve" : ""}`}
                  >
                    <div className="time">{formatTime(info.time)}</div>
                    <div className="tries">
                      {info.tries} try{info.tries > 1 ? "s" : ""}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
