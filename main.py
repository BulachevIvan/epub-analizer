# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import os
import sys
import json
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import re
import shutil
import time
import asyncio
import aiofiles
import io
import multiprocessing
from multiprocessing import Manager

from metadata_extractor import MetadataExtractor, EpubMetadata
from text_extractor import TextExtractor, TextExtractionResult
from text_analyzer import TextAnalyzer, TextAnalysisResult
from image_extractor import ImageExtractor, ImageExtractionResult
from keyword_searcher import KeywordSearcher, KeywordSearchResult
from toc_generator import TocGenerator, TocResult
from text_formatter import TextFormatter, FormattingResult
from chapter_splitter import ChapterSplitter, ChapterSplitResult
from style_processor import StyleProcessor, StyleProcessingResult
from image_transformer import apply_pixelate, apply_contrast, apply_mirror, apply_grayscale

@dataclass
class ProcessingResult:
    metadata: EpubMetadata = None
    text_analysis: TextAnalysisResult = None
    image_extraction: ImageExtractionResult = None
    keyword_search: KeywordSearchResult = None
    text_formatting: FormattingResult = None
    toc: TocResult = None
    chapters: ChapterSplitResult = None
    style_processing: StyleProcessingResult = None
    library_save_path: Optional[str] = None
    execution_times: Dict[str, float] = None
    thread_statuses: Dict[str, str] = None

    def __post_init__(self):
        if self.execution_times is None:
            self.execution_times = {}
        if self.thread_statuses is None:
            self.thread_statuses = {}

@dataclass
class TextExtractionResult:
    text: str = ""
    html_content: Dict[str, str] = field(default_factory=dict)

@dataclass
class TextAnalysisResult:
    word_count: int = 0
    char_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    search_word_frequency: int = 0

@dataclass
class ImageExtractionResult:
    count: int = 0
    output_dir: str = ""
    extracted_image_paths: List[str] = field(default_factory=list)
    pixelated_image_paths: Dict[str, str] = field(default_factory=dict)
    contrasted_image_paths: Dict[str, str] = field(default_factory=dict)
    mirrored_image_paths: Dict[str, str] = field(default_factory=dict)
    grayscale_image_paths: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.extracted_image_paths is None:
            self.extracted_image_paths = []
        if self.pixelated_image_paths is None:
            self.pixelated_image_paths = {}
        if self.contrasted_image_paths is None:
            self.contrasted_image_paths = {}
        if self.mirrored_image_paths is None:
            self.mirrored_image_paths = {}
        if self.grayscale_image_paths is None:
            self.grayscale_image_paths = {}

@dataclass
class KeywordSearchResult:
    match_count: int = 0
    matches: List[str] = field(default_factory=list)

@dataclass
class TocResult:
    toc_text: str = ""
    toc_html: str = ""

@dataclass
class FormattingResult:
    formatted_text: str = ""
    formatted_headers_count: int = 0
    bold_headers: Dict[str, str] = field(default_factory=dict)
    uppercase_headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class ChapterSplitResult:
    total_chapters: int = 0
    output_zip: str = ""
    chapter_files: List[str] = field(default_factory=list)

@dataclass
class StyleProcessingResult:
    processed_styles: Dict[str, str] = None
    total_styles: int = 0
    optimized_size: int = 0
    original_size: int = 0

    def __post_init__(self):
        if self.processed_styles is None:
            self.processed_styles = {}

