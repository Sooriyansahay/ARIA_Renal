-- Add feedback column to conversations table
-- This allows storing feedback directly with each conversation

-- Add feedback column to conversations table
ALTER TABLE conversations 
ADD COLUMN feedback VARCHAR(20) DEFAULT NULL 
CHECK (feedback IS NULL OR feedback IN ('helpful', 'not_helpful', 'partially_helpful'));

-- Create index on feedback column for better query performance
CREATE INDEX IF NOT EXISTS idx_conversations_feedback ON conversations(feedback);

-- Update RLS policies to allow updating feedback column
-- Allow anonymous users to update feedback on conversations
CREATE POLICY "Allow anonymous update feedback" ON conversations
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);

-- Grant UPDATE permission to anon role for feedback updates
GRANT UPDATE ON conversations TO anon;

-- Update conversation analytics view to include feedback statistics
CREATE OR REPLACE VIEW conversation_analytics AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as total_conversations,
    AVG(response_time) as avg_response_time,
    AVG(question_length) as avg_question_length,
    AVG(response_length) as avg_response_length,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(CASE WHEN feedback = 'helpful' THEN 1 END) as helpful_feedback,
    COUNT(CASE WHEN feedback = 'not_helpful' THEN 1 END) as not_helpful_feedback,
    COUNT(CASE WHEN feedback = 'partially_helpful' THEN 1 END) as partially_helpful_feedback,
    COUNT(CASE WHEN feedback IS NOT NULL THEN 1 END) as total_feedback,
    ROUND(
        (COUNT(CASE WHEN feedback = 'helpful' THEN 1 END) * 100.0 / 
         NULLIF(COUNT(CASE WHEN feedback IS NOT NULL THEN 1 END), 0)), 2
    ) as helpful_percentage
FROM conversations
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- Create feedback summary view for overall statistics
CREATE OR REPLACE VIEW feedback_summary_conversations AS
SELECT 
    feedback,
    COUNT(*) as total_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 2) as percentage
FROM conversations
WHERE feedback IS NOT NULL
GROUP BY feedback
ORDER BY total_count DESC;

-- Grant access to the updated analytics views
GRANT SELECT ON conversation_analytics TO anon, authenticated;
GRANT SELECT ON feedback_summary_conversations TO anon, authenticated;

-- Add comment to document the feedback column
COMMENT ON COLUMN conversations.feedback IS 'User feedback on the TA response: helpful, not_helpful, or partially_helpful';