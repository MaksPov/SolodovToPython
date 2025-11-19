#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import tempfile
import shutil
import time
from PyPDF2 import PdfMerger

def extract_lab_number(filename):
    """Извлекает номер лабораторной работы из имени файла"""
    # Ищем паттерн "Работа X" или "работа X"
    match = re.search(r'[Рр]абота\s+(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0

def get_lab_files(results_dir):
    """Получает список лабораторных работ и сортирует их по номеру"""
    lab_files = []
    
    for filename in os.listdir(results_dir):
        if filename.startswith('+Лабораторная') and filename.endswith('.docx'):
            filepath = os.path.join(results_dir, filename)
            lab_num = extract_lab_number(filename)
            lab_files.append((lab_num, filepath, filename))
    
    # Сортируем по номеру
    lab_files.sort(key=lambda x: x[0])
    return lab_files

def convert_docx_to_pdf(docx_path, pdf_path):
    """Конвертирует DOCX в PDF используя LibreOffice"""
    try:
        # Используем LibreOffice в headless режиме для конвертации
        # LibreOffice создает PDF в указанной директории
        outdir = os.path.dirname(pdf_path)
        cmd = [
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', outdir,
            docx_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # LibreOffice создает PDF с тем же именем, но расширением .pdf
        # Имя файла берется из исходного файла
        source_filename = os.path.basename(docx_path)
        pdf_filename = os.path.splitext(source_filename)[0] + '.pdf'
        expected_pdf = os.path.join(outdir, pdf_filename)
        
        # Небольшая задержка, чтобы файл успел записаться на диск
        time.sleep(0.5)
        
        # Проверяем, создан ли файл в указанной директории
        if os.path.exists(expected_pdf):
            # Перемещаем в нужное место, если имена не совпадают
            if expected_pdf != pdf_path:
                shutil.move(expected_pdf, pdf_path)
            return True
        
        # Попробуем найти PDF в директории исходного файла
        alt_pdf = os.path.splitext(docx_path)[0] + '.pdf'
        if os.path.exists(alt_pdf):
            shutil.move(alt_pdf, pdf_path)
            return True
        
        # Попробуем найти в текущей директории
        if os.path.exists(pdf_filename):
            shutil.move(pdf_filename, pdf_path)
            return True
        
        print(f"Ошибка: PDF файл не был создан для {docx_path}")
        print(f"Ожидался: {expected_pdf}")
        print(f"Альтернативный путь: {alt_pdf}")
        if result.stdout:
            print(f"Вывод: {result.stdout}")
        if result.stderr and "Warning" not in result.stderr:
            print(f"Ошибки: {result.stderr}")
        return False
            
    except subprocess.TimeoutExpired:
        print(f"Таймаут при конвертации {docx_path}")
        return False
    except Exception as e:
        print(f"Ошибка при конвертации {docx_path}: {e}")
        return False

def merge_pdfs(pdf_files, output_path):
    """Объединяет несколько PDF файлов в один"""
    merger = PdfMerger()
    
    for pdf_path in pdf_files:
        if os.path.exists(pdf_path):
            print(f"Добавляю: {os.path.basename(pdf_path)}")
            merger.append(pdf_path)
        else:
            print(f"Предупреждение: файл не найден {pdf_path}")
    
    merger.write(output_path)
    merger.close()
    print(f"Объединенный PDF сохранен: {output_path}")

def main():
    # Пути
    results_dir = "/media/maskpov/Povarov_IVT44u/СЕМЕСТР 3/МЗЯП/SolodovToPython/results"
    pdf_dir = "/media/maskpov/Povarov_IVT44u/СЕМЕСТР 3/МЗЯП/SolodovToPython/results/pdf"
    output_pdf = os.path.join(pdf_dir, "Объединенные_лабораторные_работы.pdf")
    
    # Создаем временную папку для промежуточных PDF
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Получаем список лабораторных работ
        lab_files = get_lab_files(results_dir)
        
        if not lab_files:
            print("Лабораторные работы не найдены!")
            return
        
        print(f"Найдено лабораторных работ: {len(lab_files)}")
        print("Порядок обработки:")
        for lab_num, filepath, filename in lab_files:
            print(f"  {lab_num}. {filename}")
        
        # Конвертируем каждый DOCX в PDF
        pdf_files = []
        for lab_num, docx_path, filename in lab_files:
            print(f"\nКонвертирую: {filename}")
            pdf_filename = os.path.splitext(filename)[0] + '.pdf'
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            if convert_docx_to_pdf(docx_path, pdf_path):
                pdf_files.append(pdf_path)
            else:
                print(f"Ошибка при конвертации {filename}")
        
        if not pdf_files:
            print("Не удалось конвертировать ни одного файла!")
            return
        
        # Объединяем все PDF
        print(f"\nОбъединяю {len(pdf_files)} PDF файлов...")
        merge_pdfs(pdf_files, output_pdf)
        
        print(f"\nГотово! Объединенный файл: {output_pdf}")
        
    finally:
        # Удаляем временную папку
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()

