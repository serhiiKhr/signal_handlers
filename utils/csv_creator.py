import pandas as pd

def save_data_to_csv(file_path, datarows):
    df = pd.DataFrame(datarows).set_index('filename')
    
    # Aligning the "filename" column by width
    max_filename_length = max(df.index.str.len())  # Find the maximum length of the filename
    df.index = df.index.str.ljust(max_filename_length)  # Add spaces to the filenames to align them
    
    # Align the remaining columns by width
    max_lengths = {col: max(df[col].apply(lambda x: len(str(x)))) for col in df.columns}  # Maximum length for each column
    max_lengths = {col: max(max_lengths[col], len(col)) for col in df.columns}  # Take into account the length of the headers
    
    if file_path:
        # Save the file with indents as delimiters
        with open(file_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"{'filename':<{max_filename_length}}")
            f.write('\t' + '\t'.join([f"{col:<{max_lengths[col]}}" for col in df.columns]) + '\n')
            # Data
            for index, row in df.iterrows():
                f.write(f"{index:<{max_filename_length}}")
                f.write('\t' + '\t'.join([f"{str(val):<{max_lengths[col]}}" for val, col in zip(row, df.columns)]) + '\n')
        print(f"Файл сохранен по пути: {file_path}")
    else:
        print("Сохранение отменено.")
