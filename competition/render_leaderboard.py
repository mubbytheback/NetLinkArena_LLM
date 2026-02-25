#!/usr/bin/env python3
"""Render leaderboard CSV to markdown format."""

import csv
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "leaderboard" / "leaderboard.csv"
MD_PATH = ROOT / "leaderboard" / "leaderboard.md"

def read_rows():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if (r.get("team") or "").strip()]
    return rows

def main():
    rows = read_rows()
    
    # Sort by score desc, then timestamp desc
    def score_key(r):
        try:
            return float(r.get("score", "-inf"))
        except ValueError:
            return float("-inf")
            
    def ts_key(r):
        try:
            ts_str = r.get("timestamp_utc", "")
            if not ts_str:
                return datetime.min.replace(tzinfo=timezone.utc)
            
            # Handle both with and without timezone
            if 'Z' in ts_str or '+' in ts_str:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
            
            return dt
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)
    
    # Apply sorting
    rows.sort(key=lambda r: (score_key(r), ts_key(r)), reverse=True)
    
    lines = []
    lines.append("# Leaderboard\n\n")
    lines.append("This leaderboard is **auto-updated** when a submission is processed.\n\n")
    
    lines.append("| Rank | Team | Model | Score | Date (UTC) | Notes |\n")
    lines.append("|---:|---|---|---:|---|---|\n")
    
    # Kaggle-style ranking: tied scores share the same rank
    current_rank = 1
    prev_score = None
    
    for idx, r in enumerate(rows):
        team = (r.get("team") or "").strip()
        model = (r.get("model") or "").strip()
        score = r.get("score", "")
        ts = (r.get("timestamp_utc") or "").strip()
        notes = (r.get("notes") or "").strip()
        
        # Calculate rank (Kaggle-style)
        try:
            score_float = float(score)
            if prev_score is None or score_float < prev_score:
                current_rank = idx + 1
            prev_score = score_float
        except ValueError:
            current_rank = idx + 1
        
        # Format model
        model_disp = f"`{model}`" if model else ""
        
        # Format score
        try:
            score_disp = f"{float(score):.4f}" if score else "-"
        except ValueError:
            score_disp = score
        
        # Write row
        lines.append(f"| {current_rank} | {team} | {model_disp} | {score_disp} | {ts} | {notes} |\n")
    
    # Ensure directory exists
    MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"✅ Leaderboard successfully rendered at {MD_PATH}")

if __name__ == "__main__":
    main()
