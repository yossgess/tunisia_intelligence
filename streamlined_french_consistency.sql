-- =====================================================
-- Streamlined French Language Consistency Schema
-- =====================================================
-- This script implements the streamlined French consistency logic:
-- 1. Only "content" column is fed to LLM
-- 2. Content is translated to French if not already French
-- 3. All AI outputs are generated in French by default

-- Step 1: Add only the necessary French translation column
-- =====================================================

-- Add content_fr column to articles table (for translated content only)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'articles' AND column_name = 'content_fr') THEN
        ALTER TABLE public.articles 
        ADD COLUMN content_fr text;
    END IF;
END $$;

-- Add content_fr column to social_media_posts table (for translated content only)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'social_media_posts' AND column_name = 'content_fr') THEN
        ALTER TABLE public.social_media_posts 
        ADD COLUMN content_fr text;
    END IF;
END $$;

-- Step 2: Update sentiment constraints to use French labels
-- =====================================================

-- Update articles sentiment constraint
ALTER TABLE public.articles 
DROP CONSTRAINT IF EXISTS articles_sentiment_check;

ALTER TABLE public.articles 
ADD CONSTRAINT articles_sentiment_check 
CHECK (sentiment::text = ANY (ARRAY['positif'::character varying::text, 'négatif'::character varying::text, 'neutre'::character varying::text]));

-- Update social_media_posts sentiment constraint
ALTER TABLE public.social_media_posts 
DROP CONSTRAINT IF EXISTS social_media_posts_sentiment_check;

ALTER TABLE public.social_media_posts 
ADD CONSTRAINT social_media_posts_sentiment_check 
CHECK (sentiment::text = ANY (ARRAY['positif'::character varying::text, 'négatif'::character varying::text, 'neutre'::character varying::text]));

-- Update social_media_comments sentiment constraint
ALTER TABLE public.social_media_comments 
DROP CONSTRAINT IF EXISTS social_media_comments_sentiment_check;

ALTER TABLE public.social_media_comments 
ADD CONSTRAINT social_media_comments_sentiment_check 
CHECK (sentiment::text = ANY (ARRAY['positif'::character varying::text, 'négatif'::character varying::text, 'neutre'::character varying::text]));

-- Step 3: Create indexes for French content search
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_articles_content_fr ON public.articles USING gin(to_tsvector('french', content_fr)) WHERE content_fr IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_social_posts_content_fr ON public.social_media_posts USING gin(to_tsvector('french', content_fr)) WHERE content_fr IS NOT NULL;

-- Step 4: Update enrichment functions for streamlined approach
-- =====================================================

-- Drop existing function first to avoid conflicts
DROP FUNCTION IF EXISTS update_article_enrichment;

