-- Инициализация базы данных Todo-Timed
-- Создание основных таблиц

-- Таблица списков задач
CREATE TABLE IF NOT EXISTS task_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,  -- YYYY-MM-DD
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(date)
);

-- Таблица основных задач (включая повторяющиеся)
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER,  -- NULL для повторяющихся задач
    title TEXT NOT NULL,
    notes TEXT DEFAULT '',
    due_at TEXT,  -- ISO8601 datetime
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, completed, cancelled
    recurrence_rule TEXT,  -- RRULE строка
    recurrence_start TEXT,  -- ISO8601 datetime
    timezone TEXT DEFAULT 'UTC',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (list_id) REFERENCES task_lists (id) ON DELETE CASCADE
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_task_lists_date ON task_lists(date);
CREATE INDEX IF NOT EXISTS idx_tasks_list_id ON tasks(list_id);
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_recurrence ON tasks(recurrence_rule);

-- Вставка начальных данных
INSERT OR IGNORE INTO task_lists (date, title, created_at, updated_at)
VALUES (
    date('now'),
    'Список дел на ' || date('now'),
    datetime('now'),
    datetime('now')
);
