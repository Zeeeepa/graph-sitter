-- Add a new task to the system
-- Parameters: organization_id, codebase_id (optional), title, description, task_type, priority, assigned_to (optional), created_by

INSERT INTO tasks (
    organization_id,
    codebase_id,
    title,
    description,
    task_type,
    priority,
    assigned_to,
    created_by,
    metadata
) VALUES (
    $1::UUID,  -- organization_id
    $2::UUID,  -- codebase_id (can be NULL)
    $3::TEXT,  -- title
    $4::TEXT,  -- description
    $5::TEXT,  -- task_type
    COALESCE($6::INTEGER, 0),  -- priority (default 0)
    $7::UUID,  -- assigned_to (can be NULL)
    $8::UUID,  -- created_by
    COALESCE($9::JSONB, '{}'::JSONB)  -- metadata (default empty object)
)
RETURNING 
    id,
    title,
    status,
    created_at;

