# Flow Track v2.2 - Zero-Latency Editor, Single Instance & Localization

🎉 **What's New**

### 🚀 V6 Zero-Latency Editor
- **Independent Window Architecture**: The text editor has been completely re-engineered as an independent pop-up (V6). Typing is now buttery smooth with **0ms latency**, detached from the main UI thread.
- **Smart Text Alignment**: No more scrolling fatigue. Long text automatically scrolls back to the start (**Auto-Home**) when you finish editing or when the app loads, ensuring a clean and readable view.

### 🛡️ Robust System Architecture
- **Single Instance Lock**: Introduced a **Windows Kernel-Level Mutex** mechanism. Repeatedly clicking the app icon is now safe—it strictly prevents duplicate processes, ensuring your scheduled tasks never conflict.
- **100% Localization Coverage**: We conducted a full codebase audit. Every single log entry, error message, and tooltip now supports strict **Chinese/English** switching without any hardcoded leftovers.

### ✨ UI/UX Refinements
- **Smooth Theme Animations**: The Sun/Moon toggle button now features fluid rotational animations when switching modes.
- **Visual Stability**: Fixed scrollbar discrepancies and optimized the layout for the new independent editor window.

---
*Recommended: This is a critical update for stability and performance. Please close any running instances before installing.*
