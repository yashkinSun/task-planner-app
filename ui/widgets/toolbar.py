"""
Панель инструментов с основными действиями
"""

import logging
from typing import Optional

from PySide6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence

logger = logging.getLogger(__name__)


class MainToolBar(QToolBar):
    """Основная панель инструментов"""
    
    # Сигналы для действий
    add_task_requested = Signal()
    edit_task_requested = Signal()
    delete_task_requested = Signal()
    mark_done_requested = Signal()
    go_to_today_requested = Signal()
    settings_requested = Signal()
    refresh_requested = Signal()
    
    def __init__(self, localization, parent=None):
        super().__init__(parent)
        self.localization = localization
        self.actions_dict = {}
        
        self.setup_toolbar()
        self.create_actions()
        self.update_localization()
    
    def setup_toolbar(self):
        """Настройка панели инструментов"""
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(self.iconSize())  # Используем стандартный размер
    
    def create_actions(self):
        """Создание действий панели инструментов"""
        try:
            # Добавить задачу
            self.add_action = QAction(self)
            self.add_action.setShortcut(QKeySequence.StandardKey.New)
            self.add_action.triggered.connect(self.add_task_requested.emit)
            self.actions_dict['add'] = self.add_action
            self.addAction(self.add_action)
            
            # Редактировать задачу
            self.edit_action = QAction(self)
            self.edit_action.setShortcut(QKeySequence("Ctrl+E"))
            self.edit_action.triggered.connect(self.edit_task_requested.emit)
            self.edit_action.setEnabled(False)  # Включается при выборе задачи
            self.actions_dict['edit'] = self.edit_action
            self.addAction(self.edit_action)
            
            # Разделитель
            self.addSeparator()
            
            # Отметить как выполненное
            self.done_action = QAction(self)
            self.done_action.setShortcut(QKeySequence("Ctrl+D"))
            self.done_action.triggered.connect(self.mark_done_requested.emit)
            self.done_action.setEnabled(False)  # Включается при выборе задачи
            self.actions_dict['done'] = self.done_action
            self.addAction(self.done_action)
            
            # Удалить задачу
            self.delete_action = QAction(self)
            self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
            self.delete_action.triggered.connect(self.delete_task_requested.emit)
            self.delete_action.setEnabled(False)  # Включается при выборе задачи
            self.actions_dict['delete'] = self.delete_action
            self.addAction(self.delete_action)
            
            # Разделитель
            self.addSeparator()
            
            # Перейти к сегодня
            self.today_action = QAction(self)
            self.today_action.setShortcut(QKeySequence("Ctrl+T"))
            self.today_action.triggered.connect(self.go_to_today_requested.emit)
            self.actions_dict['today'] = self.today_action
            self.addAction(self.today_action)
            
            # Обновить
            self.refresh_action = QAction(self)
            self.refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
            self.refresh_action.triggered.connect(self.refresh_requested.emit)
            self.actions_dict['refresh'] = self.refresh_action
            self.addAction(self.refresh_action)
            
            # Разделитель
            self.addSeparator()
            
            # Настройки
            self.settings_action = QAction(self)
            self.settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
            self.settings_action.triggered.connect(self.settings_requested.emit)
            self.actions_dict['settings'] = self.settings_action
            self.addAction(self.settings_action)
            
            logger.debug("Действия панели инструментов созданы")
            
        except Exception as e:
            logger.error(f"Ошибка создания действий панели инструментов: {e}")
    
    def update_localization(self):
        """Обновить локализацию панели инструментов"""
        try:
            # Обновляем тексты действий
            if 'add' in self.actions_dict:
                self.actions_dict['add'].setText(self.localization.get_text("toolbar.add"))
                self.actions_dict['add'].setToolTip(
                    f"{self.localization.get_text('toolbar.add')} (Ctrl+N)"
                )
            
            if 'edit' in self.actions_dict:
                self.actions_dict['edit'].setText(self.localization.get_text("toolbar.edit"))
                self.actions_dict['edit'].setToolTip(
                    f"{self.localization.get_text('toolbar.edit')} (Ctrl+E)"
                )
            
            if 'done' in self.actions_dict:
                self.actions_dict['done'].setText(self.localization.get_text("toolbar.done"))
                self.actions_dict['done'].setToolTip(
                    f"{self.localization.get_text('toolbar.done')} (Ctrl+D)"
                )
            
            if 'delete' in self.actions_dict:
                self.actions_dict['delete'].setText(self.localization.get_text("toolbar.delete"))
                self.actions_dict['delete'].setToolTip(
                    f"{self.localization.get_text('toolbar.delete')} (Del)"
                )
            
            if 'today' in self.actions_dict:
                self.actions_dict['today'].setText(self.localization.get_text("toolbar.today"))
                self.actions_dict['today'].setToolTip(
                    f"{self.localization.get_text('toolbar.today')} (Ctrl+T)"
                )
            
            if 'refresh' in self.actions_dict:
                self.actions_dict['refresh'].setText(self.localization.get_text("toolbar.refresh"))
                self.actions_dict['refresh'].setToolTip(
                    f"{self.localization.get_text('toolbar.refresh')} (F5)"
                )
            
            if 'settings' in self.actions_dict:
                self.actions_dict['settings'].setText(self.localization.get_text("toolbar.settings"))
                self.actions_dict['settings'].setToolTip(
                    f"{self.localization.get_text('toolbar.settings')} (Ctrl+,)"
                )
            
            logger.debug("Локализация панели инструментов обновлена")
            
        except Exception as e:
            logger.error(f"Ошибка обновления локализации панели инструментов: {e}")
    
    def set_task_actions_enabled(self, enabled: bool):
        """Включить/выключить действия, требующие выбранной задачи"""
        try:
            task_dependent_actions = ['edit', 'done', 'delete']
            for action_name in task_dependent_actions:
                if action_name in self.actions_dict:
                    self.actions_dict[action_name].setEnabled(enabled)
                    
        except Exception as e:
            logger.error(f"Ошибка изменения состояния действий: {e}")
    
    def set_done_action_text(self, is_completed: bool):
        """Изменить текст действия 'выполнено' в зависимости от статуса задачи"""
        try:
            if 'done' in self.actions_dict:
                if is_completed:
                    text = self.localization.get_text("toolbar.undo_done")
                    tooltip = f"{text} (Ctrl+D)"
                else:
                    text = self.localization.get_text("toolbar.done")
                    tooltip = f"{text} (Ctrl+D)"
                
                self.actions_dict['done'].setText(text)
                self.actions_dict['done'].setToolTip(tooltip)
                
        except Exception as e:
            logger.error(f"Ошибка изменения текста действия 'выполнено': {e}")
    
    def get_action(self, action_name: str) -> Optional[QAction]:
        """Получить действие по имени"""
        return self.actions_dict.get(action_name)


