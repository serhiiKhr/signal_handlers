import pandas as pd

def save_data_to_csv(file_path, datarows):
    df = pd.DataFrame(datarows).set_index('filename')
    
    # Выравнивание столбца "filename" по ширине
    max_filename_length = max(df.index.str.len())  # Находим максимальную длину имени файла
    df.index = df.index.str.ljust(max_filename_length)  # Добавляем пробелы к файлам, чтобы они выровнялись
    
    # Выравнивание остальных столбцов по ширине
    max_lengths = {col: max(df[col].apply(lambda x: len(str(x)))) for col in df.columns}  # Максимальная длина по каждому столбцу
    max_lengths = {col: max(max_lengths[col], len(col)) for col in df.columns}  # Учитываем длину заголовков
    
    if file_path:
        # Сохраняем файл с отступами в качестве разделителей
        with open(file_path, 'w', encoding='utf-8') as f:
            # Заголовок
            f.write(f"{'filename':<{max_filename_length}}")
            f.write('\t' + '\t'.join([f"{col:<{max_lengths[col]}}" for col in df.columns]) + '\n')
            # Данные
            for index, row in df.iterrows():
                f.write(f"{index:<{max_filename_length}}")
                f.write('\t' + '\t'.join([f"{str(val):<{max_lengths[col]}}" for val, col in zip(row, df.columns)]) + '\n')
        print(f"Файл сохранен по пути: {file_path}")
    else:
        print("Сохранение отменено.")
