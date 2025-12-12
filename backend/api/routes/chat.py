"""
Chat Route
Handles chat endpoint with RAG and MCP tool integration.
"""

import os
import json
import httpx
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message schema."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str = Field(..., description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Previous conversation messages"
    )
    use_rag: bool = Field(default=True, description="Whether to use RAG")
    use_tools: bool = Field(default=True, description="Whether to use MCP tools")


class ChatResponse(BaseModel):
    """Chat response schema."""
    response: str
    sources: List[Dict[str, Any]] = []
    tool_calls: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}


class RAGQueryRequest(BaseModel):
    """RAG query request schema."""
    query: str = Field(..., description="Query string")
    top_k: Optional[int] = Field(default=5, description="Number of results")
    category: Optional[str] = Field(default=None, description="Document category filter")


# System prompt for the assistant
SYSTEM_PROMPT = """You are the WCE Campus Assistant, an AI helper for Walchand College of Engineering students and faculty.

Your role:
1. Answer questions about academic regulations, exam schedules, timetables, and notices
2. Provide accurate information based ONLY on the provided context
3. Help students with study planning and exam preparation
4. Guide users to relevant documents and resources

Guidelines:
- ONLY use information from the provided context to answer questions
- If the context doesn't contain relevant information, say "I don't have information about that in my knowledge base"
- Always cite your sources by mentioning which document the information came from
- Be helpful, friendly, and concise
- For timetable queries, suggest using the timetable viewer
- For study planning, offer to create a study schedule

When you need to:
- Check today's timetable: Use the read_timetable tool
- Find upcoming exams: Use the notify_upcoming_exams tool
- Create a study plan: Use the generate_study_plan tool
- Browse available documents: Use the browse_local_files tool

Current context from documents:
{context}

Available sources:
{sources}
"""


def detect_tool_intent(message: str) -> Optional[Dict[str, Any]]:
    """
    Detect if the message requires a tool call.
    
    Args:
        message: User message
        
    Returns:
        Tool call info or None
    """
    message_lower = message.lower()
    
    # Timetable queries
    timetable_keywords = ["timetable", "class today", "schedule", "classes", "lecture"]
    if any(kw in message_lower for kw in timetable_keywords):
        # Extract day if mentioned
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "today", "tomorrow"]
        day = None
        for d in days:
            if d in message_lower:
                day = d
                break
        return {
            "tool": "read_timetable_file",
            "params": {"day": day or "today"}
        }
    
    # Exam queries
    exam_keywords = ["exam", "upcoming exam", "next exam", "exam schedule", "exam date"]
    if any(kw in message_lower for kw in exam_keywords):
        return {
            "tool": "notify_upcoming_exams",
            "params": {}
        }
    
    # Study plan queries
    study_keywords = ["study plan", "study schedule", "prepare for", "how to study", "exam preparation"]
    if any(kw in message_lower for kw in study_keywords):
        return {
            "tool": "generate_study_plan",
            "params": {"subjects": [], "exam_date": None, "hours_per_day": 6}
        }
    
    # File browsing queries
    file_keywords = ["list files", "show documents", "available files", "browse files", "notices"]
    if any(kw in message_lower for kw in file_keywords):
        return {
            "tool": "browse_local_files",
            "params": {"path": os.getenv("DATA_DIR", "./data")}
        }
    
    return None


async def call_mcp_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call an MCP tool on the MCP server.
    
    Args:
        tool_name: Name of the tool to call
        params: Tool parameters
        
    Returns:
        Tool response
    """
    mcp_host = os.getenv("MCP_SERVER_HOST", "localhost")
    mcp_port = int(os.getenv("MCP_SERVER_PORT", 8002))
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{mcp_host}:{mcp_port}/tools/{tool_name}",
                json=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"error": str(e), "tool": tool_name}
    except Exception as e:
        return {"error": str(e), "tool": tool_name}


async def generate_llm_response(
    message: str,
    context: str,
    sources: List[Dict[str, Any]],
    conversation_history: List[ChatMessage],
    tool_results: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate response using Groq.
    
    Args:
        message: User message
        context: RAG context
        sources: Source documents
        conversation_history: Previous messages
        tool_results: Results from MCP tools
        
    Returns:
        Generated response
    """
    try:
        from groq import Groq
    except ImportError:
        return "Groq package not installed. Please install with: pip install groq"
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Groq API key not configured. Please set GROQ_API_KEY environment variable."
    
    client = Groq(api_key=api_key)
    
    # Format sources
    sources_text = "\n".join([
        f"- {s.get('filename', 'Unknown')} ({s.get('category', 'unknown')})"
        for s in sources
    ])
    
    # Build system prompt
    system_prompt = SYSTEM_PROMPT.format(
        context=context or "No relevant context found.",
        sources=sources_text or "No sources available."
    )
    
    # Add tool results if available
    if tool_results:
        system_prompt += f"\n\nTool Results:\n{json.dumps(tool_results, indent=2)}"
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for msg in conversation_history[-10:]:  # Last 10 messages
        messages.append({"role": msg.role, "content": msg.content})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    try:
        model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest):
    """
    Main chat endpoint.
    
    Processes user message with RAG retrieval and optional MCP tool calls.
    """
    message = chat_request.message
    conversation_history = chat_request.conversation_history or []
    
    # Get RAG pipeline from app state
    rag_pipeline = request.app.state.rag_pipeline
    
    sources = []
    context = ""
    tool_calls = []
    tool_results = None
    
    # Check for tool intent
    if chat_request.use_tools:
        tool_intent = detect_tool_intent(message)
        if tool_intent:
            tool_results = await call_mcp_tool(
                tool_intent["tool"],
                tool_intent["params"]
            )
            tool_calls.append({
                "tool": tool_intent["tool"],
                "params": tool_intent["params"],
                "result": tool_results
            })
    
    # Perform RAG retrieval
    if chat_request.use_rag:
        try:
            rag_result = rag_pipeline.query(message)
            context = rag_result.get("context", "")
            sources = rag_result.get("sources", [])
        except Exception as e:
            print(f"RAG query error: {e}")
    
    # Generate response
    response_text = await generate_llm_response(
        message=message,
        context=context,
        sources=sources,
        conversation_history=conversation_history,
        tool_results=tool_results
    )
    
    return ChatResponse(
        response=response_text,
        sources=sources,
        tool_calls=tool_calls,
        metadata={
            "rag_enabled": chat_request.use_rag,
            "tools_enabled": chat_request.use_tools,
            "context_length": len(context)
        }
    )


@router.post("/rag/query")
async def rag_query(request: Request, query_request: RAGQueryRequest):
    """
    Direct RAG query endpoint.
    
    Returns raw retrieval results without LLM processing.
    """
    rag_pipeline = request.app.state.rag_pipeline
    
    try:
        result = rag_pipeline.query(
            query=query_request.query,
            top_k=query_request.top_k,
            filter_category=query_request.category
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(request: Request):
    """Get RAG pipeline statistics."""
    rag_pipeline = request.app.state.rag_pipeline
    return rag_pipeline.get_stats()
