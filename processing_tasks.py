import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any
import multiprocessing
from dataclasses import dataclass, field

# Импортируем необходимые классы и dataclasses
# from main import TextExtractionResult, ChapterSplitResult, MetadataExtractor # Пример
# from chapter_splitter import ChapterSplitter
# from metadata_extractor import MetadataExtractor

# Предполагается, что эти классы и dataclasses будут доступны или импортированы

def process_chapters_parallel(text_result: Any, chapter_splitter: Any) -> Dict[str, str]:
    """Параллельная обработка глав."""
    try:
        # Разбиваем текст на главы
        chapters = chapter_splitter.split_text_into_chapters(text_result.text)

        if not chapters:
            print("Не удалось разбить текст на главы")
            return {}

        # Используем минимум между количеством глав и доступными ядрами
        max_workers = min(len(chapters), os.cpu_count() or 4)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_process_single_chapter, chapter_text, chapter_num): chapter_num
                for chapter_num, chapter_text in chapters.items()
            }

            results = {}
            for future in as_completed(futures):
                chapter_num = futures[future]
                try:
                    results[chapter_num] = future.result()
                except Exception as e:
                    print(f"Ошибка при обработке главы {chapter_num}: {str(e)}")

            return results
    except Exception as e:
        print(f"Ошибка при параллельной обработке глав: {str(e)}")
        return {}

def _process_single_chapter(chapter_text: str, chapter_num: int) -> str:
    """Обработка одной главы."""
    try:
        # Здесь можно добавить дополнительную обработку главы
        # Например, форматирование, анализ и т.д.
        return chapter_text
    except Exception as e:
        print(f"Ошибка при обработке главы {chapter_num}: {str(e)}")
        return ""

def process_metadata_parallel(metadata_extractor: Any) -> Dict[str, Any]:
    """Параллельная обработка метаданных."""
    try:
        metadata_tasks = [
            ('title', metadata_extractor.extract_title),
            ('author', metadata_extractor.extract_author),
            ('publisher', metadata_extractor.extract_publisher),
            ('date', metadata_extractor.extract_date),
            ('language', metadata_extractor.extract_language),
            ('description', metadata_extractor.extract_description)
        ]

        with ThreadPoolExecutor(max_workers=len(metadata_tasks)) as executor:
            futures = {
                executor.submit(task[1]): task[0]
                for task in metadata_tasks
            }

            results = {}
            for future in as_completed(futures):
                field = futures[future]
                try:
                    results[field] = future.result()
                except Exception as e:
                    print(f"Ошибка при извлечении {field}: {str(e)}")

            return results
    except Exception as e:
        print(f"Ошибка при параллельной обработке метаданных: {str(e)}")
        return {} 