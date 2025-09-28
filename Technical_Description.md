# Todo-Timed: Техническая документация разработчика

## Оглавление

1. [Обзор архитектуры](#обзор-архитектуры)
2. [Структура проекта](#структура-проекта)
3. [Модули и компоненты](#модули-и-компоненты)
4. [Модели данных](#модели-данных)
5. [База данных](#база-данных)
6. [Пользовательский интерфейс](#пользовательский-интерфейс)
7. [Система уведомлений](#система-уведомлений)
8. [Локализация](#локализация)
9. [Настройки](#настройки)
10. [API и интерфейсы](#api-и-интерфейсы)
11. [Сборка и развертывание](#сборка-и-развертывание)
12. [Тестирование](#тестирование)
13. [Расширение функциональности](#расширение-функциональности)

---

## Обзор архитектуры

### Архитектурный паттерн
Todo-Timed построен на основе **Model-View-Controller (MVC)** архитектуры с использованием Qt/PySide6 фреймворка.

### Основные принципы
- **Модульность**: Четкое разделение ответственности между компонентами
- **Расширяемость**: Легкое добавление новых функций
- **Надежность**: Graceful degradation и обработка ошибок
- **Локализация**: Поддержка множественных языков
- **Кроссплатформенность**: Работа на Windows, Linux, macOS

### Диаграмма архитектуры
```
┌─────────────────────────────────────────────────────────────┐
│                    Todo-Timed Application                   │
├─────────────────────────────────────────────────────────────┤
│                     Presentation Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ MainWindow  │  │   Dialogs   │  │      Widgets        │  │
│  │             │  │             │  │                     │  │
│  │ - Calendar  │  │ - TaskEditor│  │ - CalendarWidget    │  │
│  │ - TaskList  │  │ - Settings  │  │ - TaskListWidget    │  │
│  │ - Toolbar   │  │             │  │ - ToolBar           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     Business Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Database   │  │Notifications│  │    Localization     │  │
│  │             │  │             │  │                     │  │
│  │ - CRUD Ops  │  │ - Reminders │  │ - Multi-language    │  │
│  │ - Migrations│  │ - Scheduler │  │ - Fallback system   │  │
│  │ - Validation│  │             │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Models    │  │   Settings  │  │   Resource Manager  │  │
│  │             │  │             │  │                     │  │
│  │ - Task      │  │ - User Prefs│  │ - File paths        │  │
│  │ - Recurrence│  │ - Themes    │  │ - Asset loading     │  │
│  │ - Occurrence│  │             │  │ - Fallback handling │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Storage Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   SQLite    │  │ JSON Files  │  │    File System      │  │
│  │             │  │             │  │                     │  │
│  │ - tasks.db  │  │ - settings  │  │ - Locales           │  │
│  │ - migrations│  │ - locales   │  │ - Resources         │  │
│  │             │  │             │  │ - Logs              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Структура проекта

```
todo-timed/
├── app.py                          # Точка входа приложения
├── requirements.txt                # Python зависимости
├── build.py                        # Скрипт сборки в .exe
├── todo-timed.spec                 # Конфигурация PyInstaller
├── README.md                       # Пользовательская документация
├── VALIDATION_REPORT.md            # Отчет о соответствии ТЗ
│
├── core/                           # Бизнес-логика
│   ├── __init__.py
│   ├── database.py                 # Работа с базой данных
│   ├── localization.py             # Система локализации
│   ├── models.py                   # Модели данных
│   ├── notifications.py            # Система уведомлений
│   ├── resource_manager.py         # Управление ресурсами
│   └── settings.py                 # Настройки приложения
│
├── ui/                             # Пользовательский интерфейс
│   ├── __init__.py
│   ├── main_window.py              # Главное окно
│   │
│   ├── dialogs/                    # Диалоговые окна
│   │   ├── __init__.py
│   │   └── task_editor.py          # Редактор задач
│   │
│   └── widgets/                    # Пользовательские виджеты
│       ├── __init__.py
│       ├── calendar_widget.py      # Виджет календаря
│       ├── task_list.py            # Список задач
│       └── toolbar.py              # Панели инструментов
│
├── resources/                      # Ресурсы приложения
│   ├── images/                     # Изображения
│   │   └── background.png          # Фоновое изображение
│   │
│   └── styles/                     # Стили оформления
│       ├── light.qss               # Светлая тема
│       └── dark.qss                # Темная тема
│
├── locales/                        # Файлы локализации
│   ├── ru.json                     # Русский язык
│   └── en.json                     # Английский язык
│
└── migrations/                     # Миграции базы данных
    ├── 001_init.sql                # Начальная схема
    └── 002_occurrences.sql         # Экземпляры задач
```

---

## Модули и компоненты

### Core модули

#### 1. `core/models.py`
**Назначение**: Определение моделей данных и бизнес-логики

**Основные классы**:
```python
class TaskStatus(Enum):
    """Статусы задач"""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class RecurrenceFrequency(Enum):
    """Частота повторений"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Task:
    """Основная модель задачи"""
    - id: Optional[int]
    - title: str
    - description: Optional[str]
    - due_date: Optional[date]
    - due_time: Optional[time]
    - status: TaskStatus
    - recurrence_rule: Optional[RecurrenceRule]
    - created_at: Optional[datetime]
    - updated_at: Optional[datetime]

class RecurrenceRule:
    """Правило повторения задач"""
    - frequency: RecurrenceFrequency
    - interval: int
    - until: Optional[date]

class TaskOccurrence:
    """Экземпляр повторяющейся задачи"""
    - id: Optional[int]
    - task_id: int
    - occurrence_date: date
    - title: Optional[str]
    - description: Optional[str]
    - due_date: Optional[date]
    - due_time: Optional[time]
    - status: TaskStatus
```

**Методы валидации**:
- `validate_task(task: Task) -> List[str]`
- `validate_recurrence_rule(rule: RecurrenceRule) -> List[str]`

#### 2. `core/database.py`
**Назначение**: Управление базой данных SQLite

**Основные методы**:
```python
class Database:
    def __init__(self, db_path: Optional[Path] = None)
    def connect(self) -> None
    def run_migrations(self) -> None
    
    # CRUD операции для задач
    def create_task(self, task: Task) -> int
    def update_task(self, task: Task) -> None
    def delete_task(self, task: Task) -> None
    def get_task_by_id(self, task_id: int) -> Optional[Task]
    def get_tasks_by_date(self, target_date: date) -> List[Task]
    
    # CRUD операции для экземпляров
    def create_task_occurrence(self, occurrence: TaskOccurrence) -> int
    def update_task_occurrence(self, occurrence: TaskOccurrence) -> None
    def delete_task_occurrence(self, occurrence: TaskOccurrence) -> None
    def get_task_occurrences_by_date(self, target_date: date) -> List[TaskOccurrence]
    
    def close(self) -> None
```

**Особенности**:
- Автоматические миграции при запуске
- Поддержка внешних ключей
- Транзакционная безопасность
- Graceful degradation при ошибках

#### 3. `core/resource_manager.py`
**Назначение**: Централизованное управление ресурсами

**Основные методы**:
```python
class ResourceManager:
    @staticmethod
    def get_app_data_dir() -> Path
    @staticmethod
    def get_project_root() -> Path
    @staticmethod
    def get_resources_dir() -> Path
    @staticmethod
    def get_migrations_dir() -> Path
    
    def get_image_path(self, filename: str) -> Optional[Path]
    def get_style_path(self, filename: str) -> Optional[Path]
    def get_locale_path(self, filename: str) -> Optional[Path]
```

**Fallback система**:
- Поиск ресурсов в нескольких локациях
- Graceful degradation при отсутствии файлов
- Логирование проблем с ресурсами

#### 4. `core/settings.py`
**Назначение**: Управление настройками приложения

**Настройки по умолчанию**:
```python
DEFAULT_SETTINGS = {
    'language': 'ru',
    'theme': 'system',
    'start_minimized': False,
    'minimize_to_tray': True,
    'autostart': False,
    'snooze_minutes': 10,
    'expansion_horizon_days': 90,
    'grace_minutes': 10,
    'window_geometry': None,
    'window_state': None,
}
```

**API**:
```python
class Settings:
    def load(self) -> None
    def save(self) -> None
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any) -> None
    
    # Свойства для основных настроек
    @property
    def language(self) -> str
    @property
    def theme(self) -> str
    # ... и другие
```

#### 5. `core/localization.py`
**Назначение**: Система локализации с fallback

**Основные методы**:
```python
class Localization:
    def __init__(self, language: str = "ru")
    def get_text(self, key: str, **kwargs) -> str
    def set_language(self, language: str) -> bool
    def get_available_languages(self) -> List[str]
```

**Особенности**:
- Fallback на английский язык
- Поддержка параметров в строках
- Иерархическая структура ключей (например: `"dialogs.task_editor.title"`)

#### 6. `core/notifications.py`
**Назначение**: Система уведомлений и напоминаний

**Основные классы**:
```python
class NotificationManager:
    def show_notification(self, title: str, message: str, icon: str = "info") -> None
    def show_reminder(self, task: Union[Task, TaskOccurrence]) -> None

class ReminderScheduler:
    def __init__(self, database: Database, notification_manager: NotificationManager)
    def start(self) -> None
    def stop(self) -> None
    def check_reminders(self) -> None
```

### UI модули

#### 1. `ui/main_window.py`
**Назначение**: Главное окно приложения

**Основные компоненты**:
- Календарь для выбора даты
- Список задач для выбранной даты
- Панель инструментов
- Статусная строка
- Система меню

**Сигналы**:
```python
class MainWindow(QMainWindow):
    closing = Signal()  # Сигнал закрытия окна
```

**Основные методы**:
```python
def setup_ui(self) -> None
def setup_menu(self) -> None
def connect_signals(self) -> None
def on_date_selected(self, selected_date: date) -> None
def on_task_toggled(self, task, checked: bool) -> None
def add_task(self) -> None
def edit_task(self, task) -> None
def delete_task(self, task) -> None
def on_task_saved(self, task) -> None
```

#### 2. `ui/dialogs/task_editor.py`
**Назначение**: Диалог создания и редактирования задач

**Сигналы**:
```python
class TaskEditorDialog(QDialog):
    task_saved = Signal(object)  # Task или TaskOccurrence
```

**Основные секции**:
- Основная информация (название, описание)
- Дата и время
- Настройки повторений
- Предварительный просмотр повторений

**Методы**:
```python
def setup_ui(self) -> None
def connect_signals(self) -> None
def load_task_data(self) -> None
def save_task(self) -> None
def update_preview(self) -> None
```

#### 3. `ui/widgets/calendar_widget.py`
**Назначение**: Виджет календаря с выделением дат с задачами

**Сигналы**:
```python
class CalendarWidget(QWidget):
    date_selected = Signal(date)
```

**Особенности**:
- Выделение дат с задачами
- Навигация по месяцам
- Быстрый переход к сегодняшней дате

#### 4. `ui/widgets/task_list.py`
**Назначение**: Список задач с возможностью редактирования

**Сигналы**:
```python
class TaskListWidget(QWidget):
    task_toggled = Signal(object, bool)
    task_edit_requested = Signal(object)
    task_delete_requested = Signal(object)
    add_task_requested = Signal()
```

**Методы**:
```python
def add_task(self, task) -> None
def remove_task(self, task) -> None
def update_task(self, task) -> None
def clear_tasks(self) -> None
```

#### 5. `ui/widgets/toolbar.py`
**Назначение**: Панели инструментов

**Классы**:
- `MainToolBar`: Основная панель инструментов
- `StatusToolBar`: Статусная панель

**Сигналы**:
```python
class MainToolBar(QToolBar):
    add_task_requested = Signal()
    edit_task_requested = Signal()
    delete_task_requested = Signal()
    mark_done_requested = Signal()
    go_to_today_requested = Signal()
    settings_requested = Signal()
    refresh_requested = Signal()
```

---

## Модели данных

### Схема базы данных

#### Таблица `tasks`
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    due_date TEXT,  -- ISO format date
    due_time TEXT,  -- ISO format time
    status TEXT NOT NULL DEFAULT 'pending',
    recurrence_frequency TEXT,  -- daily, weekly, monthly, yearly
    recurrence_interval INTEGER DEFAULT 1,
    recurrence_until TEXT,  -- ISO format date
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### Таблица `task_occurrences`
```sql
CREATE TABLE task_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    occurrence_date TEXT NOT NULL,  -- ISO format date
    title TEXT,
    description TEXT,
    due_date TEXT,
    due_time TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
);
```

#### Таблица `migrations`
```sql
CREATE TABLE migrations (
    id INTEGER PRIMARY KEY,
    filename TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Связи между моделями

```
Task (1) ←→ (N) TaskOccurrence
│
├── id → task_id (FK)
├── recurrence_rule → occurrence_date
└── title, description → overridable in occurrence
```

### Жизненный цикл задач

1. **Создание задачи**:
   - Обычная задача: сохраняется в `tasks`
   - Повторяющаяся задача: сохраняется в `tasks` + создаются экземпляры в `task_occurrences`

2. **Редактирование**:
   - Обычная задача: обновляется в `tasks`
   - Экземпляр повторяющейся: обновляется в `task_occurrences`

3. **Удаление**:
   - Обычная задача: удаляется из `tasks`
   - Повторяющаяся задача: удаляется из `tasks` + каскадное удаление экземпляров
   - Экземпляр: удаляется только из `task_occurrences`

---

## База данных

### Система миграций

Миграции выполняются автоматически при запуске приложения:

1. Проверяется таблица `migrations`
2. Находятся неприменённые файлы в `migrations/`
3. Выполняются SQL скрипты в алфавитном порядке
4. Записывается информация о применённых миграциях

### Транзакции

Все операции записи выполняются в транзакциях:
```python
try:
    cursor = self.connection.execute("INSERT INTO ...")
    self.connection.commit()
except Exception as e:
    self.connection.rollback()
    raise
```

### Индексы

Рекомендуемые индексы для производительности:
```sql
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_task_occurrences_date ON task_occurrences(occurrence_date);
CREATE INDEX idx_task_occurrences_task_id ON task_occurrences(task_id);
```

---

## Пользовательский интерфейс

### Архитектура UI

Todo-Timed использует **Model-View** архитектуру Qt:
- **Model**: Данные из базы данных
- **View**: Qt виджеты
- **Signals/Slots**: Связь между компонентами

### Система тем

Поддерживаются темы оформления:
- `light.qss`: Светлая тема
- `dark.qss`: Темная тема
- `system`: Автоматический выбор по системе

### Стилизация

Пример стилей для кнопок:
```css
QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}
```

### Адаптивность

UI адаптируется к размеру окна:
- Сплиттер между календарем и списком задач
- Минимальные размеры компонентов
- Сохранение геометрии окна

---

## Система уведомлений

### Архитектура

```
ReminderScheduler → NotificationManager → System Notifications
       ↑                      ↑
   QTimer (60s)         Platform-specific
```

### Типы уведомлений

1. **Напоминания о задачах**:
   - За 10 минут до срока (настраивается)
   - В момент наступления срока
   - Просроченные задачи

2. **Системные уведомления**:
   - Ошибки сохранения
   - Успешные операции
   - Предупреждения

### Планировщик напоминаний

```python
class ReminderScheduler:
    def __init__(self, database, notification_manager):
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(60000)  # Проверка каждую минуту
    
    def check_reminders(self):
        now = datetime.now()
        # Проверка задач, требующих напоминания
        # Отправка уведомлений
```

---

## Локализация

### Структура файлов локализации

```json
{
  "app": {
    "title": "Todo-Timed",
    "error": "Ошибка",
    "warning": "Предупреждение"
  },
  "menu": {
    "file": "Файл",
    "edit": "Правка",
    "view": "Вид"
  },
  "dialogs": {
    "task_editor": {
      "title_new": "Новая задача",
      "title_edit": "Редактирование задачи"
    }
  }
}
```

### Использование в коде

```python
# Получение локализованного текста
title = self.localization.get_text("dialogs.task_editor.title_new")

# С параметрами
message = self.localization.get_text("notifications.task_due", task_title="Встреча")
```

### Добавление нового языка

1. Создать файл `locales/xx.json` (где xx - код языка)
2. Скопировать структуру из `en.json`
3. Перевести все строки
4. Добавить язык в `Localization.get_available_languages()`

---

## Настройки

### Файл настроек

Настройки сохраняются в JSON формате:
```json
{
  "language": "ru",
  "theme": "system",
  "start_minimized": false,
  "minimize_to_tray": true,
  "snooze_minutes": 10,
  "window_geometry": "...",
  "window_state": "..."
}
```

### Расположение файлов

- **Windows**: `%USERPROFILE%\.todo-timed\settings.json`
- **Linux**: `~/.todo-timed/settings.json`
- **macOS**: `~/.todo-timed/settings.json`

### API настроек

```python
# Чтение настройки
language = settings.get('language', 'ru')

# Запись настройки (автоматическое сохранение)
settings.set('language', 'en')

# Использование свойств
settings.language = 'en'
current_theme = settings.theme
```

---

## API и интерфейсы

### Основные интерфейсы

#### ITaskRepository
```python
class ITaskRepository:
    def create_task(self, task: Task) -> int
    def update_task(self, task: Task) -> None
    def delete_task(self, task: Task) -> None
    def get_task_by_id(self, task_id: int) -> Optional[Task]
    def get_tasks_by_date(self, target_date: date) -> List[Task]
```

#### INotificationProvider
```python
class INotificationProvider:
    def show_notification(self, title: str, message: str, icon: str) -> None
    def is_available(self) -> bool
```

### Сигналы и слоты

#### Основные сигналы приложения
```python
# MainWindow
date_selected = Signal(date)
task_toggled = Signal(object, bool)
task_edit_requested = Signal(object)
task_delete_requested = Signal(object)

# TaskEditorDialog
task_saved = Signal(object)

# CalendarWidget
date_selected = Signal(date)

# TaskListWidget
task_toggled = Signal(object, bool)
add_task_requested = Signal()
```

### События жизненного цикла

```python
# Запуск приложения
app.initialize_components()
app.create_main_window()
app.setup_system_tray()
app.main_window.show()

# Завершение приложения
reminder_scheduler.stop()
database.close()
settings.save()
```

---

## Сборка и развертывание

### Зависимости

```txt
PySide6>=6.5.0
```

### Сборка в исполняемый файл

```python
# build.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    'app.py',
    '--name=Todo-Timed',
    '--windowed',
    '--onefile',
    '--add-data=resources;resources',
    '--add-data=locales;locales',
    '--add-data=migrations;migrations',
    '--hidden-import=PySide6.QtCore',
    '--hidden-import=PySide6.QtWidgets',
    '--hidden-import=PySide6.QtGui'
])
```

### Конфигурация PyInstaller

```python
# todo-timed.spec
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('locales', 'locales'),
        ('migrations', 'migrations')
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
```

### Развертывание

1. **Разработка**:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```

2. **Сборка**:
   ```bash
   python build.py
   ```

3. **Распространение**:
   - Исполняемый файл в `dist/`
   - Не требует установки Python
   - Самодостаточный пакет

---

## Тестирование

### Структура тестов

```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_database.py
│   ├── test_settings.py
│   └── test_localization.py
├── integration/
│   ├── test_task_crud.py
│   └── test_ui_interactions.py
└── fixtures/
    ├── test_data.json
    └── test_database.db
```

### Примеры тестов

#### Тестирование моделей
```python
def test_task_creation():
    task = Task()
    task.title = "Test Task"
    task.due_date = date.today()
    
    errors = validate_task(task)
    assert len(errors) == 0

def test_recurrence_rule_validation():
    rule = RecurrenceRule(
        frequency=RecurrenceFrequency.DAILY,
        interval=1
    )
    
    errors = validate_recurrence_rule(rule)
    assert len(errors) == 0
```

#### Тестирование базы данных
```python
def test_task_crud():
    db = Database(":memory:")
    
    task = Task()
    task.title = "Test Task"
    
    # Create
    task_id = db.create_task(task)
    assert task_id > 0
    
    # Read
    loaded_task = db.get_task_by_id(task_id)
    assert loaded_task.title == "Test Task"
    
    # Update
    loaded_task.title = "Updated Task"
    db.update_task(loaded_task)
    
    # Delete
    db.delete_task(loaded_task)
    assert db.get_task_by_id(task_id) is None
```

### Запуск тестов

```bash
# Все тесты
python -m pytest tests/

# Только unit тесты
python -m pytest tests/unit/

# С покрытием кода
python -m pytest --cov=core --cov=ui tests/
```

---

## Расширение функциональности

### Добавление новых типов повторений

1. **Расширить enum**:
   ```python
   class RecurrenceFrequency(Enum):
       DAILY = "daily"
       WEEKLY = "weekly"
       MONTHLY = "monthly"
       YEARLY = "yearly"
       CUSTOM = "custom"  # Новый тип
   ```

2. **Обновить логику генерации**:
   ```python
   def get_occurrences(self, start_date: date, limit: int = 100) -> List[date]:
       if self.frequency == RecurrenceFrequency.CUSTOM:
           return self._generate_custom_occurrences(start_date, limit)
       # ... существующая логика
   ```

3. **Обновить UI**:
   ```python
   self.frequency_combo.addItem(
       self.localization.get_text("recurrence.custom")
   )
   ```

### Добавление новых виджетов

1. **Создать класс виджета**:
   ```python
   class CustomWidget(QWidget):
       # Определить сигналы
       custom_signal = Signal(str)
       
       def __init__(self, parent=None):
           super().__init__(parent)
           self.setup_ui()
           self.connect_signals()
   ```

2. **Интегрировать в главное окно**:
   ```python
   self.custom_widget = CustomWidget()
   layout.addWidget(self.custom_widget)
   self.custom_widget.custom_signal.connect(self.handle_custom_event)
   ```

### Добавление новых провайдеров уведомлений

1. **Реализовать интерфейс**:
   ```python
   class EmailNotificationProvider(INotificationProvider):
       def show_notification(self, title: str, message: str, icon: str) -> None:
           # Отправка email уведомления
           pass
       
       def is_available(self) -> bool:
           return self.smtp_configured()
   ```

2. **Зарегистрировать провайдер**:
   ```python
   notification_manager.add_provider(EmailNotificationProvider())
   ```

### Добавление новых тем

1. **Создать файл стилей**:
   ```css
   /* resources/styles/custom.qss */
   QMainWindow {
       background-color: #custom-color;
   }
   ```

2. **Обновить настройки**:
   ```python
   DEFAULT_SETTINGS = {
       'theme': 'system',  # system, light, dark, custom
   }
   ```

3. **Обновить применение темы**:
   ```python
   def apply_theme(self):
       theme_map = {
           'light': 'light.qss',
           'dark': 'dark.qss',
           'custom': 'custom.qss'
       }
       style_file = theme_map.get(self.settings.theme, 'light.qss')
   ```

---

## Лучшие практики

### Обработка ошибок

1. **Всегда используйте try-except**:
   ```python
   try:
       result = risky_operation()
   except SpecificException as e:
       logger.error(f"Specific error: {e}")
       # Graceful degradation
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       # Fallback behavior
   ```

2. **Логируйте все важные события**:
   ```python
   logger.info("Starting operation")
   logger.debug(f"Processing item: {item}")
   logger.warning("Non-critical issue occurred")
   logger.error("Critical error occurred")
   ```

### Производительность

1. **Ленивая загрузка данных**:
   ```python
   def load_tasks_for_date(self, target_date: date):
       if target_date not in self.task_cache:
           self.task_cache[target_date] = self.database.get_tasks_by_date(target_date)
       return self.task_cache[target_date]
   ```

2. **Пакетные операции**:
   ```python
   def create_multiple_tasks(self, tasks: List[Task]):
       with self.database.transaction():
           for task in tasks:
               self.database.create_task(task)
   ```

### Безопасность

1. **Валидация входных данных**:
   ```python
   def set_task_title(self, title: str):
       if not title or len(title.strip()) == 0:
           raise ValueError("Title cannot be empty")
       if len(title) > 255:
           raise ValueError("Title too long")
       self.title = title.strip()
   ```

2. **Экранирование SQL**:
   ```python
   # Используйте параметризованные запросы
   cursor.execute("SELECT * FROM tasks WHERE title = ?", (title,))
   # НЕ используйте форматирование строк
   # cursor.execute(f"SELECT * FROM tasks WHERE title = '{title}'")
   ```

### Тестируемость

1. **Внедрение зависимостей**:
   ```python
   class TaskService:
       def __init__(self, database: ITaskRepository):
           self.database = database
   
   # В тестах
   mock_database = Mock(spec=ITaskRepository)
   service = TaskService(mock_database)
   ```

2. **Разделение логики и UI**:
   ```python
   # Бизнес-логика в отдельном классе
   class TaskManager:
       def create_task(self, task_data: dict) -> Task:
           # Логика создания задачи
           pass
   
   # UI только вызывает бизнес-логику
   def on_save_clicked(self):
       task_data = self.get_form_data()
       task = self.task_manager.create_task(task_data)
   ```

---

## Заключение

Todo-Timed представляет собой хорошо структурированное приложение с четким разделением ответственности между компонентами. Архитектура позволяет легко расширять функциональность, добавлять новые типы уведомлений, темы оформления и языки интерфейса.

Ключевые преимущества архитектуры:
- **Модульность**: Каждый компонент имеет четкую ответственность
- **Расширяемость**: Легко добавлять новые функции
- **Надежность**: Graceful degradation и обработка ошибок
- **Тестируемость**: Внедрение зависимостей и разделение логики
- **Локализация**: Полная поддержка множественных языков

Для дальнейшего развития рекомендуется:
1. Добавить unit и integration тесты
2. Реализовать систему плагинов
3. Добавить синхронизацию с облачными сервисами
4. Расширить возможности повторений задач
5. Добавить категории и теги для задач
