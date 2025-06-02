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
        
    def extract_metadata(self) -> EpubMetadata:
        """Извлекает метаданные из EPUB файла"""
        result = EpubMetadata()
        
        try:
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                # Находим файл OPF
                container = epub.read('META-INF/container.xml')
                root = ET.fromstring(container)
                opf_path = root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile').get('full-path')
                
                # Читаем OPF файл
                opf_content = epub.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                
                # Извлекаем метаданные
                metadata = opf_root.find('.//{http://www.idpf.org/2007/opf}metadata')
                if metadata is not None:
                    # Заголовок
                    title = metadata.find('.//{http://purl.org/dc/elements/1.1/}title')
                    if title is not None:
                        result.title = title.text
                    
                    # Автор
                    creator = metadata.find('.//{http://purl.org/dc/elements/1.1/}creator')
                    if creator is not None:
                        result.author = creator.text
                    
                    # Язык
                    language = metadata.find('.//{http://purl.org/dc/elements/1.1/}language')
                    if language is not None:
                        result.language = language.text
                    
                    # Издатель
                    publisher = metadata.find('.//{http://purl.org/dc/elements/1.1/}publisher')
                    if publisher is not None:
                        result.publisher = publisher.text
                    
                    # Дата публикации
                    date = metadata.find('.//{http://purl.org/dc/elements/1.1/}date')
                    if date is not None:
                        result.publication_date = date.text
                    
                    # Описание
                    description = metadata.find('.//{http://purl.org/dc/elements/1.1/}description')
                    if description is not None:
                        result.description = description.text
        
        except Exception as e:
            print(f"Ошибка при извлечении метаданных: {str(e)}")
            raise
        
        return result 