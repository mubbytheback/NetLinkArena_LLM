#!/usr/bin/env python3
"""Generate static HTML leaderboard with embedded data and Kaggle-style ranking."""

import pandas as pd
from datetime import datetime
from pathlib import Path

def generate_html():
    """Generate beautiful static HTML leaderboard."""
    
    csv_path = Path(__file__).parent.parent / 'leaderboard' / 'leaderboard.csv'
    if not csv_path.exists():
        print("❌ No leaderboard.csv found")
        return
    
    df = pd.read_csv(csv_path)
    
    # Sort by score descending, then by timestamp ascending (earlier = better for ties)
    df = df.sort_values(['score', 'timestamp_utc'], ascending=[False, True]).reset_index(drop=True)
    
    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    
    rows_html = ""
    current_rank = 1
    prev_score = None
    
    for idx, row in df.iterrows():
        team = row['team']
        model = row.get('model', 'Unknown')
        score = float(row['score'])
        ts = row.get('timestamp_utc', '')
        
        # Kaggle-style ranking: tied scores get same rank
        if prev_score is not None and score < prev_score:
            current_rank = idx + 1  # Jump to current position
        # If score == prev_score, keep current_rank (tied)
        
        prev_score = score
        rank = current_rank
        
        # Medal for top 3 ranks
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
        
        # Score as percentage
        score_pct = score * 100
        delay = idx * 0.1
        
        # Store model in lowercase for filtering
        model_lower = model.lower()
        
        rows_html += f'''
                    <tr data-team="{team}" data-model="{model_lower}" data-timestamp="{ts}" data-score="{score}" data-rank="{rank}" style="animation-delay: {delay}s;">
                        <td class="rank {rank_class}">{medal}{rank}</td>
                        <td class="team-name">{team}</td>
                        <td class="score primary-score" style="--fill-percent: {score_pct:.1f}%;"><span>{score:.4f}</span></td>
                        <td class="col-model">{model}</td>
                        <td>{formatted_ts}</td>
                    </tr>'''
    
    if not rows_html:
        rows_html = '<tr class="empty"><td colspan="5">No submissions yet. Be the first!</td></tr>'
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NetLinkArena Leaderboard</title>
    <link rel="stylesheet" href="leaderboard.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 NetLinkArena Leaderboard</h1>
            <p>Link Prediction Challenge</p>
        </div>
        <p class="last-updated">Last updated: {timestamp}</p>
        
        <div class="controls">
            <span class="search-wrapper">
                <span class="search-icon">🔍</span>
                <input type="text" id="search" placeholder="Search team..." class="search-input">
            </span>
            <select id="filter-model" class="filter-select">
                <option value="">All Models</option>
                <option value="gat">GAT</option>
                <option value="graphsage">GraphSAGE</option>
                <option value="gcn">GCN</option>
                <option value="baseline">Baseline</option>
                <option value="unknown">Unknown</option>
            </select>
        </div>
        
        <div class="leaderboard">
            <table id="leaderboard-table">
                <thead>
                    <tr>
                        <th class="rank">Rank</th>
                        <th>Team</th>
                        <th class="score primary-score">AUC-ROC Score</th>
                        <th class="col-model">Model</th>
                        <th>Submission Time</th>
                    </tr>
                </thead>
                <tbody>
{rows_html}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Submit your solution via Google Form to appear on the leaderboard!</p>
            <p style="margin-top: 10px;">
                <a href="https://github.com/ignatiusbalayo/NetLinkArena" target="_blank">🔗 View Repository</a>
            </p>
        </div>
    </div>
    
    <script>
        (function() {{
            const searchEl = document.getElementById('search');
            const filterModelEl = document.getElementById('filter-model');
            const table = document.getElementById('leaderboard-table');
            if (!table) return;
            
            const rows = Array.from(table.querySelectorAll('tbody tr')).filter(r => !r.classList.contains('empty'));
            
            function applyFilters() {{
                const searchQuery = (searchEl?.value || '').toLowerCase().trim();
                const modelFilter = (filterModelEl?.value || '').toLowerCase().trim();
                
                rows.forEach(row => {{
                    const team = (row.dataset.team || '').toLowerCase();
                    const model = (row.dataset.model || '').toLowerCase();
                    
                    const matchSearch = !searchQuery || team.includes(searchQuery);
                    const matchModel = !modelFilter || model === modelFilter;
                    
                    row.style.display = (matchSearch && matchModel) ? '' : 'none';
                }});
            }}
            
            searchEl?.addEventListener('input', applyFilters);
            filterModelEl?.addEventListener('change', applyFilters);
        }})();
    </script>
</body>
</html>'''
    
    html_path = Path(__file__).parent.parent / 'docs' / 'leaderboard.html'
    html_path.write_text(html, encoding='utf-8')
    print(f"✅ Static HTML leaderboard generated: {html_path}")

if __name__ == "__main__":
    generate_html()
