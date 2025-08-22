-- Create conversations table for storing TA interactions
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    user_question TEXT NOT NULL,
    ta_response TEXT NOT NULL,
    context_sources TEXT[] DEFAULT '{}',
    concepts_used TEXT[] DEFAULT '{}',
    response_time DECIMAL(10,3),
    question_length INTEGER,
    response_length INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_concepts ON conversations USING GIN(concepts_used);

-- Enable Row Level Security (RLS)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Create policies for RLS
-- Allow anonymous users to insert conversations (for the TA system)
CREATE POLICY "Allow anonymous insert" ON conversations
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Allow anonymous users to read conversations (for analytics)
CREATE POLICY "Allow anonymous select" ON conversations
    FOR SELECT
    TO anon
    USING (true);

-- Allow authenticated users full access
CREATE POLICY "Allow authenticated full access" ON conversations
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Grant permissions to anon and authenticated roles
GRANT SELECT, INSERT ON conversations TO anon;
GRANT ALL PRIVILEGES ON conversations TO authenticated;

-- Create a view for conversation analytics
CREATE OR REPLACE VIEW conversation_analytics AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as total_conversations,
    AVG(response_time) as avg_response_time,
    AVG(question_length) as avg_question_length,
    AVG(response_length) as avg_response_length,
    COUNT(DISTINCT session_id) as unique_sessions
FROM conversations
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- Grant access to the analytics view
GRANT SELECT ON conversation_analytics TO anon, authenticated;