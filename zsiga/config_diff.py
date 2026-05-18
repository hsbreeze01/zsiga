"""Config diff viewer — compare two parsed zsiga.yaml config dictionaries."""

WATCHED_SECTIONS = ("model", "budget", "transport")


def _flatten_section(data: dict, prefix: str) -> dict:
    """Recursively flatten a nested dict into {dot.path: value} pairs."""
    flat = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten_section(value, full_key))
        else:
            flat[full_key] = value
    return flat


def compare_configs(old_config: dict, new_config: dict) -> dict:
    """Compare two parsed configs, return {"changed": [...], "details": {...}}."""
    old_flat = {}
    new_flat = {}

    for section in WATCHED_SECTIONS:
        old_section = old_config.get(section)
        if isinstance(old_section, dict):
            old_flat.update(_flatten_section(old_section, section))

        new_section = new_config.get(section)
        if isinstance(new_section, dict):
            new_flat.update(_flatten_section(new_section, section))

    all_keys = set(old_flat.keys()) | set(new_flat.keys())

    changed = []
    details = {}

    for key in all_keys:
        old_val = old_flat.get(key)
        new_val = new_flat.get(key)
        if old_val != new_val:
            changed.append(key)
            details[key] = {"old": old_val, "new": new_val}

    changed.sort()
    return {"changed": changed, "details": details}
