-- Миграция для экземпляров повторяющихся задач

-- Таблица экземпляров повторяющихся задач
CREATE TABLE IF NOT EXISTS task_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    scheduled_at TEXT NOT NULL,  -- ISO8601 datetime
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, completed, cancelled
    completed_at TEXT,  -- ISO8601 datetime
    override_title TEXT,  -- Переопределение названия для конкретного экземпляра
    override_due_at TEXT,  -- Переопределение времени для конкретного экземпляра
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    UNIQUE(task_id, scheduled_at)
);

-- Таблица исключений в повторениях
CREATE TABLE IF NOT EXISTS recurrence_exceptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    exception_date TEXT NOT NULL,  -- YYYY-MM-DD
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    UNIQUE(task_id, exception_date)
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_occurrences_task_id ON task_occurrences(task_id);
CREATE INDEX IF NOT EXISTS idx_occurrences_scheduled_at ON task_occurrences(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_occurrences_status ON task_occurrences(status);
CREATE INDEX IF NOT EXISTS idx_exceptions_task_id ON recurrence_exceptions(task_id);
CREATE INDEX IF NOT EXISTS idx_exceptions_date ON recurrence_exceptions(exception_date);
