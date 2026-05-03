import json
import sys
import os

current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, "..")
sys.path.insert(0, project_root)

from app.extractors.regex_extractor import RegexExtractor
from app.extractors.spacy_extractor import SpacyExtractor

try:
    from app.extractors.llm_extractor import LlmExtractor
    HAS_LLM = True
except ImportError as e:
    print(f"[WARNING] LlmExtractor could not be imported: {e}")
    HAS_LLM = False

def load_samples(path: str) -> list:
    """Reads JSON data from the given path and returns a Python list."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def normalize_text(text: str) -> str:
    """Standardizes text to prevent comparison mismatch."""
    if not isinstance(text, str):
        return ""
    return text.strip().lower()

def evaluate_extractor(extractor, samples: list) -> dict:
    """Evaluates a single extractor against the test set."""
    total_expected = 0
    total_found = 0
    total_correct = 0

    for sample in samples:
        expected_list = sample.get("expected", [])
        
        try:
            # Polymorphism: Calling .extract() without knowing the exact object type
            extracted_objects = extractor.extract(sample["text"])
        except Exception as e:
            print(f"  [ERROR] {extractor.name} crashed while processing text: {str(e)}")
            extracted_objects = []

        # List Comprehension: Extract types and normalized text into tuples
        extracted_tuples = [
            (obj.entity_type.lower(), normalize_text(obj.entity_text))
            for obj in extracted_objects
        ]

        # Match exact expectations
        for exp in expected_list:
            total_expected += 1
            exp_pair = (exp["entity_type"].lower(), normalize_text(exp["entity_text"]))
            
            if exp_pair in extracted_tuples:
                total_correct += 1

        total_found += len(extracted_objects)

    # Prevent ZeroDivisionError
    precision = total_correct / total_found if total_found > 0 else 0.0
    recall = total_correct / total_expected if total_expected > 0 else 0.0

    return {
        "expected": total_expected,
        "found": total_found,
        "correct": total_correct,
        "precision": round(precision, 2),
        "recall": round(recall, 2)
    }

def print_results(name: str, results: dict):
    print(f"\n[{name.upper()}] RESULTS {'-'*20}")
    print(f"  Expected : {results['expected']}")
    print(f"  Found    : {results['found']}")
    print(f"  Correct  : {results['correct']}")
    print(f"  PRECISION: {results['precision']}  ")
    print(f"  RECALL   : {results['recall']} ")
    print("-" * 40)

if __name__ == "__main__":
    # 1. Locate and load test data
    data_path = os.path.join(project_root, "data", "samples.json")
    if not os.path.exists(data_path):
        print(f"[FATAL] Test data not found: {data_path}")
        sys.exit(1)
        
    print("[SYSTEM] Evaluation data loaded. Starting tests...\n")
    test_samples = load_samples(data_path)

    # 2. Instantiate extractors
    extractors_to_test = [
        RegexExtractor(),
        SpacyExtractor()
    ]
    
    # Conditionally add LLM
    if HAS_LLM:
        extractors_to_test.append(LlmExtractor())

    # 3. Execute evaluation sequence
    for ext in extractors_to_test:
        print(f"[SYSTEM] Testing {ext.name}...")
        ext_results = evaluate_extractor(ext, test_samples)
        print_results(ext.name, ext_results)