-- Streamlined article enrichment function
CREATE OR REPLACE FUNCTION update_article_enrichment(
    p_article_id bigint,
    p_sentiment character varying DEFAULT NULL,
    p_sentiment_score numeric DEFAULT NULL,
    p_keywords text DEFAULT NULL,
    p_summary text DEFAULT NULL,
    p_category character varying DEFAULT NULL,
    p_category_id integer DEFAULT NULL,
    p_confidence numeric DEFAULT NULL,
    p_content_fr text DEFAULT NULL
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.articles 
    SET 
        sentiment = COALESCE(p_sentiment, sentiment),
        sentiment_score = COALESCE(p_sentiment_score, sentiment_score),
        keywords = COALESCE(p_keywords, keywords),
        summary = COALESCE(p_summary, summary),
        category = COALESCE(p_category, category),
        category_id = COALESCE(p_category_id, category_id),
        enrichment_confidence = COALESCE(p_confidence, enrichment_confidence),
        content_fr = COALESCE(p_content_fr, content_fr),
        enriched_at = NOW(),
        updated_at = NOW()
    WHERE id = p_article_id;
    
    RETURN FOUND;
END;
$$;

-- Drop existing function first to avoid conflicts
DROP FUNCTION IF EXISTS update_post_enrichment;

-- Streamlined social media post enrichment function
CREATE OR REPLACE FUNCTION update_post_enrichment(
    p_post_id bigint,
    p_sentiment character varying DEFAULT NULL,
    p_sentiment_score numeric DEFAULT NULL,
    p_summary text DEFAULT NULL,
    p_category_id integer DEFAULT NULL,
    p_confidence numeric DEFAULT NULL,
    p_content_fr text DEFAULT NULL
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.social_media_posts 
    SET 
        sentiment = COALESCE(p_sentiment, sentiment),
        sentiment_score = COALESCE(p_sentiment_score, sentiment_score),
        summary = COALESCE(p_summary, summary),
        category_id = COALESCE(p_category_id, category_id),
        enrichment_confidence = COALESCE(p_confidence, enrichment_confidence),
        content_fr = COALESCE(p_content_fr, content_fr),
        enriched_at = NOW(),
        updated_at = NOW()
    WHERE id = p_post_id;
    
    RETURN FOUND;
END;
$$;

-- Step 5: Populate French categories (using existing structure)
-- =====================================================
INSERT INTO public.content_categories (name_en, name_ar, name_fr, description) 
VALUES 
    ('politics', 'سياسة', 'Politique', 'Actualités politiques et affaires gouvernementales'),
    ('economy', 'اقتصاد', 'Économie', 'Actualités économiques et questions financières'),
    ('society', 'مجتمع', 'Société', 'Questions sociales et actualités communautaires'),
    ('culture', 'ثقافة', 'Culture', 'Événements culturels et arts'),
    ('sports', 'رياضة', 'Sport', 'Actualités sportives et événements'),
    ('education', 'تعليم', 'Éducation', 'Actualités éducatives et académiques'),
    ('health', 'صحة', 'Santé', 'Actualités sanitaires et médicales'),
    ('technology', 'تكنولوجيا', 'Technologie', 'Technologie et innovation'),
    ('environment', 'بيئة', 'Environnement', 'Questions environnementales'),
    ('security', 'أمن', 'Sécurité', 'Questions de sécurité et de sûreté'),
    ('international', 'دولي', 'International', 'Actualités internationales'),
    ('regional', 'جهوي', 'Régional', 'Actualités régionales et locales'),
    ('justice', 'عدالة', 'Justice', 'Affaires judiciaires et juridiques'),
    ('other', 'أخرى', 'Autre', 'Contenu non catégorisé')
ON CONFLICT (name_en) DO UPDATE SET
    name_ar = EXCLUDED.name_ar,
    name_fr = EXCLUDED.name_fr,
    description = EXCLUDED.description;

-- Step 6: Create helper function to get category ID by French name
-- =====================================================
CREATE OR REPLACE FUNCTION get_category_id_by_french_name(p_category_name_fr text)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    category_id integer;
BEGIN
    SELECT id INTO category_id
    FROM public.content_categories
    WHERE LOWER(name_fr) = LOWER(p_category_name_fr);
    
    -- If not found, return 'Autre' category
    IF category_id IS NULL THEN
        SELECT id INTO category_id
        FROM public.content_categories
        WHERE name_en = 'other';
    END IF;
    
    RETURN category_id;
END;
$$;

-- Step 7: Create analytics view for streamlined approach
-- =====================================================
CREATE OR REPLACE VIEW streamlined_enrichment_analytics AS
SELECT 
    'articles' as content_type,
    COUNT(*) as total_items,
    COUNT(CASE WHEN enriched_at IS NOT NULL THEN 1 END) as enriched_items,
    COUNT(CASE WHEN content_fr IS NOT NULL THEN 1 END) as translated_items,
    COUNT(CASE WHEN sentiment IS NOT NULL THEN 1 END) as sentiment_analyzed,
    COUNT(CASE WHEN keywords IS NOT NULL THEN 1 END) as keywords_extracted,
    COUNT(CASE WHEN summary IS NOT NULL THEN 1 END) as summarized_items,
    ROUND(
        (COUNT(CASE WHEN enriched_at IS NOT NULL THEN 1 END)::numeric / 
         NULLIF(COUNT(*)::numeric, 0)) * 100, 2
    ) as enrichment_percentage,
    AVG(enrichment_confidence) as avg_confidence
FROM public.articles

UNION ALL

SELECT 
    'social_media_posts' as content_type,
    COUNT(*) as total_items,
    COUNT(CASE WHEN enriched_at IS NOT NULL THEN 1 END) as enriched_items,
    COUNT(CASE WHEN content_fr IS NOT NULL THEN 1 END) as translated_items,
    COUNT(CASE WHEN sentiment IS NOT NULL THEN 1 END) as sentiment_analyzed,
    0 as keywords_extracted, -- Posts don't have keywords in this schema
    COUNT(CASE WHEN summary IS NOT NULL THEN 1 END) as summarized_items,
    ROUND(
        (COUNT(CASE WHEN enriched_at IS NOT NULL THEN 1 END)::numeric / 
         NULLIF(COUNT(*)::numeric, 0)) * 100, 2
    ) as enrichment_percentage,
    AVG(enrichment_confidence) as avg_confidence
FROM public.social_media_posts

UNION ALL

SELECT 
    'social_media_comments' as content_type,
    COUNT(*) as total_items,
    COUNT(CASE WHEN enriched_at IS NOT NULL THEN 1 END) as enriched_items,
    0 as translated_items, -- Comments are not translated
    COUNT(CASE WHEN sentiment IS NOT NULL THEN 1 END) as sentiment_analyzed,
    0 as keywords_extracted, -- Comments don't have keywords
    0 as summarized_items, -- Comments don't have summaries
    ROUND(
        (COUNT(CASE WHEN enriched_at IS NOT NULL THEN 1 END)::numeric / 
         NULLIF(COUNT(*)::numeric, 0)) * 100, 2
    ) as enrichment_percentage,
    AVG(enrichment_confidence) as avg_confidence
FROM public.social_media_comments;

-- Step 8: Add documentation comments
-- =====================================================
COMMENT ON COLUMN public.articles.content_fr IS 'French translation of article content (only when original is not French)';
COMMENT ON COLUMN public.social_media_posts.content_fr IS 'French translation of post content (only when original is not French)';

COMMENT ON FUNCTION update_article_enrichment IS 'Updates article with AI enrichment results - all outputs in French';
COMMENT ON FUNCTION update_post_enrichment IS 'Updates social media post with AI enrichment results - all outputs in French';
COMMENT ON FUNCTION get_category_id_by_french_name IS 'Returns category ID by French category name';
COMMENT ON VIEW streamlined_enrichment_analytics IS 'Analytics view for streamlined French enrichment approach';

-- =====================================================
-- End of Streamlined French Language Consistency Schema
-- =====================================================
