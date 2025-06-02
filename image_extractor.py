import os
import zipfile
from PIL import Image
from io import BytesIO
from dataclasses import dataclass
from typing import List, Optional
import xml.etree.ElementTree as ET
from pathlib import Path

@dataclass
class ImageExtractionResult:
    count: int = 0
    output_dir: str = ""
    extracted_files: List[str] = None

    def __post_init__(self):
        if self.extracted_files is None:
            self.extracted_files = []

class ImageExtractor:
    def __init__(self, epub_path: str, output_dir: str):
        self.epub_path = epub_path
        self.output_dir = output_dir
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'}
        
        # Создаем директорию для изображений если её нет
        os.makedirs(output_dir, exist_ok=True)

    def extract_images(self) -> ImageExtractionResult:
        """Извлекает изображения из EPUB файла"""
        result = ImageExtractionResult()
        result.output_dir = self.output_dir
        
        try:
            # Создаем директорию для изображений, если она не существует
            os.makedirs(self.output_dir, exist_ok=True)
            
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                # Находим файл OPF
                container = epub.read('META-INF/container.xml')
                root = ET.fromstring(container)
                opf_path = root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile').get('full-path')
                
                # Читаем OPF файл
                opf_content = epub.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                
                # Находим все изображения
                manifest = opf_root.find('.//{http://www.idpf.org/2007/opf}manifest')
                if manifest is not None:
                    for item in manifest.findall('.//{http://www.idpf.org/2007/opf}item'):
                        if item.get('media-type', '').startswith('image/'):
                            file_path = item.get('href')
                            if file_path:
                                try:
                                    # Получаем полный путь к файлу
                                    full_path = os.path.join(os.path.dirname(opf_path), file_path).replace('\\', '/')
                                    
                                    # Извлекаем изображение
                                    image_data = epub.read(full_path)
                                    
                                    # Сохраняем изображение
                                    output_path = os.path.join(self.output_dir, os.path.basename(file_path))
                                    with open(output_path, 'wb') as f:
                                        f.write(image_data)
                                    
                                    result.extracted_files.append(output_path)
                                    result.count += 1
                                except Exception as e:
                                    print(f"Ошибка при извлечении изображения {file_path}: {str(e)}")
        
        except Exception as e:
            print(f"Ошибка при извлечении изображений: {str(e)}")
            raise
        
        return result

    def validate_images(self, result: ImageExtractionResult) -> List[str]:
        """Проверяет извлеченные изображения на валидность"""
        invalid_files = []
        
        for image_path in result.extracted_files:
            try:
                with Image.open(image_path) as img:
                    img.verify()
            except Exception as e:
                invalid_files.append(image_path)
                print(f"Ошибка валидации изображения {image_path}: {str(e)}")
        
        return invalid_files 