import json
import os
from datetime import datetime
from pathlib import Path
from box_sdk_gen import BoxClient, APIException
from box_sdk_gen.schemas import FileBaseTypeField

class BoxClient:
    """Wrapper for Box API operations"""
    
    def __init__(self, access_token: str):
        """Initialize Box client with access token"""
        self.client = BoxClient(access_token=access_token)
    
    def get_folder_by_path(self, folder_path: str) -> str:
        """
        Get folder ID by path (e.g., '/raw-data/2026-05-30/linkedin')
        Returns folder ID or creates it if it doesn't exist
        """
        try:
            # For hackathon, assume folder path exists
            # In production, implement folder traversal/creation
            print(f"✓ Folder path: {folder_path}")
            return folder_path
        except APIException as e:
            print(f"Error accessing folder: {e}")
            return None
    
    def load_json_from_box(self, folder_path: str, filename: str) -> dict:
        """
        Load JSON file from Box folder
        Args:
            folder_path: Path like '/raw-data/2026-05-30/linkedin'
            filename: File name like 'trends.json'
        Returns:
            Parsed JSON data or empty dict if not found
        """
        try:
            # For hackathon, we'll use local fallback
            full_path = f"{folder_path}/{filename}"
            print(f"  Attempting to load from Box: {full_path}")
            # In production: use Box API to download and parse
            return {}
        except Exception as e:
            print(f"  Warning: Could not load from Box ({e}), using sample data")
            return {}
    
    def save_json_to_box(self, folder_path: str, filename: str, data: dict) -> bool:
        """
        Save JSON file to Box folder
        Args:
            folder_path: Path like '/digests/2026-05-30'
            filename: File name like 'user-digest.json'
            data: Dictionary to save
        Returns:
            True if successful, False otherwise
        """
        try:
            # For hackathon, we'll save locally with Box path reference
            local_backup = f"output_{filename}"
            with open(local_backup, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  ✓ Saved to {local_backup} (would upload to Box: {folder_path}/{filename})")
            return True
        except Exception as e:
            print(f"  Error saving to Box: {e}")
            return False
    
    def list_files_in_folder(self, folder_path: str) -> list:
        """List JSON files in a Box folder"""
        try:
            # For hackathon demo
            print(f"  Listing files in Box: {folder_path}")
            return []
        except Exception as e:
            print(f"  Error listing files: {e}")
            return []


class LocalBoxSimulator:
    """Simulates Box storage for hackathon testing"""
    
    def __init__(self):
        self.base_path = Path("sample_data")
    
    def load_trends(self, platform: str, date: str = None) -> dict:
        """
        Load trends from local sample data
        Args:
            platform: 'linkedin', 'youtube', 'instagram'
            date: ISO date string (defaults to today)
        Returns:
            Parsed trends data
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Try date-specific folder first
        dated_path = self.base_path / date / f"{platform}_trends.json"
        fallback_path = self.base_path / f"{platform}_trends.json"
        
        for path in [dated_path, fallback_path]:
            if path.exists():
                print(f"  ✓ Loaded {platform} trends from {path}")
                with open(path) as f:
                    return json.load(f)
        
        print(f"  ⚠ No trends file found for {platform}")
        return {"items": []}
    
    def save_digest(self, user_id: str, date: str, digest: dict) -> bool:
        """Save digest locally (simulates Box storage)"""
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{date}_{user_id}_digest.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(digest, f, indent=2)
        
        print(f"  ✓ Saved digest to {filepath}")
        return True
