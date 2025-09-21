-- Vector Database Functions for Tunisia Intelligence System
-- This file contains all necessary SQL functions for pgvector operations

-- Enable pgvector extension
CREATE OR REPLACE FUNCTION enable_pgvector_extension()
RETURNS boolean AS $$
BEGIN
    -- Enable the pgvector extension
    CREATE EXTENSION IF NOT EXISTS vector;
    RETURN true;
EXCEPTION
    WHEN OTHERS THEN
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create vector index function
CREATE OR REPLACE FUNCTION create_vector_index(
    table_name text,
    column_name text,
    index_name text,
    index_type text DEFAULT 'hnsw',
    distance_metric text DEFAULT 'cosine'
)
RETURNS boolean AS $$
DECLARE
    sql_query text;
BEGIN
    -- Construct the CREATE INDEX query
    IF index_type = 'hnsw' THEN
        sql_query := format(
            'CREATE INDEX IF NOT EXISTS %I ON %I USING hnsw (%I vector_%s_ops)',
            index_name, table_name, column_name, distance_metric
        );
    ELSE
        sql_query := format(
            'CREATE INDEX IF NOT EXISTS %I ON %I USING ivfflat (%I vector_%s_ops) WITH (lists = 100)',
            index_name, table_name, column_name, distance_metric
        );
    END IF;
    
    -- Execute the query
    EXECUTE sql_query;
    RETURN true;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error creating index %: %', index_name, SQLERRM;
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Vector similarity search function
CREATE OR REPLACE FUNCTION vector_similarity_search(
    content_type_filter text,
    query_vector vector,
    similarity_threshold float DEFAULT 0.7,
    result_limit int DEFAULT 10,
    include_content boolean DEFAULT false
)
RETURNS TABLE(
    id text,
    similarity_score float,
    title text,
    content_preview text,
    created_at timestamptz,
    source_id int
) AS $$
DECLARE
    sql_query text;
