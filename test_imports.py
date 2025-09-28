#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех импортов приложения
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_qt_imports():
    """Тестирование импортов Qt"""
    print("Тестирование импортов Qt...")
    try:
        from PySide6.QtCore import Qt, QTimer, Signal
        print("✓ PySide6.QtCore импортирован")
        
        from PySide6.QtGui import QAction, QKeySequence, QPixmap, QPainter, QBrush, QIcon
        print("✓ PySide6.QtGui импортирован")
        
        from PySide6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
            QSplitter, QMenuBar, QMenu, QStatusBar, QMessageBox, QLabel,
            QToolBar, QSystemTrayIcon
        )
        print("✓ PySide6.QtWidgets импортирован")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка импорта Qt: {e}")
        return False

def test_core_imports():
    """Тестирование импортов core модулей"""
    print("\nТестирование импортов core модулей...")
    try:
        from core.resource_manager import ResourceManager
        print("✓ ResourceManager импортирован")
        
        from core.settings import Settings
        print("✓ Settings импортирован")
        
        from core.localization import Localization
        print("✓ Localization импортирован")
        
        from core.database import Database
        print("✓ Database импортирован")
        
        from core.models import Task, TaskList, TaskOccurrence
        print("✓ Models импортированы")
        
        from core.notifications import NotificationManager, ReminderScheduler
        print("✓ Notifications импортированы")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка импорта core: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_imports():
    """Тестирование импортов UI модулей"""
    print("\nТестирование импортов UI модулей...")
    try:
        from ui.main_window import MainWindow
        print("✓ MainWindow импортирован")
        
        from ui.widgets.calendar_widget import CalendarWidget
        print("✓ CalendarWidget импортирован")
        
        from ui.widgets.task_list import TaskListWidget
        print("✓ TaskListWidget импортирован")
        
        from ui.widgets.toolbar import MainToolBar, StatusToolBar
        print("✓ Toolbar импортирован")
        
        from ui.dialogs.task_editor import TaskEditorDialog
        print("✓ TaskEditorDialog импортирован")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка импорта UI: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_external_imports():
    """Тестирование внешних зависимостей"""
    print("\nТестирование внешних зависимостей...")
    try:
        from dateutil import rrule, relativedelta
        print("✓ dateutil импортирован")
        
        import sqlite3
        print("✓ sqlite3 импортирован")
        
        import json
        print("✓ json импортирован")
        
        import logging
        print("✓ logging импортирован")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка импорта внешних зависимостей: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("=== Тестирование импортов Todo-Timed ===\n")
    
    all_passed = True
    
    # Тестируем все группы импортов
    all_passed &= test_qt_imports()
    all_passed &= test_external_imports()
    all_passed &= test_core_imports()
    all_passed &= test_ui_imports()
    
    print(f"\n=== Результат тестирования ===")
    if all_passed:
        print("✅ Все импорты прошли успешно!")
        return 0
    else:
        print("❌ Обнаружены ошибки импортов!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
