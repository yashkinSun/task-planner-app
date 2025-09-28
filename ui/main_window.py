"""
Главное окно приложения Todo-Timed
"""

import logging
from datetime import date, datetime
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence, QPixmap, QPainter, QBrush

from core.database import Database
from core.localization import Localization
from core.settings import Settings
from core.resource_manager import ResourceManager
from core.models import Task, TaskList, TaskOccurrence

from .widgets.calendar_widget import CalendarWidget
from .widgets.task_list import TaskListWidget
from .widgets.toolbar import MainToolBar, StatusToolBar
from .dialogs.task_editor import TaskEditorDialog

logger = logging.getLogger(__name__)


class BackgroundWidget(QWidget):
    """Виджет с фоновым изображением"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_pixmap = None
        self.load_background()
    
    def load_background(self):
        """Загрузить фоновое изображение"""
        try:
            bg_path = ResourceManager.get_resource_path("resources/images/background.png")
            if bg_path and bg_path.exists():
                self.background_pixmap = QPixmap(str(bg_path))
                logger.debug("Фоновое изображение загружено")
            else:
                logger.warning("Фоновое изображение не найдено")
        except Exception as e:
            logger.error(f"Ошибка загрузки фонового изображения: {e}")
    
    def paintEvent(self, event):
        """Отрисовка фонового изображения"""
        super().paintEvent(event)
        
        if self.background_pixmap:
            try:
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                
                # Масштабируем изображение с сохранением пропорций
                scaled_pixmap = self.background_pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Центрируем изображение
                x = (self.width() - scaled_pixmap.width()) // 2
                y = (self.height() - scaled_pixmap.height()) // 2
                
                # Устанавливаем прозрачность
                painter.setOpacity(0.1)  # Очень слабый фон
                painter.drawPixmap(x, y, scaled_pixmap)
                
            except Exception as e:
                logger.error(f"Ошибка отрисовки фона: {e}")


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    # Сигналы
    closing = Signal()
    
    def __init__(self, database: Database, localization: Localization, settings: Settings, parent=None):
        super().__init__(parent)
        
        self.database = database
        self.localization = localization
        self.settings = settings
        
        self.current_date = date.today()
        self.current_task_list: Optional[TaskList] = None
        self.current_tasks = []
        
        self.setup_ui()
        self.setup_menu()
        self.connect_signals()
        self.load_current_date_tasks()
        self.apply_theme()
        self.restore_geometry()
        
        # Таймер для обновления данных
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(60000)  # Обновляем каждую минуту
    
    def setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle(self.localization.get_text("app.title"))
        self.setMinimumSize(900, 600)
        
        # Центральный виджет с фоном
        central_widget = BackgroundWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Создаем сплиттер для разделения календаря и списка задач
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Левая панель - календарь
        self.calendar_widget = CalendarWidget(self.localization)
        self.calendar_widget.setMaximumWidth(350)
        self.calendar_widget.setMinimumWidth(250)
        splitter.addWidget(self.calendar_widget)
        
        # Правая панель - список задач
        self.task_list_widget = TaskListWidget(self.localization)
        splitter.addWidget(self.task_list_widget)
        
        # Устанавливаем пропорции сплиттера
        splitter.setSizes([300, 600])
        
        # Панель инструментов
        self.toolbar = MainToolBar(self.localization)
        self.addToolBar(self.toolbar)
        
        # Статусная строка
        self.status_toolbar = StatusToolBar(self.localization)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.status_toolbar)
        
        logger.debug("Интерфейс главного окна настроен")
    
    def setup_menu(self):
        """Настройка меню"""
        try:
            menubar = self.menuBar()
            
            # Меню "Файл"
            file_menu = menubar.addMenu(self.localization.get_text("menu.file"))
            
            # Новая задача
            new_task_action = QAction(self.localization.get_text("menu.new_task"), self)
            new_task_action.setShortcut(QKeySequence.StandardKey.New)
            new_task_action.triggered.connect(self.add_task)
            file_menu.addAction(new_task_action)
            
            file_menu.addSeparator()
            
            # Выход
            exit_action = QAction(self.localization.get_text("menu.exit"), self)
            exit_action.setShortcut(QKeySequence.StandardKey.Quit)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # Меню "Правка"
            edit_menu = menubar.addMenu(self.localization.get_text("menu.edit"))
            
            # Найти
            find_action = QAction(self.localization.get_text("menu.find"), self)
            find_action.setShortcut(QKeySequence.StandardKey.Find)
            find_action.triggered.connect(self.focus_search)
            edit_menu.addAction(find_action)
            
            edit_menu.addSeparator()
            
            # Настройки
            preferences_action = QAction(self.localization.get_text("menu.preferences"), self)
            preferences_action.setShortcut(QKeySequence.StandardKey.Preferences)
            preferences_action.triggered.connect(self.show_settings)
            edit_menu.addAction(preferences_action)
            
            # Меню "Вид"
            view_menu = menubar.addMenu(self.localization.get_text("menu.view"))
            
            # Сегодня
            today_action = QAction(self.localization.get_text("calendar.today"), self)
            today_action.setShortcut(QKeySequence("Ctrl+T"))
            today_action.triggered.connect(self.go_to_today)
            view_menu.addAction(today_action)
            
            # Обновить
            refresh_action = QAction(self.localization.get_text("toolbar.refresh"), self)
            refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
            refresh_action.triggered.connect(self.refresh_data)
            view_menu.addAction(refresh_action)
            
            # Меню "Справка"
            help_menu = menubar.addMenu(self.localization.get_text("menu.help"))
            
            # О программе
            about_action = QAction(self.localization.get_text("menu.about"), self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
            
            logger.debug("Меню настроено")
            
        except Exception as e:
            logger.error(f"Ошибка настройки меню: {e}")
    
    def connect_signals(self):
        """Подключение сигналов"""
        try:
            # Календарь
            self.calendar_widget.date_selected.connect(self.on_date_selected)
            
            # Список задач
            self.task_list_widget.task_toggled.connect(self.on_task_toggled)
            self.task_list_widget.task_edit_requested.connect(self.edit_task)
            self.task_list_widget.task_delete_requested.connect(self.delete_task)
            self.task_list_widget.add_task_requested.connect(self.add_task)
            
            # Панель инструментов
            self.toolbar.add_task_requested.connect(self.add_task)
            self.toolbar.edit_task_requested.connect(self.edit_selected_task)
            self.toolbar.delete_task_requested.connect(self.delete_selected_task)
            self.toolbar.mark_done_requested.connect(self.toggle_selected_task)
            self.toolbar.go_to_today_requested.connect(self.go_to_today)
            self.toolbar.settings_requested.connect(self.show_settings)
            self.toolbar.refresh_requested.connect(self.refresh_data)
            
            logger.debug("Сигналы подключены")
            
        except Exception as e:
            logger.error(f"Ошибка подключения сигналов: {e}")
    
    def on_date_selected(self, selected_date: date):
        """Обработка выбора даты в календаре"""
        try:
            if selected_date != self.current_date:
                self.current_date = selected_date
                self.load_current_date_tasks()
                self.update_status()
                logger.debug(f"Выбрана дата: {selected_date}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки выбора даты: {e}")
    
    def load_current_date_tasks(self):
        """Загрузить задачи для текущей даты"""
        try:
            self.status_toolbar.set_status(self.localization.get_text("status.loading"))
            
            # Получаем или создаем список задач для даты
            self.current_task_list = self.database.get_task_list_by_date(self.current_date)
            if not self.current_task_list:
                self.current_task_list = TaskList(date=self.current_date)
                list_id = self.database.create_task_list(self.current_task_list)
                self.current_task_list.id = list_id
            
            # Загружаем задачи
            tasks = []
            if self.current_task_list.id:
                tasks = self.database.get_tasks_by_list_id(self.current_task_list.id)
            
            # TODO: Добавить загрузку экземпляров повторяющихся задач для этой даты
            
            self.current_tasks = tasks
            self.task_list_widget.set_tasks(tasks)
            self.task_list_widget.set_list_title(self.current_task_list.title)
            
            self.update_status()
            self.status_toolbar.set_status(self.localization.get_text("status.ready"))
            
            logger.debug(f"Загружено {len(tasks)} задач для {self.current_date}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки задач: {e}")
            self.status_toolbar.set_status(self.localization.get_text("status.error"))
            QMessageBox.critical(
                self,
                self.localization.get_text("app.error"),
                f"{self.localization.get_text('errors.load_failed')}: {str(e)}"
            )
    
    def on_task_toggled(self, task, is_completed: bool):
        """Обработка изменения статуса задачи"""
        try:
            if isinstance(task, TaskOccurrence):
                if is_completed:
                    task.mark_completed()
                else:
                    task.mark_pending()
                # TODO: Обновить в базе данных
            else:  # Task
                if is_completed:
                    task.mark_completed()
                else:
                    task.mark_pending()
                self.database.update_task(task)
            
            self.task_list_widget.update_task(task)
            self.update_status()
            
            logger.debug(f"Статус задачи изменен: {task.title if hasattr(task, 'title') else 'occurrence'}")
            
        except Exception as e:
            logger.error(f"Ошибка изменения статуса задачи: {e}")
            QMessageBox.critical(
                self,
                self.localization.get_text("app.error"),
                f"{self.localization.get_text('errors.save_failed')}: {str(e)}"
            )
    
    def add_task(self):
        """Добавить новую задачу"""
        try:
            dialog = TaskEditorDialog(self.localization, parent=self)
            dialog.task_saved.connect(self.on_task_saved)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Ошибка открытия диалога добавления задачи: {e}")
    
    def edit_task(self, task):
        """Редактировать задачу"""
        try:
            dialog = TaskEditorDialog(self.localization, task, parent=self)
            dialog.task_saved.connect(self.on_task_saved)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Ошибка открытия диалога редактирования задачи: {e}")
    
    def edit_selected_task(self):
        """Редактировать выбранную задачу"""
        # TODO: Получить выбранную задачу из списка
        pass
    
    def delete_task(self, task):
        """Удалить задачу"""
        try:
            # Подтверждение удаления
            reply = QMessageBox.question(
                self,
                self.localization.get_text("dialogs.confirm_delete.title"),
                self.localization.get_text("dialogs.confirm_delete.message"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if isinstance(task, TaskOccurrence):
                    # TODO: Удалить экземпляр повторяющейся задачи
                    pass
                else:  # Task
                    self.database.delete_task(task.id)
                
                self.task_list_widget.remove_task(task)
                self.update_status()
                
                logger.info(f"Задача удалена: {task.title if hasattr(task, 'title') else 'occurrence'}")
                
        except Exception as e:
            logger.error(f"Ошибка удаления задачи: {e}")
            QMessageBox.critical(
                self,
                self.localization.get_text("app.error"),
                f"{self.localization.get_text('errors.delete_failed')}: {str(e)}"
            )
    
    def delete_selected_task(self):
        """Удалить выбранную задачу"""
        # TODO: Получить выбранную задачу из списка
        pass
    
    def toggle_selected_task(self):
        """Переключить статус выбранной задачи"""
        # TODO: Получить выбранную задачу из списка
        pass
    
    def on_task_saved(self, task):
        """Обработка сохранения задачи"""
        try:
            if isinstance(task, TaskOccurrence):
                # TODO: Сохранить экземпляр повторяющейся задачи
                pass
            else:  # Task
                if task.id:
                    # Обновляем существующую задачу
                    self.database.update_task(task)
                    self.task_list_widget.update_task(task)
                else:
                    # Создаем новую задачу
                    task.list_id = self.current_task_list.id
                    task_id = self.database.create_task(task)
                    task.id = task_id
                    self.task_list_widget.add_task(task)
                    self.current_tasks.append(task)
            
            self.update_status()
            
            logger.info(f"Задача сохранена: {task.title if hasattr(task, 'title') else 'occurrence'}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения задачи: {e}")
            QMessageBox.critical(
                self,
                self.localization.get_text("app.error"),
                f"{self.localization.get_text('errors.save_failed')}: {str(e)}"
            )
    
    def go_to_today(self):
        """Перейти к сегодняшней дате"""
        self.calendar_widget.go_to_today()
    
    def focus_search(self):
        """Установить фокус на поле поиска"""
        # TODO: Реализовать фокус на поиске в списке задач
        pass
    
    def show_settings(self):
        """Показать диалог настроек"""
        # TODO: Реализовать диалог настроек
        QMessageBox.information(
            self,
            self.localization.get_text("app.info"),
            "Диалог настроек будет реализован в следующей версии"
        )
    
    def show_about(self):
        """Показать диалог "О программе" """
        QMessageBox.about(
            self,
            self.localization.get_text("menu.about"),
            f"{self.localization.get_text('app.title')} v1.0.0\n\n"
            f"Планировщик задач с календарем и напоминаниями"
        )
    
    def refresh_data(self):
        """Обновить данные"""
        try:
            self.load_current_date_tasks()
            # TODO: Обновить выделение дат с задачами в календаре
            logger.debug("Данные обновлены")
            
        except Exception as e:
            logger.error(f"Ошибка обновления данных: {e}")
    
    def update_status(self):
        """Обновить статусную строку"""
        try:
            # Текущая дата
            if self.localization.current_language == 'ru':
                date_str = self.current_date.strftime("%d %B %Y")
                # Заменяем английские названия месяцев на русские
                month_names = {
                    'January': 'января', 'February': 'февраля', 'March': 'марта',
                    'April': 'апреля', 'May': 'мая', 'June': 'июня',
                    'July': 'июля', 'August': 'августа', 'September': 'сентября',
                    'October': 'октября', 'November': 'ноября', 'December': 'декабря'
                }
                for eng, rus in month_names.items():
                    date_str = date_str.replace(eng, rus)
            else:
                date_str = self.current_date.strftime("%B %d, %Y")
            
            self.status_toolbar.set_current_date(date_str)
            
            # Счетчик задач
            total_tasks = len(self.current_tasks)
            completed_tasks = sum(1 for task in self.current_tasks if task.is_completed)
            self.status_toolbar.set_tasks_count(total_tasks, completed_tasks)
            
        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")
    
    def apply_theme(self):
        """Применить тему оформления"""
        try:
            theme = self.settings.get('theme', 'system')
            
            if theme == 'system':
                # TODO: Определить системную тему
                theme = 'light'
            
            # Загружаем файл стилей
            style_file = f"resources/styles/{theme}.qss"
            style_path = ResourceManager.get_resource_path(style_file)
            
            if style_path and style_path.exists():
                with open(style_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                logger.debug(f"Применена тема: {theme}")
            else:
                logger.warning(f"Файл темы не найден: {style_file}")
                
        except Exception as e:
            logger.error(f"Ошибка применения темы: {e}")
    
    def restore_geometry(self):
        """Восстановить геометрию окна"""
        try:
            geometry = self.settings.get('window_geometry')
            if geometry:
                self.restoreGeometry(geometry)
            
            state = self.settings.get('window_state')
            if state:
                self.restoreState(state)
                
        except Exception as e:
            logger.error(f"Ошибка восстановления геометрии окна: {e}")
    
    def save_geometry(self):
        """Сохранить геометрию окна"""
        try:
            self.settings.set('window_geometry', self.saveGeometry())
            self.settings.set('window_state', self.saveState())
            
        except Exception as e:
            logger.error(f"Ошибка сохранения геометрии окна: {e}")
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        try:
            # Сохраняем геометрию окна
            self.save_geometry()
            
            # Проверяем настройку сворачивания в трей
            if self.settings.get('minimize_to_tray', True):
                event.ignore()
                self.hide()
                logger.debug("Окно свернуто в трей")
            else:
                self.closing.emit()
                event.accept()
                logger.debug("Окно закрыто")
                
        except Exception as e:
            logger.error(f"Ошибка закрытия окна: {e}")
            event.accept()
    
    def update_localization(self):
        """Обновить локализацию интерфейса"""
        try:
            # Обновляем заголовок окна
            self.setWindowTitle(self.localization.get_text("app.title"))
            
            # Обновляем виджеты
            self.calendar_widget.update_localization()
            self.task_list_widget.update_localization()
            self.toolbar.update_localization()
            self.status_toolbar.update_localization()
            
            # Обновляем меню
            self.setup_menu()
            
            # Обновляем статус
            self.update_status()
            
            logger.debug("Локализация главного окна обновлена")
            
        except Exception as e:
            logger.error(f"Ошибка обновления локализации главного окна: {e}")
