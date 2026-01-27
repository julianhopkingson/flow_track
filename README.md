# Flow Track

[中文文档](README_CN.md)

> **Capture moments, automate rhythms.**

Flow Track is a lightweight, high-precision desktop automation utility. It empowers users to preset a sequence of click and text-pasting tasks at exact timestamps, freeing your hands from repetitive manual operations.

![Software Preview](assets/v2.0_ui_preview.png)

## ✨ Key Features

- **Precise Scheduling**: Uses high-fidelity 3-spinbox time inputs (HH:MM:SS) for intuitive and accurate scheduling.
- **Smart Coordinate Picker**: Built-in coordinate detection to capture target positions instantly.
- **Task Sequence Flow**: Unlimited task rows with advanced "Copy Settings" logic (auto-incrementing seconds) for rapid task creation.
- **Show Desktop Mode**: Dedicated one-click desktop toggle with smart field locking to prevent interaction conflicts.
- **Local Config Persistence**: Automatically saves your last settings to the `config/` directory, including window position and custom timers.
- **Visual Feedback System**: Neumorphic UI design with high-contrast active inputs and dynamic button states for clear operation visibility.
- **Robust Field Interactions**: Intelligent focus-lock and wheel-event interception to prevent accidental data changes during list scrolling.
- **Zero-Dependency Bundle**: Fully embedded assets with standardized `main.spec` configuration for consistent builds.

## 🚀 Quick Start

### Run the Binary
1. Download the latest release package.
2. Launch `dist/flow_track.exe`.
3. If running for the first time, it will automatically create a `config/` folder for your settings.

### Run from Source (Python)
1. Ensure Python 3.9+ is installed.
2. Install dependencies:
   ```bash
   pip install PySide6 qtawesome pywin32 pyperclip
   ```
3. Start the application:
   ```bash
   python main.py
   ```

## 🛠️ Build Instructions

This project uses PyInstaller for single-file packaging. Run the following command to generate a standalone EXE:

```bash
pyinstaller main.spec --clean --noconfirm
```

## 📄 License
This project is licensed under the [MIT](LICENSE) License.
