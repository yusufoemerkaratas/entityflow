import json
import os
import sys
from dataclasses import dataclass


current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, "..")
sys.path.insert(0, project_root)

from app.extractors.regex_extractor import RegexExtractor
from app.extractors.spacy_extractor import SpacyExtractor

try:
    from app.extractors.llm_extractor import LlmExtractor
except ImportError:
    LlmExtractor = None


TYPE_ALIASES = {
    "company": "organization",
    "country": "location",
    "domain": "url",
}


@dataclass
class EvaluationResult:
    expected: int
    found: int
    correct: int
    precision: float
    recall: float
    sample_count: int
    skipped: bool = False
    skip_reason: str | None = None
    missing_matches: list[str] | None = None


def load_samples(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    cleaned = text.strip().lower()
    cleaned = " ".join(cleaned.split())
    return cleaned.rstrip(".,;:")


def normalize_type(entity_type: str) -> str:
    canonical = entity_type.strip().lower()
    return TYPE_ALIASES.get(canonical, canonical)


def normalize_pair(entity_type: str, entity_text: str) -> tuple[str, str]:
    return normalize_type(entity_type), normalize_text(entity_text)


def instantiate_extractors() -> list:
    extractors = [RegexExtractor()]

    try:
        extractors.append(SpacyExtractor())
    except Exception as exc:
        print(f"[WARNING] SpacyExtractor unavailable: {exc}")

    if LlmExtractor is not None:
        try:
            extractors.append(LlmExtractor())
        except Exception as exc:
            print(f"[WARNING] LlmExtractor unavailable: {exc}")

    return extractors


def evaluate_extractor(extractor, samples: list[dict]) -> EvaluationResult:
    total_expected = 0
    total_found = 0
    total_correct = 0
    missing_matches: list[str] = []
    runtime_failures = 0

    for sample in samples:
        expected_list = sample.get("expected", [])
        total_expected += len(expected_list)

        try:
            extracted_objects = extractor.extract(sample["text"])
        except Exception as exc:
            error_message = str(exc)
            if getattr(extractor, "name", "") == "llm_mini":
                return EvaluationResult(
                    expected=total_expected,
                    found=0,
                    correct=0,
                    precision=0.0,
                    recall=0.0,
                    sample_count=len(samples),
                    skipped=True,
                    skip_reason=f"llm_mini unavailable in this environment: {error_message}",
                    missing_matches=[],
                )

            runtime_failures += 1
            print(f"  [ERROR] {extractor.name} failed on sample {sample['id']}: {exc}")
            continue

        extracted_pairs = {
            normalize_pair(obj.entity_type, obj.entity_text)
            for obj in extracted_objects
        }
        total_found += len(extracted_pairs)

        for expected in expected_list:
            expected_pair = normalize_pair(
                expected["entity_type"],
                expected["entity_text"],
            )
            if expected_pair in extracted_pairs:
                total_correct += 1
            else:
                missing_matches.append(
                    f"sample {sample['id']}: missing {expected_pair[0]} -> {expected_pair[1]}"
                )

    if runtime_failures == len(samples):
        return EvaluationResult(
            expected=total_expected,
            found=0,
            correct=0,
            precision=0.0,
            recall=0.0,
            sample_count=len(samples),
            skipped=True,
            skip_reason=f"{extractor.name} failed on every sample in this environment",
            missing_matches=[],
        )

    precision = total_correct / total_found if total_found > 0 else 0.0
    recall = total_correct / total_expected if total_expected > 0 else 0.0

    return EvaluationResult(
        expected=total_expected,
        found=total_found,
        correct=total_correct,
        precision=round(precision, 2),
        recall=round(recall, 2),
        sample_count=len(samples),
        missing_matches=missing_matches[:10],
    )


def print_results(name: str, result: EvaluationResult) -> None:
    print(f"\n[{name.upper()}] RESULTS {'-' * 20}")
    print(f"  Samples   : {result.sample_count}")

    if result.skipped:
        print(f"  Status    : SKIPPED")
        print(f"  Reason    : {result.skip_reason}")
        print("-" * 40)
        return

    print(f"  Expected  : {result.expected}")
    print(f"  Found     : {result.found}")
    print(f"  Correct   : {result.correct}")
    print(f"  Precision : {result.precision}")
    print(f"  Recall    : {result.recall}")

    if result.missing_matches:
        print("  Misses    :")
        for miss in result.missing_matches:
            print(f"    - {miss}")

    print("-" * 40)


if __name__ == "__main__":
    data_path = os.path.join(project_root, "data", "samples.json")
    if not os.path.exists(data_path):
        print(f"[FATAL] Test data not found: {data_path}")
        sys.exit(1)

    test_samples = load_samples(data_path)
    print(
        f"[SYSTEM] Loaded {len(test_samples)} golden samples from {data_path}. Starting evaluation...\n"
    )

    for extractor in instantiate_extractors():
        print(f"[SYSTEM] Testing {extractor.name}...")
        result = evaluate_extractor(extractor, test_samples)
        print_results(extractor.name, result)
