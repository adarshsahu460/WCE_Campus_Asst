"""
Timetable Tool
Reads class timetable for a specific day or date.
"""

import os
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

from .base import BaseTool

load_dotenv()


class TimetableTool(BaseTool):
    """
    Tool to read class timetable for a specific day.
    Supports both CSV and parsed PDF timetables.
    """
    
    def __init__(self):
        self.timetable_dir = os.getenv("TIMETABLE_DIR", "./data/timetables")
        Path(self.timetable_dir).mkdir(parents=True, exist_ok=True)
    
    @property
    def name(self) -> str:
        return "read_timetable_file"
    
    @property
    def description(self) -> str:
        return (
            "Reads the class timetable for a specific day or date. "
            "Returns the schedule with classes for each hour/period."
        )
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "day": {
                    "type": "string",
                    "description": "Day of the week (e.g., 'Monday', 'Tuesday') or 'today', 'tomorrow'",
                    "enum": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "today", "tomorrow"]
                },
                "date": {
                    "type": "string",
                    "description": "Specific date in YYYY-MM-DD format (optional, overrides day)"
                }
            }
        }
    
    def _resolve_day(self, day: Optional[str], date: Optional[str]) -> str:
        """
        Resolve the day name from input.
        
        Args:
            day: Day name or relative day
            date: Specific date
            
        Returns:
            Lowercase day name
        """
        if date:
            try:
                dt = datetime.strptime(date, "%Y-%m-%d")
                return dt.strftime("%A").lower()
            except ValueError:
                pass
        
        if not day:
            day = "today"
        
        day = day.lower()
        
        if day == "today":
            return datetime.now().strftime("%A").lower()
        elif day == "tomorrow":
            tomorrow = datetime.now() + timedelta(days=1)
            return tomorrow.strftime("%A").lower()
        
        return day
    
    def _load_csv_timetable(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load timetable from CSV file.
        Expected format: day,time,subject,teacher,room
        """
        timetable = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    timetable.append({
                        "day": row.get("day", "").lower(),
                        "time": row.get("time", row.get("period", "")),
                        "subject": row.get("subject", row.get("course", "")),
                        "teacher": row.get("teacher", row.get("faculty", "")),
                        "room": row.get("room", row.get("venue", ""))
                    })
        except Exception as e:
            print(f"Error loading CSV: {e}")
        
        return timetable
    
    def _load_all_timetables(self) -> List[Dict[str, Any]]:
        """Load all timetable files from the directory."""
        all_entries = []
        
        timetable_path = Path(self.timetable_dir)
        
        for file_path in timetable_path.glob("*.csv"):
            entries = self._load_csv_timetable(str(file_path))
            all_entries.extend(entries)
        
        return all_entries
    
    def _get_day_schedule(self, day: str) -> List[Dict[str, Any]]:
        """
        Get schedule for a specific day.
        
        Args:
            day: Day name
            
        Returns:
            List of schedule entries
        """
        all_entries = self._load_all_timetables()
        
        day_entries = [
            entry for entry in all_entries
            if entry.get("day", "").lower() == day.lower()
        ]
        
        # Sort by time
        day_entries.sort(key=lambda x: x.get("time", ""))
        
        return day_entries
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the timetable tool.
        
        Args:
            params: {"day": "monday" | "today" | "tomorrow", "date": "YYYY-MM-DD"}
            
        Returns:
            Schedule for the requested day
        """
        day = params.get("day")
        date = params.get("date")
        
        resolved_day = self._resolve_day(day, date)
        schedule = self._get_day_schedule(resolved_day)
        
        if not schedule:
            # Return sample data if no real data exists
            schedule = self._get_sample_schedule(resolved_day)
        
        return {
            "day": resolved_day.capitalize(),
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "schedule": schedule,
            "total_classes": len(schedule)
        }
    
    def _get_sample_schedule(self, day: str) -> List[Dict[str, Any]]:
        """
        Get sample schedule for demo purposes.
        
        Args:
            day: Day name
            
        Returns:
            Sample schedule
        """
        # Sample schedule for demonstration
        if day.lower() in ["saturday", "sunday"]:
            return [{"message": "No classes on weekends"}]
        
        return [
            {"time": "09:00 - 10:00", "subject": "Data Structures", "teacher": "Dr. Sharma", "room": "LH-101"},
            {"time": "10:00 - 11:00", "subject": "Computer Networks", "teacher": "Prof. Patel", "room": "LH-102"},
            {"time": "11:15 - 12:15", "subject": "Database Systems", "teacher": "Dr. Kumar", "room": "LH-103"},
            {"time": "12:15 - 01:15", "subject": "Operating Systems", "teacher": "Prof. Singh", "room": "LH-101"},
            {"time": "02:00 - 03:00", "subject": "Software Engineering", "teacher": "Dr. Desai", "room": "Lab-201"},
            {"time": "03:00 - 05:00", "subject": "Programming Lab", "teacher": "Mr. Joshi", "room": "Lab-202"}
        ]
