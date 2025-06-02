import zipfile
import re
from typing import Dict, List
from dataclasses import dataclass
import xml.etree.ElementTree as ET
import os

@dataclass
class StyleProcessingResult:
    processed_styles: Dict[str, str] = None  # путь к файлу -> обработанный CSS
    total_styles: int = 0
    optimized_size: int = 0  # размер после оптимизации в байтах
    original_size: int = 0   # исходный размер в байтах

    def __post_init__(self):
        if self.processed_styles is None:
            self.processed_styles = {}

class StyleProcessor:
    def __init__(self, epub_path: str):
        self.epub_path = epub_path
        self.ns = {
            'opf': 'http://www.idpf.org/2007/opf'
        }

    def _get_style_files(self) -> List[str]:
        """Получает список CSS файлов из EPUB"""
        try:
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                # Находим файл OPF
                container = epub.read('META-INF/container.xml')
                root = ET.fromstring(container)
                
                # Убедитесь, что пространства имен обрабатываются правильно
                namespaces = {'opf': 'http://www.idpf.org/2007/opf', 'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                rootfile = root.find('.//container:rootfile', namespaces)
                
                if rootfile is None:
                    print("Ошибка: Не найден rootfile в META-INF/container.xml")
                    return []
                    
                opf_path = rootfile.get('full-path')
                
                if opf_path is None:
                     print("Ошибка: Не найден full-path в rootfile в META-INF/container.xml")
                     return []
                
                # Читаем OPF файл
                opf_content = epub.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                
                # Ищем все CSS файлы в манифесте, используя пространства имен
                manifest = opf_root.find('.//opf:manifest', namespaces)
                style_files = []
                
                if manifest is not None:
                    for item in manifest.findall('.//opf:item', namespaces):
                        if item.get('media-type') == 'text/css':
                            # Получаем полный путь к файлу стиля относительно корня EPUB
                            style_file_path = os.path.join(os.path.dirname(opf_path), item.get('href', '')).replace('\\', '/')
                            style_files.append(style_file_path)
                else:
                     print(f"Warning: Манифест в OPF файле ({opf_path}) не найден.")
                
                return style_files
        except KeyError:
             print("Ошибка: Не найден container.xml или OPF файл в архиве EPUB.")
             return []
        except Exception as e:
            print(f"Ошибка при получении списка стилей: {str(e)}")
            return []

    def _optimize_css(self, css_content: str) -> str:
        """Оптимизирует CSS код"""
        try:
            # Удаляем комментарии
            css = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
            
            # Удаляем лишние пробелы и переносы строк
            css = re.sub(r'\s+', ' ', css)
            
            # Удаляем пробелы перед и после { } : ;
            css = re.sub(r'\s*([{}:;])\s*', r'\1', css)
            
            # Удаляем последнюю точку с запятой в блоке
            css = re.sub(r';}', '}', css)
            
            return css.strip()
        except Exception as e:
            print(f"Ошибка при оптимизации CSS: {str(e)}")
            return css_content

    def process_styles(self) -> StyleProcessingResult:
        """Обрабатывает все CSS файлы в EPUB"""
        result = StyleProcessingResult()
        
        try:
            style_files = self._get_style_files()
            if not style_files:
                print("CSS файлы не найдены в манифесте.")
                return result
            
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                for style_file in style_files:
                    try:
                        # Читаем CSS файл
                        content = epub.read(style_file)
                        original_size = len(content)
                        result.original_size += original_size
                        
                        # Декодируем и оптимизируем
                        css_text = content.decode('utf-8')
                        optimized_css = self._optimize_css(css_text)
                        
                        # Сохраняем результат только если файл успешно обработан
                        result.processed_styles[style_file] = optimized_css
                        result.optimized_size += len(optimized_css.encode('utf-8'))
                        
                    except KeyError:
                         print(f"Warning: Файл стиля {style_file} указан в манифесте, но не найден в архиве EPUB.")
                    except Exception as e:
                        print(f"Ошибка при обработке стиля {style_file}: {str(e)}")
            
            result.total_styles = len(result.processed_styles)
            return result
            
        except Exception as e:
            print(f"Критическая ошибка при обработке стилей: {str(e)}")
            return result 