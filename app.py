#!/usr/bin/env python3
"""
Todo-Timed - Планировщик задач с календарем и напоминаниями
Главный файл приложения
"""

import sys
import logging
import traceback
from pathlib import Path

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QIcon

from core.resource_manager import ResourceManager
from core.settings import Settings
from core.localization import Localization
from core.database import Database
from core.notifications import NotificationManager, ReminderScheduler
from ui.main_window import MainWindow

# Настройка логирования
def setup_logging():
    """Настройка системы логирования"""
    try:
        log_dir = ResourceManager.get_app_data_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
    except:
        log_file = "todo-timed.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)


class TodoTimedApplication:
    """Основной класс приложения"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.database = None
        self.settings = None
        self.localization = None
        self.notification_manager = None
        self.reminder_scheduler = None
        self.splash = None
        
    def initialize(self):
        """Инициализация приложения"""
        try:
            logger.info("Запуск Todo-Timed...")
            
            # Создаем QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Todo-Timed")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("Todo-Timed")
            
            # Показываем заставку
            self.show_splash()
            
            # Инициализируем компоненты
            self.init_settings()
            self.init_localization()
            self.init_database()
            self.init_notifications()
            self.init_main_window()
            
            # Подключаем сигналы
            self.connect_signals()
            
            # Скрываем заставку
            self.hide_splash()
            
            logger.info("Todo-Timed успешно инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации приложения: {e}")
            logger.error(traceback.format_exc())
            self.show_error("Ошибка инициализации", str(e))
            return False
    
    def show_splash(self):
        """Показать заставку"""
        try:
            # Пытаемся загрузить фоновое изображение для заставки
            bg_path = ResourceManager.get_resource_path("resources/images/background.png")
            if bg_path and bg_path.exists():
                pixmap = QPixmap(str(bg_path)).scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio)
            else:
                # Создаем простую заставку
                pixmap = QPixmap(400, 300)
                pixmap.fill(Qt.GlobalColor.white)
            
            self.splash = QSplashScreen(pixmap)
            self.splash.show()
            self.splash.showMessage("Загрузка Todo-Timed...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
            
            # Обрабатываем события для отображения заставки
            self.app.processEvents()
            
        except Exception as e:
            logger.warning(f"Не удалось показать заставку: {e}")
    
    def hide_splash(self):
        """Скрыть заставку"""
        try:
            if self.splash:
                self.splash.finish(self.main_window)
                self.splash = None
        except Exception as e:
            logger.warning(f"Ошибка скрытия заставки: {e}")
    
    def init_settings(self):
        """Инициализация настроек"""
        try:
            if self.splash:
                self.splash.showMessage("Загрузка настроек...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
                self.app.processEvents()
            
            self.settings = Settings()
            logger.debug("Настройки инициализированы")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации настроек: {e}")
            raise
    
    def init_localization(self):
        """Инициализация локализации"""
        try:
            if self.splash:
                self.splash.showMessage("Загрузка локализации...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
                self.app.processEvents()
            
            language = self.settings.get('language', 'ru')
            self.localization = Localization(language)
            logger.debug(f"Локализация инициализирована: {language}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации локализации: {e}")
            raise
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            if self.splash:
                self.splash.showMessage("Инициализация базы данных...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
                self.app.processEvents()
            
            self.database = Database()
            logger.debug("База данных инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def init_notifications(self):
        """Инициализация системы уведомлений"""
        try:
            if self.splash:
                self.splash.showMessage("Настройка уведомлений...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
                self.app.processEvents()
            
            self.notification_manager = NotificationManager(self.localization, self.settings)
            self.reminder_scheduler = ReminderScheduler(self.notification_manager)
            
            logger.debug("Система уведомлений инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации уведомлений: {e}")
            # Не критично, продолжаем без уведомлений
            logger.warning("Приложение будет работать без уведомлений")
    
    def init_main_window(self):
        """Инициализация главного окна"""
        try:
            if self.splash:
                self.splash.showMessage("Создание интерфейса...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
                self.app.processEvents()
            
            self.main_window = MainWindow(
                self.database,
                self.localization,
                self.settings
            )
            
            # Устанавливаем иконку приложения
            self.set_application_icon()
            
            logger.debug("Главное окно инициализировано")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации главного окна: {e}")
            raise
    
    def set_application_icon(self):
        """Установить иконку приложения"""
        try:
            # Пытаемся использовать фоновое изображение как иконку
            bg_path = ResourceManager.get_resource_path("resources/images/background.png")
            if bg_path and bg_path.exists():
                icon = QIcon(str(bg_path))
                self.app.setWindowIcon(icon)
                if self.main_window:
                    self.main_window.setWindowIcon(icon)
                    
        except Exception as e:
            logger.warning(f"Не удалось установить иконку приложения: {e}")
    
    def connect_signals(self):
        """Подключение сигналов между компонентами"""
        try:
            # Подключаем сигналы уведомлений к главному окну
            if self.notification_manager and self.main_window:
                self.notification_manager.notification_clicked.connect(self.on_notification_clicked)
                self.notification_manager.task_action_requested.connect(self.on_task_action_requested)
            
            # Подключаем сигнал закрытия главного окна
            if self.main_window:
                self.main_window.closing.connect(self.on_main_window_closing)
            
            logger.debug("Сигналы подключены")
            
        except Exception as e:
            logger.error(f"Ошибка подключения сигналов: {e}")
    
    def on_notification_clicked(self, notification_id: str):
        """Обработка клика по уведомлению"""
        try:
            if notification_id == "show_main_window":
                self.show_main_window()
                
        except Exception as e:
            logger.error(f"Ошибка обработки клика по уведомлению: {e}")
    
    def on_task_action_requested(self, task_id: int, action: str):
        """Обработка запроса действия с задачей"""
        try:
            if action == "add_task":
                self.show_main_window()
                # TODO: Открыть диалог добавления задачи
                
        except Exception as e:
            logger.error(f"Ошибка обработки действия с задачей: {e}")
    
    def on_main_window_closing(self):
        """Обработка закрытия главного окна"""
        try:
            # Останавливаем сервис уведомлений
            if self.notification_manager:
                self.notification_manager.stop_notification_service()
            
            # Отменяем все напоминания
            if self.reminder_scheduler:
                self.reminder_scheduler.cancel_all_reminders()
            
            logger.info("Приложение завершает работу")
            
        except Exception as e:
            logger.error(f"Ошибка при закрытии приложения: {e}")
    
    def show_main_window(self):
        """Показать главное окно"""
        try:
            if self.main_window:
                self.main_window.show()
                self.main_window.raise_()
                self.main_window.activateWindow()
                
        except Exception as e:
            logger.error(f"Ошибка показа главного окна: {e}")
    
    def show_error(self, title: str, message: str):
        """Показать сообщение об ошибке"""
        try:
            if self.app:
                QMessageBox.critical(None, title, message)
            else:
                print(f"ОШИБКА: {title} - {message}")
                
        except Exception as e:
            print(f"Критическая ошибка: {e}")
    
    def run(self):
        """Запуск приложения"""
        try:
            if not self.initialize():
                return 1
            
            # Показываем главное окно
            if not self.settings.get('start_minimized', False):
                self.show_main_window()
            
            # Запускаем главный цикл приложения
            return self.app.exec()
            
        except Exception as e:
            logger.error(f"Критическая ошибка выполнения: {e}")
            logger.error(traceback.format_exc())
            self.show_error("Критическая ошибка", str(e))
            return 1
        finally:
            # Очистка ресурсов
            self.cleanup()
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            if self.notification_manager:
                self.notification_manager.stop_notification_service()
            
            if self.reminder_scheduler:
                self.reminder_scheduler.cancel_all_reminders()
            
            if self.database:
                self.database.close()
            
            logger.info("Ресурсы очищены")
            
        except Exception as e:
            logger.error(f"Ошибка очистки ресурсов: {e}")


def main():
    """Точка входа в приложение"""
    try:
        # Настраиваем логирование
        setup_logging()
        
        # Создаем и запускаем приложение
        app = TodoTimedApplication()
        return app.run()
        
    except KeyboardInterrupt:
        logger.info("Приложение прервано пользователем")
        return 0
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
