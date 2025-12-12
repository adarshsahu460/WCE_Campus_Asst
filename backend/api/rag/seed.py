"""
Seed Script
Loads all documents from data directories into the vector database.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


async def seed_database():
    """
    Main seed function that loads and indexes all documents.
    """
    from rag.pipeline import RAGPipeline
    
    print("=" * 60)
    print("🌱 WCE Campus Assistant - Database Seeding")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = RAGPipeline()
    await pipeline.initialize()
    
    # Check for existing data
    existing_count = pipeline.vector_db.count()
    if existing_count > 0:
        print(f"\n⚠️  Found {existing_count} existing documents in the database.")
        response = input("Do you want to clear and re-index? (y/n): ").strip().lower()
        if response == 'y':
            pipeline.clear_index()
            print("🗑️  Cleared existing index.")
        else:
            print("Keeping existing data. New documents will be added.")
    
    # Create data directories if they don't exist
    data_dirs = [
        os.getenv("DATA_DIR", "./data"),
        os.getenv("TIMETABLE_DIR", "./data/timetables"),
        os.getenv("NOTICES_DIR", "./data/notices"),
        os.getenv("SYLLABUS_DIR", "./data/syllabus"),
        os.getenv("EXAMS_DIR", "./data/exams"),
        os.getenv("REGULATIONS_DIR", "./data/regulations")
    ]
    
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  📁 Ensured directory exists: {dir_path}")
    
    # Load and index documents
    print("\n📚 Loading and indexing documents...")
    chunks_indexed = pipeline.load_and_index_documents()
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ Seeding Complete!")
    print("=" * 60)
    print(f"  📊 Total chunks indexed: {chunks_indexed}")
    print(f"  💾 Total documents in DB: {pipeline.vector_db.count()}")
    print("\n📌 Next steps:")
    print("  1. Add PDF/CSV files to the data directories")
    print("  2. Run this script again to re-index")
    print("  3. Start the backend server with: python main.py")
    

def create_sample_data():
    """
    Create sample data files for testing.
    """
    print("\n📝 Creating sample data files...")
    
    # Sample timetable CSV
    timetable_content = """day,time,subject,teacher,room
monday,09:00 - 10:00,Data Structures,Dr. Sharma,LH-101
monday,10:00 - 11:00,Computer Networks,Prof. Patel,LH-102
monday,11:15 - 12:15,Database Systems,Dr. Kumar,LH-103
monday,02:00 - 03:00,Operating Systems,Prof. Singh,LH-101
tuesday,09:00 - 10:00,Software Engineering,Dr. Desai,LH-102
tuesday,10:00 - 11:00,Data Structures,Dr. Sharma,LH-101
tuesday,11:15 - 12:15,Computer Networks,Prof. Patel,LH-103
tuesday,02:00 - 05:00,Programming Lab,Mr. Joshi,Lab-201
wednesday,09:00 - 10:00,Database Systems,Dr. Kumar,LH-101
wednesday,10:00 - 11:00,Operating Systems,Prof. Singh,LH-102
wednesday,11:15 - 12:15,Software Engineering,Dr. Desai,LH-103
wednesday,02:00 - 05:00,Database Lab,Dr. Kumar,Lab-202
thursday,09:00 - 10:00,Computer Networks,Prof. Patel,LH-101
thursday,10:00 - 11:00,Data Structures,Dr. Sharma,LH-102
thursday,11:15 - 12:15,Operating Systems,Prof. Singh,LH-103
thursday,02:00 - 03:00,Seminar,Various,Seminar Hall
friday,09:00 - 10:00,Software Engineering,Dr. Desai,LH-101
friday,10:00 - 11:00,Database Systems,Dr. Kumar,LH-102
friday,11:15 - 12:15,Data Structures,Dr. Sharma,LH-103
friday,02:00 - 05:00,Project Work,Project Guide,Lab-203
"""
    
    timetable_dir = os.getenv("TIMETABLE_DIR", "./data/timetables")
    with open(os.path.join(timetable_dir, "class_timetable.csv"), 'w') as f:
        f.write(timetable_content)
    print(f"  ✅ Created: {timetable_dir}/class_timetable.csv")
    
    # Sample exam schedule CSV
    from datetime import datetime, timedelta
    today = datetime.now()
    
    exam_content = "subject,date,time,venue,type\n"
    exams = [
        ("Data Structures", 5, "10:00 AM"),
        ("Computer Networks", 8, "10:00 AM"),
        ("Database Systems", 11, "02:00 PM"),
        ("Operating Systems", 14, "10:00 AM"),
        ("Software Engineering", 17, "02:00 PM")
    ]
    
    for subject, days_offset, time in exams:
        exam_date = (today + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        exam_content += f"{subject},{exam_date},{time},Examination Hall,End Semester\n"
    
    exams_dir = os.getenv("EXAMS_DIR", "./data/exams")
    with open(os.path.join(exams_dir, "exam_schedule.csv"), 'w') as f:
        f.write(exam_content)
    print(f"  ✅ Created: {exams_dir}/exam_schedule.csv")
    
    # Sample academic regulations
    regulations_content = """# WCE Academic Regulations 2024-25

