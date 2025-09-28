"""
Модели данных для приложения Todo-Timed
Определяет структуры данных для задач, списков и повторений
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    """Статус задачи"""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RecurrenceFrequency(Enum):
    """Частота повторения"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


@dataclass
class TaskList:
    """Список задач на определенную дату"""
    id: Optional[int] = None
    date: Optional[date] = None
    title: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.date is None:
            self.date = date.today()
        if not self.title:
            self.title = f"Список дел на {self.date.strftime('%d.%m.%Y')}"
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class RecurrenceRule:
    """Правило повторения задачи"""
    frequency: RecurrenceFrequency
    interval: int = 1
    days_of_week: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    until_date: Optional[date] = None
    count: Optional[int] = None
    
    def to_rrule_string(self) -> str:
        """Преобразовать в строку RRULE"""
        parts = [f"FREQ={self.frequency.value}"]
        
        if self.interval > 1:
            parts.append(f"INTERVAL={self.interval}")
        
        if self.days_of_week:
            days_map = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
            days_str = ",".join(days_map[day] for day in self.days_of_week)
            parts.append(f"BYDAY={days_str}")
        
        if self.until_date:
            parts.append(f"UNTIL={self.until_date.strftime('%Y%m%d')}")
        
        if self.count:
            parts.append(f"COUNT={self.count}")
        
        return ";".join(parts)
    
    @classmethod
    def from_rrule_string(cls, rrule_string: str) -> 'RecurrenceRule':
        """Создать из строки RRULE"""
        parts = rrule_string.split(';')
        rule_dict = {}
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                rule_dict[key] = value
        
        frequency = RecurrenceFrequency(rule_dict.get('FREQ', 'DAILY'))
        interval = int(rule_dict.get('INTERVAL', 1))
        
        days_of_week = None
        if 'BYDAY' in rule_dict:
            days_map = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
            days_str = rule_dict['BYDAY']
            days_of_week = [days_map[day] for day in days_str.split(',') if day in days_map]
        
        until_date = None
        if 'UNTIL' in rule_dict:
            until_str = rule_dict['UNTIL']
            until_date = datetime.strptime(until_str, '%Y%m%d').date()
        
        count = None
        if 'COUNT' in rule_dict:
            count = int(rule_dict['COUNT'])
        
        return cls(
            frequency=frequency,
            interval=interval,
            days_of_week=days_of_week,
            until_date=until_date,
            count=count
        )


@dataclass
class Task:
    """Основная задача (может быть повторяющейся)"""
    id: Optional[int] = None
    list_id: Optional[int] = None
    title: str = ""
    notes: str = ""
    due_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    recurrence_rule: Optional[RecurrenceRule] = None
    recurrence_start: Optional[datetime] = None
    timezone: str = "UTC"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @property
    def is_recurring(self) -> bool:
        """Проверить, является ли задача повторяющейся"""
        return self.recurrence_rule is not None
    
    @property
    def is_completed(self) -> bool:
        """Проверить, выполнена ли задача"""
        return self.status == TaskStatus.COMPLETED
    
    def mark_completed(self):
        """Отметить задачу как выполненную"""
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.now()
    
    def mark_pending(self):
        """Отметить задачу как невыполненную"""
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now()


@dataclass
class TaskOccurrence:
    """Экземпляр повторяющейся задачи"""
    id: Optional[int] = None
    task_id: int = 0
    scheduled_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    completed_at: Optional[datetime] = None
    override_title: Optional[str] = None
    override_due_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Ссылка на родительскую задачу (заполняется при загрузке)
    parent_task: Optional[Task] = field(default=None, init=False)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @property
    def effective_title(self) -> str:
        """Получить эффективное название (с учетом переопределения)"""
        if self.override_title:
            return self.override_title
        if self.parent_task:
            return self.parent_task.title
        return ""
    
    @property
    def effective_due_at(self) -> Optional[datetime]:
        """Получить эффективное время выполнения"""
        if self.override_due_at:
            return self.override_due_at
        return self.scheduled_at
    
    @property
    def is_completed(self) -> bool:
        """Проверить, выполнен ли экземпляр"""
        return self.status == TaskStatus.COMPLETED
    
    def mark_completed(self):
        """Отметить экземпляр как выполненный"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def mark_pending(self):
        """Отметить экземпляр как невыполненный"""
        self.status = TaskStatus.PENDING
        self.completed_at = None
        self.updated_at = datetime.now()


@dataclass
class RecurrenceException:
    """Исключение в повторении (пропуск даты)"""
    id: Optional[int] = None
    task_id: int = 0
    exception_date: date = field(default_factory=date.today)
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


# Вспомогательные функции для валидации

def validate_task(task: Task) -> List[str]:
    """Валидация задачи"""
    errors = []
    
    if not task.title.strip():
        errors.append("Название задачи не может быть пустым")
    
    if task.due_at and task.due_at < datetime.now():
        errors.append("Время выполнения не может быть в прошлом")
    
    if task.is_recurring and not task.recurrence_rule:
        errors.append("Для повторяющейся задачи требуется правило повторения")
    
    return errors


def validate_recurrence_rule(rule: RecurrenceRule) -> List[str]:
    """Валидация правила повторения"""
    errors = []
    
    if rule.interval < 1:
        errors.append("Интервал должен быть больше 0")
    
    if rule.frequency == RecurrenceFrequency.WEEKLY and not rule.days_of_week:
        errors.append("Для еженедельного повторения нужно указать дни недели")
    
    if rule.days_of_week:
        for day in rule.days_of_week:
            if not 0 <= day <= 6:
                errors.append("Дни недели должны быть от 0 (понедельник) до 6 (воскресенье)")
    
    if rule.until_date and rule.until_date < date.today():
        errors.append("Дата окончания не может быть в прошлом")
    
    if rule.count and rule.count < 1:
        errors.append("Количество повторений должно быть больше 0")
    
    return errors
