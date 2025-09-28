"""
Система локализации с надежным fallback
Решает проблемы с отображением ключей вместо переводов
"""

import json
import logging
from typing import Dict, Any
from .resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class Localization:
    """Система локализации с fallback механизмом"""
    
    def __init__(self, language: str = 'ru'):
        self.current_language = language
        self.translations: Dict[str, Any] = {}
        self.fallback_translations: Dict[str, Any] = {}
        self.load_translations()
    
    def load_translations(self) -> None:
        """Загрузить переводы для текущего языка с fallback на английский"""
        try:
            # Загружаем английский как fallback
            self._load_language_file('en', is_fallback=True)
            
            # Загружаем текущий язык
            if self.current_language != 'en':
                self._load_language_file(self.current_language, is_fallback=False)
            else:
                self.translations = self.fallback_translations.copy()
                
            logger.info(f"Локализация загружена: {self.current_language}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки локализации: {e}")
            self._create_emergency_fallback()
    
    def _load_language_file(self, language: str, is_fallback: bool = False) -> None:
        """Загрузить файл перевода для указанного языка"""
        file_path = f"locales/{language}.json"
        resource_path = ResourceManager.get_resource_path(file_path)
        
        if resource_path and resource_path.exists():
            try:
                with open(resource_path, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                
                if is_fallback:
                    self.fallback_translations = translations
                else:
                    self.translations = translations
                    
                logger.debug(f"Загружен файл локализации: {resource_path}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON в {resource_path}: {e}")
                if not is_fallback:
                    self._create_emergency_fallback()
            except Exception as e:
                logger.error(f"Ошибка чтения файла {resource_path}: {e}")
                if not is_fallback:
                    self._create_emergency_fallback()
        else:
            logger.warning(f"Файл локализации не найден: {file_path}")
            if not is_fallback:
                self._create_emergency_fallback()
    
    def _create_emergency_fallback(self) -> None:
        """Создать аварийный fallback с базовыми переводами"""
        logger.warning("Создание аварийного fallback для локализации")
        
        emergency_translations = {
            "app": {
                "title": "Todo-Timed",
                "loading": "Loading...",
                "error": "Error"
            },
            "menu": {
                "file": "File",
                "edit": "Edit",
                "view": "View",
                "help": "Help",
                "exit": "Exit"
            },
            "toolbar": {
                "add": "Add",
                "edit": "Edit", 
                "delete": "Delete",
                "done": "Done",
                "today": "Today",
                "settings": "Settings"
            },
            "dialogs": {
                "ok": "OK",
                "cancel": "Cancel",
                "save": "Save",
                "close": "Close"
            },
            "tray": {
                "show": "Show",
                "hide": "Hide",
                "quick_add": "Quick Add",
                "exit": "Exit"
            }
        }
        
        if not self.translations:
            self.translations = emergency_translations
        if not self.fallback_translations:
            self.fallback_translations = emergency_translations
    
    def get_text(self, key: str) -> str:
        """
        Получить перевод по ключу с fallback
        
        Args:
            key: Ключ перевода в формате "section.subsection.key"
            
        Returns:
            Переведенный текст или ключ если перевод не найден
        """
        try:
            # Разбиваем ключ на части
            keys = key.split('.')
            
            # Ищем в основных переводах
            result = self._get_nested_value(self.translations, keys)
            if result is not None:
                return str(result)
            
            # Ищем в fallback переводах
            result = self._get_nested_value(self.fallback_translations, keys)
            if result is not None:
                logger.debug(f"Использован fallback для ключа: {key}")
                return str(result)
            
            # Если ничего не найдено, возвращаем ключ
            logger.warning(f"Перевод не найден для ключа: {key}")
            return key
            
        except Exception as e:
            logger.error(f"Ошибка получения перевода для ключа {key}: {e}")
            return key
    
    def _get_nested_value(self, data: Dict[str, Any], keys: list[str]) -> Any:
        """Получить значение из вложенного словаря по списку ключей"""
        try:
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current
        except Exception:
            return None
    
    def set_language(self, language: str) -> None:
        """Изменить язык интерфейса"""
        if language != self.current_language:
            self.current_language = language
            self.load_translations()
            logger.info(f"Язык изменен на: {language}")
    
    def get_available_languages(self) -> list[str]:
        """Получить список доступных языков"""
        try:
            locales_dir = ResourceManager.get_resource_path("locales")
            if locales_dir and locales_dir.is_dir():
                languages = []
                for file_path in locales_dir.glob("*.json"):
                    language = file_path.stem
                    languages.append(language)
                return sorted(languages)
        except Exception as e:
            logger.error(f"Ошибка получения списка языков: {e}")
        
        return ['en', 'ru']  # Минимальный набор
    
    def validate_translations(self) -> Dict[str, list[str]]:
        """Валидация переводов - поиск отсутствующих ключей"""
        issues = {
            'missing_keys': [],
            'empty_values': [],
            'type_mismatches': []
        }
        
        try:
            # Сравниваем с fallback переводами
            self._validate_nested_dict(
                self.fallback_translations, 
                self.translations, 
                '', 
                issues
            )
        except Exception as e:
            logger.error(f"Ошибка валидации переводов: {e}")
        
        return issues
    
    def _validate_nested_dict(self, reference: Dict[str, Any], 
                             target: Dict[str, Any], 
                             prefix: str, 
                             issues: Dict[str, list[str]]) -> None:
        """Рекурсивная валидация вложенных словарей"""
        for key, value in reference.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if key not in target:
                issues['missing_keys'].append(full_key)
            elif isinstance(value, dict):
                if isinstance(target[key], dict):
                    self._validate_nested_dict(value, target[key], full_key, issues)
                else:
                    issues['type_mismatches'].append(full_key)
            elif not target[key]:
                issues['empty_values'].append(full_key)
