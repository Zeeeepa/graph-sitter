-- Add a new codebase to the system
-- Parameters: organization_id, name, repository_url (optional), repository_path (optional), 
--            language (optional), branch (optional), metadata (optional)

INSERT INTO codebases (
    organization_id,
    name,
    repository_url,
    repository_path,
    language,
    branch,
    metadata
) VALUES (
    $1::UUID,  -- organization_id
    $2::TEXT,  -- name
    $3::TEXT,  -- repository_url (can be NULL)
    $4::TEXT,  -- repository_path (can be NULL)
    $5::TEXT,  -- language (can be NULL)
    COALESCE($6::TEXT, 'main'),  -- branch (default 'main')
    COALESCE($7::JSONB, '{}'::JSONB)  -- metadata (default empty object)
)
ON CONFLICT (organization_id, name) 
DO UPDATE SET
    repository_url = EXCLUDED.repository_url,
    repository_path = EXCLUDED.repository_path,
    language = EXCLUDED.language,
    branch = EXCLUDED.branch,
    metadata = EXCLUDED.metadata,
    updated_at = NOW()
RETURNING 
    id,
    name,
    repository_url,
    language,
    branch,
    analysis_status,
    created_at,
    updated_at;

