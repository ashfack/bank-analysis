class ExportUseCase:
    def __init__(self):
        pass

    def execute(self, export_paths, summary, category_breakdown) -> None:
      # Optional export
      if export_paths and export_paths.get("summary"):
        summary.to_csv(export_paths["summary"], index=False, sep=";")
      if export_paths and export_paths.get(
          "breakdown") and category_breakdown is not None:
        category_breakdown.to_csv(export_paths["breakdown"], index=False, sep=";")