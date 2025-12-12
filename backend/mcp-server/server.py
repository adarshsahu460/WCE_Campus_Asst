"""
MCP Server
Model Context Protocol server providing agentic tools for the WCE Campus Assistant.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import tools
from tools.timetable import TimetableTool
from tools.study_plan import StudyPlanTool
from tools.exam_notify import ExamNotifyTool
from tools.file_browser import FileBrowserTool

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="WCE Campus Assistant MCP Server",
    description="MCP server providing agentic tools for campus assistance",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize tools
timetable_tool = TimetableTool()
study_plan_tool = StudyPlanTool()
exam_notify_tool = ExamNotifyTool()
file_browser_tool = FileBrowserTool()

# Tool registry
TOOLS = {
    "read_timetable_file": timetable_tool,
    "generate_study_plan": study_plan_tool,
    "notify_upcoming_exams": exam_notify_tool,
    "browse_local_files": file_browser_tool
}


class ToolRequest(BaseModel):
    """Generic tool request model."""
    params: Dict[str, Any] = {}


class ToolResponse(BaseModel):
    """Generic tool response model."""
    success: bool
    result: Any
    error: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "WCE MCP Server",
        "version": "1.0.0",
        "available_tools": list(TOOLS.keys())
    }


@app.get("/tools")
async def list_tools():
    """List all available tools with their schemas."""
    tool_schemas = []
    
    for name, tool in TOOLS.items():
        tool_schemas.append({
            "name": name,
            "description": tool.description,
            "parameters": tool.parameters_schema
        })
    
    return {"tools": tool_schemas}


@app.get("/tools/schema")
async def get_tools_schema():
    """Get OpenAI-compatible function calling schema."""
    functions = []
    
    for name, tool in TOOLS.items():
        functions.append({
            "name": name,
            "description": tool.description,
            "parameters": tool.parameters_schema
        })
    
    return {"functions": functions}


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: ToolRequest):
    """
    Call a specific tool.
    
    Args:
        tool_name: Name of the tool to call
        request: Tool parameters
        
    Returns:
        Tool execution result
    """
    if tool_name not in TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available: {list(TOOLS.keys())}"
        )
    
    tool = TOOLS[tool_name]
    
    try:
        result = await tool.execute(request.params)
        return ToolResponse(
            success=True,
            result=result
        )
    except Exception as e:
        return ToolResponse(
            success=False,
            result=None,
            error=str(e)
        )


# Direct tool endpoints
@app.post("/tools/read_timetable_file/execute")
async def execute_timetable(day: Optional[str] = None, date: Optional[str] = None):
    """Execute timetable tool directly."""
    result = await timetable_tool.execute({"day": day, "date": date})
    return result


@app.post("/tools/generate_study_plan/execute")
async def execute_study_plan(
    subjects: List[str],
    exam_date: str,
    hours_per_day: int = 6
):
    """Execute study plan tool directly."""
    result = await study_plan_tool.execute({
        "subjects": subjects,
        "exam_date": exam_date,
        "hours_per_day": hours_per_day
    })
    return result


@app.post("/tools/notify_upcoming_exams/execute")
async def execute_exam_notify(days_ahead: int = 7):
    """Execute exam notification tool directly."""
    result = await exam_notify_tool.execute({"days_ahead": days_ahead})
    return result


@app.post("/tools/browse_local_files/execute")
async def execute_file_browser(path: Optional[str] = None):
    """Execute file browser tool directly."""
    result = await file_browser_tool.execute({"path": path})
    return result


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", 8002))
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True
    )
