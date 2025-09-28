"""
Система настроек приложения
Сохранение и загрузка пользовательских предпочтений
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from .resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class Settings:
    """Управление настройками приложения"""
    
    DEFAULT_SETTINGS = {
        'language': 'ru',
        'theme': 'system',  # system, light, dark
        'start_minimized': False,
        'minimize_to_tray': True,
        'autostart': False,
        'snooze_minutes': 10,
        'expansion_horizon_days': 90,
        'grace_minutes': 10,
        'window_geometry': None,
        'window_state': None,
    }
    
    def __init__(self):
        self.settings_file = ResourceManager.get_app_data_dir() / "settings.json"
        self._settings: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Загрузить настройки из файла"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Объединяем с настройками по умолчанию
                self._settings = {**self.DEFAULT_SETTINGS, **loaded_settings}
                logger.info(f"Настройки загружены из {self.settings_file}")
            else:
                self._settings = self.DEFAULT_SETTINGS.copy()
                logger.info("Используются настройки по умолчанию")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
            self._settings = self.DEFAULT_SETTINGS.copy()
    
    def save(self) -> None:
        """Сохранить настройки в файл"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Настройки сохранены в {self.settings_file}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение настройки"""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Установить значение настройки"""
        self._settings[key] = value
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Получить все настройки"""
        return self._settings.copy()
    
    def reset_to_defaults(self) -> None:
        """Сбросить настройки к значениям по умолчанию"""
        self._settings = self.DEFAULT_SETTINGS.copy()
        self.save()
        logger.info("Настройки сброшены к значениям по умолчанию")
    
    def setup_autostart(self, enabled: bool) -> bool:
        """
        Настроить автозапуск приложения
        
        Args:
            enabled: Включить или выключить автозапуск
            
        Returns:
            True если операция успешна
        """
        try:
            import sys
            import os
            from pathlib import Path
            
            if sys.platform != "win32":
                logger.warning("Автозапуск поддерживается только на Windows")
                return False
            
            # Путь к папке автозапуска
            startup_folder = Path(os.environ['APPDATA']) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            shortcut_path = startup_folder / "TodoTimed.lnk"
            
            if enabled:
                # Создаем ярлык для автозапуска
                try:
                    import win32com.client
                    
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortCut(str(shortcut_path))
                    shortcut.Targetpath = sys.executable
                    shortcut.Arguments = "--minimized"
                    shortcut.WorkingDirectory = str(Path(sys.executable).parent)
                    shortcut.save()
                    
                    logger.info("Автозапуск включен")
                    return True
                    
                except ImportError:
                    logger.error("Для автозапуска требуется pywin32")
                    return False
            else:
                # Удаляем ярлык автозапуска
                if shortcut_path.exists():
                    shortcut_path.unlink()
                    logger.info("Автозапуск выключен")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка настройки автозапуска: {e}")
            return False
