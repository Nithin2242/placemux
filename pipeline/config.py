from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    source_path: Path
    output_dir: Path
    log_dir: Path
    start_date: str | None = None
    end_date: str | None = None
    min_support: float = 0.02
    min_confidence: float = 0.30
    min_lift: float = 1.20
    max_itemset_length: int = 3

    def validate(self) -> None:
        if not self.source_path.exists():
            raise FileNotFoundError(
                f"Source dataset not found: {self.source_path}"
            )

        if not 0 < self.min_support <= 1:
            raise ValueError("min_support must be between 0 and 1.")

        if not 0 < self.min_confidence <= 1:
            raise ValueError("min_confidence must be between 0 and 1.")

        if self.min_lift < 0:
            raise ValueError("min_lift cannot be negative.")

        if self.max_itemset_length < 1:
            raise ValueError("max_itemset_length must be at least 1.")