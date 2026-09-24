from typing import Dict

import pandas as pd
from pandas.io.formats.style import Styler

from budgeter.budget_status import BudgetStatus, get_budget_status
from model.models import BudgetView


STATUS_COLORS: Dict[BudgetStatus, str] = {
    BudgetStatus.NEUTRAL: "#FFFFFF",
    BudgetStatus.DARK_GREEN: "#548235",
    BudgetStatus.LIGHT_GREEN: "#50BE5B",
    BudgetStatus.ORANGE: "#ED7D31",
    BudgetStatus.RED: "#C00000",
}


def build_pilotage_table(view: BudgetView) -> pd.DataFrame:
    """Build the wide cycles-by-clusters table rendered by Streamlit."""
    rows = [
        {
            "Cycle": "BUDGET THÉORIQUE",
            **{cluster: view.get_budget(cluster) for cluster in view.clusters},
        }
    ]
    rows.extend(
        {
            "Cycle": cycle,
            **{cluster: view.get_amount(cycle, cluster) for cluster in view.clusters},
        }
        for cycle in view.cycles
    )
    return pd.DataFrame(rows, columns=["Cycle", *view.clusters])


def style_pilotage_table(table: pd.DataFrame, view: BudgetView) -> Styler:
    """Apply shared budget colors while preserving numeric cells."""
    def style_column(column: pd.Series) -> list[str]:
        if column.name == "Cycle":
            return [
                "font-weight: bold; color: #1E3A5F" if row == 0 else "font-weight: bold"
                for row in range(len(column))
            ]

        limit = view.get_budget(column.name)
        styles = ["font-weight: bold; color: #1E90FF; background-color: #F3F7FC"]
        for value in column.iloc[1:]:
            status = get_budget_status(float(value), limit, column.name)
            background = STATUS_COLORS[status]
            foreground = "#1F2937" if status == BudgetStatus.NEUTRAL else "#FFFFFF"
            styles.append(f"background-color: {background}; color: {foreground}")
        return styles

    return table.style.apply(style_column, axis=0).format(
        {column: "{:,.0f} €" for column in view.clusters},
        na_rep="—",
    )
