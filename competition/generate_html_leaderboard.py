#!/usr/bin/env python3
"""Generate static HTML leaderboard with embedded data and animated background."""

import pandas as pd
from datetime import datetime
from pathlib import Path

def generate_html():
    """Generate beautiful static HTML leaderboard."""
    
    # Read leaderboard CSV
    csv_path = Path(__file__).parent.parent / 'leaderboard' / 'leaderboard.csv'
    if not csv_path.exists():
        print("❌ No leaderboard.csv found")
        return
    
    df = pd.read_csv(csv_path)
    
    # Sort by score descending
    df = df.sort_values('score', ascending=False).reset_index(drop=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    
    # Generate table rows
    rows_html = ""
    for idx, row in df.iterrows():
        rank = idx + 1
        team = row['team']
        model = row.get('model', 'Unknown')
        score = float(row['score'])
        ts = row.get('timestamp_utc', '')
        notes = row.get('notes', '')
        
        # Medal for top 3
        medal = ""
        rank_class = ""
        if rank == 1:
            medal = '<span class="medal">🥇 </span>'
            rank_class = "rank-1"
        elif rank == 2:
            medal = '<span class="medal">🥈 </span>'
            rank_class = "rank-2"
        elif rank == 3:
            medal = '<span class="medal">🥉 </span>'
            rank_class = "rank-3"
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            formatted_ts = dt.strftime("%B %d, %Y at %H:%M:%S")
        except:
            formatted_ts = ts
        
        # Score as percentage (AUC-ROC is 0-1, display as 0-100%)
        score_pct = score * 100
        
        # Animation delay
        delay = idx * 0.1
        
        rows_html += f'''
                    <tr data-team="{team}" data-model-type="{model.lower()}" data-timestamp="{ts}" data-score="{score}" data-rank="{rank}" style="animation-delay: {delay}s;">
                        <td class="rank {rank_class}">{medal}{rank}</td>
                        <td class="team-name">{team}</td>
                        <td class="score primary-score" style="--fill-percent: {score_pct:.1f}%;"><span>{score:.4f}</span></td>
                        <td class="col-model">{model}</td>
                        <td>{formatted_ts}</td>
                    </tr>'''
    
    # If no submissions
    if not rows_html:
        rows_html = '<tr class="empty"><td colspan="5">No submissions yet. Be the first!</td></tr>'
    
    # Complete HTML with animated background
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NetLinkArena Leaderboard</title>
    <link rel="stylesheet" href="leaderboard.css">
</head>
<body>
    <canvas id="graph-canvas"></canvas>
    
    <div class="container">
        <div class="header">
            <h1>🏆 NetLinkArena Leaderboard</h1>
            <p>Link Prediction Challenge</p>
        </div>
        <p class="last-updated">Last updated: {timestamp}</p>
        
        <div class="controls">
            <span class="search-wrapper">
                <span class="search-icon">🔍</span>
                <input type="text" id="search" placeholder="team" class="search-input">
            </span>
            <select id="filter-model" class="filter-select">
                <option value="">filter by model type</option>
                <option value="human">Human</option>
                <option value="llm">LLM</option>
                <option value="human+llm">Human+LLM</option>
            </select>
        </div>
        
        <div class="leaderboard">
            <table id="leaderboard-table">
                <thead>
                    <tr>
                        <th class="rank sortable" data-sort="rank">Rank</th>
                        <th class="sortable" data-sort="team">Team</th>
                        <th class="score primary-score sortable" data-sort="score">AUC-ROC Score <span style="color: #f39c12; font-size: 1.2em; font-weight: bold; text-shadow: 0 0 8px rgba(243, 156, 18, 0.6);">↓</span></th>
                        <th class="col-model sortable" data-sort="model_type">Model Type</th>
                        <th class="sortable" data-sort="timestamp">Submission Time</th>
                    </tr>
                </thead>
                <tbody>
{rows_html}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Submit your solution via Google Form to appear on the leaderboard!</p>
            <p style="margin-top: 10px; font-size: 0.95em;">
                <a href="https://github.com/ignatiusbalayo/NetLinkArena" 
                   target="_blank" 
                   rel="noopener noreferrer">
                    🔗 View Repository on GitHub
                </a>
            </p>
        </div>
    </div>
    
    <script src="leaderboard.js"></script>
</body>
</html>'''
    
    # Save HTML
    html_path = Path(__file__).parent.parent / 'docs' / 'leaderboard.html'
    html_path.write_text(html, encoding='utf-8')
    print(f"✅ Static HTML leaderboard generated: {html_path}")

if __name__ == "__main__":
    generate_html()
