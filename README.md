# Flow Track

[中文文档](README_CN.md)

> **Capture moments, automate rhythms.**

Flow Track is a lightweight, high-precision desktop automation utility. It empowers users to preset a sequence of click and text-pasting tasks at exact timestamps, freeing your hands from repetitive manual operations.

![Software Preview](assets/v1.0_ui_preview.png)

## ✨ Key Features

- **Precise Scheduling**: Supports second-level configuration, ensuring tasks trigger exactly at the preset time.
- **Smart Coordinate Picker**: Built-in coordinate detection to capture target positions instantly.
- **Task Sequence Flow**: Add unlimited task rows to combine clicks, delays, desktop showing, and more.
- **Local Config Persistence**: Automatically saves your last settings to the `config/` directory.
- **Zero-Dependency Bundle**: Application icon and language files are fully embedded. Run the single EXE file anywhere without external assets.

## 🚀 Quick Start

### Run the Binary
1. Download the latest release package.
2. Launch `dist/flow_track.exe`.
3. If running for the first time, it will automatically create a `config/` folder for your settings.

### Run from Source (Python)
1. Ensure Python 3.9+ is installed.
2. Install dependencies:
   ```bash
   pip install pywin32 pyperclip
   ```
3. Start the application:
   ```bash
   python flow_track.py
   ```

## 🛠️ Build Instructions

This project uses PyInstaller for single-file packaging. Run the following command to generate a standalone EXE:

```bash
pyinstaller flow_track.spec --noconfirm
```

## 📄 License
This project is licensed under the [MIT](LICENSE) License.