BEGIN
    -- Build the query based on content type
    CASE content_type_filter
        WHEN 'article' THEN
            sql_query := format('
                SELECT 
                    a.id::text,
                    (1 - (ce.content_embedding <=> $1))::float as similarity_score,
                    a.title::text as title,
                    %s as content_preview,
                    a.created_at,
                    COALESCE(a.source_id, 0)::int as source_id
                FROM articles a
                JOIN content_embeddings ce ON ce.content_type = ''article'' AND ce.content_id = a.id
                WHERE ce.content_embedding IS NOT NULL
                    AND (1 - (ce.content_embedding <=> $1)) >= $2
                ORDER BY ce.content_embedding <=> $1
                LIMIT $3',
                CASE WHEN include_content THEN 'LEFT(a.content, 200)' ELSE 'NULL::text' END
            );
        WHEN 'post' THEN
            sql_query := format('
                SELECT 
                    smp.id::text,
                    (1 - (ce.content_embedding <=> $1))::float as similarity_score,
                    LEFT(smp.content, 100)::text as title,
                    %s as content_preview,
                    smp.created_at,
                    COALESCE(smp.source_id, 0)::int as source_id
                FROM social_media_posts smp
                JOIN content_embeddings ce ON ce.content_type = ''post'' AND ce.content_id = smp.id
                WHERE ce.content_embedding IS NOT NULL
                    AND (1 - (ce.content_embedding <=> $1)) >= $2
                ORDER BY ce.content_embedding <=> $1
                LIMIT $3',
                CASE WHEN include_content THEN 'LEFT(smp.content, 200)' ELSE 'NULL::text' END
            );
        WHEN 'comment' THEN
            sql_query := format('
                SELECT 
                    smc.id::text,
                    (1 - (ce.content_embedding <=> $1))::float as similarity_score,
                    LEFT(smc.content, 50)::text as title,
                    %s as content_preview,
                    smc.created_at,
                    0::int as source_id
                FROM social_media_comments smc
                JOIN content_embeddings ce ON ce.content_type = ''comment'' AND ce.content_id = smc.id
                WHERE ce.content_embedding IS NOT NULL
                    AND (1 - (ce.content_embedding <=> $1)) >= $2
                ORDER BY ce.content_embedding <=> $1
                LIMIT $3',
                CASE WHEN include_content THEN 'LEFT(smc.content, 200)' ELSE 'NULL::text' END
            );
        ELSE
            -- Search across all content types
            sql_query := format('
                SELECT * FROM (
                    SELECT 
                        a.id::text,
                        (1 - (ce.content_embedding <=> $1))::float as similarity_score,
                        a.title::text as title,
                        %s as content_preview,
                        a.created_at,
                        COALESCE(a.source_id, 0)::int as source_id
                    FROM articles a
                    JOIN content_embeddings ce ON ce.content_type = ''article'' AND ce.content_id = a.id
                    WHERE ce.content_embedding IS NOT NULL
                        AND (1 - (ce.content_embedding <=> $1)) >= $2
                    UNION ALL
                    SELECT 
                        smp.id::text,
                        (1 - (ce.content_embedding <=> $1))::float as similarity_score,
                        LEFT(smp.content, 100)::text as title,
                        %s as content_preview,
                        smp.created_at,
                        COALESCE(smp.source_id, 0)::int as source_id
                    FROM social_media_posts smp
                    JOIN content_embeddings ce ON ce.content_type = ''post'' AND ce.content_id = smp.id
                    WHERE ce.content_embedding IS NOT NULL
                        AND (1 - (ce.content_embedding <=> $1)) >= $2
                    UNION ALL
                    SELECT 
                        smc.id::text,
                        (1 - (ce.content_embedding <=> $1))::float as similarity_score,
                        LEFT(smc.content, 50)::text as title,
                        %s as content_preview,
                        smc.created_at,
                        0::int as source_id
                    FROM social_media_comments smc
                    JOIN content_embeddings ce ON ce.content_type = ''comment'' AND ce.content_id = smc.id
                    WHERE ce.content_embedding IS NOT NULL
                        AND (1 - (ce.content_embedding <=> $1)) >= $2
                ) combined_results
                ORDER BY similarity_score DESC
                LIMIT $3',
                CASE WHEN include_content THEN 'LEFT(a.content, 200)' ELSE 'NULL::text' END,
                CASE WHEN include_content THEN 'LEFT(smp.content, 200)' ELSE 'NULL::text' END,
                CASE WHEN include_content THEN 'LEFT(smc.content, 200)' ELSE 'NULL::text' END
            );
    END CASE;
    
    -- Execute and return results
    RETURN QUERY EXECUTE sql_query USING query_vector, similarity_threshold, result_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get vector statistics function
CREATE OR REPLACE FUNCTION get_vector_statistics()
RETURNS TABLE(
    total_vectors bigint,
    by_content_type jsonb,
    avg_dimensions float,
    storage_size_mb float
) AS $$
DECLARE
    stats_result record;
    content_type_stats jsonb := '{}';
BEGIN
    -- Initialize counters
    total_vectors := 0;
    avg_dimensions := 0;
    storage_size_mb := 0;
    
    -- Get statistics from content_embeddings table
    SELECT 
        COUNT(*) as vector_count,
        COALESCE(AVG(vector_dims(content_embedding)), 0) as avg_dims,
        COALESCE(pg_total_relation_size('content_embeddings'), 0) as table_size
    INTO stats_result
    FROM content_embeddings 
    WHERE content_embedding IS NOT NULL;
    
    -- Update totals
    total_vectors := stats_result.vector_count;
    avg_dimensions := stats_result.avg_dims;
    storage_size_mb := stats_result.table_size / 1024.0 / 1024.0;
    
    -- Get statistics by content type
    FOR stats_result IN
        SELECT 
            content_type,
            COUNT(*) as type_count
        FROM content_embeddings 
        WHERE content_embedding IS NOT NULL
        GROUP BY content_type
    LOOP
        content_type_stats := content_type_stats || 
            jsonb_build_object(stats_result.content_type, stats_result.type_count);
    END LOOP;
    
    -- Return results
    by_content_type := content_type_stats;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check pgvector extension function
