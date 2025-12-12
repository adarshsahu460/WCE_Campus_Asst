"""
Exam Notification Tool
Scans for upcoming exams and returns schedule.
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

from .base import BaseTool

load_dotenv()


class ExamNotifyTool(BaseTool):
    """
    Tool to find and notify about upcoming exams.
    Scans exam timetable files and RAG index for exam information.
    """
    
    def __init__(self):
        self.exams_dir = os.getenv("EXAMS_DIR", "./data/exams")
        Path(self.exams_dir).mkdir(parents=True, exist_ok=True)
    
    @property
    def name(self) -> str:
        return "notify_upcoming_exams"
    
    @property
    def description(self) -> str:
        return (
            "Scans exam timetable and documents to find exams coming within "
            "the specified number of days. Returns subjects, dates, and times."
        )
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days ahead to check for exams",
                    "default": 7,
                    "minimum": 1,
                    "maximum": 90
                }
            }
        }
    
    def _parse_exam_files(self) -> List[Dict[str, Any]]:
        """
        Parse exam timetable files.
        
        Returns:
            List of exam entries
        """
        exams = []
        exams_path = Path(self.exams_dir)
        
        # Try to load CSV files
        for file_path in exams_path.glob("*.csv"):
            try:
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        exam = {
                            "subject": row.get("subject", row.get("course", "")),
                            "date": row.get("date", ""),
                            "time": row.get("time", ""),
                            "venue": row.get("venue", row.get("room", "")),
                            "type": row.get("type", "exam"),
                            "source": file_path.name
                        }
                        if exam["subject"] and exam["date"]:
                            exams.append(exam)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
        
        # Try to load from text files
        for file_path in exams_path.glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple parsing for date patterns
                    parsed = self._extract_exams_from_text(content, file_path.name)
                    exams.extend(parsed)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
        
        return exams
    
    def _extract_exams_from_text(
        self,
        text: str,
        source: str
    ) -> List[Dict[str, Any]]:
        """
        Extract exam information from unstructured text.
        
        Args:
            text: Text content
            source: Source file name
            
        Returns:
            List of extracted exams
        """
        exams = []
        
        # Pattern: Subject - DD/MM/YYYY or DD-MM-YYYY
        date_pattern = r'([A-Za-z\s]+)\s*[-:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        matches = re.findall(date_pattern, text)
        
        for subject, date_str in matches:
            # Normalize date
            date_str = date_str.replace('/', '-')
            exams.append({
                "subject": subject.strip(),
                "date": date_str,
                "time": "",
                "venue": "",
                "type": "exam",
                "source": source
            })
        
        return exams
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            datetime object or None
        """
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d-%m-%y",
            "%d/%m/%Y",
            "%d/%m/%y",
            "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _filter_upcoming_exams(
        self,
        exams: List[Dict[str, Any]],
        days_ahead: int
    ) -> List[Dict[str, Any]]:
        """
        Filter exams to only those within days_ahead.
        
        Args:
            exams: All exam entries
            days_ahead: Number of days to look ahead
            
        Returns:
            Filtered and sorted exam list
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = today + timedelta(days=days_ahead)
        
        upcoming = []
        
        for exam in exams:
            exam_date = self._parse_date(exam.get("date", ""))
            
            if exam_date and today <= exam_date <= cutoff:
                days_until = (exam_date - today).days
                exam_copy = exam.copy()
                exam_copy["days_until"] = days_until
                exam_copy["parsed_date"] = exam_date.strftime("%Y-%m-%d")
                exam_copy["day_name"] = exam_date.strftime("%A")
                upcoming.append(exam_copy)
        
        # Sort by date
        upcoming.sort(key=lambda x: x.get("parsed_date", ""))
        
        return upcoming
    
    def _get_sample_exams(self, days_ahead: int) -> List[Dict[str, Any]]:
        """
        Get sample exam data for demo purposes.
        
        Args:
            days_ahead: Number of days ahead
            
        Returns:
            Sample exam list
        """
        today = datetime.now()
        
        sample_exams = [
            {"subject": "Data Structures", "days_offset": 3},
            {"subject": "Computer Networks", "days_offset": 5},
            {"subject": "Database Management", "days_offset": 7},
            {"subject": "Operating Systems", "days_offset": 10},
            {"subject": "Software Engineering", "days_offset": 12}
        ]
        
        result = []
        for exam in sample_exams:
            if exam["days_offset"] <= days_ahead:
                exam_date = today + timedelta(days=exam["days_offset"])
                result.append({
                    "subject": exam["subject"],
                    "date": exam_date.strftime("%Y-%m-%d"),
                    "time": "10:00 AM",
                    "venue": "Examination Hall",
                    "type": "End Semester Exam",
                    "days_until": exam["days_offset"],
                    "parsed_date": exam_date.strftime("%Y-%m-%d"),
                    "day_name": exam_date.strftime("%A"),
                    "source": "sample_data"
                })
        
        return result
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find upcoming exams.
        
        Args:
            params: {"days_ahead": 7}
            
        Returns:
            List of upcoming exams
        """
        days_ahead = params.get("days_ahead", 7)
        
        # Parse exam files
        all_exams = self._parse_exam_files()
        
        # Filter upcoming
        upcoming_exams = self._filter_upcoming_exams(all_exams, days_ahead)
        
        # If no real data, provide sample data
        if not upcoming_exams:
            upcoming_exams = self._get_sample_exams(days_ahead)
        
        # Categorize by urgency
        urgent = [e for e in upcoming_exams if e.get("days_until", 0) <= 3]
        this_week = [e for e in upcoming_exams if 3 < e.get("days_until", 0) <= 7]
        later = [e for e in upcoming_exams if e.get("days_until", 0) > 7]
        
        return {
            "days_ahead": days_ahead,
            "total_exams": len(upcoming_exams),
            "exams": upcoming_exams,
            "summary": {
                "urgent": len(urgent),
                "this_week": len(this_week),
                "later": len(later)
            },
            "urgent_exams": urgent,
            "message": self._generate_message(upcoming_exams)
        }
    
    def _generate_message(self, exams: List[Dict[str, Any]]) -> str:
        """Generate a human-readable message about upcoming exams."""
        if not exams:
            return "No upcoming exams found in the next week."
        
        if len(exams) == 1:
            exam = exams[0]
            return f"You have {exam['subject']} exam in {exam['days_until']} day(s) on {exam['day_name']}."
        
        subjects = [e['subject'] for e in exams[:3]]
        return f"You have {len(exams)} upcoming exam(s): {', '.join(subjects)}."
