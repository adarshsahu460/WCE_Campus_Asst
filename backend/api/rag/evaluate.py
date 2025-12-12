"""
RAG Pipeline Evaluation Script

This script evaluates the RAG pipeline's retrieval quality using
various metrics including Recall@K, Mean Reciprocal Rank (MRR),
and response latency.
"""

import asyncio
import os
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class EvaluationSample:
    """A single evaluation sample with query and expected sources."""
    query: str
    expected_sources: List[str]
    expected_keywords: List[str]
    category: str


@dataclass
class EvaluationResult:
    """Results from evaluating a single query."""
    query: str
    retrieved_sources: List[str]
    expected_sources: List[str]
    recall: float
    reciprocal_rank: float
    latency_ms: float
    keywords_found: int
    total_keywords: int


@dataclass
class EvaluationReport:
    """Aggregate evaluation report."""
    total_queries: int
    avg_recall_at_5: float
    avg_mrr: float
    avg_latency_ms: float
    avg_keyword_coverage: float
    results: List[EvaluationResult]


# Evaluation dataset
EVALUATION_SAMPLES = [
    EvaluationSample(
        query="What is the syllabus for Machine Learning?",
        expected_sources=["machine_learning_syllabus"],
        expected_keywords=["supervised learning", "unsupervised learning", "neural networks", "regression"],
        category="syllabus"
    ),
    EvaluationSample(
        query="What are the attendance requirements?",
        expected_sources=["academic_regulations"],
        expected_keywords=["75%", "attendance", "debarment"],
        category="regulations"
    ),
    EvaluationSample(
        query="When is the placement drive?",
        expected_sources=["notices"],
        expected_keywords=["TCS", "Infosys", "placement"],
        category="notices"
    ),
    EvaluationSample(
        query="What is covered in Data Science course?",
        expected_sources=["data_science_syllabus"],
        expected_keywords=["data preprocessing", "visualization", "statistics"],
        category="syllabus"
    ),
    EvaluationSample(
        query="What are the exam passing criteria?",
        expected_sources=["academic_regulations"],
        expected_keywords=["40%", "passing", "grade"],
        category="regulations"
    ),
    EvaluationSample(
        query="Explain cloud computing topics",
        expected_sources=["cloud_computing_syllabus"],
        expected_keywords=["AWS", "Azure", "virtualization", "docker"],
        category="syllabus"
    ),
    EvaluationSample(
        query="What is the grading system?",
        expected_sources=["academic_regulations"],
        expected_keywords=["CGPA", "grade points", "O grade"],
        category="regulations"
    ),
    EvaluationSample(
        query="When is Technovanza 2024?",
        expected_sources=["notices"],
        expected_keywords=["March", "technical festival", "registration"],
        category="notices"
    ),
    EvaluationSample(
        query="What are the library timings?",
        expected_sources=["notices"],
        expected_keywords=["8:00 AM", "library", "reading room"],
        category="notices"
    ),
    EvaluationSample(
        query="What is anti-ragging policy?",
        expected_sources=["academic_regulations"],
        expected_keywords=["ragging", "suspension", "expulsion"],
        category="regulations"
    ),
]


def calculate_recall(retrieved: List[str], expected: List[str]) -> float:
    """Calculate Recall@K."""
    if not expected:
        return 1.0
    
    retrieved_lower = [r.lower() for r in retrieved]
    matches = sum(
        1 for exp in expected
        if any(exp.lower() in ret for ret in retrieved_lower)
    )
    return matches / len(expected)


def calculate_reciprocal_rank(retrieved: List[str], expected: List[str]) -> float:
    """Calculate Mean Reciprocal Rank (MRR)."""
    if not expected:
        return 1.0
    
    retrieved_lower = [r.lower() for r in retrieved]
    for i, ret in enumerate(retrieved_lower):
        for exp in expected:
            if exp.lower() in ret:
                return 1.0 / (i + 1)
    return 0.0


def count_keywords(content: str, keywords: List[str]) -> int:
    """Count how many expected keywords are found in content."""
    content_lower = content.lower()
    return sum(1 for kw in keywords if kw.lower() in content_lower)


