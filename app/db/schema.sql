CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    raw_text TEXT NOT NULL,
    source_type TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    char_count INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE extractions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    extractor_name TEXT NOT NULL,
    extractor_version TEXT NOT NULL,
    processing_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    extraction_id INTEGER NOT NULL REFERENCES extractions(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    entity_text TEXT NOT NULL,
    normalized_value TEXT,
    confidence FLOAT,
    span_start INTEGER,
    span_end INTEGER,
    review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected'))
);


CREATE INDEX idx_documents_content_hash ON documents(content_hash);
CREATE INDEX idx_extractions_document_id ON extractions(document_id);
CREATE INDEX idx_entities_extraction_id ON entities(extraction_id);
CREATE INDEX idx_entities_entity_type ON entities(entity_type);
CREATE INDEX idx_entities_review_status ON entities(review_status);