"""
File Browser Tool
Browses local files and directories for notices and documents.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

from .base import BaseTool

load_dotenv()


class FileBrowserTool(BaseTool):
    """
    Tool to browse local files and directories.
    Lists available notices, PDFs, and other documents.
    """
    
    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", "./data")
        self.allowed_extensions = {'.pdf', '.csv', '.txt', '.md', '.doc', '.docx'}
    
    @property
    def name(self) -> str:
        return "browse_local_files"
    
    @property
    def description(self) -> str:
        return (
            "Browses local files and directories to list available documents, "
            "notices, and PDFs. Can filter by file type or directory."
        )
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to browse (relative to data directory or absolute)"
                },
                "file_type": {
                    "type": "string",
                    "description": "Filter by file extension (e.g., 'pdf', 'csv')",
                    "enum": ["pdf", "csv", "txt", "md", "all"]
                },
                "category": {
                    "type": "string",
                    "description": "Document category to browse",
                    "enum": ["timetables", "notices", "syllabus", "exams", "regulations", "all"]
                }
            }
        }
    
    def _get_category_path(self, category: str) -> str:
        """Get directory path for a category."""
        category_dirs = {
            "timetables": os.getenv("TIMETABLE_DIR", "./data/timetables"),
            "notices": os.getenv("NOTICES_DIR", "./data/notices"),
            "syllabus": os.getenv("SYLLABUS_DIR", "./data/syllabus"),
            "exams": os.getenv("EXAMS_DIR", "./data/exams"),
            "regulations": os.getenv("REGULATIONS_DIR", "./data/regulations"),
            "all": self.data_dir
        }
        return category_dirs.get(category, self.data_dir)
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File information dict
        """
        try:
            stat = file_path.stat()
            return {
                "name": file_path.name,
                "path": str(file_path),
                "extension": file_path.suffix.lower(),
                "size_bytes": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            }
        except Exception as e:
            return {
                "name": file_path.name,
                "path": str(file_path),
                "error": str(e)
            }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _list_directory(
        self,
        directory: str,
        file_type: Optional[str] = None,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Args:
            directory: Directory path
            file_type: Optional file type filter
            recursive: Whether to search recursively
            
        Returns:
            Directory listing
        """
        path = Path(directory)
        
        if not path.exists():
            return {
                "error": f"Directory not found: {directory}",
                "files": [],
                "directories": []
            }
        
        files = []
        directories = []
        
        # Determine extensions to include
        if file_type and file_type != "all":
            extensions = {f".{file_type}"}
        else:
            extensions = self.allowed_extensions
        
        # List contents
        pattern = "**/*" if recursive else "*"
        
        for item in path.glob(pattern):
            if item.is_file():
                if item.suffix.lower() in extensions:
                    files.append(self._get_file_info(item))
            elif item.is_dir() and not recursive:
                directories.append({
                    "name": item.name,
                    "path": str(item)
                })
        
        # Sort files by name
        files.sort(key=lambda x: x.get("name", ""))
        directories.sort(key=lambda x: x.get("name", ""))
        
        return {
            "directory": str(path),
            "files": files,
            "directories": directories,
            "total_files": len(files),
            "total_directories": len(directories)
        }
    
    def _get_categories_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all categories."""
        categories = ["timetables", "notices", "syllabus", "exams", "regulations"]
        summary = []
        
        for category in categories:
            path = Path(self._get_category_path(category))
            
            if path.exists():
                files = list(path.glob("**/*"))
                file_count = sum(1 for f in files if f.is_file())
                summary.append({
                    "category": category,
                    "path": str(path),
                    "file_count": file_count
                })
            else:
                summary.append({
                    "category": category,
                    "path": str(path),
                    "file_count": 0,
                    "exists": False
                })
        
        return summary
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Browse files and directories.
        
        Args:
            params: {
                "path": "./data/notices",
                "file_type": "pdf",
                "category": "notices"
            }
            
        Returns:
            Directory listing with file details
        """
        path = params.get("path")
        file_type = params.get("file_type")
        category = params.get("category")
        
        # Determine which directory to browse
        if category:
            browse_path = self._get_category_path(category)
        elif path:
            # Handle relative paths
            if not os.path.isabs(path):
                browse_path = os.path.join(self.data_dir, path)
            else:
                browse_path = path
        else:
            # Default: show all categories summary
            return {
                "mode": "categories_summary",
                "categories": self._get_categories_summary(),
                "data_directory": self.data_dir
            }
        
        # List directory
        result = self._list_directory(browse_path, file_type)
        
        # Add category info if available
        if category:
            result["category"] = category
        
        return result
