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


CREATE TABLE IF NOT EXISTS vision_inspections (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    image_width INTEGER NOT NULL,
    image_height INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vision_detections (
    id SERIAL PRIMARY KEY,
    inspection_id INTEGER NOT NULL REFERENCES vision_inspections(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x INTEGER NOT NULL,
    bbox_y INTEGER NOT NULL,
    bbox_width INTEGER NOT NULL,
    bbox_height INTEGER NOT NULL,
    review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending', 'accepted', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_vision_detections_inspection_id ON vision_detections(inspection_id);
CREATE INDEX IF NOT EXISTS idx_vision_detections_review_status ON vision_detections(review_status);