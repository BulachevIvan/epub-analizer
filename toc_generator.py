import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
import os

@dataclass
class TocEntry:
    title: str
    href: str
    level: int
    children: List['TocEntry'] = field(default_factory=list)
    num_children: int = 0

@dataclass
class TocResult:
    chapters: List[Dict[str, str]] = None
    total_chapters: int = 0

    def __post_init__(self):
        if self.chapters is None:
            self.chapters = []

class TocGenerator:
    def __init__(self, epub_path: str):
        self.epub_path = epub_path
        self.namespaces = {
            'ncx': 'http://www.daisy.org/z3986/2005/ncx/',
            'opf': 'http://www.idpf.org/2007/opf',
            'xhtml': 'http://www.w3.org/1999/xhtml'
        }

    def generate_toc(self) -> TocResult:
        """Генерирует оглавление из EPUB файла"""
        result = TocResult()
        
        try:
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
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
                        if manifest is not None:
                            for item in manifest.findall('.//{http://www.idpf.org/2007/opf}item'):
                                if item.get('id') == toc_id:
                                    ncx_path = os.path.join(os.path.dirname(opf_path), item.get('href')).replace('\\', '/')
                                    try:
                                        ncx_content = epub.read(ncx_path)
                                        ncx_root = ET.fromstring(ncx_content)
                                        
                                        # Извлекаем главы из NCX
                                        nav_points = ncx_root.findall('.//{http://www.daisy.org/z3986/2005/ncx/}navPoint')
                                        for nav_point in nav_points:
                                            text = nav_point.find('.//{http://www.daisy.org/z3986/2005/ncx/}text').text
                                            src = nav_point.find('.//{http://www.daisy.org/z3986/2005/ncx/}content').get('src')
                                            result.chapters.append({
                                                'title': text,
                                                'src': src
                                            })
                                        
                                        result.total_chapters = len(result.chapters)
                                    except Exception as e:
                                        print(f"Ошибка при чтении NCX файла {ncx_path}: {str(e)}")
        
        except Exception as e:
            print(f"Ошибка при генерации оглавления: {str(e)}")
            raise
        
        return result

    def generate(self) -> TocResult:
        """Генерирует оглавление из EPUB файла"""
        result = TocResult()
        
        try:
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                print("Содержимое EPUB файла:")
                for file in epub.namelist():
                    print(f"- {file}")

                # Находим файл OPF
                container = epub.read('META-INF/container.xml')
                root = ET.fromstring(container)
                opf_path = root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile').get('full-path')
                print(f"\nПуть к OPF файлу: {opf_path}")
                
                # Читаем OPF файл
                opf_content = epub.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                
                # Пробуем найти навигационный файл (EPUB3)
                nav_path = None
                manifest = opf_root.find('.//opf:manifest', self.namespaces)
                if manifest is not None:
                    print("\nЭлементы манифеста:")
                    for item in manifest.findall('.//opf:item', self.namespaces):
                        item_id = item.get('id', '')
                        item_href = item.get('href', '')
                        item_media_type = item.get('media-type', '')
                        item_properties = item.get('properties', '')
                        print(f"- ID: {item_id}, HREF: {item_href}, Type: {item_media_type}, Props: {item_properties}")
                        
                        if item.get('properties') == 'nav':
                            nav_path = item.get('href')
                            print(f"\nНайден навигационный файл: {nav_path}")
                            break
                
                if nav_path:
                    # EPUB3 формат
                    try:
                        nav_content = epub.read(nav_path)
                        soup = BeautifulSoup(nav_content, 'html.parser')
                        nav = soup.find('nav', attrs={'epub:type': 'toc'})
                        if nav:
                            result.entries = self._process_epub3_nav(nav)
                            result.count = self._count_entries(result.entries)
                            print(f"\nУспешно обработан EPUB3 навигационный файл")
                        else:
                            print("\nНе найден элемент nav с атрибутом epub:type='toc'")
                    except Exception as e:
                        print(f"\nОшибка при обработке EPUB3 навигационного файла: {str(e)}")
                else:
                    # EPUB2 формат (NCX)
                    print("\nПробуем EPUB2 формат (NCX)")
                    spine = opf_root.find('.//opf:spine', self.namespaces)
                    if spine is not None:
                        toc_id = spine.get('toc')
                        print(f"ID оглавления из spine: {toc_id}")
                        if toc_id:
                            for item in manifest.findall('.//opf:item', self.namespaces):
                                if item.get('id') == toc_id:
                                    ncx_path = item.get('href')
                                    print(f"Найден путь к NCX файлу: {ncx_path}")
                                    if ncx_path:
                                        try:
                                            # Добавляем префикс OPS/ к пути файла
                                            full_ncx_path = f"OPS/{ncx_path}"
                                            print(f"Полный путь к NCX файлу: {full_ncx_path}")
                                            ncx_content = epub.read(full_ncx_path)
                                            ncx_root = ET.fromstring(ncx_content)
                                            nav_map = ncx_root.find('.//ncx:navMap', self.namespaces)
                                            if nav_map is not None:
                                                result.entries = self._process_nav_points(nav_map)
                                                result.count = self._count_entries(result.entries)
                                                print("Успешно обработан NCX файл")
                                            else:
                                                print("Не найден элемент navMap в NCX файле")
                                        except Exception as e:
                                            print(f"Ошибка при обработке NCX файла: {str(e)}")
        
        except Exception as e:
            print(f"Ошибка при генерации оглавления: {str(e)}")
        
        return result

    def _process_epub3_nav(self, nav_element, level: int = 1) -> List[TocEntry]:
        """Обрабатывает навигационные элементы EPUB3"""
        entries = []
        
        for li in nav_element.find_all('li', recursive=False):
            a = li.find('a')
            if a:
                title = a.get_text(strip=True)
                href = a.get('href', '')
                
                # Создаем запись
                entry = TocEntry(
                    title=title,
                    href=href,
                    level=level,
                    children=self._process_epub3_nav(li, level + 1) if li.find('ol') else []
                )
                entry.num_children = len(entry.children)
                entries.append(entry)
        
        return entries

    def _process_nav_points(self, nav_point: ET.Element, level: int = 1) -> List[TocEntry]:
        """Обрабатывает навигационные точки EPUB2"""
        entries = []
        
        for point in nav_point.findall('.//ncx:navPoint', self.namespaces):
            # Извлекаем заголовок
            text_elem = point.find('.//ncx:text', self.namespaces)
            title = text_elem.text if text_elem is not None else ""
            
            # Извлекаем ссылку
            content_elem = point.find('.//ncx:content', self.namespaces)
            href = content_elem.get('src') if content_elem is not None else ""
            
            # Создаем запись
            entry = TocEntry(
                title=title,
                href=href,
                level=level,
                children=self._process_nav_points(point, level + 1)
            )
            entry.num_children = len(entry.children)
            entries.append(entry)
        
        return entries

    def _count_entries(self, entries: List[TocEntry]) -> int:
        """Подсчитывает общее количество записей в оглавлении"""
        count = len(entries)
        for entry in entries:
            count += self._count_entries(entry.children)
        return count

    def save_to_json(self, result: TocResult, output_file: str):
        """Сохраняет оглавление в JSON файл"""
        import json
        
        def entry_to_dict(entry: TocEntry) -> dict:
            return {
                'title': entry.title,
                'href': entry.href,
                'level': entry.level,
                'num_children': entry.num_children,
                'children': [entry_to_dict(child) for child in entry.children]
            }
        
        toc_dict = {
            'count': result.count,
            'entries': [entry_to_dict(entry) for entry in result.entries]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(toc_dict, f, ensure_ascii=False, indent=2) 