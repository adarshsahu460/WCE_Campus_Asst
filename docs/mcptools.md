# MCP Tools Documentation

## Overview

The Model Context Protocol (MCP) server provides structured tools for the WCE Campus Assistant. Each tool handles specific campus-related functionality and follows a consistent interface pattern.

## Tool Registry

| Tool Name | Description | Use Case |
|-----------|-------------|----------|
| `timetable` | Fetch class schedules | "What classes do I have today?" |
| `study_plan` | Generate study plans | "Help me prepare for my exams" |
| `exam_notify` | Get exam reminders | "When are my upcoming exams?" |
| `file_browser` | Browse documents | "What syllabus documents are available?" |

---

## 1. Timetable Tool

### Purpose
Retrieves class timetables for students based on their class, division, and day.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `class_name` | string | Yes | Class name (e.g., "TE", "BE") |
| `division` | string | No | Division (default: "A") |
| `day` | string | No | Day of week or "today"/"tomorrow" |

### Example Request

```json
{
  "name": "timetable",
  "arguments": {
    "class_name": "TE",
    "division": "A",
    "day": "today"
  }
}
```

### Example Response

```json
{
  "success": true,
  "data": {
    "class": "TE",
    "division": "A",
    "day": "Monday",
    "date": "2024-01-15",
    "schedule": [
      {"time": "09:00-10:00", "subject": "Machine Learning", "room": "301"},
      {"time": "10:00-11:00", "subject": "Data Science", "room": "302"},
      {"time": "11:15-12:15", "subject": "Cloud Computing", "room": "Lab 1"}
    ]
  }
}
```

### Data Source
- CSV files in `/data/timetables/`
- Format: `{class}_{division}_timetable.csv`

---

## 2. Study Plan Tool

### Purpose
Generates personalized study plans based on subjects, available time, and exam dates.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subjects` | array | Yes | List of subjects to study |
| `days_available` | integer | No | Days until exam (default: 7) |
| `hours_per_day` | integer | No | Study hours per day (default: 6) |

### Example Request

```json
{
  "name": "study_plan",
  "arguments": {
    "subjects": ["Machine Learning", "Data Science", "Cloud Computing"],
    "days_available": 10,
    "hours_per_day": 8
  }
}
```

### Example Response

```json
{
  "success": true,
  "data": {
    "total_hours": 80,
    "subjects": ["Machine Learning", "Data Science", "Cloud Computing"],
    "schedule": [
      {
        "day": 1,
        "date": "2024-01-15",
        "sessions": [
          {"subject": "Machine Learning", "hours": 3, "focus": "Supervised Learning"},
          {"subject": "Data Science", "hours": 3, "focus": "Data Preprocessing"},
          {"subject": "Cloud Computing", "hours": 2, "focus": "Introduction"}
        ]
      }
    ],
    "tips": [
      "Start with concepts you find most difficult",
      "Take breaks every 45-60 minutes",
      "Review previous day's material each morning"
    ]
  }
}
```

### Algorithm
- Distributes study time based on subject complexity
- Includes revision days before exams
- Balances subjects to avoid fatigue

---

## 3. Exam Notify Tool

### Purpose
Retrieves upcoming exams and categorizes them by urgency.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `class_name` | string | No | Filter by class |
| `days_ahead` | integer | No | Look-ahead days (default: 30) |

### Example Request

```json
{
  "name": "exam_notify",
  "arguments": {
    "class_name": "TE",
    "days_ahead": 14
  }
}
```

### Example Response

```json
{
  "success": true,
  "data": {
    "upcoming_exams": [
      {
        "subject": "Machine Learning",
        "date": "2024-01-20",
        "type": "End Semester",
        "days_remaining": 5,
        "urgency": "high"
      },
      {
        "subject": "Data Science",
        "date": "2024-01-25",
        "type": "End Semester",
        "days_remaining": 10,
        "urgency": "medium"
      }
    ],
    "summary": {
      "total": 2,
      "high_urgency": 1,
      "medium_urgency": 1,
      "low_urgency": 0
    }
  }
}
```

### Urgency Levels
- **High**: ≤ 7 days remaining
- **Medium**: 8-14 days remaining
- **Low**: > 14 days remaining

### Data Source
- CSV/JSON files in `/data/exams/`

---

## 4. File Browser Tool

### Purpose
Lists available documents in the knowledge base by category or file type.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category |
| `file_type` | string | No | Filter by extension |

### Categories
- `syllabus` - Course syllabi
- `notices` - Official notices
- `regulations` - Academic regulations
- `timetables` - Class schedules
- `exams` - Exam schedules

### Example Request

```json
{
  "name": "file_browser",
  "arguments": {
    "category": "syllabus",
    "file_type": "pdf"
  }
}
```

### Example Response

```json
{
  "success": true,
  "data": {
    "category": "syllabus",
    "files": [
      {
        "name": "computer_engineering_te_syllabus.pdf",
        "path": "/data/syllabus/computer_engineering_te_syllabus.pdf",
        "size": "2.5 MB",
        "modified": "2024-01-10"
      },
      {
        "name": "information_technology_te_syllabus.pdf",
        "path": "/data/syllabus/information_technology_te_syllabus.pdf",
        "size": "2.1 MB",
        "modified": "2024-01-10"
      }
    ],
    "total_files": 2
  }
}
```

---

## Adding New Tools

### 1. Create Tool Class

```python
# backend/mcp-server/tools/my_tool.py
from .base import BaseTool, ToolResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "Description of what the tool does"
    
    parameters = {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param1"]
    }
    
    async def execute(self, param1: str, **kwargs) -> ToolResult:
        # Implementation
        return ToolResult(
            success=True,
            data={"result": "value"}
        )
```

### 2. Register Tool

```python
# backend/mcp-server/tools/__init__.py
from .my_tool import MyTool

AVAILABLE_TOOLS = [
    # ... existing tools
    MyTool(),
]
```

### 3. Update Schema

Add tool definition to `/backend/mcp-server/schema.json`:

```json
{
  "name": "my_tool",
  "description": "Description of what the tool does",
  "parameters": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "Parameter description"
      }
    },
    "required": ["param1"]
  }
}
```

---

## Error Handling

All tools return consistent error responses:

```json
{
  "success": false,
  "error": "Error message describing what went wrong",
  "data": null
}
```

### Common Error Codes

| Error | Description |
|-------|-------------|
| `TOOL_NOT_FOUND` | Requested tool doesn't exist |
| `INVALID_PARAMS` | Missing or invalid parameters |
| `DATA_NOT_FOUND` | Requested data not available |
| `EXECUTION_ERROR` | Runtime error during execution |

---

## API Reference

### List Tools

```
GET /tools
```

Returns list of all available tools with their schemas.

### Execute Tool

```
POST /tools/execute
```

**Request Body:**
```json
{
  "name": "tool_name",
  "arguments": {
    "param1": "value1"
  }
}
```

**Response:**
```json
{
  "success": true,
  "tool": "tool_name",
  "data": { ... }
}
```
