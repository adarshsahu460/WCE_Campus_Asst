"""
Study Plan Generator Tool
Creates a day-wise study plan based on subjects and exam date.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from .base import BaseTool

load_dotenv()


class StudyPlanTool(BaseTool):
    """
    Tool to generate personalized study plans.
    Creates a day-wise study schedule based on subjects, exam date, and available hours.
    """
    
    @property
    def name(self) -> str:
        return "generate_study_plan"
    
    @property
    def description(self) -> str:
        return (
            "Generates a day-wise study plan based on the list of subjects, "
            "exam date, and available study hours per day. Returns a structured "
            "schedule with topics allocated per day."
        )
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subjects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of subjects to study"
                },
                "exam_date": {
                    "type": "string",
                    "description": "Exam date in YYYY-MM-DD format"
                },
                "hours_per_day": {
                    "type": "integer",
                    "description": "Available study hours per day",
                    "default": 6,
                    "minimum": 1,
                    "maximum": 16
                }
            },
            "required": ["subjects", "exam_date"]
        }
    
    def _calculate_days_remaining(self, exam_date: str) -> int:
        """
        Calculate days remaining until exam.
        
        Args:
            exam_date: Exam date string
            
        Returns:
            Number of days remaining
        """
        try:
            exam_dt = datetime.strptime(exam_date, "%Y-%m-%d")
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            delta = (exam_dt - today).days
            return max(0, delta)
        except ValueError:
            return 7  # Default to 7 days if date parsing fails
    
    def _allocate_time_per_subject(
        self,
        subjects: List[str],
        total_hours: float
    ) -> Dict[str, float]:
        """
        Allocate study hours per subject.
        
        Args:
            subjects: List of subjects
            total_hours: Total available hours
            
        Returns:
            Dict mapping subject to allocated hours
        """
        if not subjects:
            return {}
        
        # Equal distribution by default
        hours_per_subject = total_hours / len(subjects)
        
        return {subject: round(hours_per_subject, 1) for subject in subjects}
    
    def _generate_daily_schedule(
        self,
        subjects: List[str],
        hours_per_day: int,
        days_remaining: int
    ) -> List[Dict[str, Any]]:
        """
        Generate daily study schedule.
        
        Args:
            subjects: List of subjects
            hours_per_day: Hours available per day
            days_remaining: Days until exam
            
        Returns:
            List of daily schedules
        """
        schedule = []
        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate hours per subject per day
        subjects_per_day = min(len(subjects), 3)  # Max 3 subjects per day
        hours_per_subject = hours_per_day / subjects_per_day
        
        for day_num in range(days_remaining):
            day_date = current_date + timedelta(days=day_num + 1)
            
            # Rotate subjects
            day_subjects = []
            for i in range(subjects_per_day):
                subject_index = (day_num * subjects_per_day + i) % len(subjects)
                day_subjects.append({
                    "subject": subjects[subject_index],
                    "hours": round(hours_per_subject, 1),
                    "focus": self._get_study_focus(day_num, days_remaining)
                })
            
            day_schedule = {
                "day": day_num + 1,
                "date": day_date.strftime("%Y-%m-%d"),
                "day_name": day_date.strftime("%A"),
                "subjects": day_subjects,
                "total_hours": hours_per_day,
                "tips": self._get_day_tips(day_num, days_remaining)
            }
            
            schedule.append(day_schedule)
        
        return schedule
    
    def _get_study_focus(self, day_num: int, total_days: int) -> str:
        """Get study focus based on days remaining."""
        progress = day_num / max(total_days, 1)
        
        if progress < 0.3:
            return "concepts_and_theory"
        elif progress < 0.6:
            return "practice_problems"
        elif progress < 0.85:
            return "revision_and_notes"
        else:
            return "quick_review"
    
    def _get_day_tips(self, day_num: int, total_days: int) -> List[str]:
        """Get study tips for the day."""
        progress = day_num / max(total_days, 1)
        
        tips = ["Take regular breaks (25 min study, 5 min break)"]
        
        if progress < 0.3:
            tips.append("Focus on understanding core concepts")
            tips.append("Create summary notes for each topic")
        elif progress < 0.6:
            tips.append("Practice previous year questions")
            tips.append("Solve numerical problems")
        elif progress < 0.85:
            tips.append("Review your notes and summaries")
            tips.append("Focus on weak areas")
        else:
            tips.append("Quick revision only - don't learn new topics")
            tips.append("Get good sleep before exam")
        
        return tips
    
    def _generate_summary(
        self,
        subjects: List[str],
        days_remaining: int,
        hours_per_day: int
    ) -> Dict[str, Any]:
        """Generate plan summary."""
        total_study_hours = days_remaining * hours_per_day
        hours_per_subject = total_study_hours / len(subjects) if subjects else 0
        
        return {
            "total_days": days_remaining,
            "total_study_hours": total_study_hours,
            "hours_per_subject": round(hours_per_subject, 1),
            "subjects_count": len(subjects),
            "daily_hours": hours_per_day
        }
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a study plan.
        
        Args:
            params: {
                "subjects": ["Math", "Physics"],
                "exam_date": "2025-01-15",
                "hours_per_day": 6
            }
            
        Returns:
            Complete study plan with day-wise schedule
        """
        subjects = params.get("subjects", [])
        exam_date = params.get("exam_date", "")
        hours_per_day = params.get("hours_per_day", 6)
        
        # Validate inputs
        if not subjects:
            return {
                "error": "No subjects provided",
                "message": "Please provide at least one subject to create a study plan"
            }
        
        if not exam_date:
            # Default to 7 days from now
            exam_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Calculate days
        days_remaining = self._calculate_days_remaining(exam_date)
        
        if days_remaining == 0:
            return {
                "error": "Exam is today or has passed",
                "message": "Cannot create study plan for past or current date exams",
                "suggestion": "Focus on quick revision and rest well"
            }
        
        # Generate schedule
        daily_schedule = self._generate_daily_schedule(
            subjects, hours_per_day, days_remaining
        )
        
        summary = self._generate_summary(subjects, days_remaining, hours_per_day)
        
        return {
            "exam_date": exam_date,
            "subjects": subjects,
            "summary": summary,
            "daily_schedule": daily_schedule,
            "recommendations": [
                "Start with difficult subjects when you're fresh",
                "Take a 15-minute break after every 2 hours",
                "Review today's topics before sleeping",
                "Stay hydrated and eat healthy",
                "Get at least 7 hours of sleep"
            ]
        }
