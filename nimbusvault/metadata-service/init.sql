CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY,
    filename VARCHAR,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    user_id UUID,
    tags TEXT[]
);
