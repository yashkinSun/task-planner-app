"""
Менеджер ресурсов - централизованное управление путями к файлам
Решает проблемы с путями в dev/production окружениях
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


class ResourceManager:
    """Централизованное управление ресурсами приложения"""
    
    _app_dir: Optional[Path] = None
    _is_frozen: Optional[bool] = None
    
    @classmethod
    def get_app_dir(cls) -> Path:
        """Получить корневую директорию приложения"""
        if cls._app_dir is None:
            if cls.is_frozen():
                # Собранное приложение
                cls._app_dir = Path(sys.executable).parent
            else:
                # Режим разработки
                cls._app_dir = Path(__file__).parent.parent
        return cls._app_dir
    
    @classmethod
    def is_frozen(cls) -> bool:
        """Проверить, запущено ли приложение как собранный exe"""
        if cls._is_frozen is None:
            cls._is_frozen = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        return cls._is_frozen
    
    @classmethod
    def get_resource_path(cls, relative_path: Union[str, Path]) -> Optional[Path]:
        """
        Получить абсолютный путь к ресурсу с fallback
        
        Args:
            relative_path: Относительный путь к ресурсу
            
        Returns:
            Абсолютный путь к ресурсу или None если не найден
        """
        relative_path = Path(relative_path)
        
        # Список возможных расположений ресурса
        search_paths = [
            cls.get_app_dir() / relative_path,
        ]
        
        # Для собранного приложения добавляем дополнительные пути
        if cls.is_frozen():
            search_paths.extend([
                Path(sys._MEIPASS) / relative_path,
                Path(sys.executable).parent / relative_path,
            ])
        
        # Ищем ресурс в возможных расположениях
        for path in search_paths:
            if path.exists():
                logger.debug(f"Ресурс найден: {path}")
                return path
        
        logger.warning(f"Ресурс не найден: {relative_path}")
        logger.debug(f"Искали в: {[str(p) for p in search_paths]}")
        return None
    
    @classmethod
    def get_app_data_dir(cls) -> Path:
        """Получить директорию для данных приложения в %APPDATA%"""
        if sys.platform == "win32":
            import os
            appdata = Path(os.environ.get('APPDATA', ''))
            app_data_dir = appdata / "TodoTimed"
        else:
            # Для других ОС (для тестирования)
            app_data_dir = Path.home() / ".todotimed"
        
        app_data_dir.mkdir(parents=True, exist_ok=True)
        return app_data_dir
    
    @classmethod
    def ensure_resource_exists(cls, relative_path: Union[str, Path], 
                              fallback_content: Optional[str] = None) -> Path:
        """
        Убедиться что ресурс существует, создать fallback если нужно
        
        Args:
            relative_path: Относительный путь к ресурсу
            fallback_content: Содержимое для создания fallback файла
            
        Returns:
            Путь к ресурсу (существующему или созданному)
        """
        resource_path = cls.get_resource_path(relative_path)
        
        if resource_path and resource_path.exists():
            return resource_path
        
        # Создаем fallback в app_data если ресурс не найден
        if fallback_content is not None:
            fallback_path = cls.get_app_data_dir() / relative_path
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not fallback_path.exists():
                fallback_path.write_text(fallback_content, encoding='utf-8')
                logger.info(f"Создан fallback ресурс: {fallback_path}")
            
            return fallback_path
        
        # Возвращаем путь даже если файл не существует
        return cls.get_app_dir() / relative_path
    
    @classmethod
    def list_resources(cls, directory: Union[str, Path]) -> list[Path]:
        """Получить список всех ресурсов в директории"""
        dir_path = cls.get_resource_path(directory)
        if dir_path and dir_path.is_dir():
            return list(dir_path.rglob('*'))
        return []
