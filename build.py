#!/usr/bin/env python3
"""
Скрипт для сборки приложения Todo-Timed с помощью PyInstaller.

Этот скрипт автоматизирует процесс сборки, включая все необходимые ресурсы,
локализации и данные в единый исполняемый файл или директорию.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# --- Конфигурация сборки ---
APP_NAME = "Todo-Timed"
ENTRY_POINT = "app.py"
ICON_PATH = "resources/images/background.png"

# Директории и файлы для включения в сборку
ASSETS = [
    ("resources", "resources"),
    ("locales", "locales"),
    ("migrations", "migrations"),
]

# Скрытые импорты для PyInstaller
HIDDEN_IMPORTS = [
    "PySide6.QtCore",
    "PySide6.QtGui", 
    "PySide6.QtWidgets",
    "PySide6.QtGui.QAction",
    "dateutil.rrule",
    "dateutil.relativedelta",
    "sqlite3",
    "json",
    "logging",
    "pathlib"
]

# --- Функции для сборки ---

def get_project_root() -> Path:
    """Возвращает корневую директорию проекта."""
    return Path(__file__).parent.resolve()

def clear_previous_builds(root: Path):
    """Очищает директории от предыдущих сборок."""
    print("Очистка предыдущих сборок...")
    dist_dir = root / "dist"
    build_dir = root / "build"
    spec_file = root / f"{APP_NAME}.spec"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"Удалена директория: {dist_dir}")

    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"Удалена директория: {build_dir}")

    # Не удаляем spec файл, так как он настроен вручную
    print("Очистка завершена.")

def run_pyinstaller(root: Path):
    """Запускает PyInstaller с необходимыми параметрами."""
    print("Запуск PyInstaller...")
    
    # Используем готовый spec файл
    spec_file = root / f"{APP_NAME.lower()}.spec"
    
    if spec_file.exists():
        print(f"Используется конфигурация из {spec_file}")
        pyinstaller_cmd = [
            sys.executable,
            "-m", "PyInstaller",
            str(spec_file)
        ]
    else:
        print("Spec файл не найден, используется автоматическая конфигурация")
        pyinstaller_cmd = [
            sys.executable,
            "-m", "PyInstaller",
            "--name", APP_NAME,
            "--onefile",
            "--windowed",
            f"--icon={ICON_PATH}",
            "--clean",
            ENTRY_POINT,
        ]

        # Добавляем ресурсы
        for src, dest in ASSETS:
            pyinstaller_cmd.extend(["--add-data", f"{src}{os.pathsep}{dest}"])

        # Добавляем скрытые импорты
        for hidden_import in HIDDEN_IMPORTS:
            pyinstaller_cmd.extend(["--hidden-import", hidden_import])

    print(f"Команда для сборки: {' '.join(pyinstaller_cmd)}")

    try:
        # Запускаем процесс сборки
        result = subprocess.run(pyinstaller_cmd, check=True, cwd=root, 
                              capture_output=True, text=True)
        print("PyInstaller успешно завершил работу.")
        if result.stdout:
            print("Вывод PyInstaller:")
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Ошибка при выполнении PyInstaller:", file=sys.stderr)
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        sys.exit(1)

def main():
    """Главная функция скрипта сборки."""
    root = get_project_root()
    os.chdir(root)

    print(f"Начало сборки проекта '{APP_NAME}' в директории {root}")

    # 1. Очистка
    clear_previous_builds(root)

    # 2. Запуск PyInstaller
    run_pyinstaller(root)

    print("\nСборка успешно завершена!")
    print(f"Исполняемый файл находится в директории: {root / 'dist'}")
    
    # Показываем содержимое директории dist
    dist_dir = root / "dist"
    if dist_dir.exists():
        print("\nСодержимое директории dist:")
        for item in dist_dir.iterdir():
            print(f"  {item.name}")

if __name__ == "__main__":
    main()
