import re
from dataclasses import dataclass, field
from typing import Dict, List
from collections import Counter

@dataclass
class TextAnalysisResult:
    word_count: int = 0
    char_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    word_frequency: Dict[str, int] = field(default_factory=dict)
    search_word_frequency: int = 0

class TextAnalyzer:
    def __init__(self):
        self.word_pattern = re.compile(r'\b[а-яА-ЯёЁa-zA-Z]+\b', re.UNICODE)
        self.sentence_pattern = re.compile(r'[.!?]+', re.UNICODE)
        self.paragraph_pattern = re.compile(r'\n\s*\n', re.UNICODE)

    def analyze_text(self, text: str, search_pattern: str = None) -> TextAnalysisResult:
        """Анализирует текст и возвращает статистику"""
        result = TextAnalysisResult()
        
        # Подсчет слов
        words = re.findall(r'\b\w+\b', text.lower())
        result.word_count = len(words)
        
        # Подсчет символов
        result.char_count = len(text)
        
        # Подсчет предложений
        sentences = re.split(r'[.!?]+', text)
        result.sentence_count = len([s for s in sentences if s.strip()])
        
        # Подсчет параграфов
        paragraphs = text.split('\n\n')
        result.paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # Подсчет частоты искомого слова
        if search_pattern:
            result.search_word_frequency = len(re.findall(r'\b' + re.escape(search_pattern.lower()) + r'\b', text.lower()))
        
        return result

    def analyze(self, text: str, search_pattern: str = None) -> TextAnalysisResult:
        """Анализирует текст и возвращает результаты"""
        result = TextAnalysisResult()
        
        if not text:
            return result
            
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Нормализуем пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Подсчитываем символы
        result.char_count = len(text)
        
        # Подсчитываем предложения
        result.sentence_count = len(self.sentence_pattern.findall(text))
        
        # Подсчитываем параграфы
        result.paragraph_count = len(self.paragraph_pattern.findall(text)) + 1
        
        # Подсчитываем слова
        words = self.word_pattern.findall(text.lower())
        result.word_count = len(words)
        
        # Подсчитываем частоту слов
        word_freq = {}
        for word in words:
            if len(word) > 2:  # Игнорируем короткие слова
                word_freq[word] = word_freq.get(word, 0) + 1
        
        result.word_frequency = word_freq
        
        # Если указан поисковый паттерн, подсчитываем его частоту
        if search_pattern:
            search_pattern = search_pattern.lower()
            result.search_word_frequency = word_freq.get(search_pattern, 0)
                
        return result 