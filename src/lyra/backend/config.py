import json
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from .models import Colors, Fonts

APP_NAME = "Lyra"


def _config_file() -> Path:
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.GenericConfigLocation
    )
    return Path(base) / APP_NAME / "config.json"


@dataclass
class Config:
    library_path: str | None = None
    structure_library: bool = False
    colors: Colors = field(default_factory=Colors)
    dynamic_colors: bool = False
    fonts: Fonts = field(default_factory=Fonts)

    def to_dict(self) -> dict:
        return {
            "library_path": self.library_path,
            "structure_library": self.structure_library,
            "colors": self.colors.to_dict(),
            "dynamic_colors": self.dynamic_colors,
            "fonts": self.fonts.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        def section(key: str) -> dict:
            value = data.get(key)
            return value if isinstance(value, dict) else {}

        return cls(
            library_path=data.get("library_path"),
            structure_library=bool(data.get("structure_library", False)),
            colors=Colors.from_dict(section("colors")),
            dynamic_colors=bool(data.get("dynamic_colors", False)),
            fonts=Fonts.from_dict(section("fonts")),
        )

    @classmethod
    def load(cls) -> "Config":
        try:
            data = json.loads(_config_file().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        return cls.from_dict(data) if isinstance(data, dict) else cls()

    def save(self) -> None:
        path = _config_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=4, ensure_ascii=False), encoding="utf-8"
        )
