"""
Document Loader Module
Handles loading of PDF, CSV, and text files for the RAG pipeline.
"""

import os
import csv
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import PyPDF2
import fitz  # PyMuPDF for better PDF handling
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Document:
    """Represents a loaded document with metadata."""
    content: str
    metadata: Dict[str, Any]
    source: str
    doc_type: str


class DocumentLoader:
    """
    Universal document loader supporting PDF, CSV, and text files.
    Uses environment variables for data directories.
    """
    
    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", "./data")
        self.timetable_dir = os.getenv("TIMETABLE_DIR", "./data/timetables")
        self.notices_dir = os.getenv("NOTICES_DIR", "./data/notices")
        self.syllabus_dir = os.getenv("SYLLABUS_DIR", "./data/syllabus")
        self.exams_dir = os.getenv("EXAMS_DIR", "./data/exams")
        self.regulations_dir = os.getenv("REGULATIONS_DIR", "./data/regulations")
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create data directories if they don't exist."""
        directories = [
            self.data_dir,
            self.timetable_dir,
            self.notices_dir,
            self.syllabus_dir,
            self.exams_dir,
            self.regulations_dir
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def load_pdf(self, file_path: str) -> Document:
        """
        Load a PDF file and extract its text content.
        Uses PyMuPDF for better text extraction.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Document object with extracted content
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        text_content = []
        
        try:
            # Try PyMuPDF first (better quality)
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    text_content.append(f"[Page {page_num + 1}]\n{text}")
            doc.close()
        except Exception as e:
            # Fallback to PyPDF2
            print(f"PyMuPDF failed, falling back to PyPDF2: {e}")
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        text_content.append(f"[Page {page_num + 1}]\n{text}")
        
        return Document(
            content="\n\n".join(text_content),
            metadata={
                "source": file_path,
                "type": "pdf",
                "filename": os.path.basename(file_path),
                "page_count": len(text_content)
            },
            source=file_path,
            doc_type="pdf"
        )
    
    def load_csv(self, file_path: str) -> Document:
        """
        Load a CSV file and convert to structured text.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Document object with CSV content as text
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        rows = []
        headers = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames or []
            
            for row in reader:
                # Convert each row to readable text
                row_text = " | ".join([f"{k}: {v}" for k, v in row.items() if v])
                rows.append(row_text)
        
        # Create structured content
        content = f"Headers: {', '.join(headers)}\n\n"
        content += "\n".join(rows)
        
        return Document(
            content=content,
            metadata={
                "source": file_path,
                "type": "csv",
                "filename": os.path.basename(file_path),
                "headers": headers,
                "row_count": len(rows)
            },
            source=file_path,
            doc_type="csv"
        )
    
    def load_text(self, file_path: str) -> Document:
        """
        Load a text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Document object with text content
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return Document(
            content=content,
            metadata={
                "source": file_path,
                "type": "text",
                "filename": os.path.basename(file_path),
                "char_count": len(content)
            },
            source=file_path,
            doc_type="text"
        )
    
    def load_file(self, file_path: str) -> Document:
        """
        Auto-detect file type and load appropriately.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Document object
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            return self.load_pdf(file_path)
        elif ext == '.csv':
            return self.load_csv(file_path)
        elif ext in ['.txt', '.md', '.text']:
            return self.load_text(file_path)
        else:
            # Try to load as text
            return self.load_text(file_path)
    
    def load_directory(self, directory: str, recursive: bool = True) -> List[Document]:
        """
        Load all supported files from a directory.
        
        Args:
            directory: Path to the directory
            recursive: Whether to search subdirectories
            
        Returns:
            List of Document objects
        """
        documents = []
        supported_extensions = {'.pdf', '.csv', '.txt', '.md', '.text'}
        
        path = Path(directory)
        
        if not path.exists():
            print(f"Directory not found: {directory}")
            return documents
        
        pattern = "**/*" if recursive else "*"
        
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    doc = self.load_file(str(file_path))
                    documents.append(doc)
                    print(f"✅ Loaded: {file_path}")
                except Exception as e:
                    print(f"❌ Failed to load {file_path}: {e}")
        
        return documents
    
    def load_all_data(self) -> List[Document]:
        """
        Load all documents from all configured data directories.
        
        Returns:
            List of all Document objects
        """
        all_documents = []
        
        directories = [
            (self.timetable_dir, "timetable"),
            (self.notices_dir, "notice"),
            (self.syllabus_dir, "syllabus"),
            (self.exams_dir, "exam"),
            (self.regulations_dir, "regulation")
        ]
        
        for directory, category in directories:
            print(f"\n📁 Loading {category} documents from {directory}...")
            docs = self.load_directory(directory)
            
            # Add category to metadata
            for doc in docs:
                doc.metadata["category"] = category
            
            all_documents.extend(docs)
            print(f"   Loaded {len(docs)} {category} documents")
        
        print(f"\n📊 Total documents loaded: {len(all_documents)}")
        return all_documents
