-- TaskBox initial schema.
--
-- The types intentionally use portable SQL (TEXT for UUIDs and timestamps),
-- so this migration can be exercised with SQLite in the early labs and run by
-- PostgreSQL in the production lab.  Application code stores ISO-8601 UTC
-- timestamps and UUID strings in both databases.

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memberships (
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (project_id, user_id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    created_by TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    assignee_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'done', 'archived')),
    priority INTEGER NOT NULL DEFAULT 0 CHECK (priority BETWEEN 0 AND 4),
    due_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS webhook_receipts (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    signature TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'received' CHECK (status IN ('received', 'processed', 'failed')),
    received_at TEXT NOT NULL,
    processed_at TEXT,
    error TEXT,
    metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id, id);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON memberships(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project_cursor ON tasks(project_id, created_at, id);
CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status, created_at, id);
CREATE INDEX IF NOT EXISTS idx_webhook_receipts_status ON webhook_receipts(status, received_at);