## Chapter 1: General Information

### 1.1 About WCE
Walchand College of Engineering (WCE), Sangli is an autonomous institute affiliated to Shivaji University, Kolhapur. Established in 1947, it is one of the oldest and most prestigious engineering colleges in Maharashtra.

### 1.2 Academic Calendar
The academic year consists of two semesters:
- Odd Semester: July to December
- Even Semester: January to May

## Chapter 2: Examination Rules

### 2.1 Eligibility Criteria
- Minimum 75% attendance is mandatory for appearing in end-semester examinations
- Students must complete all internal assessments and laboratory work
- No dues certificate is required from all departments

### 2.2 Grading System
The college follows a 10-point CGPA system:
- O (Outstanding): 10 points - 90% and above
- A+ (Excellent): 9 points - 80-89%
- A (Very Good): 8 points - 70-79%
- B+ (Good): 7 points - 60-69%
- B (Above Average): 6 points - 50-59%
- C (Average): 5 points - 45-49%
- P (Pass): 4 points - 40-44%
- F (Fail): 0 points - Below 40%

### 2.3 Re-examination Policy
- Students who fail in any subject can appear for re-examination
- Re-examination fee: Rs. 500 per subject
- Maximum two re-examination attempts per subject

## Chapter 3: Code of Conduct

### 3.1 Dress Code
- Students must wear formal attire on campus
- ID cards are mandatory at all times
- Laboratory safety equipment must be worn in labs

### 3.2 Library Rules
- Maintain silence in the library
- Books can be borrowed for 14 days
- Late fee: Rs. 2 per day per book

### 3.3 Hostel Rules
- Hostel gate closes at 10:00 PM
- Guests not allowed in hostel rooms
- Mess timing: Breakfast 7:30-9:00, Lunch 12:30-2:00, Dinner 7:30-9:00

## Chapter 4: Academic Integrity

### 4.1 Anti-Plagiarism Policy
- All assignments must be original work
- Plagiarism above 20% will result in rejection
- Repeated offenses may lead to disciplinary action

### 4.2 Examination Malpractice
- Strict action against copying and cheating
- First offense: Warning and exam cancellation
- Second offense: Suspension for one semester
"""
    
    regulations_dir = os.getenv("REGULATIONS_DIR", "./data/regulations")
    with open(os.path.join(regulations_dir, "academic_regulations.txt"), 'w') as f:
        f.write(regulations_content)
    print(f"  ✅ Created: {regulations_dir}/academic_regulations.txt")
    
    # Sample notice
    notice_content = """# Department Notice

**Date:** December 12, 2024
**Subject:** Important Announcement Regarding End Semester Examinations

Dear Students,

This is to inform all students of the Computer Science and Engineering department:

