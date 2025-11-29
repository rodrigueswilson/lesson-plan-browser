-- Migration: Add template_path and signature_image_path fields to users table
-- This allows each user to have their own lesson plan template and signature image
-- Run this in Supabase SQL Editor

-- Add template_path column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'template_path'
    ) THEN
        ALTER TABLE users ADD COLUMN template_path TEXT;
        RAISE NOTICE 'Added template_path column to users table';
    ELSE
        RAISE NOTICE 'template_path column already exists';
    END IF;
END $$;

-- Add signature_image_path column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'signature_image_path'
    ) THEN
        ALTER TABLE users ADD COLUMN signature_image_path TEXT;
        RAISE NOTICE 'Added signature_image_path column to users table';
    ELSE
        RAISE NOTICE 'signature_image_path column already exists';
    END IF;
END $$;

