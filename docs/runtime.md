# Runtime and configuration

The live entry point is `python main.py`. Install the complete `requirements.txt` in a dedicated environment and review `src/config/app_config.py` for provider and Langfuse configuration. Run `python scripts/prepare_config.py` to create missing local configuration files without overwriting existing ones. The HTTP response exposes `data.summary` as a string; it is not a labeled obligations dataset or a validated task-extraction JSON schema.

Use the component navigation and validation boundaries in the root [README](../README.md). Runtime services and external providers are not started by the offline replay.
