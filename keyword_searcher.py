import re
from dataclasses import dataclass
from typing import List

@dataclass
class KeywordSearchResult:
    match_count: int = 0
    matches: List[str] = None

    def __post_init__(self):
        if self.matches is None:
            self.matches = []

class KeywordSearcher:
    def __init__(self, search_pattern: str):
        self.search_pattern = search_pattern
        
    def search_keywords(self, text: str) -> KeywordSearchResult:
        """Ищет ключевые слова в тексте"""
        result = KeywordSearchResult()
        
        try:
            # Ищем все вхождения искомого слова
            pattern = r'\b' + re.escape(self.search_pattern.lower()) + r'\b'
            matches = re.finditer(pattern, text.lower())
            
            # Собираем контекст для каждого совпадения
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                result.matches.append(context)
            
            result.match_count = len(result.matches)
        
        except Exception as e:
            print(f"Ошибка при поиске ключевых слов: {str(e)}")
            raise
        
        return result 