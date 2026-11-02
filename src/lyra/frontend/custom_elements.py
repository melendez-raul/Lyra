from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QSlider, QWidget


class ClickSlider(QSlider):
    """Slider que salta a donde haces clic y se arrastra desde cualquier punto."""

    def __init__(
        self,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(orientation, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dragging = False

    def _value_at(self, pos: QPointF) -> int:
        if self.orientation() == Qt.Orientation.Horizontal:
            ratio = pos.x() / max(1, self.width())
        else:  # en vertical, el mínimo está abajo
            ratio = 1.0 - pos.y() / max(1, self.height())
        ratio = max(0.0, min(1.0, ratio))
        if self.invertedAppearance():
            ratio = 1.0 - ratio
        return self.minimum() + round(ratio * (self.maximum() - self.minimum()))

    def _move_to(self, pos: QPointF) -> None:
        value = self._value_at(pos)
        if value != self.value():
            self.setValue(value)
            self.sliderMoved.emit(value)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        self._dragging = True
        self.setSliderDown(True)
        self.sliderPressed.emit()
        self._move_to(event.position())
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if not self._dragging:
            super().mouseMoveEvent(event)
            return
        self._move_to(event.position())
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if not (self._dragging and event.button() == Qt.MouseButton.LeftButton):
            super().mouseReleaseEvent(event)
            return
        self._move_to(event.position())
        self._dragging = False
        self.setSliderDown(False)
        self.sliderReleased.emit()
        event.accept()
