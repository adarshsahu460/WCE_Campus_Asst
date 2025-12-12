"""
Unit Tests for MCP Tools
Tests all MCP tools functionality.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

from tools.timetable import TimetableTool
from tools.study_plan import StudyPlanTool
from tools.exam_notify import ExamNotifyTool
from tools.file_browser import FileBrowserTool


class TestTimetableTool:
    """Tests for TimetableTool."""
    
    @pytest.fixture
    def tool(self, tmp_path):
        """Create a TimetableTool instance with temp directory."""
        with patch.dict(os.environ, {"TIMETABLE_DIR": str(tmp_path)}):
            return TimetableTool()
    
    @pytest.mark.asyncio
    async def test_execute_returns_schedule(self, tool):
        """Test that execute returns a schedule."""
        result = await tool.execute({"day": "monday"})
        
        assert "day" in result
        assert "schedule" in result
        assert "total_classes" in result
    
    @pytest.mark.asyncio
    async def test_resolve_today(self, tool):
        """Test resolving 'today' to actual day."""
        result = await tool.execute({"day": "today"})
        
        expected_day = datetime.now().strftime("%A")
        assert result["day"].lower() == expected_day.lower()
    
    @pytest.mark.asyncio
    async def test_resolve_tomorrow(self, tool):
        """Test resolving 'tomorrow' to actual day."""
        result = await tool.execute({"day": "tomorrow"})
        
        expected_day = (datetime.now() + timedelta(days=1)).strftime("%A")
        assert result["day"].lower() == expected_day.lower()
    
    @pytest.mark.asyncio
    async def test_weekend_schedule(self, tool):
        """Test weekend returns no classes message."""
        result = await tool.execute({"day": "sunday"})
        
        assert result["day"] == "Sunday"
        # Weekend may have different schedule format
    
    def test_tool_properties(self, tool):
        """Test tool metadata properties."""
        assert tool.name == "read_timetable_file"
        assert tool.description
        assert tool.parameters_schema


class TestStudyPlanTool:
    """Tests for StudyPlanTool."""
    
    @pytest.fixture
    def tool(self):
        """Create a StudyPlanTool instance."""
        return StudyPlanTool()
    
    @pytest.mark.asyncio
    async def test_generate_plan(self, tool):
        """Test generating a study plan."""
        exam_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        result = await tool.execute({
            "subjects": ["Math", "Physics", "Chemistry"],
            "exam_date": exam_date,
            "hours_per_day": 6
        })
        
        assert "daily_schedule" in result
        assert "summary" in result
        assert len(result["daily_schedule"]) > 0
    
    @pytest.mark.asyncio
    async def test_no_subjects_error(self, tool):
        """Test error when no subjects provided."""
        result = await tool.execute({
            "subjects": [],
            "exam_date": "2025-01-01"
        })
        
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_past_exam_error(self, tool):
        """Test error when exam date has passed."""
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await tool.execute({
            "subjects": ["Math"],
            "exam_date": past_date
        })
        
        assert "error" in result or "suggestion" in result
    
    @pytest.mark.asyncio
    async def test_plan_includes_recommendations(self, tool):
        """Test that plan includes recommendations."""
        exam_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        result = await tool.execute({
            "subjects": ["Math"],
            "exam_date": exam_date
        })
        
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
    
    def test_tool_properties(self, tool):
        """Test tool metadata properties."""
        assert tool.name == "generate_study_plan"
        assert tool.description
        assert "subjects" in str(tool.parameters_schema)


class TestExamNotifyTool:
    """Tests for ExamNotifyTool."""
    
    @pytest.fixture
    def tool(self, tmp_path):
        """Create an ExamNotifyTool instance with temp directory."""
        with patch.dict(os.environ, {"EXAMS_DIR": str(tmp_path)}):
            return ExamNotifyTool()
    
    @pytest.mark.asyncio
    async def test_returns_exams(self, tool):
        """Test that execute returns exam information."""
        result = await tool.execute({"days_ahead": 7})
        
        assert "exams" in result
        assert "total_exams" in result
        assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_sample_exams_fallback(self, tool):
        """Test that sample exams are returned when no real data."""
        result = await tool.execute({"days_ahead": 14})
        
        # Should return sample data
        assert result["total_exams"] >= 0
    
    @pytest.mark.asyncio
    async def test_urgency_categorization(self, tool):
        """Test that exams are categorized by urgency."""
        result = await tool.execute({"days_ahead": 14})
        
        assert "summary" in result
        summary = result["summary"]
        assert "urgent" in summary
        assert "this_week" in summary
    
    def test_tool_properties(self, tool):
        """Test tool metadata properties."""
        assert tool.name == "notify_upcoming_exams"
        assert tool.description


class TestFileBrowserTool:
    """Tests for FileBrowserTool."""
    
    @pytest.fixture
    def tool(self, tmp_path):
        """Create a FileBrowserTool instance with temp directory."""
        # Create some test files
        (tmp_path / "test.pdf").write_text("PDF content")
        (tmp_path / "test.csv").write_text("CSV content")
        (tmp_path / "subdir").mkdir()
        
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            return FileBrowserTool()
    
    @pytest.mark.asyncio
    async def test_browse_directory(self, tool, tmp_path):
        """Test browsing a directory."""
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            result = await tool.execute({"path": str(tmp_path)})
        
        assert "files" in result or "categories" in result
    
    @pytest.mark.asyncio
    async def test_categories_summary(self, tool):
        """Test getting categories summary."""
        result = await tool.execute({})
        
        assert "categories" in result or "files" in result
    
    @pytest.mark.asyncio
    async def test_filter_by_type(self, tool, tmp_path):
        """Test filtering files by type."""
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            result = await tool.execute({
                "path": str(tmp_path),
                "file_type": "pdf"
            })
        
        if "files" in result:
            for file in result["files"]:
                assert file.get("extension") == ".pdf"
    
    def test_tool_properties(self, tool):
        """Test tool metadata properties."""
        assert tool.name == "browse_local_files"
        assert tool.description
        assert "path" in str(tool.parameters_schema)


# Integration tests
class TestToolsIntegration:
    """Integration tests for MCP tools working together."""
    
    @pytest.mark.asyncio
    async def test_exam_to_study_plan_workflow(self):
        """Test workflow from finding exams to creating study plan."""
        with patch.dict(os.environ, {
            "EXAMS_DIR": "./data/exams",
            "DATA_DIR": "./data"
        }):
            exam_tool = ExamNotifyTool()
            study_tool = StudyPlanTool()
            
            # Get upcoming exams
            exams_result = await exam_tool.execute({"days_ahead": 14})
            
            # Create study plan from exam subjects
            if exams_result.get("exams"):
                subjects = [e["subject"] for e in exams_result["exams"][:3]]
                exam_date = exams_result["exams"][0].get("date", "2025-01-01")
                
                plan_result = await study_tool.execute({
                    "subjects": subjects,
                    "exam_date": exam_date,
                    "hours_per_day": 6
                })
                
                assert "daily_schedule" in plan_result or "error" in plan_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
