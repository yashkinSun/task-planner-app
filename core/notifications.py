"""
Система уведомлений и напоминаний
Кроссплатформенная реализация с fallback для Linux
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QSystemTrayIcon, QMessageBox

logger = logging.getLogger(__name__)


class NotificationManager(QObject):
    """Менеджер уведомлений с поддержкой системного трея"""
    
    # Сигналы
    notification_clicked = Signal(str)  # notification_id
    task_action_requested = Signal(int, str)  # task_id, action
    
    def __init__(self, localization, settings):
        super().__init__()
        self.localization = localization
        self.settings = settings
        self.tray_icon = None
        self.notification_service_running = False
        
        # Инициализируем системный трей
        self.init_system_tray()
        
    def init_system_tray(self):
        """Инициализация системного трея"""
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon()
                self.tray_icon.setToolTip("Todo-Timed")
                
                # Подключаем сигналы
                self.tray_icon.activated.connect(self.on_tray_activated)
                
                logger.debug("Системный трей инициализирован")
            else:
                logger.warning("Системный трей недоступен")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации системного трея: {e}")
    
    def show_notification(self, title: str, message: str, notification_type: str = "info", 
                         duration: int = 5000, task_id: Optional[int] = None):
        """Показать уведомление"""
        try:
            # Определяем иконку уведомления
            if notification_type == "warning":
                icon = QSystemTrayIcon.MessageIcon.Warning
            elif notification_type == "error":
                icon = QSystemTrayIcon.MessageIcon.Critical
            else:
                icon = QSystemTrayIcon.MessageIcon.Information
            
            # Показываем уведомление через системный трей
            if self.tray_icon and self.tray_icon.isVisible():
                self.tray_icon.showMessage(title, message, icon, duration)
                logger.debug(f"Уведомление показано: {title}")
            else:
                # Fallback - показываем через QMessageBox
                self.show_fallback_notification(title, message, notification_type)
                
        except Exception as e:
            logger.error(f"Ошибка показа уведомления: {e}")
            # Последний fallback
            print(f"УВЕДОМЛЕНИЕ: {title} - {message}")
    
    def show_fallback_notification(self, title: str, message: str, notification_type: str):
        """Fallback уведомление через QMessageBox"""
        try:
            if notification_type == "error":
                QMessageBox.critical(None, title, message)
            elif notification_type == "warning":
                QMessageBox.warning(None, title, message)
            else:
                QMessageBox.information(None, title, message)
                
        except Exception as e:
            logger.error(f"Ошибка fallback уведомления: {e}")
    
    def show_task_reminder(self, task_title: str, due_time: datetime, task_id: int):
        """Показать напоминание о задаче"""
        try:
            title = self.localization.get("notifications.reminder_title", "Task Reminder")
            due_str = due_time.strftime("%H:%M")
            message = f"{task_title}\n{self.localization.get('notifications.due_at', 'Due at:')} {due_str}"
            
            self.show_notification(title, message, "info", 10000, task_id)
            
        except Exception as e:
            logger.error(f"Ошибка показа напоминания: {e}")
    
    def show_overdue_notification(self, task_title: str, was_due: datetime, task_id: int):
        """Показать уведомление о просроченной задаче"""
        try:
            title = self.localization.get("notifications.overdue_title", "Overdue Task")
            due_str = was_due.strftime("%H:%M")
            message = f"{task_title}\n{self.localization.get('notifications.was_due_at', 'Was due at:')} {due_str}"
            
            self.show_notification(title, message, "warning", 15000, task_id)
            
        except Exception as e:
            logger.error(f"Ошибка показа уведомления о просрочке: {e}")
    
    def show_daily_summary(self, tasks_count: int, completed_count: int):
        """Показать ежедневную сводку"""
        try:
            title = self.localization.get("notifications.daily_summary_title", "Daily Summary")
            message = f"{self.localization.get('notifications.tasks_today', 'Tasks today')}: {tasks_count}\n"
            message += f"{self.localization.get('notifications.completed', 'Completed')}: {completed_count}"
            
            self.show_notification(title, message, "info", 8000)
            
        except Exception as e:
            logger.error(f"Ошибка показа ежедневной сводки: {e}")
    
    def on_tray_activated(self, reason):
        """Обработка активации системного трея"""
        try:
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                self.notification_clicked.emit("show_main_window")
                
        except Exception as e:
            logger.error(f"Ошибка обработки активации трея: {e}")
    
    def start_notification_service(self):
        """Запуск сервиса уведомлений"""
        try:
            if self.tray_icon:
                self.tray_icon.show()
            
            self.notification_service_running = True
            logger.debug("Сервис уведомлений запущен")
            
        except Exception as e:
            logger.error(f"Ошибка запуска сервиса уведомлений: {e}")
    
    def stop_notification_service(self):
        """Остановка сервиса уведомлений"""
        try:
            if self.tray_icon:
                self.tray_icon.hide()
            
            self.notification_service_running = False
            logger.debug("Сервис уведомлений остановлен")
            
        except Exception as e:
            logger.error(f"Ошибка остановки сервиса уведомлений: {e}")


class ReminderScheduler(QObject):
    """Планировщик напоминаний"""
    
    def __init__(self, notification_manager: NotificationManager):
        super().__init__()
        self.notification_manager = notification_manager
        self.active_reminders: Dict[int, QTimer] = {}
        self.reminder_lock = threading.Lock()
        
    def schedule_reminder(self, task_id: int, task_title: str, reminder_time: datetime):
        """Запланировать напоминание"""
        try:
            with self.reminder_lock:
                # Отменяем существующее напоминание для этой задачи
                self.cancel_reminder(task_id)
                
                # Вычисляем время до напоминания
                now = datetime.now()
                if reminder_time <= now:
                    logger.debug(f"Время напоминания уже прошло для задачи {task_id}")
                    return
                
                delay_ms = int((reminder_time - now).total_seconds() * 1000)
                
                # Создаем таймер
                timer = QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(lambda: self.trigger_reminder(task_id, task_title, reminder_time))
                timer.start(delay_ms)
                
                self.active_reminders[task_id] = timer
                
                logger.debug(f"Напоминание запланировано для задачи {task_id} на {reminder_time}")
                
        except Exception as e:
            logger.error(f"Ошибка планирования напоминания: {e}")
    
    def trigger_reminder(self, task_id: int, task_title: str, reminder_time: datetime):
        """Срабатывание напоминания"""
        try:
            with self.reminder_lock:
                # Удаляем таймер из активных
                if task_id in self.active_reminders:
                    del self.active_reminders[task_id]
            
            # Показываем напоминание
            self.notification_manager.show_task_reminder(task_title, reminder_time, task_id)
            
            logger.debug(f"Напоминание сработало для задачи {task_id}")
            
        except Exception as e:
            logger.error(f"Ошибка срабатывания напоминания: {e}")
    
    def cancel_reminder(self, task_id: int):
        """Отменить напоминание"""
        try:
            with self.reminder_lock:
                if task_id in self.active_reminders:
                    timer = self.active_reminders[task_id]
                    timer.stop()
                    del self.active_reminders[task_id]
                    logger.debug(f"Напоминание отменено для задачи {task_id}")
                    
        except Exception as e:
            logger.error(f"Ошибка отмены напоминания: {e}")
    
    def cancel_all_reminders(self):
        """Отменить все напоминания"""
        try:
            with self.reminder_lock:
                for timer in self.active_reminders.values():
                    timer.stop()
                self.active_reminders.clear()
                logger.debug("Все напоминания отменены")
                
        except Exception as e:
            logger.error(f"Ошибка отмены всех напоминаний: {e}")
    
    def get_active_reminders_count(self) -> int:
        """Получить количество активных напоминаний"""
        with self.reminder_lock:
            return len(self.active_reminders)
    
    def reschedule_reminders_for_task(self, task_id: int, task_title: str, new_due_time: datetime):
        """Перепланировать напоминания для задачи"""
        try:
            # Отменяем старое напоминание
            self.cancel_reminder(task_id)
            
            # Планируем новое напоминание за 15 минут до срока
            reminder_time = new_due_time - timedelta(minutes=15)
            if reminder_time > datetime.now():
                self.schedule_reminder(task_id, task_title, reminder_time)
                
        except Exception as e:
            logger.error(f"Ошибка перепланирования напоминаний: {e}")


class OverdueChecker(QObject):
    """Проверка просроченных задач"""
    
    def __init__(self, database, notification_manager: NotificationManager):
        super().__init__()
        self.database = database
        self.notification_manager = notification_manager
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_overdue_tasks)
        
    def start_checking(self, interval_minutes: int = 30):
        """Запустить проверку просроченных задач"""
        try:
            self.check_timer.start(interval_minutes * 60 * 1000)  # Конвертируем в миллисекунды
            logger.debug(f"Проверка просроченных задач запущена с интервалом {interval_minutes} минут")
            
        except Exception as e:
            logger.error(f"Ошибка запуска проверки просроченных задач: {e}")
    
    def stop_checking(self):
        """Остановить проверку просроченных задач"""
        try:
            self.check_timer.stop()
            logger.debug("Проверка просроченных задач остановлена")
            
        except Exception as e:
            logger.error(f"Ошибка остановки проверки просроченных задач: {e}")
    
    def check_overdue_tasks(self):
        """Проверить просроченные задачи"""
        try:
            now = datetime.now()
            overdue_tasks = self.database.get_overdue_tasks(now)
            
            for task in overdue_tasks:
                if task.due_datetime and not task.completed:
                    self.notification_manager.show_overdue_notification(
                        task.title, task.due_datetime, task.id
                    )
            
            if overdue_tasks:
                logger.debug(f"Найдено {len(overdue_tasks)} просроченных задач")
                
        except Exception as e:
            logger.error(f"Ошибка проверки просроченных задач: {e}")
