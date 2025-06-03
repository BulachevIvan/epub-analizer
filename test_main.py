import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Добавляем директорию проекта в sys.path, чтобы импортировать модули
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main # Изменяем импорт

# Мокаем внешние зависимости, которые касаются работы с файлами,
# чтобы тесты были изолированы и не требовали реальных файлов EPUB.
# Мы не будем мокать TextAnalyzer, KeywordSearcher, ChapterSplitter, MetadataExtractor
# так как именно их логику мы хотим тестировать через EpubProcessor или напрямую.

@pytest.fixture
def mock_processor():
    """Фикстура для создания мока EpubProcessor с замоканными файловыми операциями."""
    # Мокаем зависимости, которые взаимодействуют с файловой системой
    with patch('main.MetadataExtractor') as MockMetadataExtractor, \
         patch('main.TextExtractor') as MockTextExtractor, \
         patch('main.ImageExtractor') as MockImageExtractor, \
         patch('main.TocGenerator') as MockTocGenerator, \
         patch('main.ChapterSplitter') as MockChapterSplitter, \
         patch('main.StyleProcessor') as MockStyleProcessor, \
         patch('main.shutil.copy2') as mock_copy2, \
         patch('main.os.makedirs') as mock_makedirs:

        # Создаем реальные экземпляры классов, которые мы хотим тестировать
        real_text_analyzer = main.TextAnalyzer() # Используем main.TextAnalyzer
        real_keyword_searcher = main.KeywordSearcher("тест") # Используем main.KeywordSearcher
        real_chapter_splitter = main.ChapterSplitter() # Используем main.ChapterSplitter

        # Мокаем экземпляр MetadataExtractor, так как мы не тестируем его внутреннюю логику здесь
        mock_metadata_extractor_instance = MockMetadataExtractor.return_value
        mock_text_extractor_instance = MockTextExtractor.return_value

        # Настраиваем моки методов, которые вызываются внутри EpubProcessor
        mock_text_extractor_instance.extract_text.return_value = main.TextExtractionResult(text="Пример текста") # Мокаем результат извлечения текста

        processor = main.EpubProcessor("dummy.epub", "тест", "./library") # Используем main.EpubProcessor
        processor.text_analyzer = real_text_analyzer # Подменяем мок реальным экземпляром
        processor.keyword_searcher = real_keyword_searcher # Подменяем мок реальным экземпляром
        processor.chapter_splitter = real_chapter_splitter # Подменяем мок реальным экземпляром
        processor.metadata_extractor = mock_metadata_extractor_instance # Используем мок для метаданных
        processor.text_extractor = mock_text_extractor_instance # Используем мок для извлечения текста

        # Мокаем методы MetadataExtractor для тестирования process_metadata_parallel
        mock_metadata_extractor_instance.extract_title.return_value = "Тестовая Книга"
        mock_metadata_extractor_instance.extract_author.return_value = "Тест Авторович"
        mock_metadata_extractor_instance.extract_publisher.return_value = "Тест Издательство"
        mock_metadata_extractor_instance.extract_date.return_value = "2023-01-01"
        mock_metadata_extractor_instance.extract_language.return_value = "ru"
        mock_metadata_extractor_instance.extract_description.return_value = "Это описание тестовой книги."

        yield processor

# Тесты для analyze_text
def test_analyze_text(mock_processor):
    """Тестирование функции analyze_text."""
    sample_text_result = main.TextExtractionResult(text="Это первый абзац. Это второе предложение.\n\nЭто третий абзац с искомым словом тест.") # Используем main.TextExtractionResult
    mock_processor.search_pattern = "тест"
    result = mock_processor.analyze_text(sample_text_result)

    assert type(result).__name__ == main.TextAnalysisResult.__name__ # Проверяем имя типа
    assert result.word_count > 0
    assert result.sentence_count > 0
    assert result.paragraph_count == 2
    assert result.search_word_frequency == 1 # Проверяем, что слово "тест" найдено 1 раз
    assert mock_processor.result.text_analysis == result
    assert mock_processor.result.thread_statuses.get('analyze_text') == "Успешно выполнено"

