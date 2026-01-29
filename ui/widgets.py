from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRectF, QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
import qtawesome as qta

class SunMoonToggle(QCheckBox):
    def __init__(self, theme_name="Light", parent=None):
        super().__init__(parent)
        self.setFixedSize(62, 32)
        self.setCursor(Qt.PointingHandCursor)
        self._thumb_pos = 32.0 if theme_name == "Dark" else 2.0
        self.setChecked(theme_name == "Dark")
        
        # 动画设置 (修复版：显式绑定 TargetObject 和 PropertyName)
        self.anim = QPropertyAnimation(self)
        self.anim.setTargetObject(self)
        self.anim.setPropertyName(b"thumb_pos")
        self.anim.setDuration(400)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        # 颜色配置 (v3.0 Raised Effect)
        self._colors = {
            "light_track": QColor("#E2E8F0"),
            "dark_track": QColor("#2D3748"),
            "thumb": QColor("#26D07C"),
            "icon_inactive": QColor("#A0AEC0"),
            "highlight": QColor("#FFFFFF"), # 默认高亮
            "shadow": QColor("#CBD5E0")     # 默认阴影
        }
        self._sun_icon = None
        self._moon_icon = None

    def _update_3d_colors(self):
        """根据当前状态动态更新 3D 效果颜色。"""
        # 这里我们直接从 ThemeManager 拿或根据 isChecked 简单判断
        # 为了极速响应，我们在 paintEvent 实时算或缓存
        pass

    def get_thumb_pos(self):
        return self._thumb_pos

    def set_thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()

    # 标准化显式属性定义
    thumb_pos = Property(float, get_thumb_pos, set_thumb_pos)

    def checkStateSet(self):
        super().checkStateSet()
        if hasattr(self, 'anim'):
            self.anim.stop()
            self.anim.setStartValue(self._thumb_pos)
            self.anim.setEndValue(32.0 if self.isChecked() else 2.0)
            self.anim.start()

    def set_theme_state(self, theme_name):
        """智能同步：如果已经在进行正确的动画，则不强行覆盖位置。"""
        target_pos = 32.0 if theme_name == "Dark" else 2.0
        
        self.blockSignals(True)
        self.setChecked(theme_name == "Dark")
        self.blockSignals(False)

        if self.anim.state() == QPropertyAnimation.Running:
            if self.anim.endValue() == target_pos:
                return

        self._thumb_pos = target_pos
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self.isChecked())
        super().mouseReleaseEvent(event)

    def _draw_sun(self, p, center, r, color):
        """原生绘制太阳形状 (v3.3 简约圆环风格)"""
        p.save()
        p.setPen(QPen(color, 1.5))
        p.setBrush(Qt.NoBrush)
        
        # 1. 绘制太阳的中心圆环 (r-1 使其视觉更饱满)
        p.drawEllipse(center, r-1, r-1) 
        
        # 2. 绘制 8 条发散的太阳光芒
        p.translate(center)
        for _ in range(8):
            p.drawLine(0, -r, 0, -r-2) # 调整长度使其更雅致
            p.rotate(45)
        p.restore()

    def _ensure_icons(self):
        # 仅保留月亮图标 Pixmap，太阳改为原生绘制
        if self._moon_icon is None:
            try:
                self._moon_icon = qta.icon('fa5s.moon', color='#FFFFFF').pixmap(16, 16)
            except:
                pass

    def paintEvent(self, event):
        from PySide6.QtGui import QLinearGradient
        self._ensure_icons()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        is_dark = self.isChecked()
        rect = self.rect().toRectF()
        
        # --- 3.3 物理化单层绘图 (Physical Single-Layer v3.3) ---
        # 核心：不再使用任何外部偏移图层，所有光影通过内部渐变实现
        if is_dark:
            base_color = self._colors["dark_track"]
            # Dark 模式：微调暗部，使其更通透 (darker 103 instead of 105)
            top_color = base_color.lighter(110)
            bottom_color = base_color.darker(103)
        else:
            base_color = self._colors["light_track"]
            # Light 模式：略微加深对比度，使 3D 边缘更加分明
            top_color = QColor("#FFFFFF")
            bottom_color = QColor("#DDE2E8")

        # 1. 直接绘制轨道主体
        # 统一使用线性渐变，从 (0,0) 到 (0, height)
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        grad.setColorAt(0, top_color)     # 顶部 1px 亮缘
        grad.setColorAt(0.1, base_color)  # 恢复到 10% 范围
        grad.setColorAt(0.9, base_color)  # 保持主色
        grad.setColorAt(1, bottom_color)  # 底部 1px 暗缘 (已调亮)
        
        p.setPen(Qt.NoPen)
        p.setBrush(grad)
        # 绘制唯一的背景矩形，由于没有了偏移层，底部绝不会出现异常亮缝
        p.drawRoundedRect(rect, 16, 16)

        # 2. 绘制辅助图标 (背景层)
        if self._moon_icon:
            # 右侧(月)
            p.setOpacity(0.3 if not is_dark else 1.0)
            p.drawPixmap(40, 8, 16, 16, self._moon_icon)
            # 左侧(日) - 使用原生绘制，颜色为灰色模拟不活跃
            p.setOpacity(0.3 if is_dark else 1.0)
            self._draw_sun(p, rect.topLeft() + QPointF(14, 16), 5, QColor("#FFFFFF"))
        
        # 3. 绘制滑块 (Thumb) - v3.4 增大饱满度
        p.setOpacity(1.0)
        p.setPen(Qt.NoPen)
        
        # 直径从 24 增至 28，垂直偏移从 4px 减至 2px，更贴合边界
        thumb_rect = QRectF(self._thumb_pos, 2, 28, 28)
        
        # Thumb 投影 (精细化：仅向下偏移 1px)
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawEllipse(thumb_rect.translated(0, 1)) 
        
        # Thumb 主体：采用与轨道类似的渐变，增强立体圆度
        t_grad = QLinearGradient(thumb_rect.topLeft(), thumb_rect.bottomLeft())
        t_grad.setColorAt(0, self._colors["thumb"].lighter(105))
        t_grad.setColorAt(1, self._colors["thumb"].darker(110))
        p.setBrush(t_grad)
        p.drawEllipse(thumb_rect)
        
        # Thumb 顶部微型高光圈
        p.setPen(QPen(QColor(255, 255, 255, 100), 1))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(thumb_rect.adjusted(0.5, 0.5, -0.5, -0.5))

        # 4. 滑块上方图标 (前景层)
        p.setPen(Qt.NoPen)
        p.setOpacity(1.0)
        if is_dark and self._moon_icon:
            icon_rect = thumb_rect.adjusted(4, 4, -4, -4).toRect()
            p.drawPixmap(icon_rect, self._moon_icon)
        elif not is_dark:
            # 活跃状态的太阳，颜色为白色
            self._draw_sun(p, thumb_rect.center(), 5, QColor("#FFFFFF"))
        
        p.end()