1. **Examination Schedule**: The end semester examinations will commence from December 20, 2024.

2. **Hall Ticket Distribution**: Hall tickets will be available from December 15, 2024, at the examination section.

3. **Exam Timing**: Morning session: 10:00 AM to 1:00 PM, Afternoon session: 2:00 PM to 5:00 PM

4. **Important Instructions**:
   - Carry your hall ticket and college ID card
   - Reach the examination hall 30 minutes before the exam
   - Electronic devices are strictly prohibited
   - Use only blue or black ink pens

5. **COVID-19 Guidelines**: Wearing masks is mandatory inside the examination hall.

For any queries, contact the examination section.

Best regards,
Dr. P. S. Patil
Head of Department
Computer Science and Engineering
"""
    
    notices_dir = os.getenv("NOTICES_DIR", "./data/notices")
    with open(os.path.join(notices_dir, "exam_notice.txt"), 'w') as f:
        f.write(notice_content)
    print(f"  ✅ Created: {notices_dir}/exam_notice.txt")
    
    # Sample syllabus
    syllabus_content = """# Data Structures Syllabus

## Course Code: CS301
## Credits: 4 (3L + 1T)

### Unit 1: Introduction to Data Structures (8 hours)
- Basic Terminology: Data, Information, Data Structure
- Classification of Data Structures
- Arrays: 1D, 2D, Multi-dimensional
- Time and Space Complexity Analysis
- Big O, Omega, and Theta Notations

### Unit 2: Stacks and Queues (8 hours)
- Stack ADT: Operations, Implementation
- Applications: Expression Evaluation, Parenthesis Matching
- Queue ADT: Simple, Circular, Priority Queue
- Deque (Double-Ended Queue)
- Applications of Queues

### Unit 3: Linked Lists (8 hours)
- Singly Linked List: Operations, Implementation
- Doubly Linked List
- Circular Linked List
- Applications: Polynomial Representation
- Comparison with Arrays

### Unit 4: Trees (10 hours)
- Tree Terminology and Representation
- Binary Trees: Types and Properties
- Tree Traversals: Inorder, Preorder, Postorder
- Binary Search Trees (BST)
- AVL Trees: Rotations and Balancing
- B-Trees and B+ Trees

### Unit 5: Graphs (8 hours)
- Graph Terminology and Representation
- Graph Traversals: BFS and DFS
- Shortest Path Algorithms: Dijkstra, Floyd-Warshall
- Minimum Spanning Tree: Prim's, Kruskal's
- Topological Sorting

### Unit 6: Searching and Sorting (6 hours)
- Linear and Binary Search
- Hashing: Hash Functions, Collision Resolution
- Sorting Algorithms: Bubble, Selection, Insertion
- Advanced Sorting: Merge Sort, Quick Sort, Heap Sort
- Comparison of Sorting Algorithms

## Reference Books:
1. "Data Structures Using C" - Reema Thareja
2. "Introduction to Algorithms" - Cormen, Leiserson, Rivest, Stein
3. "Data Structures and Algorithms Made Easy" - Narasimha Karumanchi

## Evaluation Scheme:
- Internal Assessment: 30 marks
- End Semester Exam: 70 marks
- Practical: 50 marks (separate)
"""
    
    syllabus_dir = os.getenv("SYLLABUS_DIR", "./data/syllabus")
    with open(os.path.join(syllabus_dir, "data_structures_syllabus.txt"), 'w') as f:
        f.write(syllabus_content)
    print(f"  ✅ Created: {syllabus_dir}/data_structures_syllabus.txt")
    
    print("\n✅ Sample data files created successfully!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed the WCE Campus Assistant database")
    parser.add_argument(
        "--create-samples",
        action="store_true",
        help="Create sample data files for testing"
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Only seed the database without creating samples"
    )
    
    args = parser.parse_args()
    
    if args.create_samples or not args.seed_only:
        create_sample_data()
    
    if not args.create_samples or args.seed_only:
        asyncio.run(seed_database())
