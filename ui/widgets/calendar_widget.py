"""
Виджет календаря для выбора даты и навигации
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCalendarWidget, 
    QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Signal, QDate, Qt
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class CalendarWidget(QWidget):
    """Виджет календаря с быстрой навигацией"""
    
    # Сигналы
    date_selected = Signal(date)  # Выбрана новая дата
    
    def __init__(self, localization, parent=None):
        super().__init__(parent)
        self.localization = localization
        self.current_date = date.today()
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Заголовок с быстрой навигацией
        self.create_header(layout)
        
        # Основной календарь
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setSelectedDate(QDate.currentDate())
        
        # Настройка локализации календаря
        self.setup_calendar_localization()
        
        layout.addWidget(self.calendar)
        
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Кнопки быстрого перехода
        self.create_quick_navigation(layout)
    
    def create_header(self, layout):
        """Создать заголовок с навигацией"""
        header_layout = QHBoxLayout()
        
        # Кнопка "Сегодня"
        self.today_button = QPushButton(self.localization.get_text("calendar.today"))
        self.today_button.setProperty("primary", True)
        header_layout.addWidget(self.today_button)
        
        header_layout.addStretch()
        
        # Текущая дата
        self.date_label = QLabel()
        font = QFont()
        font.setBold(True)
        self.date_label.setFont(font)
        self.update_date_label()
        header_layout.addWidget(self.date_label)
        
        layout.addLayout(header_layout)
    
    def create_quick_navigation(self, layout):
        """Создать кнопки быстрой навигации"""
        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(4)
        
        # Первый ряд кнопок
        row1_layout = QHBoxLayout()
        
        self.yesterday_button = QPushButton(self.localization.get_text("calendar.yesterday"))
        self.tomorrow_button = QPushButton(self.localization.get_text("calendar.tomorrow"))
        
        row1_layout.addWidget(self.yesterday_button)
        row1_layout.addWidget(self.tomorrow_button)
        
        nav_layout.addLayout(row1_layout)
        
        # Второй ряд кнопок
        row2_layout = QHBoxLayout()
        
        self.this_week_button = QPushButton(self.localization.get_text("calendar.this_week"))
        self.next_week_button = QPushButton(self.localization.get_text("calendar.next_week"))
        
        row2_layout.addWidget(self.this_week_button)
        row2_layout.addWidget(self.next_week_button)
        
        nav_layout.addLayout(row2_layout)
        
        layout.addLayout(nav_layout)
    
    def setup_calendar_localization(self):
        """Настройка локализации календаря"""
        try:
            # Устанавливаем первый день недели (понедельник)
            self.calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
            
            # Названия месяцев и дней недели устанавливаются автоматически
            # на основе системной локали Qt
            
        except Exception as e:
            logger.warning(f"Ошибка настройки локализации календаря: {e}")
    
    def connect_signals(self):
        """Подключение сигналов"""
        # Основной календарь
        self.calendar.selectionChanged.connect(self.on_calendar_selection_changed)
        
        # Кнопки навигации
        self.today_button.clicked.connect(self.go_to_today)
        self.yesterday_button.clicked.connect(self.go_to_yesterday)
        self.tomorrow_button.clicked.connect(self.go_to_tomorrow)
        self.this_week_button.clicked.connect(self.go_to_this_week)
        self.next_week_button.clicked.connect(self.go_to_next_week)
    
    def on_calendar_selection_changed(self):
        """Обработка изменения выбранной даты в календаре"""
        try:
            selected_qdate = self.calendar.selectedDate()
            selected_date = selected_qdate.toPython()
            
            if selected_date != self.current_date:
                self.current_date = selected_date
                self.update_date_label()
                self.date_selected.emit(selected_date)
                logger.debug(f"Выбрана дата: {selected_date}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки выбора даты: {e}")
    
    def update_date_label(self):
        """Обновить отображение текущей даты"""
        try:
            # Форматируем дату в зависимости от языка
            if self.localization.current_language == 'ru':
                formatted_date = self.current_date.strftime("%d %B %Y")
                # Заменяем английские названия месяцев на русские
                month_names = {
                    'January': 'января', 'February': 'февраля', 'March': 'марта',
                    'April': 'апреля', 'May': 'мая', 'June': 'июня',
                    'July': 'июля', 'August': 'августа', 'September': 'сентября',
                    'October': 'октября', 'November': 'ноября', 'December': 'декабря'
                }
                for eng, rus in month_names.items():
                    formatted_date = formatted_date.replace(eng, rus)
            else:
                formatted_date = self.current_date.strftime("%B %d, %Y")
            
            self.date_label.setText(formatted_date)
            
        except Exception as e:
            logger.error(f"Ошибка обновления метки даты: {e}")
            self.date_label.setText(str(self.current_date))
    
    def set_selected_date(self, target_date: date):
        """Установить выбранную дату программно"""
        try:
            qdate = QDate(target_date.year, target_date.month, target_date.day)
            self.calendar.setSelectedDate(qdate)
            # on_calendar_selection_changed будет вызван автоматически
            
        except Exception as e:
            logger.error(f"Ошибка установки даты: {e}")
    
    def get_selected_date(self) -> date:
        """Получить текущую выбранную дату"""
        return self.current_date
    
    # Методы быстрой навигации
    
    def go_to_today(self):
        """Перейти к сегодняшней дате"""
        self.set_selected_date(date.today())
    
    def go_to_yesterday(self):
        """Перейти к вчерашней дате"""
        yesterday = self.current_date - timedelta(days=1)
        self.set_selected_date(yesterday)
    
    def go_to_tomorrow(self):
        """Перейти к завтрашней дате"""
        tomorrow = self.current_date + timedelta(days=1)
        self.set_selected_date(tomorrow)
    
    def go_to_this_week(self):
        """Перейти к началу текущей недели (понедельник)"""
        today = date.today()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        self.set_selected_date(monday)
    
    def go_to_next_week(self):
        """Перейти к началу следующей недели"""
        today = date.today()
        days_since_monday = today.weekday()
        next_monday = today + timedelta(days=7 - days_since_monday)
        self.set_selected_date(next_monday)
    
    def highlight_dates_with_tasks(self, dates_with_tasks: list[date]):
        """
        Выделить даты, на которые есть задачи
        
        Args:
            dates_with_tasks: Список дат с задачами
        """
        try:
            # Сбрасываем предыдущие выделения
            self.calendar.setDateTextFormat(QDate(), self.calendar.dateTextFormat(QDate()))
            
            # Выделяем даты с задачами
            from PySide6.QtGui import QTextCharFormat, QColor
            
            format_with_tasks = QTextCharFormat()
            format_with_tasks.setBackground(QColor(0, 120, 212, 50))  # Полупрозрачный синий
            format_with_tasks.setForeground(QColor(0, 120, 212))      # Синий текст
            
            for task_date in dates_with_tasks:
                qdate = QDate(task_date.year, task_date.month, task_date.day)
                self.calendar.setDateTextFormat(qdate, format_with_tasks)
                
        except Exception as e:
            logger.error(f"Ошибка выделения дат с задачами: {e}")
    
    def update_localization(self):
        """Обновить локализацию виджета"""
        try:
            # Обновляем тексты кнопок
            self.today_button.setText(self.localization.get_text("calendar.today"))
            self.yesterday_button.setText(self.localization.get_text("calendar.yesterday"))
            self.tomorrow_button.setText(self.localization.get_text("calendar.tomorrow"))
            self.this_week_button.setText(self.localization.get_text("calendar.this_week"))
            self.next_week_button.setText(self.localization.get_text("calendar.next_week"))
            
            # Обновляем метку даты
            self.update_date_label()
            
            logger.debug("Локализация календаря обновлена")
            
        except Exception as e:
            logger.error(f"Ошибка обновления локализации календаря: {e}")