CREATE OR REPLACE FUNCTION check_pgvector_extension()
RETURNS TABLE(enabled boolean) AS $$
BEGIN
    RETURN QUERY
    SELECT EXISTS(
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check vector indexes function
CREATE OR REPLACE FUNCTION check_vector_indexes()
RETURNS TABLE(all_exist boolean, missing_indexes text[]) AS $$
DECLARE
    expected_indexes text[] := ARRAY[
        'idx_content_embeddings_content_embedding_hnsw',
        'idx_content_embeddings_title_embedding_hnsw',
        'idx_content_embeddings_entity_embedding_hnsw'
    ];
    existing_indexes text[];
    missing text[];
    idx text;
BEGIN
    -- Get existing vector indexes
    SELECT array_agg(indexname) INTO existing_indexes
    FROM pg_indexes 
    WHERE indexname = ANY(expected_indexes);
    
    -- Find missing indexes
    missing := ARRAY[]::text[];
    FOREACH idx IN ARRAY expected_indexes
    LOOP
        IF NOT (idx = ANY(COALESCE(existing_indexes, ARRAY[]::text[]))) THEN
            missing := array_append(missing, idx);
        END IF;
    END LOOP;
    
    -- Return results
    all_exist := (array_length(missing, 1) IS NULL);
    missing_indexes := missing;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Rebuild vector indexes function
CREATE OR REPLACE FUNCTION rebuild_vector_indexes()
RETURNS boolean AS $$
DECLARE
    index_config record;
    success_count int := 0;
    total_count int := 0;
BEGIN
    -- Define index configurations for content_embeddings table
    FOR index_config IN
        SELECT 
            'content_embeddings' as table_name,
            'content_embedding' as column_name,
            'idx_content_embeddings_content_embedding_hnsw' as index_name
        UNION ALL
        SELECT 
            'content_embeddings' as table_name,
            'title_embedding' as column_name,
            'idx_content_embeddings_title_embedding_hnsw' as index_name
        UNION ALL
        SELECT 
            'content_embeddings' as table_name,
            'entity_embedding' as column_name,
            'idx_content_embeddings_entity_embedding_hnsw' as index_name
    LOOP
        total_count := total_count + 1;
        
        BEGIN
            -- Drop existing index
            EXECUTE format('DROP INDEX IF EXISTS %I', index_config.index_name);
            
            -- Recreate index
            IF create_vector_index(
                index_config.table_name,
                index_config.column_name,
                index_config.index_name,
                'hnsw',
                'cosine'
            ) THEN
                success_count := success_count + 1;
            END IF;
            
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Failed to rebuild index %: %', index_config.index_name, SQLERRM;
        END;
    END LOOP;
    
    RETURN (success_count = total_count);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Cross-source semantic similarity view
CREATE OR REPLACE VIEW semantic_content_correlation AS
SELECT 
    a.id as article_id,
    a.title as article_title,
    smp.id as social_post_id,
    LEFT(smp.content, 100) as social_content_preview,
    (1 - (ce1.content_embedding <=> ce2.content_embedding)) as semantic_similarity,
    a.sentiment_score as article_sentiment,
    smp.sentiment_score as social_sentiment,
    a.created_at as article_date,
    smp.publish_date as social_date
FROM articles a
JOIN content_embeddings ce1 ON ce1.content_type = 'article' AND ce1.content_id = a.id
CROSS JOIN social_media_posts smp
JOIN content_embeddings ce2 ON ce2.content_type = 'post' AND ce2.content_id = smp.id
WHERE ce1.content_embedding IS NOT NULL 
    AND ce2.content_embedding IS NOT NULL
    AND (1 - (ce1.content_embedding <=> ce2.content_embedding)) > 0.7
ORDER BY semantic_similarity DESC;

-- Entity mention similarity view
CREATE OR REPLACE VIEW entity_semantic_mentions AS
SELECT 
    e.id as entity_id,
    e.canonical_name as entity_name,
    em.content_type as source_table,
    em.content_id as source_id,
    (1 - (ee.entity_embedding <=> ce.content_embedding)) as semantic_relevance,
    em.entity_sentiment_score,
    em.context_snippet
FROM entities e
JOIN entity_mentions em ON e.id = em.entity_id
JOIN content_embeddings ee ON ee.content_type = 'entity' AND ee.content_id = e.id
JOIN content_embeddings ce ON ce.content_type = em.content_type AND ce.content_id = em.content_id
WHERE ee.entity_embedding IS NOT NULL
    AND ce.content_embedding IS NOT NULL
ORDER BY semantic_relevance DESC;

-- Topic clustering function using vector similarity
CREATE OR REPLACE FUNCTION find_content_clusters(
    similarity_threshold float DEFAULT 0.8,
    min_cluster_size int DEFAULT 3
)
RETURNS TABLE(
    cluster_id int,
    content_type text,
    content_id text,
    content_title text,
    cluster_size int
) AS $$
DECLARE
    cluster_counter int := 0;
    processed_items text[] := ARRAY[]::text[];
    current_item record;
    similar_items record;
    cluster_items text[];
BEGIN
    -- Process articles
    FOR current_item IN 
        SELECT 'article' as content_type, a.id::text as content_id, a.title, ce.content_embedding
        FROM articles a
        JOIN content_embeddings ce ON ce.content_type = 'article' AND ce.content_id = a.id
        WHERE ce.content_embedding IS NOT NULL
            AND a.id::text != ALL(processed_items)
    LOOP
        cluster_items := ARRAY[current_item.content_id];
        
        -- Find similar articles
        FOR similar_items IN
            SELECT a.id::text as similar_id, a.title
            FROM articles a
            JOIN content_embeddings ce ON ce.content_type = 'article' AND ce.content_id = a.id
            WHERE ce.content_embedding IS NOT NULL
                AND a.id::text != current_item.content_id
                AND a.id::text != ALL(processed_items)
                AND (1 - (ce.content_embedding <=> current_item.content_embedding)) >= similarity_threshold
        LOOP
            cluster_items := array_append(cluster_items, similar_items.similar_id);
        END LOOP;
        
        -- If cluster is large enough, return it
        IF array_length(cluster_items, 1) >= min_cluster_size THEN
            cluster_counter := cluster_counter + 1;
            processed_items := processed_items || cluster_items;
            
            -- Return cluster members
            FOR i IN 1..array_length(cluster_items, 1) LOOP
                SELECT 
                    cluster_counter,
                    'article',
                    cluster_items[i],
                    a.title,
                    array_length(cluster_items, 1)
                INTO 
                    cluster_id,
                    content_type,
                    content_id,
                    content_title,
                    cluster_size
                FROM articles a
                WHERE a.id::text = cluster_items[i];
                
                RETURN NEXT;
            END LOOP;
        ELSE
            processed_items := array_append(processed_items, current_item.content_id);
        END IF;
    END LOOP;
    
    -- Process social media posts similarly
    FOR current_item IN 
        SELECT 'post' as content_type, smp.id::text as content_id, 
               LEFT(smp.content, 100) as title, ce.content_embedding
        FROM social_media_posts smp
        JOIN content_embeddings ce ON ce.content_type = 'post' AND ce.content_id = smp.id
        WHERE ce.content_embedding IS NOT NULL
            AND smp.id::text != ALL(processed_items)
    LOOP
        cluster_items := ARRAY[current_item.content_id];
        
        -- Find similar posts
        FOR similar_items IN
            SELECT smp.id::text as similar_id, LEFT(smp.content, 100) as title
            FROM social_media_posts smp
            JOIN content_embeddings ce ON ce.content_type = 'post' AND ce.content_id = smp.id
            WHERE ce.content_embedding IS NOT NULL
                AND smp.id::text != current_item.content_id
                AND smp.id::text != ALL(processed_items)
                AND (1 - (ce.content_embedding <=> current_item.content_embedding)) >= similarity_threshold
        LOOP
            cluster_items := array_append(cluster_items, similar_items.similar_id);
        END LOOP;
        
        -- If cluster is large enough, return it
        IF array_length(cluster_items, 1) >= min_cluster_size THEN
            cluster_counter := cluster_counter + 1;
            processed_items := processed_items || cluster_items;
            
            -- Return cluster members
            FOR i IN 1..array_length(cluster_items, 1) LOOP
                SELECT 
                    cluster_counter,
                    'post',
                    cluster_items[i],
                    LEFT(smp.content, 100),
                    array_length(cluster_items, 1)
                INTO 
                    cluster_id,
                    content_type,
                    content_id,
                    content_title,
                    cluster_size
                FROM social_media_posts smp
                WHERE smp.id::text = cluster_items[i];
                
                RETURN NEXT;
            END LOOP;
        ELSE
            processed_items := array_append(processed_items, current_item.content_id);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
