import json
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT))


from tools.knowledge_index import KnowledgeIndex


DATASET_PATH = PROJECT_ROOT / "benchmarks" / "rag" / "dataset.json"
RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"

def reciprocal_rank(results, expected_sources):
    for rank, result in enumerate(results, start=1):
        if result["source"] in expected_sources:
            return 1.0 / rank

    return 0.0

def deduplicate_sources(results):
    unique = []
    seen = set()

    for result in results:
        source = result["source"]

        if source in seen:
            continue

        seen.add(source)
        unique.append(result)

    return unique

def recall_at_k(results, expected_sources, k):
    retrieved = {
        result["source"]
        for result in results[:k]
    }

    return int(bool(retrieved.intersection(expected_sources)))


def main():
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        dataset = json.load(f)

    index = KnowledgeIndex()

    query_results = []

    for item in dataset["queries"]:
        query = item["query"]
        expected_sources = set(item["expected_sources"])

        start = time.perf_counter()

        results = index.search(
            query=query,
            top_k=5,
        )

        results = deduplicate_sources(results)
        
        latency_ms = (time.perf_counter() - start) * 1000

        result = {
            "id": item["id"],
            "query": query,
            "expected_sources": sorted(expected_sources),
            "retrieved_sources": [
                result["source"]
                for result in results
            ],
            "recall_at_1": recall_at_k(
                results,
                expected_sources,
                1,
            ),
            "recall_at_3": recall_at_k(
                results,
                expected_sources,
                3,
            ),
            "recall_at_5": recall_at_k(
                results,
                expected_sources,
                5,
            ),
            "mrr": reciprocal_rank(
                results,
                expected_sources,
            ),
            "latency_ms": round(latency_ms, 3),
        }

        query_results.append(result)

    count = len(query_results)

    summary = {
        "queries": count,
        "recall_at_1": round(
            sum(r["recall_at_1"] for r in query_results) / count,
            4,
        ),
        "recall_at_3": round(
            sum(r["recall_at_3"] for r in query_results) / count,
            4,
        ),
        "recall_at_5": round(
            sum(r["recall_at_5"] for r in query_results) / count,
            4,
        ),
        "mrr": round(
            sum(r["mrr"] for r in query_results) / count,
            4,
        ),
        "average_latency_ms": round(
            sum(r["latency_ms"] for r in query_results) / count,
            3,
        ),
    }

    output = {
        "summary": summary,
        "queries": query_results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_DIR / "rag_baseline.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            output,
            f,
            indent=2,
        )

    print("\n========== RAG Evaluation ==========")

    print(f"Queries:          {summary['queries']}")
    print(f"Recall@1:         {summary['recall_at_1']:.4f}")
    print(f"Recall@3:         {summary['recall_at_3']:.4f}")
    print(f"Recall@5:         {summary['recall_at_5']:.4f}")
    print(f"MRR:              {summary['mrr']:.4f}")
    print(
        f"Average latency:  "
        f"{summary['average_latency_ms']:.3f} ms"
    )

    print(f"\nResults saved to: {output_path}")

    print("\nPer-query results:")

    for result in query_results:
        print(
            f"\n{result['id']}: "
            f"{result['query']}"
        )

        print(
            f"  Recall@1={result['recall_at_1']} "
            f"Recall@3={result['recall_at_3']} "
            f"Recall@5={result['recall_at_5']} "
            f"MRR={result['mrr']:.4f}"
        )

        print(
            f"  Retrieved: "
            f"{result['retrieved_sources']}"
        )


if __name__ == "__main__":
    main()