class EpubProcessor:
    def __init__(self, epub_path: str, search_pattern: str = None, library_dir: str = "./library"):
        self.epub_path = epub_path
        self.search_pattern = search_pattern
        self.library_dir = library_dir
        self.result = ProcessingResult()
        self.metadata_extractor = MetadataExtractor(epub_path)
        self.text_extractor = TextExtractor()
        self.text_analyzer = TextAnalyzer()
        self.image_extractor = ImageExtractor(epub_path, "extracted_images")
        self.keyword_searcher = KeywordSearcher(search_pattern)
        self.text_formatter = TextFormatter()
        self.toc_generator = TocGenerator(epub_path)
        self.chapter_splitter = ChapterSplitter()
        self.style_processor = StyleProcessor(epub_path)
        
        os.makedirs(self.library_dir, exist_ok=True)

    def extract_metadata(self) -> EpubMetadata:
        """Извлекает метаданные из EPUB файла"""
        try:
            result = self.metadata_extractor.extract_metadata()
            self.result.metadata = result
            self.result.thread_statuses['extract_metadata'] = "Успешно выполнено"
            return result
        except Exception as e:
            self.result.thread_statuses['extract_metadata'] = f"Ошибка: {str(e)}"
            raise

    def extract_text(self) -> TextExtractionResult:
        """Извлекает текст из EPUB файла"""
        try:
            result = self.text_extractor.extract_text(self.epub_path)
            self.result.thread_statuses['extract_text'] = "Текст успешно извлечен"
            return result
        except Exception as e:
            self.result.thread_statuses['extract_text'] = f"Ошибка: {str(e)}"
            raise

    def analyze_text(self, text_result: TextExtractionResult) -> TextAnalysisResult:
        """Анализирует извлеченный текст"""
        try:
            result = self.text_analyzer.analyze_text(text_result.text, self.search_pattern)
            self.result.text_analysis = result
            self.result.thread_statuses['analyze_text'] = "Успешно выполнено"
            return result
        except Exception as e:
            self.result.thread_statuses['analyze_analysis'] = f"Ошибка: {str(e)}"
            raise

    def extract_images(self) -> ImageExtractionResult:
        """Извлекает изображения из EPUB файла и применяет преобразования."""
        try:
            # Сначала извлекаем оригинальные изображения
            extraction_result = self.image_extractor.extract_images()
            self.result.image_extraction = extraction_result

            # Применяем преобразования параллельно
            transformed_image_paths = {
                'pixelated': {}, 'contrasted': {}, 'mirrored': {}, 'grayscale': {}
            }
            
            if extraction_result.extracted_image_paths:
                with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
                    futures = []
                    for original_path in extraction_result.extracted_image_paths:
                        # Генерируем пути для сохранения трансформированных изображений
                        base_name = os.path.basename(original_path)
                        pixelated_path = os.path.join(self.image_extractor.output_dir, f"pixelated_{base_name}")
                        contrasted_path = os.path.join(self.image_extractor.output_dir, f"contrasted_{base_name}")
                        mirrored_path = os.path.join(self.image_extractor.output_dir, f"mirrored_{base_name}")
                        grayscale_path = os.path.join(self.image_extractor.output_dir, f"grayscale_{base_name}")
                        
                        # Добавляем задачи в пул потоков
                        futures.append(executor.submit(apply_pixelate, original_path, pixelated_path))
                        futures.append(executor.submit(apply_contrast, original_path, contrasted_path))
                        futures.append(executor.submit(apply_mirror, original_path, mirrored_path))
                        futures.append(executor.submit(apply_grayscale, original_path, grayscale_path))
                        
                        # Сохраняем связь между оригиналом и результатом в словарях
                        transformed_image_paths['pixelated'][original_path] = pixelated_path
                        transformed_image_paths['contrasted'][original_path] = contrasted_path
                        transformed_image_paths['mirrored'][original_path] = mirrored_path
                        transformed_image_paths['grayscale'][original_path] = grayscale_path
                        
                    # Ожидаем завершения всех задач (опционально, можно обрабатывать результаты по мере готовности)
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            print(f"Ошибка при параллельном преобразовании изображения: {str(e)}")

            # Обновляем результат извлечения с путями к трансформированным изображениям
            extraction_result.pixelated_image_paths = transformed_image_paths['pixelated']
            extraction_result.contrasted_image_paths = transformed_image_paths['contrasted']
            extraction_result.mirrored_image_paths = transformed_image_paths['mirrored']
            extraction_result.grayscale_image_paths = transformed_image_paths['grayscale']

            self.result.image_extraction = extraction_result
            self.result.thread_statuses['extract_images'] = "Изображения успешно извлечены и преобразованы"
            return extraction_result
        except Exception as e:
            self.result.thread_statuses['extract_images'] = f"Ошибка: {str(e)}"
            raise

    def search_keywords(self, text_result: TextExtractionResult) -> KeywordSearchResult:
        """Ищет ключевые слова в тексте"""
        try:
            result = self.keyword_searcher.search_keywords(text_result.text)
            self.result.keyword_search = result
            self.result.thread_statuses['search_keywords'] = "Успешно выполнено"
            return result
        except Exception as e:
            self.result.thread_statuses['search_keywords'] = f"Ошибка: {str(e)}"
            raise

    def format_text(self) -> FormattingResult:
        """Форматирует текст"""
        try:
            result = self.text_formatter.format_text(self.epub_path)
            self.result.text_formatting = result
            self.result.thread_statuses['format_text'] = "Успешно выполнено"
            return result
        except Exception as e:
            self.result.thread_statuses['format_text'] = f"Ошибка: {str(e)}"
            raise

    def generate_toc(self) -> TocResult:
        """Генерирует оглавление"""
        try:
            result = self.toc_generator.generate_toc()
            self.result.toc = result
            self.result.thread_statuses['generate_toc'] = "Успешно выполнено"
            return result
        except Exception as e:
            self.result.thread_statuses['generate_toc'] = f"Ошибка: {str(e)}"
            raise

    def split_chapters(self) -> ChapterSplitResult:
        """Разделяет книгу на главы"""
        try:
            result = self.chapter_splitter.split_chapters(self.epub_path)
            self.result.chapters = result
            self.result.thread_statuses['split_chapters'] = "Успешно выполнено"
            return result
        except Exception as e:
            self.result.thread_statuses['split_chapters'] = f"Ошибка: {str(e)}"
            raise

    def process_styles(self) -> StyleProcessingResult:
        """Обрабатывает стили EPUB файла"""
        try:
            result = self.style_processor.process_styles()
            self.result.style_processing = result
            self.result.thread_statuses['process_styles'] = "Успешно выполнено"
            return result
        except Exception as e:
            self.result.thread_statuses['process_styles'] = f"Ошибка: {str(e)}"
            raise

    def process_chapters_parallel(self, text_result: TextExtractionResult) -> Dict[str, str]:
        """Параллельная обработка глав"""
        try:
            # Разбиваем текст на главы
            chapters = self.chapter_splitter.split_text_into_chapters(text_result.text)
            
            if not chapters:
                print("Не удалось разбить текст на главы")
                return {}
            
            # Используем минимум между количеством глав и доступными ядрами
            max_workers = min(len(chapters), os.cpu_count() or 4)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._process_single_chapter, chapter_text, chapter_num): chapter_num
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

    def _process_single_chapter(self, chapter_text: str, chapter_num: int) -> str:
        """Обработка одной главы"""
        try:
            # Здесь можно добавить дополнительную обработку главы
            # Например, форматирование, анализ и т.д.
            return chapter_text
        except Exception as e:
            print(f"Ошибка при обработке главы {chapter_num}: {str(e)}")
            return ""

    def process_metadata_parallel(self) -> Dict[str, any]:
        """Параллельная обработка метаданных"""
        try:
            metadata_tasks = [
                ('title', self.metadata_extractor.extract_title),
                ('author', self.metadata_extractor.extract_author),
                ('publisher', self.metadata_extractor.extract_publisher),
                ('date', self.metadata_extractor.extract_date),
                ('language', self.metadata_extractor.extract_language),
                ('description', self.metadata_extractor.extract_description)
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

    def add_to_my_library(self) -> str:
        """Сохраняет обработанную книгу в директорию библиотеки."""
        try:
            # Генерируем путь для сохранения в библиотеке
            book_name = os.path.basename(self.epub_path)
            library_path = os.path.join(self.library_dir, book_name)
            
            # Копируем файл
            shutil.copy2(self.epub_path, library_path)
            
            self.result.library_save_path = library_path
            self.result.thread_statuses['add_to_my_library'] = "Книга успешно добавлена в библиотеку"
            return library_path
        except Exception as e:
            self.result.thread_statuses['add_to_my_library'] = f"Ошибка при добавлении в библиотеку: {str(e)}"
            raise

    def process_parallel(self) -> ProcessingResult:
        """Параллельная обработка EPUB файла"""
        start_time = time.time()
        operation_times = {}
        
        # Извлекаем текст и сразу анализируем его
        text_start = time.time()
        text_result = self.extract_text()
        self.analyze_text(text_result)
        operation_times['extract_text'] = time.time() - text_start
        
        # Запускаем все операции параллельно
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}
            
            # Базовые операции
            base_operations = [
                (self.extract_metadata, 'extract_metadata'),
                (self.extract_images, 'extract_images'),
                (lambda: self.search_keywords(text_result), 'search_keywords'),
                (self.format_text, 'format_text'),
                (self.generate_toc, 'generate_toc'),
                (self.split_chapters, 'split_chapters'),
                (self.process_styles, 'process_styles'),
                (self.add_to_my_library, 'add_to_my_library')
            ]
            
            # Запускаем все операции
            for operation, name in base_operations:
                op_start = time.time()
                future = executor.submit(operation)
                futures[future] = (name, op_start)
            
            for future in as_completed(futures):
                operation_name, op_start = futures[future]
                try:
                    future.result()
                    # Правильно измеряем время выполнения каждой операции после её завершения
                    operation_times[operation_name] = time.time() - op_start
                except Exception as e:
                    print(f"Ошибка при выполнении {operation_name}: {str(e)}")
                    # Если произошла ошибка, можно установить время выполнения в 0 или другое значение
                    operation_times[operation_name] = 0.0 # Или другое значение по умолчанию при ошибке

        # Сохраняем времена выполнения отдельных операций
        self.result.execution_times = operation_times
        
        # Общее время - сумма времен выполнения всех операций
        self.result.execution_times['total_time'] = sum(operation_times.values())
        
        # Также сохраним общее время выполнения самого метода process_parallel (Wall time)
        self.result.execution_times['process_parallel_wall_time'] = time.time() - start_time

        return self.result

    def save_results(self, output_file: str = "output_report.json"):
        """Сохраняет результаты обработки в JSON файл"""
        result_dict = {
            "execution_times": self.result.execution_times,
            "metadata": asdict(self.result.metadata) if self.result.metadata else None,
            "text_analysis": {
                "word_count": self.result.text_analysis.word_count,
                "char_count": self.result.text_analysis.char_count,
                "sentence_count": self.result.text_analysis.sentence_count,
                "paragraph_count": self.result.text_analysis.paragraph_count,
                "search_word_frequency": {self.search_pattern: self.result.text_analysis.search_word_frequency}
            } if self.result.text_analysis else None,
            "image_extraction": {
                "count": self.result.image_extraction.count,
                "output_dir": self.result.image_extraction.output_dir,
                "extracted_image_paths": self.result.image_extraction.extracted_image_paths,
                "pixelated_image_paths": self.result.image_extraction.pixelated_image_paths,
                "contrasted_image_paths": self.result.image_extraction.contrasted_image_paths,
                "mirrored_image_paths": self.result.image_extraction.mirrored_image_paths,
                "grayscale_image_paths": self.result.image_extraction.grayscale_image_paths
            } if self.result.image_extraction else None,
            "keyword_search": {
                "match_count": self.result.keyword_search.match_count,
                "matches": self.result.keyword_search.matches[:5]
            } if self.result.keyword_search else None,
            "text_formatting": {
                "formatted_headers_count": self.result.text_formatting.formatted_headers_count,
                "bold_headers": list(self.result.text_formatting.bold_headers.keys()),
                "uppercase_headers": list(self.result.text_formatting.uppercase_headers.keys())
            } if self.result.text_formatting else None,
            "chapters": {
                "total_chapters": self.result.chapters.total_chapters,
                "output_zip": self.result.chapters.output_zip
            } if self.result.chapters else None,
            "style_processing": {
                "total_styles": self.result.style_processing.total_styles,
                "original_size": self.result.style_processing.original_size,
                "optimized_size": self.result.style_processing.optimized_size,
                "compression_ratio": round((1 - self.result.style_processing.optimized_size / self.result.style_processing.original_size) * 100, 2) if self.result.style_processing.original_size > 0 else 0,
                "processed_files": list(self.result.style_processing.processed_styles.keys())
            } if self.result.style_processing else None,
            "library_save_path": self.result.library_save_path,
            "thread_statuses": self.result.thread_statuses
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)

def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py <путь_к_epub> [слово_для_поиска]")
        sys.exit(1)
        
    # Путь к EPUB файлу
    epub_path = sys.argv[1]
    
    # Слово для поиска (если указано)
    search_pattern = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Создаем процессор и запускаем обработку
    processor = EpubProcessor(epub_path, search_pattern)
    result = processor.process_parallel()
    
    # Сохраняем результаты
    processor.save_results()

if __name__ == "__main__":
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
