## 🔧 Generating an `.exe` file

To generate an executable file, follow these steps:

1. **Generate `main.spec`**

   Run the following command once to let PyInstaller create a configuration file:

   ```
   pyinstaller --onefile --noconsole main.py
   ```

2. **Edit `main.spec`**

   Locate the `Analysis` block and add the required files to the `datas` section:

   ```python
   datas=[
       ('translations.json', '.'),
       (r'To\DWDataReaderLib64.dll', 'dwdatareader')
   ],
   ```

3. **Build the `.exe` using `main.spec`**

   Run:

   ```
    pyinstaller main.spec
   ```

After completing these steps, the executable file will appear in the `dist/` folder.
