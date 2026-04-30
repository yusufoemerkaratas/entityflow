# EntityFlow Database Schema

## Overview

EntityFlow stores uploaded text documents, extraction runs, and extracted entities in three core tables:

- `documents`
- `extractions`
- `entities`

This separation makes the system easier to extend, query, and maintain.

## Table: documents

The `documents` table stores the raw input text and its metadata.

### Purpose
- Keep the original uploaded text
- Track the source of the text
- Prevent duplicate uploads using a content hash

### Main fields
- `id`: primary key
- `raw_text`: original input text
- `source_type`: where the text came from
- `content_hash`: unique fingerprint of the text
- `char_count`: text length
- `uploaded_at`: upload timestamp

## Table: extractions

The `extractions` table stores one extraction run for one document.

### Purpose
- Track which extractor was used
- Track extractor version
- Store processing time
- Allow multiple extractor runs on the same document

### Main fields
- `id`: primary key
- `document_id`: foreign key to `documents`
- `extractor_name`: extractor identifier
- `extractor_version`: extractor version
- `processing_ms`: runtime in milliseconds
- `created_at`: extraction timestamp

## Table: entities

The `entities` table stores the individual extracted entities produced by an extraction.

### Purpose
- Store structured extracted values
- Support filtering and review
- Keep text spans for highlighting in the UI

### Main fields
- `id`: primary key
- `extraction_id`: foreign key to `extractions`
- `entity_type`: type of entity
- `entity_text`: extracted text
- `normalized_value`: cleaned or normalized value
- `confidence`: model confidence score
- `span_start`: start character position
- `span_end`: end character position
- `review_status`: human review status

## Relationships

- One document can have many extractions
- One extraction can have many entities

## Notes

- `content_hash` must be unique to prevent duplicate documents
- Foreign keys enforce data integrity
- Indexes are added for common lookup fields