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

@dataclass
class ProcessingResult:
    metadata: EpubMetadata = None
    text_analysis: TextAnalysisResult = None
    image_extraction: ImageExtractionResult = None
    keyword_search: KeywordSearchResult = None
    text_formatting: FormattingResult = None
    toc: TocResult = None
    chapters: ChapterSplitResult = None
    execution_times: Dict[str, float] = None
    thread_statuses: Dict[str, str] = None

    def __post_init__(self):
        if self.execution_times is None:
            self.execution_times = {}
        if self.thread_statuses is None:
            self.thread_statuses = {}

class EpubProcessor:
    def __init__(self, epub_path: str, search_pattern: str = None):
        self.epub_path = epub_path
        self.search_pattern = search_pattern
        self.result = ProcessingResult()
        self.metadata_extractor = MetadataExtractor(epub_path)
        self.text_extractor = TextExtractor()
        self.text_analyzer = TextAnalyzer()
        self.image_extractor = ImageExtractor(epub_path, "extracted_images")
        self.keyword_searcher = KeywordSearcher(search_pattern)
        self.text_formatter = TextFormatter()
        self.toc_generator = TocGenerator(epub_path)
        self.chapter_splitter = ChapterSplitter()
        
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
            self.result.thread_statuses['analyze_text'] = f"Ошибка: {str(e)}"
            raise

    def extract_images(self) -> ImageExtractionResult:
        """Извлекает изображения из EPUB файла"""
        try:
            result = self.image_extractor.extract_images()
            self.result.image_extraction = result
            self.result.thread_statuses['extract_images'] = "Успешно выполнено"
            return result
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

    def process_parallel(self) -> ProcessingResult:
        """Параллельная обработка EPUB файла"""
        start_time = time.time()
        
        # Извлекаем текст и сразу анализируем его
        text_result = self.extract_text()
        self.analyze_text(text_result)
        
        # Запускаем остальные операции параллельно
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.extract_metadata): 'extract_metadata',
                executor.submit(self.extract_images): 'extract_images',
                executor.submit(self.search_keywords, text_result): 'search_keywords',
                executor.submit(self.format_text): 'format_text',
                executor.submit(self.generate_toc): 'generate_toc',
                executor.submit(self.split_chapters): 'split_chapters'
            }
            
            for future in as_completed(futures):
                operation = futures[future]
                try:
                    result = future.result()
                    self.result.execution_times[operation] = time.time() - start_time
                except Exception as e:
                    print(f"Ошибка при выполнении {operation}: {str(e)}")
        
        self.result.execution_times['total_time'] = time.time() - start_time
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
                "output_dir": self.result.image_extraction.output_dir
            } if self.result.image_extraction else None,
            "keyword_search": {
                "match_count": self.result.keyword_search.match_count,
                "matches": self.result.keyword_search.matches[:5]  # Ограничиваем до 5 совпадений
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
