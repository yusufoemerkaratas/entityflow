# Demo Script (60-90 seconds)

Hi, I am Yusuf. This is EntityFlow, a lightweight NLP pipeline that extracts structured entities from unstructured text.

First, I upload a raw text document. The backend stores it with SHA-256 deduplication and returns the document id.

Next, I run three extractors side by side: regex, spaCy, and a small LLM-based extractor. You can see the outputs in parallel, with each entity type labeled and the span highlighted in the original text.

The review step is human-in-the-loop: I can approve or reject each entity, and the decision is saved to the database.

The goal is to compare extraction quality quickly, validate results, and keep a clean audit trail of what was accepted.

That is the core workflow. Thank you.