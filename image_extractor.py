import os
import zipfile
from PIL import Image
from io import BytesIO
from dataclasses import dataclass, field
from typing import List, Optional
import xml.etree.ElementTree as ET
from pathlib import Path

@dataclass
class ImageExtractionResult:
    count: int = 0
    output_dir: str = ""
    extracted_image_paths: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.extracted_image_paths is None:
            self.extracted_image_paths = []

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
                # Убедитесь, что пространства имен обрабатываются правильно
                namespaces = {'opf': 'http://www.idpf.org/2007/opf', 'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                rootfile = root.find('.//container:rootfile', namespaces)
                
                if rootfile is None:
                    raise ValueError("Не найден rootfile в container.xml")
                    
                opf_path = rootfile.get('full-path')
                
                if opf_path is None:
                    raise ValueError("Не найден full-path в rootfile")
                
                # Читаем OPF файл
                opf_content = epub.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                
                # Находим все изображения в манифесте
                manifest = opf_root.find('.//opf:manifest', namespaces)
                if manifest is not None:
                    for item in manifest.findall('.//opf:item', namespaces):
                        if item.get('media-type', '').startswith('image/'):
                            file_path = item.get('href')
                            if file_path:
                                try:
                                    # Получаем полный путь к файлу относительно корня EPUB
                                    full_path_in_epub = os.path.join(os.path.dirname(opf_path), file_path).replace('\\', '/')
                                    
                                    # Извлекаем изображение
                                    image_data = epub.read(full_path_in_epub)
                                    
                                    # Генерируем имя файла для сохранения, сохраняя расширение
                                    original_filename = os.path.basename(file_path)
                                    output_path = os.path.join(self.output_dir, original_filename)
                                    
                                    # Сохраняем изображение
                                    with open(output_path, 'wb') as f:
                                        f.write(image_data)
                                    
                                    result.extracted_image_paths.append(output_path)
                                    result.count += 1
                                except KeyError:
                                     print(f"Warning: Изображение {full_path_in_epub} не найдено в архиве.")
                                except Exception as e:
                                    print(f"Ошибка при извлечении изображения {file_path}: {str(e)}")
        
        except FileNotFoundError:
            print(f"Ошибка: EPUB файл не найден по пути {self.epub_path}")
            raise
        except zipfile.BadZipFile:
             print(f"Ошибка: Файл {self.epub_path} не является корректным ZIP архивом (EPUB).")
             raise
        except Exception as e:
            print(f"Ошибка при извлечении изображений: {str(e)}")
            raise
        
        return result

    def validate_images(self, result: ImageExtractionResult) -> List[str]:
        """Проверяет извлеченные изображения на валидность"""
        invalid_files = []
        
        for image_path in result.extracted_image_paths:
            try:
                with Image.open(image_path) as img:
                    img.verify()
            except Exception as e:
                invalid_files.append(image_path)
                print(f"Ошибка валидации изображения {image_path}: {str(e)}")
        
        return invalid_files 