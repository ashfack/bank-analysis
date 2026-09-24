from io import BytesIO
from typing import Sequence

from model.models import BudgetView, EnrichedTransaction
from report_generator.excel_architect import ExcelArchitect


class ExcelReportWriter:
    """Generate an Excel report entirely in memory."""

    def write(
        self,
        view: BudgetView,
        transactions: Sequence[EnrichedTransaction],
    ) -> bytes:
        output = BytesIO()
        ExcelArchitect(output).generate(view, list(transactions))
        return output.getvalue()
