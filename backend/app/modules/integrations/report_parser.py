"""Parse MLflow and WandB reports to extract performance metrics."""
import re


def parse_mlflow_metrics(run_data: dict) -> dict:
    metrics = run_data.get("metrics", {})
    return {
        "accuracy": metrics.get("accuracy") or metrics.get("val_accuracy"),
        "loss": metrics.get("loss") or metrics.get("val_loss"),
        "f1_score": metrics.get("f1") or metrics.get("f1_score"),
        "auc": metrics.get("auc") or metrics.get("roc_auc"),
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "raw_metrics": metrics,
    }


def parse_wandb_metrics(run_data: dict) -> dict:
    summary = run_data.get("summary", {})
    return {
        "accuracy": summary.get("accuracy") or summary.get("val/accuracy"),
        "loss": summary.get("loss") or summary.get("val/loss"),
        "f1_score": summary.get("f1") or summary.get("f1_score"),
        "auc": summary.get("auc") or summary.get("roc_auc"),
        "precision": summary.get("precision"),
        "recall": summary.get("recall"),
        "raw_metrics": summary,
    }


def format_metrics_for_annex_iv(parsed_metrics: dict) -> str:
    parts = []
    field_labels = [
        ("accuracy", "Accuracy"),
        ("loss", "Loss"),
        ("f1_score", "F1 Score"),
        ("auc", "AUC-ROC"),
        ("precision", "Precision"),
        ("recall", "Recall"),
    ]
    for key, label in field_labels:
        val = parsed_metrics.get(key)
        if val is not None:
            parts.append(f"{label}: {val:.4f}" if isinstance(val, float) else f"{label}: {val}")
    return ", ".join(parts) if parts else "No metrics available"
