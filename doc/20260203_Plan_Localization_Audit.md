# Localization Audit & Fix Plan (v2.2+)

## 1. 发现的问题 (Identified Issues)
在代码审查中，发现以下日志信息直接使用了硬编码的 F-String，导致切换语言时仍显示英文，且不符合国际化规范。

### A. `ui/main_window.py`
| 行号 | 原始内容 | 建议 Key |
| :--- | :--- | :--- |
| **262** | `f"Theme changed to {new_theme}"` | `log_theme_changed` |
| **493** | `f"Language changed to {lang}"` | `log_lang_changed` |
| **389** | `f"Error Timer {idx+1}: {str(e)}"` | `error_timer_generic` |
| **541** | `f"Error loading config: {str(e)}"` | `error_config_load_generic` |

### B. `core/timer_engine.py`
| 行号 | 原始内容 | 建议 Key |
| :--- | :--- | :--- |
| **139** | `f"Error Timer {t_no}: {msg}"` | `error_timer_generic` (复用) |

---

## 2. 修复方案 (Fix Proposal)

### 步骤 1: 更新 `assets/language.ini`
在 `[中文]` 和 `[English]` 两个 Section 中补充缺失的键值对。

**[中文]**
```ini
log_theme_changed = 主题已切换为 {theme}
log_lang_changed = 语言已切换为 {lang}
error_timer_generic = 定时器 {timer_no} 错误: {error}
error_config_load_generic = 加载配置出错: {error}
```

**[English]**
```ini
log_theme_changed = Theme changed to {theme}
log_lang_changed = Language changed to {lang}
error_timer_generic = Error Timer {timer_no}: {error}
error_config_load_generic = Error loading config: {error}
```

### 步骤 2: 代码实现 (Implementation)

1.  **修改 `ui/main_window.py`**:
    -   将硬编码字符串替换为 `self.config.get_message(KEY, ...)` 调用。
2.  **修改 `core/timer_engine.py`**:
    -   在 Lambda 函数中注入 `config` 上下文（需要确认 `TimerEngine` 是否持有 `config`，经检查 line 117 已持有）。
    -   利用 `self.config.get_message` 格式化错误信息。

---

## 3. 风险评估
- **无风险**。纯文本替换，不涉及核心逻辑变更。

## 4. 等待指令
文档已生成。请输入 **'执行'** 以应用上述修复。
