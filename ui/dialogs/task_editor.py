"""
Диалог редактирования задач с поддержкой повторений
"""

import logging
from datetime import datetime, date, time
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QDateEdit, QTimeEdit, QCheckBox, QComboBox, QPushButton, QGroupBox,
    QLabel, QListWidget, QMessageBox, QSpinBox, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, QDate, QTime, Signal
from PySide6.QtGui import QFont

from core.models import Task, TaskOccurrence, RecurrenceRule, RecurrenceFrequency, TaskStatus, validate_task, validate_recurrence_rule

logger = logging.getLogger(__name__)


class TaskEditorDialog(QDialog):
    """Диалог редактирования задач"""
    
    # Сигналы
    task_saved = Signal(object)  # Task или TaskOccurrence
    
    def __init__(self, localization, task=None, parent=None):
        super().__init__(parent)
        self.localization = localization
        self.task = task  # Task или TaskOccurrence для редактирования
        self.is_editing = task is not None
        self.is_occurrence = isinstance(task, TaskOccurrence)
        
        self.setup_ui()
        self.connect_signals()
        self.load_task_data()
        self.update_recurrence_visibility()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        self.setModal(True)
        self.setMinimumSize(500, 600)
        
        # Заголовок
        if self.is_editing:
            if self.is_occurrence:
                title = self.localization.get_text("dialogs.task_editor.title_edit") + " (Экземпляр)"
            else:
                title = self.localization.get_text("dialogs.task_editor.title_edit")
        else:
            title = self.localization.get_text("dialogs.task_editor.title_new")
        
        self.setWindowTitle(title)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Основная информация
        self.create_basic_info_section(layout)
        
        # Время выполнения
        self.create_datetime_section(layout)
        
        # Повторение (только для новых задач или редактирования основной задачи)
        if not self.is_occurrence:
            self.create_recurrence_section(layout)
        
        # Предварительный просмотр повторений
        if not self.is_occurrence:
            self.create_preview_section(layout)
        
        # Кнопки
        self.create_buttons(layout)
    
    def create_basic_info_section(self, layout):
        """Создать секцию основной информации"""
        basic_group = QGroupBox(self.localization.get_text("dialogs.task_editor.basic_info"))
        basic_layout = QFormLayout(basic_group)
        
        # Название задачи
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(self.localization.get_text("task.title"))
        basic_layout.addRow(self.localization.get_text("task.title") + "*:", self.title_input)
        
        # Описание
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText(self.localization.get_text("task.notes"))
        basic_layout.addRow(self.localization.get_text("task.notes") + ":", self.notes_input)
        
        layout.addWidget(basic_group)
    
    def create_datetime_section(self, layout):
        """Создать секцию даты и времени"""
        datetime_group = QGroupBox(self.localization.get_text("task.due_date"))
        datetime_layout = QFormLayout(datetime_group)
        
        # Дата
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        datetime_layout.addRow(self.localization.get_text("task.due_date") + ":", self.date_input)
        
        # Время
        time_layout = QHBoxLayout()
        
        self.has_time_checkbox = QCheckBox(self.localization.get_text("task.due_time"))
        time_layout.addWidget(self.has_time_checkbox)
        
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime(9, 0))  # По умолчанию 9:00
        self.time_input.setEnabled(False)
        time_layout.addWidget(self.time_input)
        
        time_layout.addStretch()
        datetime_layout.addRow("", time_layout)
        
        layout.addWidget(datetime_group)
    
    def create_recurrence_section(self, layout):
        """Создать секцию повторения"""
        self.recurrence_group = QGroupBox(self.localization.get_text("dialogs.task_editor.repeat"))
        recurrence_layout = QVBoxLayout(self.recurrence_group)
        
        # Чекбокс включения повторения
        self.repeat_checkbox = QCheckBox(self.localization.get_text("dialogs.task_editor.repeat"))
        recurrence_layout.addWidget(self.repeat_checkbox)
        
        # Контейнер для настроек повторения
        self.recurrence_container = QWidget()
        recurrence_container_layout = QFormLayout(self.recurrence_container)
        
        # Частота
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems([
            self.localization.get_text("recurrence.daily"),
            self.localization.get_text("recurrence.weekly"),
            self.localization.get_text("recurrence.monthly"),
            self.localization.get_text("recurrence.yearly")
        ])
        recurrence_container_layout.addRow(
            self.localization.get_text("dialogs.task_editor.frequency") + ":",
            self.frequency_combo
        )
        
        # Интервал
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel(self.localization.get_text("recurrence.every")))
        
        self.interval_input = QSpinBox()
        self.interval_input.setMinimum(1)
        self.interval_input.setMaximum(999)
        self.interval_input.setValue(1)
        interval_layout.addWidget(self.interval_input)
        
        self.interval_label = QLabel(self.localization.get_text("recurrence.days"))
        interval_layout.addWidget(self.interval_label)
        interval_layout.addStretch()
        
        recurrence_container_layout.addRow(
            self.localization.get_text("dialogs.task_editor.interval") + ":",
            interval_layout
        )
        
        # Дни недели (для еженедельного повторения)
        self.days_group = QGroupBox(self.localization.get_text("dialogs.task_editor.days_of_week"))
        days_layout = QHBoxLayout(self.days_group)
        
        self.day_checkboxes = []
        day_names = [
            self.localization.get_text("calendar.monday"),
            self.localization.get_text("calendar.tuesday"),
            self.localization.get_text("calendar.wednesday"),
            self.localization.get_text("calendar.thursday"),
            self.localization.get_text("calendar.friday"),
            self.localization.get_text("calendar.saturday"),
            self.localization.get_text("calendar.sunday")
        ]
        
        for i, day_name in enumerate(day_names):
            checkbox = QCheckBox(day_name[:2])  # Сокращенное название
            checkbox.setToolTip(day_name)
            self.day_checkboxes.append(checkbox)
            days_layout.addWidget(checkbox)
        
        self.days_group.setVisible(False)
        recurrence_container_layout.addRow(self.days_group)
        
        # Окончание повторения
        end_group = QGroupBox(self.localization.get_text("recurrence.until"))
        end_layout = QVBoxLayout(end_group)
        
        # Радиокнопки для выбора типа окончания
        self.end_never_radio = QRadioButton(self.localization.get_text("recurrence.never"))
        self.end_never_radio.setChecked(True)
        end_layout.addWidget(self.end_never_radio)
        
        # До даты
        end_date_layout = QHBoxLayout()
        self.end_date_radio = QRadioButton(self.localization.get_text("recurrence.until") + ":")
        end_date_layout.addWidget(self.end_date_radio)
        
        self.end_date_input = QDateEdit()
        self.end_date_input.setDate(QDate.currentDate().addDays(30))
        self.end_date_input.setEnabled(False)
        end_date_layout.addWidget(self.end_date_input)
        end_date_layout.addStretch()
        
        end_layout.addLayout(end_date_layout)
        
        # Количество повторений
        end_count_layout = QHBoxLayout()
        self.end_count_radio = QRadioButton(self.localization.get_text("recurrence.count") + ":")
        end_count_layout.addWidget(self.end_count_radio)
        
        self.end_count_input = QSpinBox()
        self.end_count_input.setMinimum(1)
        self.end_count_input.setMaximum(999)
        self.end_count_input.setValue(10)
        self.end_count_input.setEnabled(False)
        end_count_layout.addWidget(self.end_count_input)
        end_count_layout.addStretch()
        
        end_layout.addLayout(end_count_layout)
        
        recurrence_container_layout.addRow(end_group)
        
        # Группировка радиокнопок
        self.end_button_group = QButtonGroup()
        self.end_button_group.addButton(self.end_never_radio, 0)
        self.end_button_group.addButton(self.end_date_radio, 1)
        self.end_button_group.addButton(self.end_count_radio, 2)
        
        self.recurrence_container.setEnabled(False)
        recurrence_layout.addWidget(self.recurrence_container)
        
        layout.addWidget(self.recurrence_group)
    
    def create_preview_section(self, layout):
        """Создать секцию предварительного просмотра"""
        self.preview_group = QGroupBox(self.localization.get_text("dialogs.task_editor.preview"))
        preview_layout = QVBoxLayout(self.preview_group)
        
        self.preview_list = QListWidget()
        self.preview_list.setMaximumHeight(120)
        preview_layout.addWidget(self.preview_list)
        
        self.preview_group.setVisible(False)
        layout.addWidget(self.preview_group)
    
    def create_buttons(self, layout):
        """Создать кнопки диалога"""
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Кнопка отмены
        self.cancel_button = QPushButton(self.localization.get_text("dialogs.cancel"))
        buttons_layout.addWidget(self.cancel_button)
        
        # Кнопка сохранения
        self.save_button = QPushButton(self.localization.get_text("dialogs.save"))
        self.save_button.setProperty("primary", True)
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
    
    def connect_signals(self):
        """Подключение сигналов"""
        # Основные кнопки
        self.save_button.clicked.connect(self.save_task)
        self.cancel_button.clicked.connect(self.reject)
        
        # Время
        self.has_time_checkbox.toggled.connect(self.time_input.setEnabled)
        
        # Повторение
        if hasattr(self, 'repeat_checkbox'):
            self.repeat_checkbox.toggled.connect(self.on_repeat_toggled)
            self.frequency_combo.currentTextChanged.connect(self.on_frequency_changed)
            self.end_button_group.buttonToggled.connect(self.on_end_type_changed)
            
            # Обновление предварительного просмотра
            self.frequency_combo.currentTextChanged.connect(self.update_preview)
            self.interval_input.valueChanged.connect(self.update_preview)
            for checkbox in self.day_checkboxes:
                checkbox.toggled.connect(self.update_preview)
            self.end_date_input.dateChanged.connect(self.update_preview)
            self.end_count_input.valueChanged.connect(self.update_preview)
            self.date_input.dateChanged.connect(self.update_preview)
            self.time_input.timeChanged.connect(self.update_preview)
    
    def load_task_data(self):
        """Загрузить данные задачи для редактирования"""
        if not self.task:
            return
        
        try:
            if self.is_occurrence:
                # Загружаем данные экземпляра
                self.title_input.setText(self.task.effective_title)
                if self.task.parent_task and self.task.parent_task.notes:
                    self.notes_input.setPlainText(self.task.parent_task.notes)
                
                due_at = self.task.effective_due_at
                if due_at:
                    self.date_input.setDate(QDate(due_at.year, due_at.month, due_at.day))
                    self.time_input.setTime(QTime(due_at.hour, due_at.minute))
                    self.has_time_checkbox.setChecked(True)
                    self.time_input.setEnabled(True)
            else:
                # Загружаем данные основной задачи
                self.title_input.setText(self.task.title)
                self.notes_input.setPlainText(self.task.notes)
                
                if self.task.due_at:
                    due_at = self.task.due_at
                    self.date_input.setDate(QDate(due_at.year, due_at.month, due_at.day))
                    self.time_input.setTime(QTime(due_at.hour, due_at.minute))
                    self.has_time_checkbox.setChecked(True)
                    self.time_input.setEnabled(True)
                
                # Загружаем настройки повторения
                if self.task.recurrence_rule:
                    self.repeat_checkbox.setChecked(True)
                    self.load_recurrence_data(self.task.recurrence_rule)
            
            logger.debug("Данные задачи загружены в диалог")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки данных задачи: {e}")
    
    def load_recurrence_data(self, rule: RecurrenceRule):
        """Загрузить данные правила повторения"""
        try:
            # Частота
            frequency_map = {
                RecurrenceFrequency.DAILY: 0,
                RecurrenceFrequency.WEEKLY: 1,
                RecurrenceFrequency.MONTHLY: 2,
                RecurrenceFrequency.YEARLY: 3
            }
            self.frequency_combo.setCurrentIndex(frequency_map.get(rule.frequency, 0))
            
            # Интервал
            self.interval_input.setValue(rule.interval)
            
            # Дни недели
            if rule.days_of_week:
                for day in rule.days_of_week:
                    if 0 <= day < len(self.day_checkboxes):
                        self.day_checkboxes[day].setChecked(True)
            
            # Окончание
            if rule.until_date:
                self.end_date_radio.setChecked(True)
                qdate = QDate(rule.until_date.year, rule.until_date.month, rule.until_date.day)
                self.end_date_input.setDate(qdate)
            elif rule.count:
                self.end_count_radio.setChecked(True)
                self.end_count_input.setValue(rule.count)
            else:
                self.end_never_radio.setChecked(True)
            
        except Exception as e:
            logger.error(f"Ошибка загрузки данных повторения: {e}")
    
    def on_repeat_toggled(self, checked: bool):
        """Обработка включения/выключения повторения"""
        self.recurrence_container.setEnabled(checked)
        self.update_recurrence_visibility()
        self.update_preview()
    
    def on_frequency_changed(self, frequency_text: str):
        """Обработка изменения частоты повторения"""
        try:
            # Обновляем метку интервала
            frequency_map = {
                self.localization.get_text("recurrence.daily"): self.localization.get_text("recurrence.days"),
                self.localization.get_text("recurrence.weekly"): self.localization.get_text("recurrence.weeks"),
                self.localization.get_text("recurrence.monthly"): self.localization.get_text("recurrence.months"),
                self.localization.get_text("recurrence.yearly"): self.localization.get_text("recurrence.years")
            }
            self.interval_label.setText(frequency_map.get(frequency_text, ""))
            
            # Показываем/скрываем дни недели
            show_days = frequency_text == self.localization.get_text("recurrence.weekly")
            self.days_group.setVisible(show_days)
            
            self.update_preview()
            
        except Exception as e:
            logger.error(f"Ошибка обработки изменения частоты: {e}")
    
    def on_end_type_changed(self, button, checked: bool):
        """Обработка изменения типа окончания повторения"""
        if not checked:
            return
        
        try:
            button_id = self.end_button_group.id(button)
            
            self.end_date_input.setEnabled(button_id == 1)
            self.end_count_input.setEnabled(button_id == 2)
            
            self.update_preview()
            
        except Exception as e:
            logger.error(f"Ошибка обработки изменения типа окончания: {e}")
    
    def update_recurrence_visibility(self):
        """Обновить видимость секций повторения"""
        if hasattr(self, 'repeat_checkbox'):
            is_repeat_enabled = self.repeat_checkbox.isChecked()
            self.preview_group.setVisible(is_repeat_enabled)
    
    def update_preview(self):
        """Обновить предварительный просмотр повторений"""
        if not hasattr(self, 'repeat_checkbox') or not self.repeat_checkbox.isChecked():
            return
        
        try:
            # Создаем правило повторения
            rule = self.create_recurrence_rule()
            if not rule:
                return
            
            # Генерируем предварительный просмотр
            from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
            from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU
            
            # Получаем начальную дату
            start_date = self.date_input.date().toPython()
            start_time = self.time_input.time().toPython() if self.has_time_checkbox.isChecked() else time(9, 0)
            start_datetime = datetime.combine(start_date, start_time)
            
            # Создаем rrule
            freq_map = {
                RecurrenceFrequency.DAILY: DAILY,
                RecurrenceFrequency.WEEKLY: WEEKLY,
                RecurrenceFrequency.MONTHLY: MONTHLY,
                RecurrenceFrequency.YEARLY: YEARLY
            }
            
            rrule_kwargs = {
                'freq': freq_map[rule.frequency],
                'interval': rule.interval,
                'dtstart': start_datetime
            }
            
            if rule.days_of_week:
                weekdays = [MO, TU, WE, TH, FR, SA, SU]
                rrule_kwargs['byweekday'] = [weekdays[day] for day in rule.days_of_week]
            
            if rule.until_date:
                rrule_kwargs['until'] = datetime.combine(rule.until_date, time(23, 59, 59))
            elif rule.count:
                rrule_kwargs['count'] = min(rule.count, 10)  # Ограничиваем предварительный просмотр
            else:
                rrule_kwargs['count'] = 10  # Показываем первые 10 повторений
            
            # Генерируем даты
            rule_obj = rrule(**rrule_kwargs)
            dates = list(rule_obj)
            
            # Обновляем список предварительного просмотра
            self.preview_list.clear()
            for dt in dates[:10]:  # Показываем максимум 10 дат
                if self.has_time_checkbox.isChecked():
                    date_str = dt.strftime("%d.%m.%Y %H:%M")
                else:
                    date_str = dt.strftime("%d.%m.%Y")
                self.preview_list.addItem(date_str)
            
        except Exception as e:
            logger.error(f"Ошибка обновления предварительного просмотра: {e}")
            self.preview_list.clear()
            self.preview_list.addItem(self.localization.get_text("errors.invalid_recurrence"))
    
    def create_recurrence_rule(self) -> Optional[RecurrenceRule]:
        """Создать правило повторения из данных формы"""
        if not hasattr(self, 'repeat_checkbox') or not self.repeat_checkbox.isChecked():
            return None
        
        try:
            # Частота
            frequency_map = {
                0: RecurrenceFrequency.DAILY,
                1: RecurrenceFrequency.WEEKLY,
                2: RecurrenceFrequency.MONTHLY,
                3: RecurrenceFrequency.YEARLY
            }
            frequency = frequency_map[self.frequency_combo.currentIndex()]
            
            # Интервал
            interval = self.interval_input.value()
            
            # Дни недели
            days_of_week = None
            if frequency == RecurrenceFrequency.WEEKLY:
                days_of_week = []
                for i, checkbox in enumerate(self.day_checkboxes):
                    if checkbox.isChecked():
                        days_of_week.append(i)
                if not days_of_week:
                    days_of_week = None
            
            # Окончание
            until_date = None
            count = None
            
            if self.end_date_radio.isChecked():
                until_date = self.end_date_input.date().toPython()
            elif self.end_count_radio.isChecked():
                count = self.end_count_input.value()
            
            return RecurrenceRule(
                frequency=frequency,
                interval=interval,
                days_of_week=days_of_week,
                until_date=until_date,
                count=count
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания правила повторения: {e}")
            return None
    
    def save_task(self):
        """Сохранить задачу"""
        try:
            # Валидация основных полей
            title = self.title_input.text().strip()
            if not title:
                QMessageBox.warning(
                    self,
                    self.localization.get_text("app.warning"),
                    self.localization.get_text("errors.title_required")
                )
                self.title_input.setFocus()
                return
            
            # Создаем или обновляем задачу
            if self.is_occurrence:
                # Обновляем экземпляр повторяющейся задачи
                self.task.override_title = title if title != self.task.parent_task.title else None
                
                # Обновляем время если изменилось
                if self.has_time_checkbox.isChecked():
                    new_datetime = datetime.combine(
                        self.date_input.date().toPython(),
                        self.time_input.time().toPython()
                    )
                    if new_datetime != self.task.scheduled_at:
                        self.task.override_due_at = new_datetime
                
            else:
                # Создаем или обновляем основную задачу
                if not self.task:
                    self.task = Task()
                
                self.task.title = title
                self.task.notes = self.notes_input.toPlainText().strip()
                
                # Устанавливаем время выполнения
                if self.has_time_checkbox.isChecked():
                    self.task.due_at = datetime.combine(
                        self.date_input.date().toPython(),
                        self.time_input.time().toPython()
                    )
                else:
                    self.task.due_at = None
                
                # Устанавливаем правило повторения
                self.task.recurrence_rule = self.create_recurrence_rule()
                if self.task.recurrence_rule:
                    self.task.recurrence_start = self.task.due_at
            
            # Валидация
            if not self.is_occurrence:
                errors = validate_task(self.task)
                if self.task.recurrence_rule:
                    errors.extend(validate_recurrence_rule(self.task.recurrence_rule))
                
                if errors:
                    QMessageBox.warning(
                        self,
                        self.localization.get_text("app.warning"),
                        "\n".join(errors)
                    )
                    return
            
            # Сохраняем и закрываем диалог
            self.task_saved.emit(self.task)
            self.accept()
            
            logger.info(f"Задача сохранена: {title}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения задачи: {e}")
            QMessageBox.critical(
                self,
                self.localization.get_text("app.error"),
                f"{self.localization.get_text('errors.save_failed')}: {str(e)}"
            )
