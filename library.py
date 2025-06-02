import os
import shutil
from typing import Optional

# Предполагается, что ProcessingResult и другие необходимые dataclasses будут импортированы или доступны.
# В данном случае, функция принимает необходимые аргументы напрямую.

def save_to_library(epub_path: str, library_dir: str, result: any) -> Optional[str]:
    """Сохраняет обработанную книгу в директорию библиотеки.

    Args:
        epub_path: Путь к исходному EPUB файлу.
        library_dir: Директория библиотеки для сохранения.
        result: Объект результатов обработки (для обновления поля library_save_path).

    Returns:
        Путь, куда была сохранена книга, или None в случае ошибки.
    """
    try:
        # Генерируем путь для сохранения в библиотеке
        book_name = os.path.basename(epub_path)
        library_path = os.path.join(library_dir, book_name)

        # Копируем файл
        shutil.copy2(epub_path, library_path)

        # Обновляем результат (предполагается, что result имеет атрибут library_save_path)
        if hasattr(result, 'library_save_path'):
            result.library_save_path = library_path

        print(f"Книга успешно добавлена в библиотеку: {library_path}")
        if hasattr(result, 'thread_statuses'):
             result.thread_statuses['add_to_my_library'] = "Успешно выполнено"

        return library_path
    except Exception as e:
        print(f"Ошибка при добавлении в библиотеку: {str(e)}")
        if hasattr(result, 'thread_statuses'):
             result.thread_statuses['add_to_my_library'] = f"Ошибка: {str(e)}"
        # Пока не re-raise исключение, чтобы не прерывать process_parallel
        # raise
        return None 