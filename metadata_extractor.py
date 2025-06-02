import zipfile
import xml.etree.ElementTree as ET
from typing import Optional
from dataclasses import dataclass

@dataclass
class EpubMetadata:
    title: str = ""
    author: str = ""
    language: str = ""
    publisher: str = ""
    publication_date: str = ""
    description: str = ""

class MetadataExtractor:
    def __init__(self, epub_path: str):
        self.epub_path = epub_path
        self.ns = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'opf': 'http://www.idpf.org/2007/opf',
            'container': 'urn:oasis:names:tc:opendocument:xmlns:container'
        }
        self.opf_path = self._get_opf_path()

    def _get_opf_path(self) -> str:
        """Получает путь к OPF файлу из container.xml"""
        try:
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                container = epub.read('META-INF/container.xml')
                root = ET.fromstring(container)
                opf_path = root.find('.//container:rootfile', self.ns).get('full-path')
                return opf_path
        except Exception as e:
            print(f"Ошибка при получении пути к OPF файлу: {str(e)}")
            return 'OEBPS/content.opf'  # Возвращаем путь по умолчанию

    def _get_metadata_root(self):
        """Получает корневой элемент метаданных"""
        try:
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                content = epub.read(self.opf_path)
                return ET.fromstring(content)
        except Exception as e:
            print(f"Ошибка при чтении OPF файла: {str(e)}")
            return None

    def extract_title(self) -> str:
        """Извлекает название книги"""
        try:
            root = self._get_metadata_root()
            if root is None:
                return ""
            title = root.find('.//dc:title', self.ns)
            return title.text if title is not None else ""
        except Exception as e:
            print(f"Ошибка при извлечении названия: {str(e)}")
            return ""

    def extract_author(self) -> str:
        """Извлекает автора книги"""
        try:
            root = self._get_metadata_root()
            if root is None:
                return ""
            author = root.find('.//dc:creator', self.ns)
            return author.text if author is not None else ""
        except Exception as e:
            print(f"Ошибка при извлечении автора: {str(e)}")
            return ""

    def extract_publisher(self) -> str:
        """Извлекает издателя"""
        try:
            root = self._get_metadata_root()
            if root is None:
                return ""
            publisher = root.find('.//dc:publisher', self.ns)
            return publisher.text if publisher is not None else ""
        except Exception as e:
            print(f"Ошибка при извлечении издателя: {str(e)}")
            return ""

    def extract_date(self) -> str:
        """Извлекает дату публикации"""
        try:
            root = self._get_metadata_root()
            if root is None:
                return ""
            date = root.find('.//dc:date', self.ns)
            return date.text if date is not None else ""
        except Exception as e:
            print(f"Ошибка при извлечении даты: {str(e)}")
            return ""

    def extract_language(self) -> str:
        """Извлекает язык книги"""
        try:
            root = self._get_metadata_root()
            if root is None:
                return ""
            language = root.find('.//dc:language', self.ns)
            return language.text if language is not None else ""
        except Exception as e:
            print(f"Ошибка при извлечении языка: {str(e)}")
            return ""

    def extract_description(self) -> str:
        """Извлекает описание книги"""
        try:
            root = self._get_metadata_root()
            if root is None:
                return ""
            description = root.find('.//dc:description', self.ns)
            return description.text if description is not None else ""
        except Exception as e:
            print(f"Ошибка при извлечении описания: {str(e)}")
            return ""

    def extract_metadata(self) -> EpubMetadata:
        """Извлекает все метаданные из EPUB файла"""
        try:
            root = self._get_metadata_root()
            if root is None:
                return EpubMetadata()
            
            metadata = {}
            # Маппинг полей из DC в наши поля
            field_mapping = {
                'title': 'title',
                'creator': 'author',
                'publisher': 'publisher',
                'date': 'publication_date',
                'language': 'language',
                'description': 'description'
            }
            
            for dc_field, our_field in field_mapping.items():
                element = root.find(f'.//dc:{dc_field}', self.ns)
                if element is not None:
                    metadata[our_field] = element.text
            
            return EpubMetadata(**metadata)
        except Exception as e:
            print(f"Ошибка при извлечении метаданных: {str(e)}")
            return EpubMetadata() 