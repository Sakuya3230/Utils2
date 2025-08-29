# -*- coding: utf-8 -*-

import maya.cmds as cmds
import maya.api.OpenMaya as om2

try:
    from PySide6 import QtWidgets, QtGui, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtGui, QtCore
    
import json

# ---------------------------------------------------------------------------------- #
# COMMON
# ---------------------------------------------------------------------------------- #
def get_font():
    app = QtWidgets.QApplication.instance()
    return app.font()
    # print(f"フォント名: {default_font.family()}, サイズ: {default_font.pointSize(), default_font.pixelSize()}")

# ----------------------------------------------------------------------------------
# 展開・折りたたみ可能なウィジェット
# ----------------------------------------------------------------------------------
class CollapsibleFrame(QtWidgets.QWidget):
    toggled = QtCore.Signal(bool)  # 展開/折りたたみ時に発信されるシグナル

    kAlignLeft      = 0
    kAlignRight     = 1
    kAlignCenter    = 2
    
    kDefault        = 0
    kSolid          = 1
    kRounded        = 2
    kDashed         = 3
    
    kTriangle       = 0
    kArrow          = 1
    kPlusMinus      = 2
    kCircle         = 3

    # override method
    def __init__(self, title="Title", color=QtGui.QColor(187, 187, 187), parent=None):
        super(CollapsibleFrame, self).__init__(parent)
        self._title                 = title
        self._title_color           = color
        self._title_alignment       = self.kAlignLeft
        self._title_bar_color       = QtGui.QColor(93, 93, 93)
        self._title_bar_height      = 20
        self._icon_color            = QtGui.QColor(238, 238, 238)
        self._icon_alignment        = self.kAlignLeft
        self._icon_style            = self.kTriangle
        self._frame_style           = self.kDefault
        self._rotation_angle        = 0
        
        self._is_collapsed          = False
        self._is_collapsable        = True
        self._is_title_visible      = True
        self._is_icon_visible       = True
        self._is_animation_enabled  = True
        
        self._frame_styles = {
            self.kDefault:      "#ContentFrame{border: none; background: rgb(255, 0, 0)}",
            self.kSolid:        "#ContentFrame{border: 2px solid gray;}",
            self.kRounded:      "#ContentFrame{border: 2px solid gray; border-radius: 6px;}",
            self.kDashed:       "#ContentFrame{border: 2px dashed gray;}",
        }
        
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        # メインレイアウト
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self._updateTitleBarHeight()

        # コンテンツフレーム
        self.frame = QtWidgets.QFrame(self)
        self.frame.setObjectName("ContentFrame")
        self._updateFrameStyle()
        self._frame_geometry = self.frame.geometry()

        # 内部レイアウト
        self.content_layout = QtWidgets.QVBoxLayout(self.frame)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(5)
        self.main_layout.addWidget(self.frame)

        # アニメーション
        self.frame_animation = QtCore.QPropertyAnimation(self.frame, b"geometry")
        # self.frame_animation = QtCore.QPropertyAnimation(self.frame, b"maximumHeight")
        self.frame_animation.setDuration(200)
        
        self.icon_animation = QtCore.QVariantAnimation()
        self.icon_animation.setDuration(200)
        self.icon_animation.valueChanged.connect(self._updateIconRotation)

    def mousePressEvent(self, event):
        """タイトルバーのクリックで展開・折りたたみ"""
        if event.pos().y() < self._title_bar_height and self._is_collapsable:
            self._toggle()

    def paintEvent(self, event):
        """カスタム描画（タイトルバー + 三角形アイコン）"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # タイトルバー描画
        painter.setBrush(self._title_bar_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(0, 0, self.width(), self._title_bar_height)

        # タイトル描画
        if self._is_title_visible:
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            font_metrics = QtGui.QFontMetrics(font)
            text_width = font_metrics.horizontalAdvance(self._title)
            
            # タイトル位置
            rect = self.rect()
            if self._title_alignment == self.kAlignLeft:
                if self._is_icon_visible and self._icon_alignment == self.kAlignLeft:
                    text_x = rect.left() + 25
                else:
                    text_x = rect.left() + 10
                
            elif self._title_alignment == self.kAlignRight:
                if self._is_icon_visible and self._icon_alignment == self.kAlignRight:
                    text_x = rect.right() - text_width - 25
                else:
                    text_x = rect.right() - text_width - 10
            else:
                text_x = rect.right() / 2 - text_width / 2 

            painter.setPen(self._title_color)
            text_rect = QtCore.QRect(text_x, 0, text_width, self._title_bar_height)
            painter.drawText(text_rect, QtCore.Qt.AlignVCenter, self._title)
        
        # アイコン描画
        if self._is_icon_visible:
            # アイコン位置
            if self._icon_alignment == self.kAlignLeft:
                icon_pos = QtCore.QPoint(10, self._title_bar_height / 2)
                
            elif self._icon_alignment == self.kAlignRight:
                icon_pos = QtCore.QPoint(self.width() - 10, self._title_bar_height / 2)

            else:
                if self._is_title_visible and self._title_alignment == self.kAlignCenter:
                    icon_pos = QtCore.QPoint(self.width() / 2 - text_width / 2 - 15, self._title_bar_height / 2)
                else:
                    icon_pos = QtCore.QPoint(self.width() / 2, self._title_bar_height / 2)

            if self._icon_style == self.kTriangle:
                self._drawTriangle(painter, icon_pos)
            elif self._icon_style == self.kArrow:
                self._drawArrow(painter, icon_pos)
            elif self._icon_style == self.kPlusMinus:
                self._drawPlusMinus(painter, icon_pos)
            elif self._icon_style == self.kCircle:
                self._drawCircle(painter, icon_pos)

    def resizeEvent(self, event):
        """ウィンドウのリサイズ時にフレームのジオメトリを更新"""
        super(CollapsibleFrame, self).resizeEvent(event)
        # レイアウト内のフレームのサイズを更新
        margin = 0
        width  = self.width() - 2 * margin
        height = self.height() - 2 * margin
        self.frame_geometry = QtCore.QRect(margin, margin + self._title_bar_height, width, height - self._title_bar_height)

    # public method
    def addWidget(self, widget):
        """コンテンツ領域にウィジェットを追加"""
        self.content_layout.addWidget(widget)

    def title(self):
        """タイトル名を返す
        Returns:
            string: タイトル名
        """        
        return self._title
    
    def titleColor(self):
        """タイトルのカラーを返す
        Returns:
            QtGui.QColor: 文字の色
        """        
        return self._title_color
    
    def titleAlignment(self):
        """タイトルの配置を返す

        Returns:
            int: kAlignLeft = 0 kAlignRight = 1 kAlignCenter = 2
        """        
        return self._title_alignment
    
    def titleVisible(self):
        """タイトルの表示状態を返す

        Returns:
            bool: 表示状態
        """   
        return self._is_title_visible
    
    def titleBarColor(self):
        """タイトルバーの背景色を返す

        Returns:
            QtGui.QColor: 背景色
        """        
        return self._title_bar_color
    
    def titleBarHeight(self):
        """タイトルバーの高さを返す

        Returns:
            int: タイトルバーの高さ
        """        
        return self._title_bar_height
    
    def iconColor(self):
        """アイコンのカラーを返す
        Returns:
            QtGui.QColor: アイコンの色
        """        
        return self._icon_color    
    
    def iconAlignment(self):
        """アイコンの配置を返す

        Returns:
            int: kAlignLeft = 0 kAlignRight = 1 kAlignCenter = 2
        """        
        return self._icon_alignment
    
    def iconStyle(self):
        """アイコンのスタイルを返す

        Returns:
            int: kTriangle = 0 kPlusMinus = 1
        """        
        return self._icon_style
    
    def iconVisible(self):
        """アイコンの表示状態を返す

        Returns:
            bool: 表示状態
        """   
        return self._is_icon_visible
    
    def frameStyle(self):
        """フレームのスタイルを返す

        Returns:
            int: kDefault = 0 kSolid = 1 kRounded = 2 kDashed = 3
        """        
        return self._frame_style
        
    def isCollapsed(self):
        """フレームが折りたたまれているかどうか

        Returns:
            bool: 折りたたみ状態
        """        
        return self._is_collapsed
    
    def isCollapsable(self):
        """折りたたみが有効化どうか

        Returns:
            bool: 有効化状態
        """        
        return self._is_collapsable
    
    def isAnimationEnabled(self):
        """アニメーションが有効化どうか

        Returns:
            bool: 有効化状態
        """        
        return self._is_animation_enabled
    
    def setTitle(self, title):
        """タイトルを変更する"""
        self._title = title
        self.update()

    def setTitleColor(self, color):
        """タイトルの文字の色を変更する"""
        self._title_color = color
        self.update()

    def setTitleAlignment(self, alignment):
        """タイトルの配置を変更 (0: kAlignLeft, 1: kAlignRight, 2: kAlignCenter)"""
        if alignment in [self.kAlignLeft, self.kAlignRight, self.kAlignCenter]:
            self._title_alignment = alignment
            self.update()
        
    def setTitleVisible(self, visible):
        """タイトルの表示・非表示を切り替える"""
        self._is_title_visible = visible
        self.update()
        
    def setTitleBarColor(self, color):
        """タイトルバーの背景色を変更"""
        self._title_bar_color = color
        self.update()

    def setTitleBarHeight(self, height):
        """タイトルバーの高さを変更 最小15px"""
        self._title_bar_height = max(15, height)
        self._updateTitleBarHeight()
        self.update()

    def setIconColor(self, color):
        """アイコンの色を変更する"""
        self._icon_color = color
        self.update()

    def setIconAlignment(self, alignment):
        """アイコンの配置を変更 (0: kAlignLeft, 1: kAlignRight, 2: kAlignCenter)"""
        if alignment in [self.kAlignLeft, self.kAlignRight, self.kAlignCenter]:
            self._icon_alignment = alignment
            self.update()
            
    def setIconStyle(self, style):
        """アイコンの配置を変更 (0: left, 1: kArrow, 2: kPlusMinus, 3: kCircle)"""
        if style in [self.kTriangle, self.kArrow, self.kPlusMinus, self.kCircle]:
            self._icon_style = style
            self.update()

    def setIconVisible(self, visible):
        """タイトルの表示・非表示を切り替える"""
        self._is_icon_visible = visible
        self.update()

    def setFrameStyle(self, style):
        """フレームのスタイルを変更"""
        if style in [self.kDefault, self.kSolid, self.kRounded, self.kDashed]:
            self._frame_style = style
            self._updateFrameStyle()

    def setCollapsedEnabled(self, enabled):
        """折りたたみの効化を変更"""
        self._is_collapsable = enabled

    def setAnimationEnabled(self, enabled):
        """アニメーション有効化を変更"""
        self._is_animation_enabled = enabled

    def setContentsMargins(self, x, y, width, height):
        self.content_layout.setContentsMargins(x, y, width, height)

    def setSpacing(self, spacing):
        self.content_layout.setSpacing(spacing)

    # private method
    def _updateTitleBarHeight(self):
        self.main_layout.setContentsMargins(0, self._title_bar_height, 0, 0)
    
    def _updateFrameStyle(self):
        """フレームデザインを適用"""
        self.frame.setStyleSheet(self._frame_styles.get(self._frame_style, "border: 2px solid gray;"))

    def _updateIconRotation(self, value):
        """アイコンの回転角度を更新"""
        self._rotation_angle = value
        self.update()

    def _getContentHeight(self):
        """レイアウト内のすべてのウィジェットの合計最小高さを取得"""
        margin = 5
        total_height = margin
        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            if item.widget():
                total_height += item.widget().minimumSizeHint().height() + margin
        return total_height

    def _toggle(self):
        """折りたたみ/展開を切り替え"""
        self._is_collapsed = not self._is_collapsed

        if self._is_animation_enabled:
            # 展開と折りたたみのアニメーション
            if self._is_collapsed:
                start_rect = QtCore.QRect(self.frame.geometry().x(), self.frame.geometry().y(), self.frame.width(), self.frame.height())
                end_rect = QtCore.QRect(self.frame.geometry().x(), self.frame.geometry().y(), self.frame.width(), 0)
                self.frame_animation.setStartValue(start_rect)
                self.frame_animation.setEndValue(end_rect)                
                # self.frame_animation.setStartValue(self.frame.height())
                # self.frame_animation.setEndValue(0)
                self.frame_animation.finished.connect(lambda *args: self.frame.setVisible(not self._is_collapsed))
            else:
                
                start_rect = QtCore.QRect(self.frame.geometry().x(), self.frame.geometry().y(), self.frame.width(), self.frame.height())
                end_rect = QtCore.QRect(self.frame.geometry().x(), self.frame.geometry().y(), self.frame.width(), max(self._getContentHeight(), self.frame.sizeHint().height(), self.height()-self._title_bar_height))
                self.frame_animation.setStartValue(start_rect)
                self.frame_animation.setEndValue(end_rect)
                
                # self.frame_animation.setStartValue(0)
                # self.frame_animation.setEndValue(max(self._getContentHeight(), self.frame_geometry.height()))
                self.frame.setVisible(not self._is_collapsed)

                
            self.frame_animation.start()
            
            # アイコン回転のアニメーション
            if self._icon_alignment == self.kAlignRight:
                start_angle = 0 if self._is_collapsed else 90
                end_angle = 90 if self._is_collapsed else 0
            else:
                start_angle = 0 if self._is_collapsed else -90
                end_angle = -90 if self._is_collapsed else 0
                
            self.icon_animation.setStartValue(start_angle)
            self.icon_animation.setEndValue(end_angle)
            self.icon_animation.start()
        else:
            self.frame.setVisible(not self._is_collapsed)
        
        self.toggled.emit(self._is_collapsed)
        self.update()

    def _drawTriangle(self, painter, center):
        """展開アイコン（三角形）の描画"""
        path = QtGui.QPainterPath()
        
        if self._is_animation_enabled:
            path.moveTo(center.x() - 5, center.y() - 4)
            path.lineTo(center.x() + 5, center.y() - 4)
            path.lineTo(center.x(), center.y() + 4)
            path.closeSubpath()
            
            transform = QtGui.QTransform()
            transform.translate(center.x(), center.y())
            transform.rotate(self._rotation_angle)
            transform.translate(-center.x(), -center.y())
            path = transform.map(path)
        else:
            if self._is_collapsed:
                path.moveTo(center.x() - 4, center.y() - 5)
                path.lineTo(center.x() - 4, center.y() + 5)
                path.lineTo(center.x() + 4, center.y())
            else:
                path.moveTo(center.x() - 5, center.y() - 4)
                path.lineTo(center.x() + 5, center.y() - 4)
                path.lineTo(center.x(), center.y() + 4)
        
        painter.setBrush(self._icon_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawPath(path)
        
    def _drawArrow(self, painter, center):
        """展開アイコン（矢印）の描画"""
        path = QtGui.QPainterPath()
        
        if self._is_animation_enabled:
            path.moveTo(center.x() - 5, center.y() - 2)
            path.lineTo(center.x(), center.y() + 3)
            path.lineTo(center.x() + 5, center.y() - 2)
            
            transform = QtGui.QTransform()
            transform.translate(center.x(), center.y())
            transform.rotate(self._rotation_angle)
            transform.translate(-center.x(), -center.y())
            path = transform.map(path)
        else:
            if self._is_collapsed:
                path.moveTo(center.x() - 2, center.y() - 5)
                path.lineTo(center.x() + 3, center.y())
                path.lineTo(center.x() - 2, center.y() + 5)
            else:
                path.moveTo(center.x() - 5, center.y() - 2)
                path.lineTo(center.x(), center.y() + 3)
                path.lineTo(center.x() + 5, center.y() - 2)

        pen = QtGui.QPen(self._icon_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawPath(path)
        
    def _drawPlusMinus(self, painter, center):
        """展開アイコン（プラス、マイナス）の描画"""
        path = QtGui.QPainterPath()

        if self._is_collapsed:
            path.moveTo(center.x() - 4, center.y())
            path.lineTo(center.x() + 4, center.y())
            path.moveTo(center.x(), center.y() - 5)
            path.lineTo(center.x(), center.y() + 5)
        else:
            path.moveTo(center.x() - 5, center.y())
            path.lineTo(center.x() + 5, center.y())

        path.closeSubpath()

        pen = QtGui.QPen(self._icon_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(0, 0, 0))
        painter.drawPath(path)

    def _drawCircle(self, painter, center):
        """展開アイコン（プラス、マイナス）の描画"""
        pen = QtGui.QPen(self._icon_color)
        pen.setWidth(2)
        painter.setPen(pen)

        if self._is_collapsed:
            painter.setBrush(self._icon_color)
        else:
            painter.setBrush(QtCore.Qt.NoBrush)

        painter.drawEllipse(center, 5, 5)

class ExampleApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        # タイトル変更処理
        def on_collapsed(collapsed):
            if collapsed:
                collapsible.setTitle("折りたたみ状態")
            else:
                collapsible.setTitle("展開状態")

        # ウィジェット作成
        collapsible = CollapsibleFrame("初期タイトル")
        collapsible.setFrameStyle(CollapsibleFrame.kDefault)
        
        for i in range(3):
            btn = QtWidgets.QPushButton("aaaaaaaaa")
            collapsible.addWidget(btn)
        
        collapsible1 = CollapsibleFrame("モデル")
        collapsible1.setIconStyle(CollapsibleFrame.kArrow)
        collapsible1.setFrameStyle(CollapsibleFrame.kSolid)
        collapsible1.setTitleAlignment(CollapsibleFrame.kAlignCenter)
        collapsible1.setIconAlignment(CollapsibleFrame.kAlignCenter)
        collapsible1.setTitleBarColor(QtGui.QColor(200, 200, 100))
        collapsible1.setTitleColor(QtGui.QColor(10, 10, 10))
        
        collapsible2 = CollapsibleFrame()
        collapsible2.setIconStyle(CollapsibleFrame.kPlusMinus)
        collapsible2.setFrameStyle(CollapsibleFrame.kRounded)
        collapsible2.setIconAlignment(CollapsibleFrame.kAlignCenter)
        collapsible2.setTitleVisible(False)
        collapsible2.setTitleBarColor(QtGui.QColor(100, 200, 200))
        collapsible2.setCollapsedEnabled(False)
        
        collapsible3 = CollapsibleFrame("アニメーション")
        collapsible3.setIconStyle(CollapsibleFrame.kCircle)
        collapsible3.setFrameStyle(CollapsibleFrame.kDashed)
        collapsible3.setTitleBarColor(QtGui.QColor(200, 0, 0))
        collapsible3.setTitleColor(QtGui.QColor(0, 0, 200))
        collapsible3.setTitleAlignment(CollapsibleFrame.kAlignRight)
        collapsible3.setIconAlignment(CollapsibleFrame.kAlignRight)
        
        
        # シグナルの接続
        collapsible.toggled.connect(on_collapsed)

        layout.addWidget(collapsible)
        layout.addWidget(collapsible1)
        layout.addWidget(collapsible2)
        layout.addWidget(collapsible3)
        #layout.addStretch()

# ----------------------------------------------------------------------------------
# カラーラベル
# ----------------------------------------------------------------------------------
class ColorLabel(QtWidgets.QWidget):
    def __init__(self, text, color=QtGui.QColor(255, 0, 0), parent=None):
        super(ColorLabel, self).__init__(parent)
        self._text          = text
        self._text_color    = QtGui.QColor(187, 187, 187)
        self._icon_size     = 10
        self._icon_color    = color
        self._margin        = 10
        self._font          = get_font()
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

    # override method
    def sizeHint(self):
        font_metrics = QtGui.QFontMetrics(self._font)
        text_width = font_metrics.width(self._text)
        return QtCore.QSize(self._icon_size + self._margin + text_width, max(self._icon_size, font_metrics.height()))
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # カラー矩形描画
        rect = QtCore.QRect(0, (self.height() - self._icon_size) // 2, self._icon_size, self._icon_size)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self._icon_color)
        painter.drawRect(rect)      
        
        # テキスト描画
        painter.setFont(self._font)
        text_x = self._icon_size + self._margin
        text_rect = QtCore.QRect(text_x, 0, self.width(), self.height())
        painter.setPen(self._text_color)
        painter.drawText(text_rect, QtCore.Qt.AlignVCenter, self._text)

    # public method
    def text(self):
        return self._text
    
    def textSize(self):
        return self.font.pointSize()
    
    def textColor(self):
        return self._text_color
    
    def iconSize(self):
        return self._icon_size

    def iconColor(self):
        return self._icon_color
    
    def margin(self):
        return self._margin
    
    def setText(self, text):
        self._text = text
        self.updateGeometry()
        self.update()
    
    def setTextSize(self, size):
        self._font.setPointSize(size)
        self.updateGeometry()
        self.update()
    
    def setTextColor(self, color):
        self._text_color = color
        self.update()
    
    def setIconSize(self, size):
        self._icon_size = size
        self.updateGeometry()
        self.update()
        
    def setIconColor(self, color):
        self._icon_color = color
        self.update()
    
    def setMargin(self, margin):
        self._margin = margin
        self.updateGeometry()
        self.update()

# ----------------------------------------------------------------------------------
# フローレイアウト
# ----------------------------------------------------------------------------------
class FlowLayout(QtWidgets.QLayout):
    def __init__(self, parent=None):
        super(FlowLayout, self).__init__(parent)
        self._items = []
        self._vertical_spacing = 5
        
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(5)
            
    # override method
    def addItem(self, item):
        self._items.append(item)
        
    def count(self):
        return len(self._items)
    
    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        height = self._do_layout(QtCore.QRect(0, 0, width, 0))
        return height

    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QtCore.QSize()
        
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
            
        margins = self.contentsMargins()
        size += QtCore.QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size
    
    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect)
    
    # public method
    def verticalSpacing(self):
        """アイテムの垂直の間隔

        Returns:
            int: 間隔
        """        
        return self._vertical_spacing
    
    def setVerticalSpacing(self, spacing):
        """アイテムの垂直の間隔を設定

        Args:
            spacing (int): 間隔
        """        
        self._vertical_spacing = spacing
        self.update()
    
    # private method
    def _do_layout(self, rect):
        """サイズによってアイテムを再配置

        Args:
            rect (QtCore.QRect): レイアウトサイズ
        """        
        if not self._items:
            return
        
        x = rect.x()
        y = rect.y()
        row_height = 0
        for item in self._items:
            widget = item.widget()
            size = widget.sizeHint()
            if x + size.width() > rect.right():
                x = rect.x()
                y += row_height + self._vertical_spacing
                row_height = 0
                
            item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), size))
            x += size.width() + self.spacing()
            row_height = max(row_height, size.height())
            
        return y + row_height - rect.y()

# ----------------------------------------------------------------------------------
# 数値スライダー
# ----------------------------------------------------------------------------------
class FloatSlider(QtWidgets.QWidget):
    sliderMoved = QtCore.Signal(float)
    sliderPressed = QtCore.Signal()
    sliderReleased = QtCore.Signal()
    valueChanged = QtCore.Signal(float)
    
    # override method
    def __init__(self, parent=None):
        super(FloatSlider, self).__init__(parent)
        self.setMinimumHeight(20)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self._set_line_edit()
        
        self._value = 0.5
        self._maximum = 1.0
        self._minimum = 0.0
        self._single_step  = 0.001
        self._decimals = 3
        
        self._color = QtGui.QColor(71, 114, 179)
        self._text_color = QtGui.QColor(230, 230, 230)
        self._background_color = QtGui.QColor(84, 84, 84)
        
        self._pressed = False
        self._pressed_button = QtCore.Qt.NoButton
        self._moved = False
        self._hovered = False

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._pressed = True
            self._pressed_button = QtCore.Qt.LeftButton
            self.sliderPressed.emit()
            self.update()

    def mouseMoveEvent(self, event):
        if self._pressed_button == QtCore.Qt.LeftButton:
            self._moved = True
            self.setCursor(QtCore.Qt.BlankCursor)
            rect = self.rect()
            slider_range = self._maximum - self._minimum
            pos = max(0, min(rect.width(), event.x() - rect.x()))
            value = self._minimum + (float(pos) / float(rect.width())) * slider_range
            
            if self._single_step > 0:
                self._value = round(round(value / self._single_step) * self._single_step, self._decimals)

            self.sliderMoved.emit(self._value)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._pressed = False
            self._pressed_button = QtCore.Qt.NoButton
            # スライダーが動かなかった場合に入力切り替え
            if not self._moved:
                self._activate_edit_mode()
            else:
                self.valueChanged.emit(self._value)
            self._moved = False
            self.unsetCursor()
            self.sliderReleased.emit()
            self.update()

    def enterEvent(self, event):
        """マウスがウィジェットに入ったとき"""
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        """マウスがウィジェットから離れたとき"""
        self._hovered = False
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.begin(self)
        rect = self.rect()

        # 背景
        if self._pressed:
            painter.setBrush(QtGui.QColor(34, 34, 34))
        elif self._hovered:
            painter.setBrush(QtGui.QColor(120, 120, 120))
        else:
            painter.setBrush(self._background_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(QtCore.QRectF(0, 0, rect.width(), rect.height()), 4, 4)

        # くり抜きようのパス
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(0, 0, rect.width(), rect.height()), 4, 4)
        painter.setClipPath(path)

        # スライダー
        painter.setBrush(self._color)
        painter.setPen(QtCore.Qt.NoPen)
        width = (self._value - self._minimum) / (self._maximum - self._minimum) * rect.width()
        painter.drawRect(QtCore.QRect(0, 0, width, rect.height()))

        # 数値
        painter.setPen(self._text_color)
        painter.setFont(QtGui.QFont('Lucida Sans Unicode', 10))
        painter.drawText(rect, QtCore.Qt.AlignCenter, "{:.{}f}".format(self._value, self._decimals))

        painter.end()
    
    # public method
    def value(self):
        return self._value
    
    def maximum(self):
        return self._maximum
    
    def minimum(self):
        return self._minimum
    
    def singleStep(self):
        return self._single_step
    
    def decimals(self):
        return self._decimals
    
    def color(self):
        return self._color
    
    def textColor(self):
        return self._text_color
    
    def backgroundColor(self):
        return self._background_color
    
    def setValue(self, value):
        self._value = value
    
    def setMaximum(self, value):
        self._maximum = value
    
    def setMinimum(self, value):
        self._minimum = value
    
    def setRange(self, min_value, max_value):
        self._minimum = min_value
        self._maximum = max_value
    
    def setSingleStep(self, step):
        self._single_step = step
        
    def setDecimals(self, decimals):
        self._decimals = decimals
        
    def setColor(self, color):
        self._color = color
    
    def setTextColor(self, color):
        self._text_color = color
    
    def setBackgroundColor(self, color):
        self._background_color = color
        
    # private method
    def _set_line_edit(self):
        # 数値入力用の QLineEdit
        self._line_edit = QtWidgets.QLineEdit(self)
        self._line_edit.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self._line_edit.setFont(QtGui.QFont('Lucida Sans Unicode', 10))
        self._line_edit.setValidator(QtGui.QDoubleValidator())
        self._line_edit.setVisible(False)
        self._line_edit.setObjectName("sliderLineEdit")
        self._line_edit.setStyleSheet("#sliderLineEdit {border: none; border-radius: 5px;}")
        self._line_edit.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self._line_edit.returnPressed.connect(self._apply_text_value)
        self._line_edit.editingFinished.connect(self._apply_text_value)
        self.layout.addWidget(self._line_edit)

    def _activate_edit_mode(self):
        """スライダーを入力モードに切り替え"""
        self._line_edit.setText("{:.{}f}".format(self._value, self._decimals))
        self._line_edit.setVisible(True)
        self._line_edit.setFocus()
        self._line_edit.selectAll()
        self.update()

    def _apply_text_value(self):
        """入力値を適用しスライダーに戻す"""
        value = float(self._line_edit.text())
        self._value = round(max(self._minimum, min(self._maximum, value)), self._decimals)
        self._line_edit.setVisible(False)
        self.setFocus()
        self.valueChanged.emit(self._value)
        self.update()

class FloatSymbolSlider(FloatSlider):
    def __init__(self, parent=None):
        super(FloatSymbolSlider, self).__init__(parent)
        self._hovered_left_symbol = False
        self._hovered_right_symbol = False
        self._hovered_center = False
        
        self.setAttribute(QtCore.Qt.WA_Hover)

    def event(self, event):
        """イベントフィルター (ホバー検出)"""
        if event.type() == QtCore.QEvent.HoverMove:
            self.checkHover(event.pos())
        return super().event(event)
        
    def checkHover(self, pos):
        """ホバー状態をチェック"""
        if not self._moved:
            left_rect = QtCore.QRect(0, 0, 16, self.height())
            right_rect = QtCore.QRect(self.width() - 16, 0, 16, self.height())

            new_hover_left = left_rect.contains(pos)
            new_hover_right = right_rect.contains(pos)

            if new_hover_left != self._hovered_left_symbol:
                self._hovered_left_symbol = new_hover_left
            elif new_hover_right != self._hovered_right_symbol:
                self._hovered_right_symbol = new_hover_right
            elif not new_hover_left and not new_hover_right:
                self.setCursor(QtCore.Qt.SizeHorCursor)
                self._hovered_center = True
            else:
                self.setCursor(QtCore.Qt.ArrowCursor)
                self._hovered_center = False
            self.update()
        
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._pressed = False
            self._pressed_button = QtCore.Qt.NoButton
            if not self._moved:
                if event.x() < 16:
                    self.setValue(max(self._minimum, self._value - self._single_step))
                elif event.x() > self.width() - 16:
                    self.setValue(min(self._maximum, self._value + self._single_step))
                elif not self._moved:
                    self._activate_edit_mode()
                else:
                    self.valueChanged.emit(self._value)
                    
            self._moved = False
            self.unsetCursor()
            self.sliderReleased.emit()
            self.update()
            
    def leaveEvent(self, event):
        self._hovered_left_symbol = False
        self._hovered_right_symbol = False
        self._hovered_center = False
        self.unsetCursor()
        super(FloatSymbolSlider, self).leaveEvent(event)
        
    def paintEvent(self, event):        
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.begin(self)
        rect = self.rect()
        
        # 背景
        if self._pressed:
            painter.setBrush(QtGui.QColor(40, 40, 40))
        elif self._hovered_center:
            painter.setBrush(QtGui.QColor(120, 120, 120))
        else:
            painter.setBrush(self._background_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(QtCore.QRectF(0, 0, rect.width(), rect.height()), 4, 4)
        
        # くり抜きようのパス
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(0, 0, rect.width(), rect.height()), 4, 4)
        painter.setClipPath(path)
        
        if self._hovered:
            # シンボル
            painter.setPen(QtCore.Qt.NoPen)         
             
            if self._moved:
                painter.setBrush(QtGui.QColor(34, 34, 34))
            elif self._hovered_left_symbol:
                painter.setBrush(QtGui.QColor(120, 120, 120))
            else:
                painter.setBrush(QtGui.QColor(100, 100, 100))
            painter.drawRect(QtCore.QRect(0, 0, 16, rect.height()))
            
            if self._moved:
                painter.setBrush(QtGui.QColor(34, 34, 34))
            elif self._hovered_right_symbol:
                painter.setBrush(QtGui.QColor(120, 120, 120))
            else:
                painter.setBrush(QtGui.QColor(100, 100, 100))
            painter.drawRect(QtCore.QRect(rect.width() - 16, 0, 16, rect.height()))
            
            # 矢印
            path = QtGui.QPainterPath()
            # left arrow
            center = QtCore.QPoint(8, rect.height() / 2)
            path.moveTo(center.x() + 2, center.y() - 3)
            path.lineTo(center.x() - 2, center.y())
            path.lineTo(center.x() + 2, center.y() + 3)
            
            # right arrow
            center = QtCore.QPoint(rect.width() - 8, rect.height() / 2)
            path.moveTo(center.x() - 2, center.y() - 3)
            path.lineTo(center.x() + 2, center.y())
            path.lineTo(center.x() - 2, center.y() + 3)
        
            pen = QtGui.QPen(QtGui.QColor(222, 222, 222))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPath(path)
        
        # 数値
        painter.setPen(self._text_color)
        painter.setFont(QtGui.QFont('Lucida Sans Unicode', 10))
        painter.drawText(rect, QtCore.Qt.AlignCenter, "{:.{}f}".format(self._value, self._decimals))
        
        painter.end()

# ----------------------------------------------------------------------------------
# アイコンボタン
# ----------------------------------------------------------------------------------
class IconButton(QtWidgets.QPushButton):
    def __init__(self, icon_path, size=40, parent=None):
        super().__init__(parent)
        self.size = size  # ボタンのサイズ
        self.setFixedSize(size, size)  # ボタンの固定サイズ
        self.setStyleSheet("border: none; background: transparent;")  # 背景なし

        # アイコン画像を整える
        pixmap = self.prepare_icon(icon_path, size)
        
        # ラベルを作成してボタンに配置
        self.label = QtWidgets.QLabel(self)
        self.label.setPixmap(pixmap)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setFixedSize(size, size)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)  # 余白なし
        layout.setAlignment(QtCore.Qt.AlignCenter)

    def prepare_icon(self, icon_path, size):
        """ アイコン画像を適切なサイズに加工する """
        pixmap = QtGui.QPixmap(icon_path)

        if pixmap.isNull():
            return QtGui.QPixmap(size, size)  # 画像が無い場合のデフォルト

        # 画像の透明部分をトリミング
        cropped_pixmap = self.crop_transparent(pixmap)

        # 指定サイズにフィット
        scaled_pixmap = cropped_pixmap.scaled(size, size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        return scaled_pixmap

    def crop_transparent(self, pixmap):
        """ 透明部分をトリミングする """
        img = pixmap.toImage()
        rect = img.rect()

        # 透明部分を検出してトリミング範囲を決定
        min_x, min_y, max_x, max_y = rect.right(), rect.bottom(), rect.left(), rect.top()
        for x in range(rect.width()):
            for y in range(rect.height()):
                if img.pixelColor(x, y).alpha() > 0:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        # 透明部分を削除した新しいピクスマップを作成
        cropped_img = img.copy(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        return QtGui.QPixmap.fromImage(cropped_img)

# --- ウィジェットをテストするためのメインウィンドウ ---
class TestMainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)

        # アイコンボタンを追加（異なるサイズ・透明余白を考慮）
        button1 = IconButton(":/addBookmark.png", 50)
        button2 = IconButton(":/activeDeselectedAnimLayer.png", 50)
        button3 = IconButton(":/absoluteView.png", 50)

        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.addWidget(button3)

# ----------------------------------------------------------------------------------
# シェルフ
# ----------------------------------------------------------------------------------
class ShelfButton(QtWidgets.QPushButton):
    def __init__(self, parent=None, c=None, dcc=None, i=None, ann=None, iol=None, olc=None, olb=None):
        super(ShelfButton, self).__init__(parent)
        self._command = c
        self._doubleClickCommand = dcc
        self._icon = i
        self._annotation = ann
        self._iconLabel = iol
        self._iconLabelColor = olc
        self._labelBackground = olb
        self._clicked = False
        
        self.setFixedSize(QtCore.QSize(32, 32))
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setIconSize(QtCore.QSize(32, 32))
        self.setToolTip(self._annotation)
        self.setStyleSheet("QPushButton{border-style:none;}")
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        rect = self.rect()
        
        # pixmap = self.prepare_icon(self._icon, 32)
        pixmap = QtGui.QPixmap(self._icon)
        if self._iconLabel:
            painter = QtGui.QPainter(pixmap)
            label_bg_color = [round(i/(1/255)) for i in self._labelBackground]
            painter.setBrush(QtGui.QColor(*label_bg_color))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(0,  rect.height()*0.6, rect.width(), rect.height())
            
            label_color = [round(i/(1/255)) for i in self._iconLabelColor]
            painter.setPen(QtGui.QColor(*label_color))
            painter.setFont(QtGui.QFont(u"メイリオ", 7, QtGui.QFont.Bold, False))
            painter.drawText(rect, QtCore.Qt.AlignBottom|QtCore.Qt.AlignCenter, self._iconLabel)
            painter.end()

        self._icon_normal = QtGui.QIcon(pixmap)
        painter = QtGui.QPainter(pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceAtop)
        painter.setBrush(QtGui.QColor(255, 255, 255, 50))
        painter.drawRect(pixmap.rect())
        if self._iconLabel:
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            painter.setBrush(QtGui.QColor(*label_bg_color))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(0,  rect.height()*0.6, rect.width(), rect.height())
            painter.setPen(QtGui.QColor(*label_color))
            painter.setFont(QtGui.QFont(u"メイリオ", 7, QtGui.QFont.Bold, False))
            painter.drawText(rect, QtCore.Qt.AlignBottom|QtCore.Qt.AlignCenter, iol)
            
        painter.end()
        
        self._icon_over = QtGui.QIcon(pixmap)
        self.setIcon(self._icon_normal)
        self.clicked.connect(self.click_command)
        
    def contextMenu(self, point):
        menu = QtWidgets.QMenu(self)
        action = menu.addAction("Option")
        action.triggered.connect(self.option)
        menu.addSeparator()
        action = menu.addAction("Edit")
        action.triggered.connect(self.editButton)
        action = menu.addAction("Delete")
        action.triggered.connect(self.removeButton)
        
        menu.exec_(self.mapToGlobal(point))
        
    def enterEvent(self, event):
        self.setIcon(self._icon_over)
        return super(ShelfButton, self).enterEvent(event)
        
    def leaveEvent(self, event):
        self.setIcon(self._icon_normal)
        return super(ShelfButton, self).leaveEvent(event)
        
    def click_command(self):
        pass
        # mel.eval(self._command)

    def option(self):
        pass
        # mel.eval(self._doubleClickCommand)

    def editButton(self):
        print("---<Button Data>---")
        print("command:             ", self._command)
        print("doubleClickCommand:  ", self._doubleClickCommand)
        print("icon:                ", self._icon)
        print("annotation:          ", self._annotation)
        print("iconLabel:           ", self._iconLabel)
        print("iconLabelColor:      ", self._iconLabelColor)
        print("labelBackground:     ", self._labelBackground)
        
    def removeButton(self):
        layout = self.parent().layout()
        index = layout.indexOf(self)
        layout.takeAt(index)
 
    def prepare_icon(self, icon_path, size):
        """ アイコン画像を適切なサイズに加工する """
        pixmap = QtGui.QPixmap(icon_path)

        if pixmap.isNull():
            return QtGui.QPixmap(size, size)  # 画像が無い場合のデフォルト

        # 画像の透明部分をトリミング
        cropped_pixmap = self.crop_transparent(pixmap)

        # 指定サイズにフィット
        scaled_pixmap = cropped_pixmap.scaled(size, size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        return scaled_pixmap

    def crop_transparent(self, pixmap):
        """ 透明部分をトリミングする """
        img = pixmap.toImage()
        rect = img.rect()

        # 透明部分を検出してトリミング範囲を決定
        min_x, min_y, max_x, max_y = rect.right(), rect.bottom(), rect.left(), rect.top()
        for x in range(rect.width()):
            for y in range(rect.height()):
                if img.pixelColor(x, y).alpha() > 0:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        # 透明部分を削除した新しいピクスマップを作成
        cropped_img = img.copy(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        return QtGui.QPixmap.fromImage(cropped_img)
 
class ShelfTabLayout(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ShelfTabLayout, self).__init__(parent)
        verticalLayout_tab = QtWidgets.QVBoxLayout(self)
        verticalLayout_tab.setSpacing(0)
        verticalLayout_tab.setContentsMargins(5, 5, 5, 5)

        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.flowLayout = FlowLayout(self.scrollAreaWidgetContents)
        
        verticalLayout_tab.addWidget(self.scrollArea)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

    def contextMenu(self, point):
        menu = QtWidgets.QMenu(self)
        action = menu.addAction("addButton")
        action.triggered.connect(self.openAddButton)
        
        menu.exec_(self.mapToGlobal(point))

    def addButton(self, button):
        shelf_button = ShelfButton(
                    c=button["command"],
                    dcc=button["doubleClickCommand"],
                    i=button["iconName"],
                    ann=button["toolTips"],
                    iol=button["iconLabel"],
                    olc=button["iconLabelColor"],
                    olb=[*button["labelBackground"], button["backgroundTransparency"]])
        self.flowLayout.addWidget(shelf_button)

    def openAddButton(self):
        button = {
                "command": "SmoothBindSkin",
                "doubleClickCommand": "SmoothBindSkinOptions",
                "iconName": ":/smoothSkin.png",
                "toolTips": "SmoothBindSkin",
                "iconLabel": "",
                "iconLabelColor": [0.8, 0.8, 0.8],
                "labelBackground": [0.0, 0.0, 0.0],
                "backgroundTransparency": 0.5}
        self.addButton(button)
        
    def count(self):
        return self.flowLayout.count()
        
    def index(self, widget):
        return self.flowLayout.indexOf(widget)
        
    def item(self, index):
        return self.flowLayout.itemAt(index)    
    
class ShelfTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ShelfTab, self).__init__(parent)
        
        self._tabs = []
        self.setMinimumHeight(80)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        # ----------------------------------------------------------------------------------
        # TAB 
        # ----------------------------------------------------------------------------------
        self.tabWidget = QtWidgets.QTabWidget(self)
        
        """---LAYOUT------------------------------------------------------------------------"""
        self.verticalLayout.addWidget(self.tabWidget)
        
    def addTab(self, name="New Tab"):
        shelf_tab_layout = ShelfTabLayout(self.tabWidget)
        self.tabWidget.addTab(shelf_tab_layout, name)
        self._tabs.append(shelf_tab_layout)
        return shelf_tab_layout
        
    def removeTab(self, index):
        self.setTabOrder.removeTab(index)
        self._tabs.pop(index)
        return
           
    def addButton(self, index, shelfButton):
        tab = self._tabs[index]
        tab.addButton(shelfButton)

    def indexOf(self, widget):
        return self.tabWidget.indexOf(widget)

    def count(self):
        return self.tabWidget.count()
    
    def widget(self, index):
        return self._tabs[index]
        
    def currntWidget(self):
        return self.tabWidget.currentWidget()
    
    def currentIndex(self):
        return self.tabWidget.currentIndex()

    def visible(self, index, status):
        self.tabWidget.setTabVisible(index, status)

shelf_tab_items = {
        "File": [
                {"command": "NewScene", "doubleClickCommand": "NewSceneOptions", "iconName": ":/menuIconFile.png", "toolTips": "Create a new scene", "iconLabel": "NS", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "OpenScene", "doubleClickCommand": "OpenSceneOptions", "iconName": ":/menuIconFile.png", "toolTips": "Open a scene", "iconLabel": "OS", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "OptimizeScene", "doubleClickCommand": "OptimizeSceneOptions", "iconName": ":/menuIconFile.png", "toolTips": "Remove unused items", "iconLabel": "OSS", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "Import", "doubleClickCommand": "ImportOptions", "iconName": ":/menuIconFile.png", "toolTips": "Add the file to the current scene", "iconLabel": "IMP", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "ExportSelection", "doubleClickCommand": "ExportSelectionOptions", "iconName": ":/menuIconFile.png", "toolTips": "Export selected objects (and related info) to a new file", "iconLabel": "ES", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "ReferenceEditor", "doubleClickCommand": "Options", "iconName": ":/menuIconFile.png", "toolTips": "Edit the references for the current scene", "iconLabel": "RE", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "SetProject", "doubleClickCommand": "Options", "iconName": ":/menuIconFile.png", "toolTips": "Change the current project", "iconLabel": "SP", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5}
                ],
        "Edit": [
                {"command": "doGroup 0 1 1", "doubleClickCommand": "GroupOptions", "iconName": ":/menuIconEdit.png", "toolTips": "Group the selected object(s)", "iconLabel": "GRP", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "parentPreset(0,1)", "doubleClickCommand": "NewSceneOptions", "iconName": ":/menuIconEdit.png", "toolTips": "Parent the selected object(s) to the last selected object", "iconLabel": "P", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "parent -w", "doubleClickCommand": "NewSceneOptions", "iconName": ":/menuIconEdit.png", "toolTips": "Unparent the selected object(s)", "iconLabel": "UP", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "DeleteHistory", "doubleClickCommand": "", "iconName": ":/menuIconEdit.png", "toolTips": "Delete construction history on the selected object(s)", "iconLabel": "HIS", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "BakeNonDefHistory", "doubleClickCommand": "", "iconName": ":/menuIconEdit.png", "toolTips": "Delete modeling history on the selected object(s)", "iconLabel": "NH", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5}                ],
        "create": [
                ],
        "Modify": [
                {"command": "FreezeTransformations", "doubleClickCommand": "", "iconName": ":/menuIconModify.png", "toolTips": "FreezeTransformations", "iconLabel": "FT", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "ResetTransformations", "doubleClickCommand": "", "iconName": ":/menuIconModify.png", "toolTips": "ResetTransformations", "iconLabel": "RT", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "CenterPivot", "doubleClickCommand": "", "iconName": ":/menuIconModify.png", "toolTips": "CenterPivot", "iconLabel": "CP", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                ],
        "Display": [],
        "Window": [
                {"command": "NodeEditorWindow", "doubleClickCommand": "", "iconName": ":/menuIconWindow.png", "toolTips": "NodeEditorWindow", "iconLabel": "NE", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "HypergraphHierarchyWindow", "doubleClickCommand": "", "iconName": ":/hypergraph.png", "toolTips": "HypergraphHierarchyWindow", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "ScriptEditor", "doubleClickCommand": "", "iconName": ":/cmdWndIcon.png", "toolTips": "ScriptEditor", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "ComponentEditor", "doubleClickCommand": "", "iconName": ":/menuIconWindow.png", "toolTips": "ComponentEditor", "iconLabel": "CpEd", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "NamespaceEditor", "doubleClickCommand": "", "iconName": ":/menuIconWindow.png", "toolTips": "NamespaceEditor", "iconLabel": "NE", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "GraphEditor", "doubleClickCommand": "", "iconName": ":/teGraphEditor.png", "toolTips": "GraphEditor", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "TimeEditorWindow", "doubleClickCommand": "", "iconName": ":/getCTE.png", "toolTips": "TimeEditorWindow", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "ShapeEditor", "doubleClickCommand": "", "iconName": ":/blendShapeEditor.png", "toolTips": "ShapeEditor", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "PoseEditor", "doubleClickCommand": "", "iconName": ":/poseEditor.png", "toolTips": "PoseEditor", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "PluginManager", "doubleClickCommand": "", "iconName": ":/menuIconWindow.png", "toolTips": "PluginManager", "iconLabel": "PM", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5}
                ],
        "Skeleton": [
                {"command": "JointTool", "doubleClickCommand": "", "iconName": ":/kinJoint.png", "toolTips": "JointTool", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "InsertJointTool", "doubleClickCommand": "", "iconName": ":/kinInsert.png", "toolTips": "InsertJointTool", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "MirrorJoint", "doubleClickCommand": "MirrorJointOptions", "iconName": ":/kinMirrorJoint_S.png", "toolTips": "mirrorJoint", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "OrientJoint", "doubleClickCommand": "OrientJointOptions", "iconName": ":/orientJoint.png", "toolTips": "OrientJointOptions", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                ],
        "Skin": [
                {"command": "SmoothBindSkin", "doubleClickCommand": "SmoothBindSkinOptions", "iconName": ":/smoothSkin.png", "toolTips": "SmoothBindSkin", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "GoToBindPose", "doubleClickCommand": "", "iconName": ":/goToBindPose.png", "toolTips": "GoToBindPose", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "MirrorSkinWeights", "doubleClickCommand": "MirrorSkinWeightsOptions", "iconName": ":/mirrorSkinWeight.png", "toolTips": "MirrorSkinWeights", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "CopySkinWeights", "doubleClickCommand": "CopySkinWeightsOptions", "iconName": ":/copySkinWeight.png", "toolTips": "CopySkinWeights", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "SmoothSkinWeights", "doubleClickCommand": "SmoothSkinWeightsOptions", "iconName": ":/smoothSkinWeights.png", "toolTips": "CopySkinWeights", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "WeightHammer", "doubleClickCommand": "", "iconName": ":/menuIconSkinning.png", "toolTips": "WeightHammer", "iconLabel": "HSW", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "CopyVertexWeights", "doubleClickCommand": "", "iconName": ":/menuIconSkinning.png", "toolTips": "CopyVertexWeights", "iconLabel": "CVW", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "PasteVertexWeights", "doubleClickCommand": "", "iconName": ":/menuIconSkinning.png", "toolTips": "PasteVertexWeights", "iconLabel": "PVW", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "AddInfluence", "doubleClickCommand": "AddInfluenceOptions", "iconName": ":/addWrapInfluence.png", "toolTips": "AddInfluence", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "RemoveInfluence", "doubleClickCommand": "", "iconName": ":/removeWrapInfluence.png", "toolTips": "RemoveInfluence", "iconLabel": "", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "RemoveUnusedInfluences", "doubleClickCommand": "", "iconName": ":/menuIconSkinning.png", "toolTips": "RemoveUnusedInfluences", "iconLabel": "RUI", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                {"command": "NormalizeWeights", "doubleClickCommand": "", "iconName": ":/menuIconSkinning.png", "toolTips": "NormalizeWeights", "iconLabel": "NW", "iconLabelColor": [0.8, 0.8, 0.8], "labelBackground": [0.0, 0.0, 0.0], "backgroundTransparency": 0.5},
                ]
        }

# ----------------------------------------------------------------------------------
# メニュースタックウィジェット
# ----------------------------------------------------------------------------------
class MenuItem(QtWidgets.QPushButton):
    def __init__(self, text, color=QtGui.QColor(0, 0, 0), parent=None):
        super(MenuItem, self).__init__(text, parent)
        self.setCheckable(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self.setStyleSheet("color: {}; text-align: left; padding: 5px;".format(color.name()))
        self._default_style = "color: {}; text-align: left; padding: 5px;".format(color.name())
        self._highlight_style = "background-color: lightblue; color: black; text-align: left; padding: 5px;"

    def setSelected(self, selected):
        """選択時のハイライトを管理"""
        if selected:
            self.setStyleSheet(self._highlight_style)
        else:
            self.setStyleSheet(self._default_style)
            
class MenuGroup(QtWidgets.QWidget):
    menuClicked = QtCore.Signal(str)
    
    def __init__(self, name, color=QtGui.QColor(255, 0, 0), parent=None):
        super(MenuGroup, self).__init__(parent)
        self._menus = []
        self._menu_names = []
        
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        # self.setStyleSheet("background-color: {}; border-radius: 5px;".format(color.name()))

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.toggle_button = QtWidgets.QPushButton(name)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        # self.toggle_button.setStyleSheet("background-color: {}; text-align: left; font-weight: bold; padding: 5px;".format(color.name()))
        self.toggle_button.clicked.connect(self._toggle_visibility)

        self.menu_container = QtWidgets.QWidget()
        self.menu_layout = QtWidgets.QVBoxLayout(self.menu_container)
        self.menu_layout.setContentsMargins(15, 0, 0, 0)
        self.menu_layout.setSpacing(2)
        # self.menu_layout.addStretch(1)

        self.layout.addWidget(self.toggle_button)
        self.layout.addWidget(self.menu_container)
        
        # アニメーション
        self._anim = QtCore.QPropertyAnimation(self.menu_container, b"maximumHeight")
        self._anim.setDuration(200)

    # public method
    def menuCount(self):
        return len(self._menus)
    
    def index(self, menu):
        return self._menus.index(menu)
    
    def indexFromName(self, name):
        return self._menu_names.index(name)

    def menu(self, row):
        if not (0 <= row < len(self._menus)):
            raise IndexError("Invalid index")
        return self._menus[row]

    def isExpanded(self):
        return self.toggle_button.isChecked()

    def addMenu(self, menu):
        """メニューを追加"""
        menu.clicked.connect(lambda: self.menuClicked.emit(menu.text()))
        self.menu_layout.addWidget(menu)
        self._menus.append(menu)
        self._menu_names.append(menu.text())

    def insertMenu(self, menu, row):
        if not (0 <= row <= self.menuCount()):
            raise IndexError("Invalid index")
        
        self.menu_layout.insertWidget(row, menu)
        self._menus.insert(row, menu)
        self._menu_names.insert(row, menu.text())
        
    def removeMenu(self, row):
        """メニューを削除"""
        if not (0 <= row <= self.menuCount()):
            raise IndexError("Invalid index")
        
        menu = self._menus.pop(row)
        self._menu_names.pop(row)
        
        self.menu_layout.removeWidget(menu)
        menu.setParent(None)
        
        # メニューが空なら Stretch を追加
        if self.menuCount() == 0:
            self.menu_layout.addStretch(1)
    
    def setText(self, text):
        self.toggle_button.setText(text)
    
    def setColor(self, color):
        self.toggle_button.setStyleSheet("background-color: {}; text-align: left; font-weight: bold; padding: 5px;".format(color.name()))
            
    # private method
    def _toggle_visibility(self):
        """グループの展開・折りたたみをアニメーションで制御"""
        if self.toggle_button.isChecked():
            self.menu_container.setMaximumHeight(0)
            self.menu_container.setVisible(True)
            self._anim.setStartValue(0)
            self._anim.setEndValue(self.menu_container.sizeHint().height())
        else:
            self._anim.setStartValue(self.menu_container.height())
            self._anim.setEndValue(0)

        self._anim.start()
        
class MenuPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MenuPage, self).__init__(parent)
        
        self._menus = []
        self._menu_pages = {}
        self._groups = []
        self.selected_menu = None
        
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.menu_scroll_area = QtWidgets.QScrollArea()
        self.menu_scroll_area.setWidgetResizable(True)
        self.menu_scroll_area.setFixedWidth(200)
        self.menu_scroll_area.setStyleSheet("")
        
        self.menu_container = QtWidgets.QWidget()
        self.menu_layout = QtWidgets.QVBoxLayout(self.menu_container)
        self.menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout.setSpacing(2)
        self.menu_layout.addStretch(1)
        self.menu_scroll_area.setWidget(self.menu_container)
        
        self.page_stack = QtWidgets.QStackedWidget()
        
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        self.main_layout.addWidget(self.splitter)
        self.splitter.addWidget(self.menu_scroll_area)
        self.splitter.addWidget(self.page_stack)
        
        
    # public method
    def groupCount(self):
        return len(self._groups)
    
    def groupIndexFromName(self, name):
        keys = list(self._groups.keys())
        return keys.index(name) if name in keys else -1
    
    def addMenuGroup(self, name, color):
        """メニューグループを追加"""
        group = MenuGroup(name, color)
        group.menuClicked.connect(self.showPage)
        self.menu_layout.insertWidget(self.menu_layout.count() - 1, group)
        return group

    def addMenu(self, group, menu_item):
        """メニューを追加してページを作成"""
        group.addMenu(menu_item)

        # メニューに対応するページを作成
        page = QtWidgets.QLabel(f"{menu_item.text()} のページ", alignment=QtCore.Qt.AlignCenter)
        self.page_stack.addWidget(page)
        self._menu_pages[menu_item.text()] = page
    
    def insertGroup(self, name, index):
        if 0 >= index >= self.groupCount():
            raise IndexError("")
        
        menu_group = MenuGroup(name)
        self.menu_layout.insertWidget(index, menu_group)
    
    def insertMenu(self, name, index, group):
        if 0 >= index >= self.menuCount(group):
            raise IndexError("")

        pass
    
    def removeGroup(self, index):
        if 0 >= index >= self.groupCount():
            raise IndexError("")

        pass
    
    def removeMenu(self, index, group):
        if 0 >= index >= self.menuCount(group):
            raise IndexError("")

        pass
    
    def showPage(self, menu_name):
        """メニューをクリックしたら対応するページを表示"""
        if menu_name in self._menu_pages:
            self.page_stack.setCurrentWidget(self._menu_pages[menu_name])

            # メニューの選択状態を変更
            self.setSelectedMenu(menu_name)
            
    def setSelectedMenu(self, menu_name):
        """選択されたメニューの背景色を変更"""
        for group in self.menu_container.children():
            if isinstance(group, MenuGroup):
                for i in range(group.menuCount()):
                    menu = group.menu(i)
                    menu.setSelected(menu.text() == menu_name) 
                                  
class RunOnlyMixin(object):
    """ツールが2つ以上起動しないように既に起動しているツールを閉じる
    """
    #: :type: dict
    __RUNNING = {}
 
    def __new__(cls, *args, **kwargs):
        if cls in RunOnlyMixin.__RUNNING.keys():
            w = RunOnlyMixin.__RUNNING.pop(cls)
            try:
                w.close()
            except RuntimeError as e:
                pass
 
        ins = super(RunOnlyMixin, cls).__new__(cls, args, kwargs)
        RunOnlyMixin.__RUNNING[cls] = ins
 
        return ins   
    
    
# ----------------------------------------------------------------------------------
# プラスボタン付きタブ
# ----------------------------------------------------------------------------------    
class CustomTabBar(QtWidgets.QTabBar):
    tabAddRequested = QtCore.Signal()
    
    def __init__(self, parent=None):
        super(CustomTabBar, self).__init__(parent)
        self.setTabsClosable(True)

        # +ボタン 
        self.addTab("+")
        self.setTabEnabled(self.count() - 1, False)
        self.updateAddButtonTab()
        
    def mouseReleaseEvent(self, event):
        index = self.tabAt(event.pos())
        if index == self.count() - 1:
            self.tabAddRequested.emit()
        else:
            super(CustomTabBar, self).mouseReleaseEvent(event)
       
    def updateAddButtonTab(self):
        """+タブには ✕ ボタンを表示しない"""
        plus_index = self.count() - 1
        if plus_index >= 0:
            close_btn = self.tabButton(plus_index, QtWidgets.QTabBar.RightSide)
            if close_btn:
                close_btn.deleteLater()
                self.setTabButton(plus_index, QtWidgets.QTabBar.RightSide, None)
          
class CustomTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(CustomTabWidget, self).__init__(parent)
        self._add_widget = QtWidgets.QWidget()
        self.tabBar = CustomTabBar()
        self.setTabBar(self.tabBar) 
        
        self.tabBar.tabAddRequested.connect(self.addTabDialog)
        self.tabCloseRequested.connect(self.removeTab)

    def addTabDialog(self):
        text, ok = QtWidgets.QInputDialog.getText(
            self, 
            u"タブ名の入力", 
            u"新しいタブの名前:", 
            QtWidgets.QLineEdit.Normal, 
            "Tab"
        )
        if ok and text:
            self.addTab(CustomWidget(), text)

    def addTab(self, widget, args: str):
        index = self.count() - 1
        insert_index = self.insertTab(index, widget, args)
        self.setCurrentIndex(insert_index)
        
    def removeTab(self, index):
        super(CustomTabWidget, self).removeTab(index)
        index = self.currentIndex()
        if index == self.count() - 1:
            self.setCurrentIndex(self.count() - 2)
        if self.count() == 1:
            self.addTab(CustomWidget(), "Tab 0")
    
    def setAddWidget(self, widget):
        self._add_widget = widget
    
class CustomWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CustomWidget, self).__init__(parent)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        
        self.view = NodeListView()
        self.model = NodeListModel()
        self.view.setModel(self.model)
        self.verticalLayout.addWidget(self.view)


# ----------------------------------------------------------------------------------
# ノードがドロップできるリストビュー
# ----------------------------------------------------------------------------------    
class NodeItem(object):
    def __init__(self, node):
        self._node = node
        self._icons = set(cmds.resourceManager(nf="out_*"))
        
        sl = om2.MGlobal.getSelectionListByName(node)
        self._mObject = sl.getDependNode(0)
        self._handle = om2.MObjectHandle(self._mObject)
        
    def isValid(self):
        return self._handle.isValid() and self._handle.isAlive()
    
    def mObject(self):
        return self._mObject
        
    def name(self):
        fnDependencyNode = om2.MFnDependencyNode(self._mObject)
        return fnDependencyNode.name()
    
    def fullPathName(self):
        try:
            fnDagNode = om2.MFnDagNode(self._mObject)
            dagPath = fnDagNode.getPath()
            return dagPath.fullPathName()
        except:
            fnDependencyNode = om2.MFnDependencyNode(self._mObject)
            return fnDependencyNode.name()
    
    def icon(self):
        shape = cmds.listRelatives(self.fullPathName(), s=True, ni=True,  f=True)
        if shape:
            icon = "out_{}.png".format(cmds.nodeType(shape[0]))
        else:
            icon = "out_{}.png".format(cmds.nodeType(self.fullPathName()))

        if icon in self._icons:
            return ":/" + icon
        else:
            return ":/out_default.png"
    
class NodeListView(QtWidgets.QListView):
    def __init__(self, parent=None):
        super(NodeListView, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(False) # 複数選択のため無効化
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        self._drag_start_pos = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self._drag_start_pos = event.pos()
        super(NodeListView, self).mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if (event.buttons() & QtCore.Qt.MiddleButton) and self._drag_start_pos:
            if (event.pos() - self._drag_start_pos).manhattanLength() > QtWidgets.QApplication.startDragDistance():
                self.startCustomDrag()
                self.drag_start_pos = None
                return
        super(NodeListView, self).mouseMoveEvent(event)
        
    def startCustomDrag(self):
        indexes = self.selectedIndexes()
        if not indexes:
            return

        model = self.model()

        mime_data = model.mimeData(indexes)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mime_data)

        drag.setPixmap(drag.dragCursor(QtCore.Qt.MoveAction))  
        drag.exec_(QtCore.Qt.MoveAction)
        
    def dragEnterEvent(self, event):
        super(NodeListView, self).dragEnterEvent(event)
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        super(NodeListView, self).dragMoveEvent(event)
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        super(NodeListView, self).dropEvent(event)
        if event.mimeData().hasText():
            text = event.mimeData().text()
            nodes = text.strip().split()
            model = self.model()
            items = list(model.items())
            item_nodes = set([i.fullPathName() for i in items])
            
            add_items = []
            for node in nodes:
                if cmds.objExists(node) and node not in item_nodes:
                    add_items.append(NodeItem(node))
            row = model.rowCount()
            model.insertRows(row, len(add_items), add_items)

            event.acceptProposedAction()

class NodeListModel(QtCore.QAbstractListModel):
    MimeType = "application/x-nodeitem"
    
    def __init__(self, items=[], parent=None):
        super(NodeListModel, self).__init__(parent)
        self._items = items
    
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)
        
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return
        
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
                
        if role == QtCore.Qt.DisplayRole:
            return self._items[row].name()
        elif role == QtCore.Qt.ToolTipRole:
            return self._items[row].fullPathName()
        elif role == QtCore.Qt.DecorationRole:
            return QtGui.QPixmap(self._items[row].icon())
        return None
        
    def flags(self, index):
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.isValid():
            return flags | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled
        return flags | QtCore.Qt.ItemIsDropEnabled
    
    def supportedDropActions(self):
        return QtCore.Qt.MoveAction
    
    def mimeTypes(self):
        return ["application/x-myitem"]

    def mimeData(self, indexes):
        mime_data = QtCore.QMimeData()
        rows = [i.row() for i in indexes if i.isValid()]
        mime_data.setData("application/x-myitem", ",".join(map(str, rows)).encode())
        return mime_data

    def dropMimeData(self, data, action, row, column, parent):
        if action == QtCore.Qt.IgnoreAction:
            return False
        if not data.hasFormat("application/x-myitem"):
            return False

        # ドロップ先インデックス
        if row == -1 and parent.isValid():
            row = parent.row()
        if row == -1:
            row = self.rowCount()

        # ドラッグされた行の取得
        rows = list(map(int, data.data("application/x-myitem").data().decode().split(",")))
        rows.sort()

        self.beginResetModel()
        moving_items = [self._items[r] for r in rows]

        for r in reversed(rows):
            del self._items[r]

        for i, item in enumerate(moving_items):
            insert_row = row + i
            if insert_row > len(self._items):
                insert_row = len(self._items)
            self._items.insert(insert_row, item)
        self.endResetModel()
        return True
    
    def insertRows(self, row, count, items=None, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, row, row + count -1)
        for i, item in enumerate(items):
            self._items.insert(row + i, item)
        self.endInsertRows()
        return True
    
    def items(self):
        return self._items
        
# ----------------------------------------------------------------------------------
# 固定ヘッダーのあるリストビュー
# ----------------------------------------------------------------------------------    
class SectionedListModel(QtCore.QAbstractListModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        # data = { "A": ["apple", "avocado"], "B": ["banana", "blueberry"] }
        self.sections = []
        self.items = []
        for section, items in data.items():
            self.sections.append((len(self.items), section))  # (開始インデックス, セクション名)
            self.items.append({"type": "header", "text": section})
            for it in items:
                self.items.append({"type": "item", "text": it})

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role):
        if not index.isValid():
            return None
        item = self.items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return item["text"]
        if role == QtCore.Qt.FontRole and item["type"] == "header":
            font = QtGui.QFont()
            font.setBold(True)
            return font
        if role == QtCore.Qt.BackgroundRole and item["type"] == "header":
            return QtGui.QBrush(QtGui.QColor(230, 230, 230))
        return None

class StickyHeaderListView(QtWidgets.QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

    def paintEvent(self, event):
        super().paintEvent(event)

        model = self.model()
        if not model:
            return

        painter = QtGui.QPainter(self.viewport())

        # 現在スクロール位置の最初に見えている index
        top_index = self.indexAt(QtCore.QPoint(0, 0))
        if not top_index.isValid():
            return

        # その index から上方向に header を探す
        row = top_index.row()
        while row >= 0:
            if model.items[row]["type"] == "header":
                header_index = row
                break
            row -= 1
        else:
            return

        option = self.viewOptions()
        rect = self.visualRect(model.index(header_index, 0))

        # 次のヘッダー位置を調べる
        next_header_y = None
        for r in range(header_index + 1, model.rowCount()):
            if model.items[r]["type"] == "header":
                next_header_y = self.visualRect(model.index(r, 0)).top()
                break

        # 描画位置（押し上げ処理）
        header_rect = QtCore.QRect(rect)
        header_rect.moveTop(0)
        if next_header_y is not None and next_header_y <= header_rect.height():
            header_rect.moveTop(next_header_y - header_rect.height())

        # 背景とテキスト描画
        painter.fillRect(header_rect, QtGui.QColor(230, 230, 230))
        painter.setFont(QtGui.QFont("", weight=QtGui.QFont.Bold))
        painter.drawText(header_rect.adjusted(5, 0, 0, 0),
                         QtCore.Qt.AlignVCenter, model.items[header_index]["text"])

class StickyTreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(StickyTreeView, self).__init__(parent)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)

    def paintEvent(self, event):
        super(StickyTreeView, self).paintEvent(event)

        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # 現在スクロール位置で一番上に見えているインデックス
        top_index = self.indexAt(QtCore.QPoint(0, 0))
        if not top_index.isValid():
            return

        # そのインデックスの親を探す（親がグループ）
        parent_index = top_index.parent()
        if parent_index.isValid():
            group_index = parent_index
        else:
            group_index = top_index

        # グループ名
        group_name = group_index.data()

        # 次のグループの位置を調べる（押し上げ演出用）
        next_row = group_index.row() + 1
        next_index = group_index.sibling(next_row, 0)
        y_offset = 0
        if next_index.isValid():
            rect = self.visualRect(next_index)
            if rect.top() < self.fontMetrics().height():
                y_offset = rect.top() - self.fontMetrics().height()

        # 固定ヘッダーの矩形
        header_height = self.fontMetrics().height() + 8
        rect = QtCore.QRect(0, y_offset, self.viewport().width(), header_height)

        # 背景
        painter.fillRect(rect, QtGui.QColor(220, 220, 220, 230))

        # テキスト
        painter.setPen(QtCore.Qt.black)
        painter.drawText(rect.adjusted(4, 0, -4, 0),
                         QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                         group_name)
        painter.end()

    
# ----------------------------------------------------------------------------------
# タブの非表示
# ----------------------------------------------------------------------------------    
class TabManager(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)

        # タブウィジェット
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)

        # メニュー
        self.menu_bar = QtWidgets.QMenuBar()
        layout.setMenuBar(self.menu_bar)
        tab_menu = self.menu_bar.addMenu("Tabs")

        # タブページを準備
        self.pages = {}
        for name in ["Tab A", "Tab B", "Tab C"]:
            widget = QtWidgets.QLabel(f"This is {name}")
            self.pages[name] = widget
            self.tab_widget.addTab(widget, name)

            # メニューのチェックアクション
            act = QtWidgets.QAction(name, self, checkable=True, checked=True)
            act.toggled.connect(lambda checked, n=name: self.toggle_tab(n, checked))
            tab_menu.addAction(act)

    def toggle_tab(self, name, visible):
        widget = self.pages[name]
        index = self.tab_widget.indexOf(widget)

        if visible:
            # タブが無ければ追加
            if index == -1:
                self.tab_widget.addTab(widget, name)
        else:
            # タブがあれば削除（widget は保持）
            if index != -1:
                self.tab_widget.removeTab(index)
                
class TabWidget(QtWidgets.QTabWidget):
    def __init__(self):
        super().__init__()
        self.hidden_tabs = {}  # 非表示タブを保存しておく {name: (widget, index, icon)}

    def hideTab(self, index):
        if index < 0 or index >= self.count():
            return
        widget = self.widget(index)
        text = self.tabText(index)
        icon = self.tabIcon(index)
        # 保持
        self.hidden_tabs[text] = (widget, index, icon)
        # タブから削除
        self.removeTab(index)

    def showTab(self, name):
        if name not in self.hidden_tabs:
            return
        widget, index, icon = self.hidden_tabs.pop(name)
        # indexが範囲外の場合は最後に追加
        if index > self.count():
            index = self.count()
        self.insertTab(index, widget, icon, name)
    
    
    
    
    
    
    
    
    