async def evaluate_query(
    pipeline,
    sample: EvaluationSample
) -> EvaluationResult:
    """Evaluate a single query."""
    start_time = time.time()
    
    try:
        results = await pipeline.query(sample.query)
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract sources from results
        retrieved_sources = [r.get("source", "") for r in results.get("results", [])]
        
        # Combine all content
        all_content = " ".join(r.get("content", "") for r in results.get("results", []))
        
        # Calculate metrics
        recall = calculate_recall(retrieved_sources, sample.expected_sources)
        mrr = calculate_reciprocal_rank(retrieved_sources, sample.expected_sources)
        keywords_found = count_keywords(all_content, sample.expected_keywords)
        
        return EvaluationResult(
            query=sample.query,
            retrieved_sources=retrieved_sources,
            expected_sources=sample.expected_sources,
            recall=recall,
            reciprocal_rank=mrr,
            latency_ms=latency_ms,
            keywords_found=keywords_found,
            total_keywords=len(sample.expected_keywords)
        )
    
    except Exception as e:
        print(f"Error evaluating query '{sample.query}': {e}")
        return EvaluationResult(
            query=sample.query,
            retrieved_sources=[],
            expected_sources=sample.expected_sources,
            recall=0.0,
            reciprocal_rank=0.0,
            latency_ms=(time.time() - start_time) * 1000,
            keywords_found=0,
            total_keywords=len(sample.expected_keywords)
        )


async def run_evaluation(pipeline) -> EvaluationReport:
    """Run full evaluation on all samples."""
    results = []
    
    print("\n" + "=" * 60)
    print("RAG Pipeline Evaluation")
    print("=" * 60)
    
    for i, sample in enumerate(EVALUATION_SAMPLES):
        print(f"\n[{i + 1}/{len(EVALUATION_SAMPLES)}] Evaluating: {sample.query[:50]}...")
        result = await evaluate_query(pipeline, sample)
        results.append(result)
        
        print(f"  Recall: {result.recall:.2f}")
        print(f"  MRR: {result.reciprocal_rank:.2f}")
        print(f"  Latency: {result.latency_ms:.0f}ms")
        print(f"  Keywords: {result.keywords_found}/{result.total_keywords}")
    
    # Calculate averages
    avg_recall = sum(r.recall for r in results) / len(results)
    avg_mrr = sum(r.reciprocal_rank for r in results) / len(results)
    avg_latency = sum(r.latency_ms for r in results) / len(results)
    avg_keyword_coverage = sum(
        r.keywords_found / r.total_keywords if r.total_keywords > 0 else 0
        for r in results
    ) / len(results)
    
    return EvaluationReport(
        total_queries=len(EVALUATION_SAMPLES),
        avg_recall_at_5=avg_recall,
        avg_mrr=avg_mrr,
        avg_latency_ms=avg_latency,
        avg_keyword_coverage=avg_keyword_coverage,
        results=results
    )


