from __future__ import annotations

import os
from pathlib import Path

from nbconvert.preprocessors import ExecutePreprocessor
import nbformat


def main() -> None:
    raw_path = os.environ["NOTEBOOK_PATH"]
    notebook_path = Path(raw_path)
    timeout = int(os.environ.get("NOTEBOOK_TIMEOUT", "-1"))

    nb = nbformat.read(notebook_path, as_version=4)
    processor = ExecutePreprocessor(timeout=timeout, kernel_name=os.environ.get("NOTEBOOK_KERNEL", "python3"))
    processor.preprocess(nb, {"metadata": {"path": str(Path.cwd())}})
    nbformat.write(nb, notebook_path)


if __name__ == "__main__":
    main()
