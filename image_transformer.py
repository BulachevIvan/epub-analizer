import os
from PIL import Image, ImageEnhance, ImageOps

def apply_pixelate(image_path: str, output_path: str, pixelate_factor: int = 10):
    """Применяет пикселизацию к изображению."""
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        new_width = int(img.width / pixelate_factor)
        new_height = int(img.height / pixelate_factor)
        # Уменьшаем изображение
        img = img.resize((new_width, new_height), resample=Image.NEAREST)
        # Увеличиваем обратно с тем же режимом для эффекта пикселизации
        img = img.resize((img.width * pixelate_factor, img.height * pixelate_factor), Image.NEAREST)
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Ошибка при пикселизации изображения {image_path}: {e}")
        return None

def apply_contrast(image_path: str, output_path: str, contrast_factor: float = 2.0):
    """Применяет контраст к изображению."""
    try:
        img = Image.open(image_path)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast_factor)
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Ошибка при применении контраста к изображению {image_path}: {e}")
        return None

def apply_mirror(image_path: str, output_path: str):
    """Применяет зеркальное отражение к изображению."""
    try:
        img = Image.open(image_path)
        img = ImageOps.mirror(img)
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Ошибка при применении зеркального отражения к изображению {image_path}: {e}")
        return None

def apply_grayscale(image_path: str, output_path: str):
    """Преобразует изображение в черно-белый формат."""
    try:
        img = Image.open(image_path)
        img = img.convert('L') # Преобразование в оттенки серого (L-mode)
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Ошибка при преобразовании в черно-белый {image_path}: {e}")
        return None 