-- Add a subtask to an existing parent task
-- Parameters: parent_task_id, organization_id, title, description, task_type, priority, assigned_to (optional), created_by

INSERT INTO tasks (
    parent_task_id,
    organization_id,
    codebase_id,
    title,
    description,
    task_type,
    priority,
    assigned_to,
    created_by,
    metadata
) 
SELECT 
    $1::UUID,  -- parent_task_id
    p.organization_id,  -- inherit organization_id from parent
    COALESCE($2::UUID, p.codebase_id),  -- codebase_id (inherit from parent if not specified)
    $3::TEXT,  -- title
    $4::TEXT,  -- description
    $5::TEXT,  -- task_type
    COALESCE($6::INTEGER, 0),  -- priority (default 0)
    $7::UUID,  -- assigned_to (can be NULL)
    $8::UUID,  -- created_by
    COALESCE($9::JSONB, '{}'::JSONB)  -- metadata (default empty object)
FROM tasks p
WHERE p.id = $1::UUID
RETURNING 
    id,
    parent_task_id,
    title,
    status,
    created_at;