class StatusToolBar(QToolBar):
    """Панель статуса с информацией о текущем состоянии"""
    
    def __init__(self, localization, parent=None):
        super().__init__(parent)
        self.localization = localization
        
        self.setup_toolbar()
        self.create_widgets()
    
    def setup_toolbar(self):
        """Настройка панели статуса"""
        self.setMovable(False)
        self.setFloatable(False)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
    
    def create_widgets(self):
        """Создание виджетов панели статуса"""
        try:
            # Контейнер для виджетов
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(8, 4, 8, 4)
            layout.setSpacing(16)
            
            # Статус приложения
            self.status_label = QLabel(self.localization.get_text("status.ready"))
            layout.addWidget(self.status_label)
            
            layout.addStretch()
            
            # Информация о текущей дате
            self.date_label = QLabel()
            layout.addWidget(self.date_label)
            
            # Счетчик задач
            self.tasks_count_label = QLabel()
            layout.addWidget(self.tasks_count_label)
            
            self.addWidget(container)
            
            logger.debug("Виджеты панели статуса созданы")
            
        except Exception as e:
            logger.error(f"Ошибка создания виджетов панели статуса: {e}")
    
    def set_status(self, status: str):
        """Установить статус приложения"""
        try:
            self.status_label.setText(status)
        except Exception as e:
            logger.error(f"Ошибка установки статуса: {e}")
    
    def set_current_date(self, current_date: str):
        """Установить текущую дату"""
        try:
            self.date_label.setText(current_date)
        except Exception as e:
            logger.error(f"Ошибка установки даты: {e}")
    
    def set_tasks_count(self, total: int, completed: int):
        """Установить счетчик задач"""
        try:
            text = f"{total} {self.localization.get_text('status.tasks_count')}"
            if completed > 0:
                text += f", {completed} {self.localization.get_text('status.completed_count')}"
            self.tasks_count_label.setText(text)
        except Exception as e:
            logger.error(f"Ошибка установки счетчика задач: {e}")
    
    def update_localization(self):
        """Обновить локализацию панели статуса"""
        try:
            # Статус будет обновлен при следующем вызове set_status
            # Счетчик задач будет обновлен при следующем вызове set_tasks_count
            logger.debug("Локализация панели статуса обновлена")
            
        except Exception as e:
            logger.error(f"Ошибка обновления локализации панели статуса: {e}")
