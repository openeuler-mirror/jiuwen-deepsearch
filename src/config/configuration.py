import yaml
from pathlib import Path
from typing import Any, Type

class Configuration:
    _CONFIG_FILE = "service.yaml"
    _PARENT_LEVEL_INDEX = 2

    _config: dict[str, Any] = {}
    _loaded: bool = False

    @classmethod
    def _load(cls) -> None:
        if cls._loaded:
            return
        conf_path = Path(__file__).parents[cls._PARENT_LEVEL_INDEX] / cls._CONFIG_FILE
        with conf_path.open("r", encoding="utf-8") as f:
            cls._config = yaml.safe_load(f)
            cls._loaded = True

    @classmethod
    def get_conf(cls, *fields: str, expected_type: Type[Any] = None) -> Any:
        """Get conf values according to the key path passed in, and optionally validate the return type."""
        cls._load()
        node = cls._config
        for field in fields:
            if not isinstance(node, dict) or field not in node:
                raise KeyError(f"No field '{'.'.join(fields)}' in file '{cls._CONFIG_FILE}'")
            node = node[field]

        if expected_type is not None and not isinstance(node, expected_type):
            raise TypeError(f"Mismatched type '{expected_type}' for field '{'.'.join(fields)}' "
                            f"in file '{cls._CONFIG_FILE}'")
        return node