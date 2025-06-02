import os
import zipfile
from typing import Optional, Dict, List
from googletrans import Translator
from dataclasses import dataclass, field

# Импортируем необходимые dataclasses или их определения, если они не глобальны
# В данном случае, полагаемся на то, что TocResult и ProcessingResult определены в main

@dataclass
class TocResult:
    toc_text: str = ""
    toc_html: str = ""
    chapters: List[Dict[str, str]] = field(default_factory=list)
    total_chapters: int = 0

# Предполагается, что этот dataclass определен в main.py и доступен
# from main import ProcessingResult

def translate_first_chapter(
    epub_archive: zipfile.ZipFile,
    opf_dir: str,
    toc_result: TocResult,
    result: any # Объект результатов обработки (для обновленияtranslated_first_chapter)
) -> Optional[str]:
    """Переводит первую главу книги на английский, используя данные из TOC.

    Args:
        epub_archive: Открытый ZipFile объект EPUB архива.
        opf_dir: Директория OPF файла внутри архива.
        toc_result: Результат генерации оглавления (TocResult).
        result: Объект результатов обработки (для обновления поля translated_first_chapter).

    Returns:
        Переведенный текст первой главы или None в случае ошибки.
    """
    try:
        translator = Translator()

        # Находим путь к первой главе из TOC
        first_chapter_path = None
        if toc_result and toc_result.chapters:
            first_item = toc_result.chapters[0]
            first_chapter_path = first_item.get('src')
            if first_chapter_path and '#' in first_chapter_path:
                first_chapter_path = first_chapter_path.split('#')[0]

        if not first_chapter_path:
            print("Не удалось найти путь к первой главе из TOC.")
            if hasattr(result, 'translated_first_chapter'):
                 result.translated_first_chapter = "Не удалось найти путь к первой главе из TOC."
            return None

        # Формируем полный путь к файлу главы, добавляя директорию OPF
        full_chapter_path = opf_dir + first_chapter_path
        print(f"Попытка перевести главу по пути: {full_chapter_path}")

        # Читаем содержимое файла первой главы из архива EPUB
        chapter_content = epub_archive.read(full_chapter_path).decode('utf-8')

        # Ограничиваем текст для перевода (например, первые 1000 символов)
        text_to_translate = chapter_content[:1000]

        if not text_to_translate.strip():
             print("Текст для перевода пуст после извлечения из файла.")
             if hasattr(result, 'translated_first_chapter'):
                  result.translated_first_chapter = "Текст для перевода пуст."
             return None

        print("Перевод первых 1000 символов первой главы...")
        # Выполняем перевод
        translation = translator.translate(text_to_translate, src='auto', dest='en')

        # Сохраняем результат перевода
        if hasattr(result, 'translated_first_chapter'):
             result.translated_first_chapter = translation.text
        print("Перевод завершен.")

        return translation.text

    except Exception as e:
        print(f"Ошибка при переводе первой главы: {str(e)}")
        if hasattr(result, 'translated_first_chapter'):
             result.translated_first_chapter = f"Ошибка при переводе: {str(e)}"
        # Пока не re-raise исключение
        # raise
        return None 