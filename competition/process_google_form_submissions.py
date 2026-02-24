#!/usr/bin/env python3
"""Process Google Form submissions for NetLinkArena."""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from competition.evaluate import main as evaluate_submission
from competition.validate_submission import main as validate_submission
from competition.render_leaderboard import main as render_leaderboard

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io


def setup_google_credentials():
    """Setup Google API credentials."""
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON not found")
    
    creds_dict = json.loads(creds_json)
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
    
    return Credentials.from_service_account_info(creds_dict, scopes=scopes)


def read_submissions_from_sheet(sheet_id):
    """Read submissions from Google Sheet."""
    print("📊 Reading submissions...")
    
    credentials = setup_google_credentials()
    client = gspread.authorize(credentials)
    
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.get_worksheet(0)
    
    records = worksheet.get_all_records()
    print(f"✅ Found {len(records)} submission(s)")
    
    return records


def download_file_from_drive(file_url, output_path):
    """Download file from Google Drive."""
    if 'id=' in file_url:
        file_id = file_url.split('id=')[1].split('&')[0]
    elif '/d/' in file_url:
        file_id = file_url.split('/d/')[1].split('/')[0]
    else:
        raise ValueError(f"Cannot extract file ID from: {file_url}")
    
    credentials = setup_google_credentials()
    service = build('drive', 'v3', credentials=credentials)
    
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    with open(output_path, 'wb') as f:
        f.write(fh.getvalue())


def process_submission(record, test_labels_path, processed_teams):
    """Process a single submission."""
    team_name = record.get('1. Team Name', '').strip()
    model_type = record.get('2. Model Type', 'Unknown').strip()
    file_url = record.get('3. Submission File ( .csv)', '')
    timestamp = record.get('Timestamp', datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    if not team_name or not file_url:
        return None
    
    if team_name in processed_teams:
        print(f"⚠️ {team_name} already processed")
        return None
    
    print(f"\n{'='*60}")
    print(f"Processing: {team_name}")
    print(f"{'='*60}")
    
    temp_dir = Path('temp_submissions')
    temp_dir.mkdir(exist_ok=True)
    
    pred_file = temp_dir / f"{team_name}_predictions.csv"
    
    try:
        download_file_from_drive(file_url, pred_file)
        validate_submission(str(pred_file))
        
        import subprocess
        result = subprocess.run(
            ['python', 'competition/evaluate.py', str(pred_file), test_labels_path],
            capture_output=True,
            text=True,
            check=True
        )
        score = float(result.stdout.strip())
        print(f"✅ Score: {score:.4f}")
        
        pred_file.unlink()
        
        return {
            'team': team_name,
            'model': model_type,
            'score': f"{score:.4f}",
            'timestamp_utc': timestamp,
            'notes': f'Model: {model_type}'
        }
    except Exception as e:
        print(f"❌ Failed: {e}")
        if pred_file.exists():
            pred_file.unlink()
        return None


def update_leaderboard(new_entries):
    """Update leaderboard."""
    leaderboard_path = Path('leaderboard/leaderboard.csv')
    
    if leaderboard_path.exists():
        df = pd.read_csv(leaderboard_path)
    else:
        df = pd.DataFrame(columns=['team', 'model', 'score', 'timestamp_utc', 'notes'])
    
    for entry in new_entries:
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
        print(f"✅ Added {entry['team']}")
    
    df.to_csv(leaderboard_path, index=False)


def main():
    """Main function."""
    print("🚀 Processing Google Form Submissions")
    
    sheet_id = os.environ.get('GOOGLE_SHEETS_ID')
    if not sheet_id:
        raise ValueError("GOOGLE_SHEETS_ID not found")
    
    test_labels_path = 'data/private/test_labels.csv'
    if not os.path.exists(test_labels_path):
        test_labels = os.environ.get('TEST_LABELS_CSV')
        if test_labels:
            os.makedirs('data/private', exist_ok=True)
            with open(test_labels_path, 'w') as f:
                f.write(test_labels)
    
    leaderboard_path = Path('leaderboard/leaderboard.csv')
    processed_teams = set()
    if leaderboard_path.exists():
        df = pd.read_csv(leaderboard_path)
        processed_teams = set(df['team'].values)
    
    records = read_submissions_from_sheet(sheet_id)
    
    new_entries = []
    for record in records:
        result = process_submission(record, test_labels_path, processed_teams)
        if result:
            new_entries.append(result)
            processed_teams.add(result['team'])
    
    if new_entries:
        update_leaderboard(new_entries)
        render_leaderboard()
        print(f"✅ Added {len(new_entries)} submission(s)")
    else:
        print("✅ No new submissions")


if __name__ == "__main__":
    main()
