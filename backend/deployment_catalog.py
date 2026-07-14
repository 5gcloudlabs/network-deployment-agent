import os
from functools import lru_cache

import yaml

DEFAULT_CATALOG_PATH = "5g/deployment-catalog.yaml"


def _catalog_path() -> str:
    return os.environ.get("DEPLOYMENT_CATALOG_PATH", DEFAULT_CATALOG_PATH)


def _normalize_option(raw: dict) -> dict:
    return {
        "id": raw["id"],
        "type": raw["type"],
        "category": raw.get("category", "single-step"),
        "github_path": raw["manifest"],
        "required_params": list(raw.get("required_params", [])),
        "next_step": raw.get("next_step"),
        "description": raw.get("description", ""),
        "label": raw.get("label", raw["id"]),
    }


class DeploymentCatalog:
    def __init__(self, data: dict):
        self.version = data.get("version", 1)
        self.step_labels = dict(data.get("step_labels", {}))
        self.options = {
            option["id"]: option
            for option in (_normalize_option(item) for item in data.get("options", []))
        }

    def get_option(self, option_id: str) -> dict | None:
        return self.options.get(option_id)

    def option_ids(self) -> list[str]:
        return list(self.options.keys())

    def options_by_category(self, category: str) -> list[dict]:
        return [
            option
            for option in self.options.values()
            if option["category"] == category
        ]


@lru_cache(maxsize=1)
def get_catalog() -> DeploymentCatalog:
    from backend.workflow import fetch_template

    raw = fetch_template(_catalog_path())
    data = yaml.safe_load(raw)
    if not isinstance(data, dict) or "options" not in data:
        raise ValueError(f"Invalid deployment catalog at {_catalog_path()}")
    return DeploymentCatalog(data)


def reload_catalog() -> DeploymentCatalog:
    get_catalog.cache_clear()
    return get_catalog()
