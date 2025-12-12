"""
Upload Route
Handles file upload and indexing.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.csv', '.txt', '.md'}


def get_upload_directory(category: str) -> str:
    """
    Get the appropriate upload directory based on category.
    
    Args:
        category: Document category
        
    Returns:
        Path to upload directory
    """
    category_dirs = {
        "timetable": os.getenv("TIMETABLE_DIR", "./data/timetables"),
        "notice": os.getenv("NOTICES_DIR", "./data/notices"),
        "syllabus": os.getenv("SYLLABUS_DIR", "./data/syllabus"),
        "exam": os.getenv("EXAMS_DIR", "./data/exams"),
        "regulation": os.getenv("REGULATIONS_DIR", "./data/regulations"),
        "general": os.getenv("DATA_DIR", "./data")
    }
    
    return category_dirs.get(category, category_dirs["general"])


def validate_file(file: UploadFile) -> bool:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file
        
    Returns:
        True if valid, raises exception otherwise
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    return True


@router.post("")
@router.post("/")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    category: str = Form(default="general"),
    index_immediately: bool = Form(default=True)
):
    """
    Upload a file and optionally index it.
    
    Args:
        file: File to upload
        category: Document category (timetable, notice, syllabus, exam, regulation)
        index_immediately: Whether to index the file immediately
        
    Returns:
        Upload result
    """
    # Validate file
    validate_file(file)
    
    # Get upload directory
    upload_dir = get_upload_directory(category)
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    result = {
        "filename": file.filename,
        "category": category,
        "path": file_path,
        "size": os.path.getsize(file_path),
        "indexed": False
    }
    
    # Index if requested
    if index_immediately:
        try:
            rag_pipeline = request.app.state.rag_pipeline
            chunks_indexed = rag_pipeline.index_single_document(file_path)
            result["indexed"] = True
            result["chunks_indexed"] = chunks_indexed
        except Exception as e:
            result["index_error"] = str(e)
    
    return result


@router.post("/batch")
async def upload_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    category: str = Form(default="general"),
    index_immediately: bool = Form(default=True)
):
    """
    Upload multiple files.
    
    Args:
        files: Files to upload
        category: Document category
        index_immediately: Whether to index files immediately
        
    Returns:
        Batch upload results
    """
    results = []
    
    for file in files:
        try:
            validate_file(file)
            
            upload_dir = get_upload_directory(category)
            Path(upload_dir).mkdir(parents=True, exist_ok=True)
            
            file_path = os.path.join(upload_dir, file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            result = {
                "filename": file.filename,
                "category": category,
                "path": file_path,
                "size": os.path.getsize(file_path),
                "indexed": False,
                "success": True
            }
            
            if index_immediately:
                try:
                    rag_pipeline = request.app.state.rag_pipeline
                    chunks_indexed = rag_pipeline.index_single_document(file_path)
                    result["indexed"] = True
                    result["chunks_indexed"] = chunks_indexed
                except Exception as e:
                    result["index_error"] = str(e)
            
            results.append(result)
            
        except HTTPException as e:
            results.append({
                "filename": file.filename if file.filename else "unknown",
                "success": False,
                "error": e.detail
            })
        except Exception as e:
            results.append({
                "filename": file.filename if file.filename else "unknown",
                "success": False,
                "error": str(e)
            })
    
    successful = sum(1 for r in results if r.get("success", False))
    
    return {
        "total": len(files),
        "successful": successful,
        "failed": len(files) - successful,
        "results": results
    }


@router.post("/reindex")
async def reindex_all(request: Request):
    """
    Re-index all documents from data directories.
    
    Clears existing index and rebuilds from scratch.
    """
    try:
        rag_pipeline = request.app.state.rag_pipeline
        
        # Clear existing index
        rag_pipeline.clear_index()
        
        # Re-index all documents
        chunks_indexed = rag_pipeline.load_and_index_documents()
        
        return {
            "success": True,
            "chunks_indexed": chunks_indexed,
            "message": f"Successfully re-indexed {chunks_indexed} chunks"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """Get available document categories and their directories."""
    return {
        "categories": [
            {"name": "timetable", "directory": os.getenv("TIMETABLE_DIR", "./data/timetables")},
            {"name": "notice", "directory": os.getenv("NOTICES_DIR", "./data/notices")},
            {"name": "syllabus", "directory": os.getenv("SYLLABUS_DIR", "./data/syllabus")},
            {"name": "exam", "directory": os.getenv("EXAMS_DIR", "./data/exams")},
            {"name": "regulation", "directory": os.getenv("REGULATIONS_DIR", "./data/regulations")},
            {"name": "general", "directory": os.getenv("DATA_DIR", "./data")}
        ]
    }
