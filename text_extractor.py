from dataclasses import dataclass
import zipfile
import xml.etree.ElementTree as ET
import re

@dataclass
class TextExtractionResult:
    text: str = ""
    encoding: str = "utf-8"

class TextExtractor:
    def extract_text(self, epub_path: str) -> TextExtractionResult:
        """Извлекает текст из EPUB файла"""
        result = TextExtractionResult()
        
        try:
            with zipfile.ZipFile(epub_path, 'r') as epub:
                # Находим файл OPF
                container = epub.read('META-INF/container.xml')
                root = ET.fromstring(container)
                opf_path = root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile').get('full-path')
                
                # Читаем OPF файл
                opf_content = epub.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                
                # Находим все XHTML файлы
                manifest = opf_root.find('.//{http://www.idpf.org/2007/opf}manifest')
                if manifest is not None:
                    text_content = []
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
                                            result.encoding = encoding
                                            break
                                        except UnicodeDecodeError:
                                            continue
                                    
                                    if text is None:
                                        raise UnicodeDecodeError("Не удалось декодировать текст")
                                    
                                    # Удаляем HTML теги и лишние пробелы
                                    text = re.sub(r'<[^>]+>', ' ', text)
                                    text = re.sub(r'\s+', ' ', text).strip()
                                    text_content.append(text)
                                except Exception as e:
                                    print(f"Ошибка при обработке файла {file_path}: {str(e)}")
                    
                    result.text = '\n'.join(text_content)
        
        except Exception as e:
            print(f"Ошибка при извлечении текста: {str(e)}")
            raise
        
        return result 