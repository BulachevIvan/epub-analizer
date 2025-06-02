from dataclasses import dataclass
from typing import List, Dict
import re
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import tempfile
import shutil
import os
import gc
from collections import OrderedDict

@dataclass
class FormattingResult:
    bold_headers: Dict[str, str] = None  # Словарь: оригинальный текст -> текст с жирным шрифтом
    uppercase_headers: Dict[str, str] = None  # Словарь: оригинальный текст -> текст в верхнем регистре
    formatted_text: str = ""  # Итоговый отформатированный текст
    formatted_headers_count: int = 0  # Количество отформатированных заголовков
    _all_headers: Dict[str, str] = None  # Хранит все найденные заголовки

    def __post_init__(self):
        if self.bold_headers is None:
            self.bold_headers = OrderedDict()
        if self.uppercase_headers is None:
            self.uppercase_headers = OrderedDict()
        if self._all_headers is None:
            self._all_headers = OrderedDict()

    def add_header(self, text: str):
        """Добавляет заголовок в словари, ограничивая их размер до 10 элементов"""
        if text not in self._all_headers:
            self._all_headers[text] = text
            if len(self.bold_headers) < 10:
                self.bold_headers[text] = f'<span style="font-weight: bold;">{text}</span>'
                self.uppercase_headers[text] = text.upper()

class TextFormatter:
    def __init__(self):
        # Регулярное выражение для поиска заголовков глав
        self.chapter_pattern = re.compile(
            r'(?:^|\n)(?:Глава|Книга|Часть|Пролог|Эпилог)[\s\d]+[–-]?\s*([^\n]+)',
            re.IGNORECASE | re.MULTILINE
        )
        
    def format_text(self, epub_path: str) -> FormattingResult:
        """Форматирует текст, выделяя заголовки в HTML-файлах книги"""
        result = FormattingResult()
        
        try:
            with zipfile.ZipFile(epub_path, 'r') as epub:
                # Находим файл OPF
                container = epub.read('META-INF/container.xml')
                root = ET.fromstring(container)
                opf_path = root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile').get('full-path')
                
                # Читаем OPF файл
                opf_content = epub.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                
                # Находим NCX файл (оглавление)
                spine = opf_root.find('.//{http://www.idpf.org/2007/opf}spine')
                if spine is not None:
                    toc_id = spine.get('toc')
                    if toc_id:
                        manifest = opf_root.find('.//{http://www.idpf.org/2007/opf}manifest')
                        for item in manifest.findall('.//{http://www.idpf.org/2007/opf}item'):
                            if item.get('id') == toc_id:
                                toc_path = item.get('href')
                                if toc_path:
                                    try:
                                        full_toc_path = f"OPS/{toc_path}"
                                        toc_content = epub.read(full_toc_path)
                                        toc_root = ET.fromstring(toc_content)
                                        
                                        # Ищем заголовки в NCX
                                        for nav_point in toc_root.findall('.//{http://www.daisy.org/z3986/2005/ncx/}navPoint'):
                                            text = nav_point.find('.//{http://www.daisy.org/z3986/2005/ncx/}text')
                                            if text is not None and text.text:
                                                header_text = text.text.strip()
                                                if header_text:
                                                    result.add_header(header_text)
                                    except Exception as e:
                                        print(f"Ошибка при чтении TOC: {str(e)}")
                
                # Находим все XHTML файлы
                manifest = opf_root.find('.//{http://www.idpf.org/2007/opf}manifest')
                if manifest is not None:
                    for item in manifest.findall('.//{http://www.idpf.org/2007/opf}item'):
                        if item.get('media-type') == 'application/xhtml+xml':
                            file_path = item.get('href')
                            if file_path:
                                try:
                                    full_path = f"OPS/{file_path}"
                                    content = epub.read(full_path)
                                    
                                    # Пробуем разные кодировки
                                    encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin1']
                                    text = None
                                    
                                    for encoding in encodings:
                                        try:
                                            text = content.decode(encoding)
                                            break
                                        except UnicodeDecodeError:
                                            continue
                                    
                                    if text is None:
                                        raise UnicodeDecodeError("Не удалось декодировать текст")
                                    
                                    # Используем BeautifulSoup для парсинга HTML
                                    soup = BeautifulSoup(text, 'html.parser')
                                    
                                    # Ищем заголовки в HTML-тегах
                                    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div']):
                                        text = tag.get_text().strip()
                                        if self.chapter_pattern.match(text):
                                            result.add_header(text)
                                    
                                except Exception as e:
                                    print(f"Ошибка при обработке файла {file_path}: {str(e)}")
            
            result.formatted_headers_count = len(result._all_headers)
            
        except Exception as e:
            print(f"Ошибка при форматировании текста: {str(e)}")
        
        return result
        
    def get_formatted_headers(self, result: FormattingResult) -> List[Dict[str, str]]:
        """Возвращает список отформатированных заголовков"""
        formatted_headers = []
        for original, bold in result.bold_headers.items():
            formatted_headers.append({
                "original": original,
                "bold": bold,
                "uppercase": result.uppercase_headers.get(original, "")
            })
        return formatted_headers 