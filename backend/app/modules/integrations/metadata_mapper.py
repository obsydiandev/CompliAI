"""Map external integration outputs to Annex IV fields."""

FIELD_MAPPINGS = {
    "github": {
        "general_information.system_name": "name",
        "general_information.version": "default_branch",
        "technical_specifications.model_architecture": "description",
    },
    "mlflow": {
        "technical_specifications.performance_metrics": "metrics",
        "training_data.training_methodology": "params",
        "testing_and_validation.evaluation_metrics": "metrics",
    },
    "wandb": {
        "technical_specifications.performance_metrics": "summary",
        "training_data.training_methodology": "config",
    },
}


def map_to_annex_iv(source: str, data: dict) -> dict:
    result: dict = {}
    mappings = FIELD_MAPPINGS.get(source, {})
    for annex_path, source_key in mappings.items():
        parts = annex_path.split(".")
        section, field = parts[0], parts[1]
        if section not in result:
            result[section] = {}
        value = data.get(source_key)
        if value is not None:
            if isinstance(value, dict):
                result[section][field] = ", ".join(f"{k}: {v}" for k, v in value.items())
            else:
                result[section][field] = str(value)
    return result
