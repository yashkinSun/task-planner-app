"""
Модуль работы с базой данных SQLite
Включает миграции, репозитории и валидацию схемы
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from contextlib import contextmanager

from .resource_manager import ResourceManager
from .models import Task, TaskList, TaskOccurrence, RecurrenceException, TaskStatus

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Исключение для ошибок базы данных"""
    pass


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = ResourceManager.get_app_data_dir() / "todo_timed.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Инициализация базы данных
        self._init_database()
        self._apply_migrations()
        self._validate_schema()
    
    def _init_database(self):
        """Инициализация базы данных"""
        try:
            with self.get_connection() as conn:
                # Включаем поддержку внешних ключей
                conn.execute("PRAGMA foreign_keys = ON")
                # Настраиваем журналирование WAL для лучшей производительности
                conn.execute("PRAGMA journal_mode = WAL")
                conn.commit()
            
            logger.info(f"База данных инициализирована: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise DatabaseError(f"Не удалось инициализировать базу данных: {e}")
    
    def _apply_migrations(self):
        """Применение миграций"""
        try:
            migrations_dir = ResourceManager.get_resource_path("migrations")
            if not migrations_dir or not migrations_dir.exists():
                logger.warning("Директория миграций не найдена")
                return
            
            # Создаем таблицу для отслеживания миграций
            with self.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version TEXT PRIMARY KEY,
                        applied_at TEXT NOT NULL
                    )
                """)
                conn.commit()
            
            # Получаем список примененных миграций
            applied_migrations = self._get_applied_migrations()
            
            # Применяем новые миграции
            migration_files = sorted(migrations_dir.glob("*.sql"))
            for migration_file in migration_files:
                version = migration_file.stem
                
                if version not in applied_migrations:
                    self._apply_migration(migration_file, version)
            
            logger.info("Миграции успешно применены")
            
        except Exception as e:
            logger.error(f"Ошибка применения миграций: {e}")
            raise DatabaseError(f"Не удалось применить миграции: {e}")
    
    def _get_applied_migrations(self) -> set[str]:
        """Получить список примененных миграций"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT version FROM schema_migrations")
                return {row[0] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            # Таблица миграций еще не создана
            return set()
    
    def _apply_migration(self, migration_file: Path, version: str):
        """Применить одну миграцию"""
        try:
            migration_sql = migration_file.read_text(encoding='utf-8')
            
            with self.get_connection() as conn:
                # Выполняем миграцию
                conn.executescript(migration_sql)
                
                # Записываем информацию о применении
                conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (version, datetime.now().isoformat())
                )
                conn.commit()
            
            logger.info(f"Применена миграция: {version}")
            
        except Exception as e:
            logger.error(f"Ошибка применения миграции {version}: {e}")
            raise DatabaseError(f"Не удалось применить миграцию {version}: {e}")
    
    def _validate_schema(self):
        """Валидация схемы базы данных"""
        try:
            required_tables = ['task_lists', 'tasks', 'task_occurrences', 'recurrence_exceptions']
            
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                existing_tables = {row[0] for row in cursor.fetchall()}
            
            missing_tables = set(required_tables) - existing_tables
            if missing_tables:
                raise DatabaseError(f"Отсутствуют таблицы: {missing_tables}")
            
            logger.debug("Валидация схемы базы данных прошла успешно")
            
        except Exception as e:
            logger.error(f"Ошибка валидации схемы: {e}")
            raise DatabaseError(f"Схема базы данных некорректна: {e}")
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с соединением"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row  # Доступ к колонкам по имени
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Ошибка работы с базой данных: {e}")
            raise DatabaseError(f"Ошибка базы данных: {e}")
        finally:
            if conn:
                conn.close()
    
    # Методы для работы с списками задач
    
    def get_task_list_by_date(self, target_date: date) -> Optional[TaskList]:
        """Получить список задач по дате"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM task_lists WHERE date = ?",
                    (target_date.isoformat(),)
                )
                row = cursor.fetchone()
                
                if row:
                    return TaskList(
                        id=row['id'],
                        date=date.fromisoformat(row['date']),
                        title=row['title'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения списка задач: {e}")
            raise DatabaseError(f"Не удалось получить список задач: {e}")
    
    def create_task_list(self, task_list: TaskList) -> int:
        """Создать новый список задач"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO task_lists (date, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    task_list.date.isoformat(),
                    task_list.title,
                    task_list.created_at.isoformat(),
                    task_list.updated_at.isoformat()
                ))
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Ошибка создания списка задач: {e}")
            raise DatabaseError(f"Не удалось создать список задач: {e}")
    
    def update_task_list(self, task_list: TaskList):
        """Обновить список задач"""
        try:
            task_list.updated_at = datetime.now()
            
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE task_lists 
                    SET title = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    task_list.title,
                    task_list.updated_at.isoformat(),
                    task_list.id
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Ошибка обновления списка задач: {e}")
            raise DatabaseError(f"Не удалось обновить список задач: {e}")
    
    # Методы для работы с задачами
    
    def get_tasks_by_list_id(self, list_id: int) -> List[Task]:
        """Получить задачи по ID списка"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE list_id = ? ORDER BY due_at, created_at",
                    (list_id,)
                )
                
                tasks = []
                for row in cursor.fetchall():
                    task = self._row_to_task(row)
                    tasks.append(task)
                
                return tasks
                
        except Exception as e:
            logger.error(f"Ошибка получения задач: {e}")
            raise DatabaseError(f"Не удалось получить задачи: {e}")
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Получить задачу по ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE id = ?",
                    (task_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_task(row)
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения задачи: {e}")
            raise DatabaseError(f"Не удалось получить задачу: {e}")
    
    def create_task(self, task: Task) -> int:
        """Создать новую задачу"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO tasks (
                        list_id, title, notes, due_at, status,
                        recurrence_rule, recurrence_start, timezone,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.list_id,
                    task.title,
                    task.notes,
                    task.due_at.isoformat() if task.due_at else None,
                    task.status.value,
                    task.recurrence_rule.to_rrule_string() if task.recurrence_rule else None,
                    task.recurrence_start.isoformat() if task.recurrence_start else None,
                    task.timezone,
                    task.created_at.isoformat(),
                    task.updated_at.isoformat()
                ))
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Ошибка создания задачи: {e}")
            raise DatabaseError(f"Не удалось создать задачу: {e}")
    
    def update_task(self, task: Task):
        """Обновить задачу"""
        try:
            task.updated_at = datetime.now()
            
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE tasks SET
                        title = ?, notes = ?, due_at = ?, status = ?,
                        recurrence_rule = ?, recurrence_start = ?, timezone = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    task.title,
                    task.notes,
                    task.due_at.isoformat() if task.due_at else None,
                    task.status.value,
                    task.recurrence_rule.to_rrule_string() if task.recurrence_rule else None,
                    task.recurrence_start.isoformat() if task.recurrence_start else None,
                    task.timezone,
                    task.updated_at.isoformat(),
                    task.id
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Ошибка обновления задачи: {e}")
            raise DatabaseError(f"Не удалось обновить задачу: {e}")
    
    def delete_task(self, task_id: int):
        """Удалить задачу"""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Ошибка удаления задачи: {e}")
            raise DatabaseError(f"Не удалось удалить задачу: {e}")
    
    def _row_to_task(self, row) -> Task:
        """Преобразовать строку БД в объект Task"""
        from .models import RecurrenceRule
        
        recurrence_rule = None
        if row['recurrence_rule']:
            recurrence_rule = RecurrenceRule.from_rrule_string(row['recurrence_rule'])
        
        return Task(
            id=row['id'],
            list_id=row['list_id'],
            title=row['title'],
            notes=row['notes'] or "",
            due_at=datetime.fromisoformat(row['due_at']) if row['due_at'] else None,
            status=TaskStatus(row['status']),
            recurrence_rule=recurrence_rule,
            recurrence_start=datetime.fromisoformat(row['recurrence_start']) if row['recurrence_start'] else None,
            timezone=row['timezone'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