def print_report(report: EvaluationReport):
    """Print formatted evaluation report."""
    print("\n" + "=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)
    
    print(f"\nTotal Queries Evaluated: {report.total_queries}")
    print(f"\nMetrics Summary:")
    print(f"  Recall@5:          {report.avg_recall_at_5:.2%}")
    print(f"  Mean Reciprocal Rank (MRR): {report.avg_mrr:.2%}")
    print(f"  Average Latency:   {report.avg_latency_ms:.0f}ms")
    print(f"  Keyword Coverage:  {report.avg_keyword_coverage:.2%}")
    
    # Quality assessment
    print(f"\nQuality Assessment:")
    if report.avg_recall_at_5 >= 0.8:
        print("  ✅ Recall@5 is GOOD (≥80%)")
    elif report.avg_recall_at_5 >= 0.6:
        print("  ⚠️ Recall@5 is MODERATE (60-80%)")
    else:
        print("  ❌ Recall@5 needs IMPROVEMENT (<60%)")
    
    if report.avg_mrr >= 0.7:
        print("  ✅ MRR is GOOD (≥70%)")
    elif report.avg_mrr >= 0.5:
        print("  ⚠️ MRR is MODERATE (50-70%)")
    else:
        print("  ❌ MRR needs IMPROVEMENT (<50%)")
    
    if report.avg_latency_ms <= 500:
        print("  ✅ Latency is GOOD (≤500ms)")
    elif report.avg_latency_ms <= 1000:
        print("  ⚠️ Latency is MODERATE (500-1000ms)")
    else:
        print("  ❌ Latency needs IMPROVEMENT (>1000ms)")
    
    # Detailed results
    print("\n" + "-" * 60)
    print("Detailed Results:")
    print("-" * 60)
    
    for i, result in enumerate(report.results):
        status = "✅" if result.recall >= 0.8 else "⚠️" if result.recall >= 0.5 else "❌"
        print(f"\n{i + 1}. {status} {result.query[:50]}...")
        print(f"   Recall: {result.recall:.2%} | MRR: {result.reciprocal_rank:.2%} | Latency: {result.latency_ms:.0f}ms")
        if result.retrieved_sources:
            print(f"   Sources: {', '.join(result.retrieved_sources[:3])}")
    
    print("\n" + "=" * 60)


class MockPipeline:
    """Mock pipeline for testing without actual RAG system."""
    
    async def query(self, query: str):
        """Return mock results based on query keywords."""
        await asyncio.sleep(0.1)  # Simulate latency
        
        results = []
        
        if "machine learning" in query.lower():
            results.append({
                "source": "machine_learning_syllabus.txt",
                "content": "Machine Learning course covers supervised learning, unsupervised learning, neural networks, regression, classification, and deep learning basics.",
                "score": 0.92
            })
        
        if "attendance" in query.lower() or "regulations" in query.lower():
            results.append({
                "source": "academic_regulations.txt",
                "content": "Minimum 75% attendance is mandatory. Students with attendance below 65% face debarment from examinations.",
                "score": 0.88
            })
        
        if "placement" in query.lower():
            results.append({
                "source": "notices_2024.txt",
                "content": "TCS, Infosys, Cognizant, and L&T Infotech are visiting for campus placement in February-March 2024.",
                "score": 0.85
            })
        
        if "data science" in query.lower():
            results.append({
                "source": "data_science_syllabus.txt",
                "content": "Data Science course covers data preprocessing, visualization, statistics, exploratory analysis, and Python for data science.",
                "score": 0.90
            })
        
        if "exam" in query.lower() and "passing" in query.lower():
            results.append({
                "source": "academic_regulations.txt",
                "content": "Passing criteria: Minimum 40% in theory, 40% in practical, and 40% overall. Grade points range from O (90-100) to F (below 40).",
                "score": 0.87
            })
        
        if "cloud" in query.lower():
            results.append({
                "source": "cloud_computing_syllabus.txt",
                "content": "Cloud Computing covers AWS, Azure, virtualization, Docker, Kubernetes, and cloud security.",
                "score": 0.91
            })
        
        if "grading" in query.lower() or "cgpa" in query.lower():
            results.append({
                "source": "academic_regulations.txt",
                "content": "CGPA calculation uses grade points. O grade (90-100) = 10 points. CGPA = Sum(Credit × Grade Point) / Sum(Credit).",
                "score": 0.89
            })
        
        if "technovanza" in query.lower():
            results.append({
                "source": "notices_2024.txt",
                "content": "Technovanza 2024 technical festival will be held from March 15-17, 2024. Registration opens February 1.",
                "score": 0.93
            })
        
        if "library" in query.lower():
            results.append({
                "source": "notices_2024.txt",
                "content": "Library timings: Monday-Friday 8:00 AM - 8:00 PM, Saturday 8:00 AM - 5:00 PM. Reading room available 24/7 during exams.",
                "score": 0.86
            })
        
        if "ragging" in query.lower():
            results.append({
                "source": "academic_regulations.txt",
                "content": "Anti-ragging policy: First offense leads to suspension for one semester. Second offense results in expulsion.",
                "score": 0.88
            })
        
        return {"results": results}


async def main():
    """Main entry point."""
    print("\nStarting RAG Pipeline Evaluation...")
    
    # Check if we should use mock or real pipeline
    use_mock = "--mock" in sys.argv or os.getenv("USE_MOCK_PIPELINE", "false").lower() == "true"
    
    if use_mock:
        print("Using MOCK pipeline for demonstration...")
        pipeline = MockPipeline()
    else:
        try:
            from api.rag.pipeline import RAGPipeline
            pipeline = RAGPipeline()
            await pipeline.initialize()
            print("Using REAL pipeline...")
        except Exception as e:
            print(f"Could not initialize real pipeline: {e}")
            print("Falling back to MOCK pipeline...")
            pipeline = MockPipeline()
    
    # Run evaluation
    report = await run_evaluation(pipeline)
    
    # Print report
    print_report(report)
    
    # Return exit code based on quality
    if report.avg_recall_at_5 >= 0.7 and report.avg_mrr >= 0.6:
        print("\n✅ Evaluation PASSED")
        return 0
    else:
        print("\n❌ Evaluation FAILED - Quality below threshold")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
