from dataclasses import dataclass
from typing import Dict
import zipfile
import os
import tempfile
import xml.etree.ElementTree as ET
import re

@dataclass
class ChapterSplitResult:
    chapters: Dict[str, str] = None  # Словарь: название главы -> путь к файлу
    total_chapters: int = 0  # Общее количество глав
    output_zip: str = ""  # Путь к итоговому ZIP архиву

    def __post_init__(self):
        if self.chapters is None:
            self.chapters = {}

class ChapterSplitter:
    def __init__(self):
        # Регулярные выражения для поиска заголовков глав в разных форматах
        self.chapter_patterns = [
            # HTML формат
            re.compile(r'<h[1-6][^>]*>.*?</h[1-6]>', re.DOTALL),
            # Текстовый формат с номерами глав
            re.compile(r'(?:^|\n)(?:Глава|Книга|Часть|Пролог|Эпилог)[\s\d]+[–-]?\s*([^\n]+)', re.IGNORECASE | re.MULTILINE),
            # Текстовый формат с римскими цифрами
            re.compile(r'(?:^|\n)(?:Глава|Книга|Часть|Пролог|Эпилог)[\s]*[IVX]+[–-]?\s*([^\n]+)', re.IGNORECASE | re.MULTILINE)
        ]
        
        self.chapter_title_patterns = [
            # HTML формат
            re.compile(r'<h[1-6][^>]*>(.*?)</h[1-6]>', re.DOTALL),
            # Текстовый формат
            re.compile(r'(?:Глава|Книга|Часть|Пролог|Эпилог)[\s\d]+[–-]?\s*([^\n]+)', re.IGNORECASE),
            # Текстовый формат с римскими цифрами
            re.compile(r'(?:Глава|Книга|Часть|Пролог|Эпилог)[\s]*[IVX]+[–-]?\s*([^\n]+)', re.IGNORECASE)
        ]

    def split_text_into_chapters(self, text: str) -> Dict[int, str]:
        """Разбивает текст на главы и возвращает словарь {номер_главы: текст_главы}"""
        try:
            # Пробуем разные паттерны для поиска глав
            chapter_matches = []
            used_pattern = None
            
            for pattern in self.chapter_patterns:
                matches = list(pattern.finditer(text))
                if matches:
                    chapter_matches = matches
                    used_pattern = pattern
                    break
            
            if not chapter_matches:
                print("Не найдены заголовки глав ни в одном из поддерживаемых форматов")
                return {}
            
            chapters = {}
            # Разбиваем текст на главы
            for i in range(len(chapter_matches)):
                start = chapter_matches[i].start()
                # Если это последняя глава, берем до конца текста
                end = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(text)
                
                chapter_text = text[start:end]
                # Извлекаем номер главы из заголовка
                chapter_num = i + 1  # Нумерация глав с 1
                chapters[chapter_num] = chapter_text
            
            return chapters
        except Exception as e:
            print(f"Ошибка при разбиении текста на главы: {str(e)}")
            return {}

    def split_chapters(self, epub_path: str, output_dir: str = None) -> ChapterSplitResult:
        """Разделяет EPUB файл на главы и сохраняет их в ZIP архив"""
        result = ChapterSplitResult()
        
        try:
            # Создаем временную директорию для работы
            temp_dir = tempfile.mkdtemp()
            
            # Создаем директорию для глав
            chapters_dir = os.path.join(temp_dir, 'chapters')
            os.makedirs(chapters_dir, exist_ok=True)
            
            # Открываем EPUB файл
            with zipfile.ZipFile(epub_path, 'r') as epub:
                # Находим файл OPF
                container = epub.read('META-INF/container.xml')
                root = ET.fromstring(container)
                opf_path = root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile').get('full-path')
                
                # Читаем OPF файл
                opf_content = epub.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                
                # Находим NCX файл
                spine = opf_root.find('.//{http://www.idpf.org/2007/opf}spine')
                toc_id = spine.get('toc')
                manifest = opf_root.find('.//{http://www.idpf.org/2007/opf}manifest')
                toc_item = manifest.find(f'.//{{http://www.idpf.org/2007/opf}}item[@id="{toc_id}"]')
                
                # Собираем информацию о главах
                chapters_info = []
                if toc_item is not None:
                    toc_path = toc_item.get('href')
                    if toc_path:
                        # Читаем NCX файл
                        ncx_content = epub.read(f"OPS/{toc_path}")
                        ncx_root = ET.fromstring(ncx_content)
                        
                        # Собираем все заголовки из оглавления
                        nav_points = ncx_root.findall('.//{http://www.daisy.org/z3986/2005/ncx/}navPoint')
                        for nav_point in nav_points:
                            text = nav_point.find('.//{http://www.daisy.org/z3986/2005/ncx/}text').text
                            content = nav_point.find('.//{http://www.daisy.org/z3986/2005/ncx/}content')
                            src = content.get('src')
                            chapters_info.append((text, src))

                # Обрабатываем каждую главу
                for chapter_title, chapter_src in chapters_info:
                    try:
                        # Извлекаем имя файла из src и убираем якорь
                        file_name = os.path.basename(chapter_src.split('#')[0])
                        full_path = f"OPS/{file_name}"
                        
                        try:
                            # Читаем содержимое главы
                            content = epub.read(full_path)
                        except zipfile.BadZipFile:
                            print(f"Пропуск поврежденного файла {full_path}")
                            continue
                        except Exception as e:
                            print(f"Ошибка при чтении файла {full_path}: {str(e)}")
                            continue
                        
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
                        
                        # Сохраняем главу в текстовый файл
                        chapter_file = os.path.join(chapters_dir, f"{chapter_title}.txt")
                        with open(chapter_file, 'w', encoding='utf-8') as f:
                            f.write(text)
                        
                        result.chapters[chapter_title] = chapter_file
                        
                    except Exception as e:
                        print(f"Ошибка при обработке главы {chapter_title}: {str(e)}")
                
                result.total_chapters = len(result.chapters)
                
                # Создаем ZIP архив
                if output_dir is None:
                    output_dir = os.path.dirname(epub_path)
                output_zip = os.path.join(output_dir, 'chapters.zip')
                
                # Создаем ZIP архив с оптимизированным сжатием
                with zipfile.ZipFile(output_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as zip_file:
                    for chapter_title, chapter_file in result.chapters.items():
                        zip_file.write(chapter_file, os.path.basename(chapter_file))
                
                result.output_zip = output_zip
                
        except Exception as e:
            print(f"Ошибка при разделении на главы: {str(e)}")
        finally:
            # Удаляем временную директорию
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
        
        return result 