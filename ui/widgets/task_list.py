"""
Виджет списка задач с фильтрацией и поиском
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QComboBox, QLabel, QCheckBox, QFrame,
    QMenu, QMessageBox
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont, QAction

from core.models import Task, TaskOccurrence, TaskStatus

logger = logging.getLogger(__name__)


class TaskListItem(QWidget):
    """Виджет элемента задачи в списке"""
    
    # Сигналы
    task_toggled = Signal(object, bool)  # task/occurrence, is_completed
    task_edit_requested = Signal(object)  # task/occurrence
    task_delete_requested = Signal(object)  # task/occurrence
    
    def __init__(self, task_or_occurrence, localization, parent=None):
        super().__init__(parent)
        self.item = task_or_occurrence  # Task или TaskOccurrence
        self.localization = localization
        
        self.setup_ui()
        self.connect_signals()
        self.update_display()
    
    def setup_ui(self):
        """Настройка интерфейса элемента"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Чекбокс выполнения
        self.completed_checkbox = QCheckBox()
        layout.addWidget(self.completed_checkbox)
        
        # Основная информация о задаче
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Название задачи
        self.title_label = QLabel()
        font = QFont()
        font.setPointSize(10)
        self.title_label.setFont(font)
        info_layout.addWidget(self.title_label)
        
        # Время и дополнительная информация
        self.details_label = QLabel()
        font = QFont()
        font.setPointSize(8)
        self.details_label.setFont(font)
        self.details_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self.details_label)
        
        layout.addLayout(info_layout, 1)  # Растягиваем
        
        # Индикатор повторяющейся задачи
        self.recurring_label = QLabel("🔄")
        self.recurring_label.setVisible(False)
        layout.addWidget(self.recurring_label)
        
        # Кнопки действий (скрыты по умолчанию)
        self.edit_button = QPushButton("✏️")
        self.edit_button.setMaximumSize(24, 24)
        self.edit_button.setVisible(False)
        layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("🗑️")
        self.delete_button.setMaximumSize(24, 24)
        self.delete_button.setVisible(False)
        layout.addWidget(self.delete_button)
    
    def connect_signals(self):
        """Подключение сигналов"""
        self.completed_checkbox.toggled.connect(self.on_completed_toggled)
        self.edit_button.clicked.connect(self.on_edit_requested)
        self.delete_button.clicked.connect(self.on_delete_requested)
    
    def update_display(self):
        """Обновить отображение элемента"""
        try:
            # Определяем тип элемента и получаем данные
            if isinstance(self.item, TaskOccurrence):
                title = self.item.effective_title
                due_at = self.item.effective_due_at
                is_completed = self.item.is_completed
                is_recurring = True
            else:  # Task
                title = self.item.title
                due_at = self.item.due_at
                is_completed = self.item.is_completed
                is_recurring = self.item.is_recurring
            
            # Обновляем название
            self.title_label.setText(title or self.localization.get_text("task.title"))
            
            # Обновляем детали
            details_parts = []
            
            if due_at:
                time_str = due_at.strftime("%H:%M")
                details_parts.append(f"⏰ {time_str}")
            
            if isinstance(self.item, TaskOccurrence):
                details_parts.append("📅 " + self.localization.get_text("task.recurring"))
            
            self.details_label.setText(" | ".join(details_parts))
            
            # Обновляем чекбокс
            self.completed_checkbox.setChecked(is_completed)
            
            # Показываем индикатор повторения
            self.recurring_label.setVisible(is_recurring)
            
            # Применяем стиль для выполненных задач
            if is_completed:
                self.title_label.setStyleSheet("text-decoration: line-through; color: #888888;")
                self.details_label.setStyleSheet("text-decoration: line-through; color: #888888;")
            else:
                self.title_label.setStyleSheet("")
                self.details_label.setStyleSheet("color: #666666;")
                
        except Exception as e:
            logger.error(f"Ошибка обновления отображения задачи: {e}")
    
    def on_completed_toggled(self, checked: bool):
        """Обработка изменения статуса выполнения"""
        self.task_toggled.emit(self.item, checked)
        self.update_display()
    
    def on_edit_requested(self):
        """Обработка запроса редактирования"""
        self.task_edit_requested.emit(self.item)
    
    def on_delete_requested(self):
        """Обработка запроса удаления"""
        self.task_delete_requested.emit(self.item)
    
    def enterEvent(self, event):
        """Показать кнопки при наведении мыши"""
        self.edit_button.setVisible(True)
        self.delete_button.setVisible(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Скрыть кнопки при уходе мыши"""
        self.edit_button.setVisible(False)
        self.delete_button.setVisible(False)
        super().leaveEvent(event)


class TaskListWidget(QWidget):
    """Виджет списка задач с фильтрацией и поиском"""
    
    # Сигналы
    task_toggled = Signal(object, bool)  # task/occurrence, is_completed
    task_edit_requested = Signal(object)  # task/occurrence
    task_delete_requested = Signal(object)  # task/occurrence
    add_task_requested = Signal()
    
    def __init__(self, localization, parent=None):
        super().__init__(parent)
        self.localization = localization
        self.tasks = []  # Список Task и TaskOccurrence
        self.filtered_tasks = []
        self.current_filter = "all"
        self.search_text = ""
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Заголовок и кнопка добавления
        self.create_header(layout)
        
        # Поиск и фильтры
        self.create_search_and_filters(layout)
        
        # Список задач
        self.task_list = QListWidget()
        self.task_list.setAlternatingRowColors(True)
        layout.addWidget(self.task_list)
        
        # Статистика
        self.create_status_bar(layout)
    
    def create_header(self, layout):
        """Создать заголовок с кнопкой добавления"""
        header_layout = QHBoxLayout()
        
        # Заголовок списка
        self.list_title_label = QLabel(self.localization.get_text("app.title"))
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.list_title_label.setFont(font)
        header_layout.addWidget(self.list_title_label)
        
        header_layout.addStretch()
        
        # Кнопка добавления задачи
        self.add_button = QPushButton(self.localization.get_text("toolbar.add"))
        self.add_button.setProperty("primary", True)
        header_layout.addWidget(self.add_button)
        
        layout.addLayout(header_layout)
    
    def create_search_and_filters(self, layout):
        """Создать поиск и фильтры"""
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(4)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_label = QLabel(self.localization.get_text("toolbar.search") + ":")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.localization.get_text("toolbar.search") + "...")
        search_layout.addWidget(self.search_input)
        
        controls_layout.addLayout(search_layout)
        
        # Фильтры
        filter_layout = QHBoxLayout()
        filter_label = QLabel(self.localization.get_text("filters.all") + ":")
        filter_layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            self.localization.get_text("filters.all"),
            self.localization.get_text("filters.active"),
            self.localization.get_text("filters.completed"),
            self.localization.get_text("filters.overdue"),
            self.localization.get_text("filters.today"),
            self.localization.get_text("filters.upcoming")
        ])
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addStretch()
        controls_layout.addLayout(filter_layout)
        
        layout.addLayout(controls_layout)
        
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
    
    def create_status_bar(self, layout):
        """Создать строку статуса"""
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Статистика
        self.status_label = QLabel()
        font = QFont()
        font.setPointSize(9)
        self.status_label.setFont(font)
        self.status_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.status_label)
    
    def connect_signals(self):
        """Подключение сигналов"""
        self.add_button.clicked.connect(lambda _: self.add_task_requested.emit())
        self.search_input.textChanged.connect(self.on_search_changed)
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        
        # Контекстное меню для списка
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_context_menu)
    
    def set_tasks(self, tasks: List):
        """Установить список задач"""
        self.tasks = tasks
        self.apply_filters()
    
    def add_task(self, task):
        """Добавить задачу в список"""
        self.tasks.append(task)
        self.apply_filters()
    
    def update_task(self, updated_task):
        """Обновить задачу в списке"""
        for i, task in enumerate(self.tasks):
            if (hasattr(task, 'id') and hasattr(updated_task, 'id') and 
                task.id == updated_task.id and type(task) == type(updated_task)):
                self.tasks[i] = updated_task
                break
        self.apply_filters()
    
    def remove_task(self, task_to_remove):
        """Удалить задачу из списка"""
        self.tasks = [task for task in self.tasks 
                     if not (hasattr(task, 'id') and hasattr(task_to_remove, 'id') and
                            task.id == task_to_remove.id and type(task) == type(task_to_remove))]
        self.apply_filters()
    
    def on_search_changed(self, text: str):
        """Обработка изменения поискового запроса"""
        self.search_text = text.lower()
        # Добавляем небольшую задержку для оптимизации
        QTimer.singleShot(300, self.apply_filters)
    
    def on_filter_changed(self, filter_text: str):
        """Обработка изменения фильтра"""
        filter_map = {
            self.localization.get_text("filters.all"): "all",
            self.localization.get_text("filters.active"): "active",
            self.localization.get_text("filters.completed"): "completed",
            self.localization.get_text("filters.overdue"): "overdue",
            self.localization.get_text("filters.today"): "today",
            self.localization.get_text("filters.upcoming"): "upcoming"
        }
        self.current_filter = filter_map.get(filter_text, "all")
        self.apply_filters()
    
    def apply_filters(self):
        """Применить фильтры и поиск"""
        try:
            # Фильтрация по статусу
            filtered = []
            now = datetime.now()
            today = date.today()
            
            for task in self.tasks:
                # Определяем параметры задачи
                if isinstance(task, TaskOccurrence):
                    is_completed = task.is_completed
                    due_at = task.effective_due_at
                    title = task.effective_title
                else:  # Task
                    is_completed = task.is_completed
                    due_at = task.due_at
                    title = task.title
                
                # Применяем фильтр по статусу
                if self.current_filter == "active" and is_completed:
                    continue
                elif self.current_filter == "completed" and not is_completed:
                    continue
                elif self.current_filter == "overdue":
                    if not due_at or is_completed or due_at > now:
                        continue
                elif self.current_filter == "today":
                    if not due_at or due_at.date() != today:
                        continue
                elif self.current_filter == "upcoming":
                    if not due_at or due_at.date() <= today:
                        continue
                
                # Применяем поиск
                if self.search_text:
                    if self.search_text not in title.lower():
                        continue
                
                filtered.append(task)
            
            self.filtered_tasks = filtered
            self.update_list_display()
            self.update_status()
            
        except Exception as e:
            logger.error(f"Ошибка применения фильтров: {e}")
    
    def update_list_display(self):
        """Обновить отображение списка"""
        try:
            # Очищаем список
            self.task_list.clear()
            
            # Добавляем отфильтрованные задачи
            for task in self.filtered_tasks:
                item = QListWidgetItem()
                task_widget = TaskListItem(task, self.localization)
                
                # Подключаем сигналы
                task_widget.task_toggled.connect(self.task_toggled.emit)
                task_widget.task_edit_requested.connect(self.task_edit_requested.emit)
                task_widget.task_delete_requested.connect(self.task_delete_requested.emit)
                
                # Устанавливаем размер элемента
                item.setSizeHint(task_widget.sizeHint())
                
                # Добавляем в список
                self.task_list.addItem(item)
                self.task_list.setItemWidget(item, task_widget)
                
        except Exception as e:
            logger.error(f"Ошибка обновления отображения списка: {e}")
    
    def update_status(self):
        """Обновить строку статуса"""
        try:
            total_count = len(self.filtered_tasks)
            completed_count = sum(1 for task in self.filtered_tasks 
                                if (task.is_completed if isinstance(task, TaskOccurrence) 
                                   else task.is_completed))
            
            status_text = f"{total_count} {self.localization.get_text('status.tasks_count')}"
            if completed_count > 0:
                status_text += f", {completed_count} {self.localization.get_text('status.completed_count')}"
            
            self.status_label.setText(status_text)
            
        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")
    
    def show_context_menu(self, position):
        """Показать контекстное меню"""
        try:
            item = self.task_list.itemAt(position)
            if not item:
                return
            
            menu = QMenu(self)
            
            # Действия для задачи
            edit_action = QAction(self.localization.get_text("toolbar.edit"), self)
            edit_action.triggered.connect(lambda: self.task_edit_requested.emit(
                self.task_list.itemWidget(item).item))
            menu.addAction(edit_action)
            
            delete_action = QAction(self.localization.get_text("toolbar.delete"), self)
            delete_action.triggered.connect(lambda: self.task_delete_requested.emit(
                self.task_list.itemWidget(item).item))
            menu.addAction(delete_action)
            
            menu.exec(self.task_list.mapToGlobal(position))
            
        except Exception as e:
            logger.error(f"Ошибка показа контекстного меню: {e}")
    
    def set_list_title(self, title: str):
        """Установить заголовок списка"""
        self.list_title_label.setText(title)
    
    def update_localization(self):
        """Обновить локализацию виджета"""
        try:
            # Обновляем тексты элементов управления
            self.add_button.setText(self.localization.get_text("toolbar.add"))
            self.search_input.setPlaceholderText(self.localization.get_text("toolbar.search") + "...")
            
            # Обновляем фильтры
            current_index = self.filter_combo.currentIndex()
            self.filter_combo.clear()
            self.filter_combo.addItems([
                self.localization.get_text("filters.all"),
                self.localization.get_text("filters.active"),
                self.localization.get_text("filters.completed"),
                self.localization.get_text("filters.overdue"),
                self.localization.get_text("filters.today"),
                self.localization.get_text("filters.upcoming")
            ])
            self.filter_combo.setCurrentIndex(current_index)
            
            # Обновляем отображение
            self.update_list_display()
            self.update_status()
            
            logger.debug("Локализация списка задач обновлена")
            
        except Exception as e:
            logger.error(f"Ошибка обновления локализации списка задач: {e}")
