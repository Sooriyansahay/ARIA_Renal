-- Create feedback table for storing user feedback on TA responses
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_index INTEGER NOT NULL,
    user_question TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    feedback_type VARCHAR(20) NOT NULL CHECK (feedback_type IN ('helpful', 'not_helpful', 'partially_helpful')),
    concepts_covered TEXT[] DEFAULT '{}',
    response_time DECIMAL(10,3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_conversation_id ON feedback(conversation_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at DESC);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_feedback_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_feedback_updated_at
    BEFORE UPDATE ON feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_feedback_updated_at();

-- Enable Row Level Security (RLS)
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- Create policies for RLS
-- Allow anonymous users to insert feedback (for the TA system)
CREATE POLICY "Allow anonymous insert feedback" ON feedback
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Allow anonymous users to update their own feedback (for changing feedback)
CREATE POLICY "Allow anonymous update feedback" ON feedback
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);

-- Allow anonymous users to read feedback (for analytics)
CREATE POLICY "Allow anonymous select feedback" ON feedback
    FOR SELECT
    TO anon
    USING (true);

-- Allow authenticated users full access
CREATE POLICY "Allow authenticated full access feedback" ON feedback
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Grant permissions to anon and authenticated roles
GRANT SELECT, INSERT, UPDATE ON feedback TO anon;
GRANT ALL PRIVILEGES ON feedback TO authenticated;

-- Create a view for feedback analytics
CREATE OR REPLACE VIEW feedback_analytics AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    feedback_type,
    COUNT(*) as feedback_count,
    COUNT(DISTINCT session_id) as unique_sessions,
    AVG(response_time) as avg_response_time
FROM feedback
GROUP BY DATE_TRUNC('day', created_at), feedback_type
ORDER BY date DESC, feedback_type;

-- Create overall feedback summary view
CREATE OR REPLACE VIEW feedback_summary AS
SELECT 
    feedback_type,
    COUNT(*) as total_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 2) as percentage
FROM feedback
GROUP BY feedback_type
ORDER BY total_count DESC;

-- Grant access to the analytics views
GRANT SELECT ON feedback_analytics TO anon, authenticated;
GRANT SELECT ON feedback_summary TO anon, authenticated;