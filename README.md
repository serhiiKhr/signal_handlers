## 🔧 Generating an `.exe` file

To generate an executable file, follow these steps:

1. **Generate `main.spec`**

   Run the following command once to let PyInstaller create a configuration file:

   ```
   pyinstaller --onefile --noconsole main.py
   ```

2. **Edit `main.spec`**

   Locate the `Analysis` block and add the required files to the `datas` section:

   ```
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


## 📘 Documentation for the `.json` Configuration File

This JSON file defines the configuration used for processing measurement files, performing signal analysis, saving statistics, and displaying graphs. Below is a detailed explanation of each field:

### 🔧 Top-Level Fields
```javascript
{
   "output_path": "C:/Desktop",              // Path to save the final output files.
   "source_program": "mera",                 // Identifier of the source program (e.g., "mera", "observe").
   "channels": ["ch1", "ch2", "ch3"],        //  List of channel names to be used globally unless overridden per file.
   "groups_settings": {                      // Grouping configuration for combined visualization or processing.
        "groups": [["ch1", "ch2"], ["ch3"]], // Lists of channel names grouped together for analysis/plotting.
        "single_image_group": false          // Whether to save groups into a single image or separately.
   },
   "stats_settings": {
        "save_stats": true,                  // Enable or disable statistics saving. 
        "output_file_path": ""               // Path to save the statistics file (optional if blank).
   },
   "show_graph": true,                       // Whether to display the resulting plots after processing.
   "method": {                               // Settings for the signal processing method (e.g., STFT).      
      "name": "stft",                        // Method name (e.g., `"stft"`).
      "nperseg": 1024,                       // Number of samples per segment. 
      "window": "hann",                      // Window function name (e.g., `"hann"`).
      "min_freq": 5,                         // Minimum frequency to include in analysis.
      "max_freq": 2000,                      // Maximum frequency to include in analysis.
      "overlap_percent": 50,                 // Percentage of overlap between segments.
      "min_display_freq": 50                 // Minimum frequency shown in the plot. 
   },
   // Each item in the `files` list represents a measurement file with optional overrides:
   "files": [                                // List of files to process, each with its own optional overrides. 
      {
         "file_path": "D:\\path\\to\\file",  // Path to the input measurement file.  
         "time_frames": [                    // List of named segments (optional). Each defines a time range to process. 
               // Override channel list for this file (optional).
               {
                  "name": "0.3",             // Display name for the segment.
                  "start_time": 0,           // Start time of the segment (in seconds).
                  "end_time": 110.1          // End time of the segment (in seconds).
               },  
               { "name": "MAX", "start_time": 900, "end_time": 1100 }
         ],
         "channels": ["ch4", "ch5", "ch6"],  // Override channel list for this file (optional).
         "groups_settings": {                // Override grouping configuration (optional).
               "groups": [
                  ["ch5", "ch6"], 
                  ["ch4"]
               ],
               "single_image_group": true
         }
      },
      {
         "file_path": "D:\\path\\to\\file",
         "show_graph": false,                // Whether to display the resulting plots after processing.
         "stats_settings": {                 // Override statistics settings (optional).
               "save_stats": true,
               "output_file_path": ""
         }
      },
      {
         "file_path": "D:\\path\\to\\file",
         "show_graph": true,
         "groups_settings": {
               "groups": []
         },
         "stats_settings": {
               "save_stats": true,
               "output_file_path": ""
         }
      }
   ]
}

```
**Important Notes:**

- If `groups_settings` is **not specified** in a file entry, the **global `groups_settings`** will be used as default.
- If you want to **exclude a file from grouping altogether**, you must explicitly set `"groups": []` in that file’s `groups_settings` — this prevents fallback to the global configuration.


## 📄 Prompt for JSON Configuration Generation
This repository supports JSON-based configuration for batch signal processing.
To simplify the generation of the JSON file, you can use a pre-defined prompt with ChatGPT.
Just copy and paste the prompt below into any ChatGPT session and describe your parameters in natural language.
ChatGPT will return a properly structured configuration file ready to use with this application.

```
Prompt (in English):

Generate a JSON configuration file for vibration data analysis. The structure is as follows:

Global parameters:

output_path: D:\results\output

source_program: "mera"

channels: ["Xпп", "Yпп", "Zпп"]

groups_settings:
{
  "groups": [],
  "single_image_group": false
}
show_graph: false

stats_settings:
{
  "save_stats": true,
  "output_file_path": "D:\\results"
}
method:
{
  "name": "stft",
  "nperseg": 1024,
  "window": "hann",
  "min_freq": 5,
  "max_freq": 2000,
  "overlap_percent": 50,
  "min_display_freq": 100
}
Files:
Add one file with the following parameters:

file_path: D:\path\to\file

time_frames: one segment from 60 to 600 seconds with an auto-generated name, e.g., "file_1m_to_10m"

channels: same as global

groups_settings: same as global

show_graph: false

stats_settings: same as global

⚠️ Important: Do not include any comments in the resulting JSON. The output must be valid JSON.
```