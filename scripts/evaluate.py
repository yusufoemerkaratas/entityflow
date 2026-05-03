import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.extractors.regex_extractor import RegexExtractor
from app.extractors.spacy_extractor import SpacyExtractor


def load_samples(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(text: str) -> str:
    return text.strip().lower()


def evaluate_extractor(extractor, samples: list) -> dict:
    total_expected = 0
    total_found = 0
    total_correct = 0

    for sample in samples:
        expected = sample["expected"]
        extracted = extractor.extract(sample["text"])

        extracted_normalized = [
            (e.entity_type.lower(), normalize(e.entity_text))
            for e in extracted
        ]

        for exp in expected:
            total_expected += 1
            exp_pair = (exp["entity_type"].lower(), normalize(exp["entity_text"]))
            if exp_pair in extracted_normalized:
                total_correct += 1

        total_found += len(extracted)

    precision = total_correct / total_found if total_found > 0 else 0.0
    recall = total_correct / total_expected if total_expected > 0 else 0.0

    return {
        "total_expected": total_expected,
        "total_found": total_found,
        "total_correct": total_correct,
        "precision": round(precision, 2),
        "recall": round(recall, 2),
    }


def print_results(name: str, results: dict):
    print(f"\n{'='*40}")
    print(f"Extractor : {name}")
    print(f"  Expected : {results['total_expected']}")
    print(f"  Found    : {results['total_found']}")
    print(f"  Correct  : {results['total_correct']}")
    print(f"  Precision: {results['precision']}")
    print(f"  Recall   : {results['recall']}")
    print(f"{'='*40}")


if __name__ == "__main__":
    samples_path = os.path.join(os.path.dirname(__file__), "..", "data", "samples.json")
    samples = load_samples(samples_path)

    regex_extractor = RegexExtractor()
    spacy_extractor = SpacyExtractor()

    regex_results = evaluate_extractor(regex_extractor, samples)
    spacy_results = evaluate_extractor(spacy_extractor, samples)

    print_results("RegexExtractor", regex_results)
    print_results("SpacyExtractor", spacy_results)