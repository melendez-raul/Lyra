from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..rules import DEFAULT_SIZE, HINT_WIDTH, AppWidget, Radius


class AlbumArt(AppWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("albumArt", parent)
        self._pixmap = QPixmap()
        self._scaled = QPixmap()
        self._scaled_size = QSize()
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self.setMinimumSize(0, 0)

    def set_cover(self, path: str | Path | None) -> None:
        self._pixmap = QPixmap(str(path)) if path else QPixmap()
        self._scaled_size = QSize()
        self.updateGeometry()
        self.update()

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        if self._pixmap.isNull():
            return 0
        return round(width * self._pixmap.height() / self._pixmap.width())

    def sizeHint(self) -> QSize:
        if self._pixmap.isNull():
            return QSize(DEFAULT_SIZE, DEFAULT_SIZE)
        return QSize(HINT_WIDTH, self.heightForWidth(HINT_WIDTH))

    def _fitted(self) -> QSize:
        size = self._pixmap.size()
        size.scale(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        return size

    def _scaled_pixmap(self, target: QSize) -> QPixmap:
        if self._scaled_size != target:
            dpr = self.devicePixelRatioF()
            self._scaled = self._pixmap.scaled(
                target * dpr,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._scaled.setDevicePixelRatio(dpr)
            self._scaled_size = target
        return self._scaled

    def paintEvent(self, event) -> None:
        if self._pixmap.isNull():
            return
        target = self._fitted()
        x = (self.width() - target.width()) / 2
        y = (self.height() - target.height()) / 2
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )
        clip = QPainterPath()
        clip.addRoundedRect(
            QRectF(x, y, target.width(), target.height()), Radius.SM, Radius.SM
        )
        painter.setClipPath(clip)
        painter.drawPixmap(round(x), round(y), self._scaled_pixmap(target))
