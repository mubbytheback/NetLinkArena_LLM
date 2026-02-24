#!/usr/bin/env python3
"""
Process Google Form submissions for NetLinkArena.

Workflow:
1. Read submissions from Google Sheet
2. Download CSV files from Google Drive
3. Validate and evaluate each submission
4. Update leaderboard CSV
5. Render leaderboard markdown and HTML
6. Commit changes
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from competition.evaluate import main as evaluate_submission
from competition.validate_submission import main as validate_submission
from competition.render_leaderboard import main as render_leaderboard
from competition.generate_html_leaderboard import generate_html

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io


def setup_google_credentials():
    """Setup Google API credentials from environment variable."""
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON not found in environment")
    
    creds_dict = json.loads(creds_json)
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
    
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return credentials


def read_submissions_from_sheet(sheet_id):
    """Read submissions from Google Sheet."""
    print("📊 Reading submissions from Google Sheet...")
    
    credentials = setup_google_credentials()
    client = gspread.authorize(credentials)
    
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.get_worksheet(0)  # First sheet
    
    # Get all records
    records = worksheet.get_all_records()
    print(f"✅ Found {len(records)} submission(s)")
    
    return records


def download_file_from_drive(file_url, output_path):
    """Download file from Google Drive given its URL."""
    print(f"📥 Downloading file...")
    
    # Extract file ID from URL
    if 'id=' in file_url:
        file_id = file_url.split('id=')[1].split('&')[0]
    elif '/d/' in file_url:
        file_id = file_url.split('/d/')[1].split('/')[0]
    else:
        raise ValueError(f"Cannot extract file ID from URL: {file_url}")
    
    credentials = setup_google_credentials()
    service = build('drive', 'v3', credentials=credentials)
    
    # Download file
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    # Save to file
    with open(output_path, 'wb') as f:
        f.write(fh.getvalue())
    
    print(f"✅ Downloaded to: {output_path}")
    return output_path


def process_submission(record, test_labels_path, processed_teams):
    """Process a single submission."""
    
    # EXACT column names from Google Form
    team_name = record.get('1. Team Name', '').strip()
    model_type = record.get('2. Model Type', 'Unknown').strip()
    file_url = record.get('3. Submission File ( .csv)', '')
    timestamp = record.get('Timestamp', datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    if not team_name:
        print(f"⚠️ Skipping: No team name")
        return None
    
    if not file_url:
        print(f"⚠️ Skipping {team_name}: No file uploaded")
        return None
    
    # Check if already processed
    if team_name in processed_teams:
        print(f"⚠️ Skipping {team_name}: Already processed")
        return None
    
    print(f"\n{'='*60}")
    print(f"Processing: {team_name}")
    print(f"Model Type: {model_type}")
    print(f"{'='*60}")
    
    # Create temp directory
    temp_dir = Path('temp_submissions')
    temp_dir.mkdir(exist_ok=True)
    
    # Download predictions
    pred_file = temp_dir / f"{team_name}_predictions.csv"
    
    try:
        download_file_from_drive(file_url, pred_file)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None
    
    # Validate
    print("🔍 Validating...")
    try:
        validate_submission(str(pred_file))
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        if pred_file.exists():
            pred_file.unlink()
        return None
    
    # Evaluate
    print("📊 Evaluating...")
    try:
        import subprocess
        result = subprocess.run(
            ['python', 'competition/evaluate.py', str(pred_file), test_labels_path],
            capture_output=True,
            text=True,
            check=True
        )
        score = float(result.stdout.strip())
        print(f"✅ Score: {score:.4f}")
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        if pred_file.exists():
            pred_file.unlink()
        return None
    
    # Clean up
    if pred_file.exists():
        pred_file.unlink()
    
    return {
        'team': team_name,
        'model': model_type,
        'score': f"{score:.4f}",
        'timestamp_utc': timestamp,
        'notes': f'Model: {model_type}'
    }


def update_leaderboard(new_entries):
    """Update leaderboard CSV with new entries."""
    leaderboard_path = Path('leaderboard/leaderboard.csv')
    
    # Read existing leaderboard
    if leaderboard_path.exists():
        df = pd.read_csv(leaderboard_path)
    else:
        df = pd.DataFrame(columns=['team', 'model', 'score', 'timestamp_utc', 'notes'])
    
    existing_teams = set(df['team'].values)
    
    added = 0
    for entry in new_entries:
        if entry['team'] in existing_teams:
            print(f"⚠️ {entry['team']} already in leaderboard - skipping")
            continue
        
        # Add new entry
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
        print(f"✅ Added {entry['team']} to leaderboard")
        added += 1
    
    if added > 0:
        df.to_csv(leaderboard_path, index=False)
        print(f"💾 Leaderboard saved ({added} new entries)")
    
    return added


def main():
    """Main processing function."""
    print("🚀 NetLinkArena - Processing Google Form Submissions")
    print("="*60)
    
    # Get configuration from environment
    sheet_id = os.environ.get('GOOGLE_SHEETS_ID')
    if not sheet_id:
        raise ValueError("GOOGLE_SHEETS_ID not found in environment")
    
    # Setup test labels
    test_labels_path = 'data/private/test_labels.csv'
    if not os.path.exists(test_labels_path):
        test_labels = os.environ.get('TEST_LABELS_CSV')
        if test_labels:
            os.makedirs('data/private', exist_ok=True)
            with open(test_labels_path, 'w') as f:
                f.write(test_labels)
        else:
            raise ValueError("TEST_LABELS_CSV not found")
    
    # Read current leaderboard to get processed teams
    leaderboard_path = Path('leaderboard/leaderboard.csv')
    processed_teams = set()
    if leaderboard_path.exists():
        df = pd.read_csv(leaderboard_path)
        processed_teams = set(df['team'].values)
        print(f"📋 Current leaderboard has {len(processed_teams)} team(s)")
    
    # Read submissions from Google Sheet
    records = read_submissions_from_sheet(sheet_id)
    
    if not records:
        print("✅ No submissions found")
        return
    
    # Process each submission
    new_entries = []
    for record in records:
        result = process_submission(record, test_labels_path, processed_teams)
        if result:
            new_entries.append(result)
            processed_teams.add(result['team'])  # Track to avoid duplicates in same run
    
    if not new_entries:
        print("✅ No new valid submissions")
        return
    
    # Update leaderboard
    added = update_leaderboard(new_entries)
    
    if added > 0:
        # Render leaderboard markdown
        print("\n📝 Rendering leaderboard markdown...")
        render_leaderboard()
        
        # Generate static HTML
        print("🎨 Generating static HTML leaderboard...")
        generate_html()
        
        print(f"\n✅ Processing complete! Added {added} submission(s)")
    else:
        print("✅ No new entries added")


if __name__ == "__main__":
    main()