def test_analyze_text_empty(mock_processor):
    """Тестирование analyze_text с пустым текстом."""
    sample_text_result = main.TextExtractionResult(text="") # Используем main.TextExtractionResult
    mock_processor.search_pattern = "тест"
    result = mock_processor.analyze_text(sample_text_result)

    assert type(result).__name__ == main.TextAnalysisResult.__name__ # Проверяем имя типа
    assert result.word_count == 0
    assert result.char_count == 0
    assert result.sentence_count == 0
    assert result.paragraph_count == 0
    assert result.search_word_frequency == 0
    assert mock_processor.result.text_analysis == result
    assert mock_processor.result.thread_statuses.get('analyze_text') == "Успешно выполнено"


# Тесты для search_keywords
def test_search_keywords(mock_processor):
    """Тестирование функции search_keywords."""
    sample_text_result = main.TextExtractionResult(text="Текст с несколькими вхождениями слова тест. Тест прошел успешно. Еще один тест.") # Используем main.TextExtractionResult
    mock_processor.search_pattern = "тест"
    result = mock_processor.search_keywords(sample_text_result)

    assert type(result).__name__ == main.KeywordSearchResult.__name__ # Проверяем имя типа
    assert result.match_count == 3
    assert len(result.matches) == 3 # Ожидаем 3 совпадения
    assert "тест" in result.matches[0].lower() # Проверяем, что совпадения содержат искомое слово
    assert mock_processor.result.keyword_search == result
    assert mock_processor.result.thread_statuses.get('search_keywords') == "Успешно выполнено"

def test_search_keywords_no_match(mock_processor):
    """Тестирование search_keywords без совпадений."""
    sample_text_result = main.TextExtractionResult(text="В этом тексте нет искомого слова.") # Используем main.TextExtractionResult
    mock_processor.search_pattern = "тест"
    result = mock_processor.search_keywords(sample_text_result)

    assert type(result).__name__ == main.KeywordSearchResult.__name__ # Проверяем имя типа
    assert result.match_count == 0
    assert len(result.matches) == 0
    assert mock_processor.result.keyword_search == result
    assert mock_processor.result.thread_statuses.get('search_keywords') == "Успешно выполнено"

# Тесты для process_chapters_parallel
def test_process_chapters_parallel(mock_processor):
    """Тестирование параллельной обработки глав."""
    # Мокаем метод split_text_into_chapters, чтобы контролировать разделение на главы
    with patch.object(mock_processor.chapter_splitter, 'split_text_into_chapters', return_value={
        1: "Текст первой главы.",
        2: "Текст второй главы с каким-то содержанием.",
        3: "Короткая третья глава."
    }) as mock_split:
        sample_text_result = main.TextExtractionResult(text="Большой текст книги с разделителями глав.") # Используем main.TextExtractionResult
        processed_chapters = mock_processor.process_chapters_parallel(sample_text_result)

        mock_split.assert_called_once_with(sample_text_result.text) # Проверяем, что метод разделения был вызван
        assert isinstance(processed_chapters, dict)
        assert len(processed_chapters) == 3 # Ожидаем 3 обработанные главы
        assert 1 in processed_chapters
        assert 2 in processed_chapters
        assert 3 in processed_chapters
        assert processed_chapters[1] == "Текст первой главы." # Проверяем, что текст глав сохранен (поскольку _process_single_chapter пока просто возвращает текст)

# Тесты для process_metadata_parallel
def test_process_metadata_parallel(mock_processor):
    """Тестирование параллельной обработки метаданных."""
    # Результаты мокаются в фикстуре mock_processor
    metadata_results = mock_processor.process_metadata_parallel()

    assert isinstance(metadata_results, dict)
    assert len(metadata_results) == 6 # Ожидаем результаты для всех 6 полей
    assert metadata_results['title'] == "Тестовая Книга"
    assert metadata_results['author'] == "Тест Авторович"
    assert metadata_results['publisher'] == "Тест Издательство"
    assert metadata_results['date'] == "2023-01-01"
    assert metadata_results['language'] == "ru"
    assert metadata_results['description'] == "Это описание тестовой книги."

    # Проверяем, что методы экстрактора метаданных были вызваны
    mock_processor.metadata_extractor.extract_title.assert_called_once()
    mock_processor.metadata_extractor.extract_author.assert_called_once()
    mock_processor.metadata_extractor.extract_publisher.assert_called_once()
    mock_processor.metadata_extractor.extract_date.assert_called_once()
    mock_processor.metadata_extractor.extract_language.assert_called_once()
    mock_processor.metadata_extractor.extract_description.assert_called_once() 