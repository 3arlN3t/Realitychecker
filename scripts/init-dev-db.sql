-- Development database initialization script
-- This script sets up the development database with sample data

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create development-specific tables or data
-- (This will be executed after the main application tables are created)

-- Insert sample data for development
-- Note: This will be executed only if tables exist
DO $$
BEGIN
    -- Check if tables exist before inserting sample data
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN
        -- Insert sample users if table exists
        INSERT INTO users (id, phone_number, first_interaction, last_interaction, total_requests, blocked)
        VALUES 
            ('550e8400-e29b-41d4-a716-446655440001', '+1234567890', NOW() - INTERVAL '7 days', NOW() - INTERVAL '1 hour', 15, false),
            ('550e8400-e29b-41d4-a716-446655440002', '+1987654321', NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 hours', 8, false),
            ('550e8400-e29b-41d4-a716-446655440003', '+1555123456', NOW() - INTERVAL '1 day', NOW() - INTERVAL '30 minutes', 3, true)
        ON CONFLICT (phone_number) DO NOTHING;
    END IF;

    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'interactions') THEN
        -- Insert sample interactions if table exists
        INSERT INTO interactions (id, user_id, message_type, analysis_result, response_time, error, created_at)
        VALUES 
            ('550e8400-e29b-41d4-a716-446655440101', '550e8400-e29b-41d4-a716-446655440001', 'text', '{"trust_score": 85, "classification": "Legit", "reasons": ["Professional company", "Reasonable salary", "Clear job description"]}', 1.2, NULL, NOW() - INTERVAL '1 hour'),
            ('550e8400-e29b-41d4-a716-446655440102', '550e8400-e29b-41d4-a716-446655440002', 'pdf', '{"trust_score": 25, "classification": "Likely Scam", "reasons": ["Requests upfront payment", "Too good to be true salary", "Poor grammar"]}', 2.8, NULL, NOW() - INTERVAL '2 hours'),
            ('550e8400-e29b-41d4-a716-446655440103', '550e8400-e29b-41d4-a716-446655440003', 'text', NULL, 0.0, 'OpenAI API error', NOW() - INTERVAL '30 minutes')
        ON CONFLICT (id) DO NOTHING;
    END IF;
END $$;