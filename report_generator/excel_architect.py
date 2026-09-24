import pandas as pd
from typing import Dict, Any, List
from budgeter.budget_status import get_budget_status
from model.models import BudgetView, EnrichedTransaction

class ExcelArchitect:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.sheet_pilotage = "📑 Pilotage"
        self.sheet_mapping = "🔍 AI Mapping"
        self.sheet_details = "📝 Ledger"

    def generate(self, view: BudgetView, raw_transactions: List[EnrichedTransaction]):
        """
        The Main Entry Point.
        Uses BudgetView for summary and raw_transactions for the deep-dive ledger.
        """
        # 1. Prepare Dataframes
        pilotage_df = self._prepare_pilotage_df(view)
        mapping_df = pd.DataFrame([vars(c) for c in view.processed_categories])
        mapping_df = mapping_df.sort_values("master_cluster").reset_index(drop=True)
        ledger_df = self._prepare_ledger_df(view, raw_transactions)
        ledger_df = ledger_df.sort_values(['cycle', 'master_cluster'], ascending=[False, True]).reset_index(drop=True)

        with pd.ExcelWriter(self.output_path, engine='xlsxwriter') as writer:
            # Write raw data
            pilotage_df.to_excel(writer, sheet_name=self.sheet_pilotage, startrow=1)
            mapping_df.to_excel(writer, sheet_name=self.sheet_mapping, index=False)
            ledger_df.to_excel(writer, sheet_name=self.sheet_details, index=False)
            
            # Apply specialized Excel logic (Colors & Links)
            self._apply_advanced_styling(writer, view, pilotage_df, mapping_df, ledger_df)

    def _prepare_pilotage_df(self, view: BudgetView) -> pd.DataFrame:
        data = []
        for cycle in view.cycles:
            row = {"cycle": cycle}
            for cluster in view.clusters:
                row[cluster] = view.get_amount(cycle, cluster)
            data.append(row)
        return pd.DataFrame(data).set_index("cycle")

    def _prepare_ledger_df(self, view: BudgetView, raw_transactions: List[EnrichedTransaction]) -> pd.DataFrame:
        df = pd.DataFrame([vars(item) for item in raw_transactions])
        # Ensure AI-discovered clusters are attached to the ledger
        cat_map = {c.category: c.master_cluster for c in view.processed_categories}
        df['master_cluster'] = df['category'].map(cat_map)
        return df.sort_values(['cycle', 'master_cluster', 'amount'], ascending=[False, True, False])

    def _apply_advanced_styling(self, writer, view: BudgetView, pivot, mapping, ledger):
        wb = writer.book
        ws_p = writer.sheets[self.sheet_pilotage]
        styles = self._get_styles(wb)

        # 1. Create Named Ranges for Hyperlinks (The 'Smart' part)
        map_links = self._create_named_ranges(wb, mapping, self.sheet_mapping, "MAP", 1)
        ledger_links = self._create_named_ranges(wb, ledger, self.sheet_details, "LDR", 1, 
                                                group_cols=['cycle', 'master_cluster'])

        # 2. Render Navigation Header (Row 0)
        ws_p.write(0, 0, "cycle", styles['header'])
        for c_idx, cluster in enumerate(view.clusters):
            target = map_links.get(cluster)
            ws_p.write_url(0, c_idx + 1, f"internal:{target}" if target else "", 
                           cell_format=styles['header'], string=cluster)

        # 3. Render Budget Line (Row 1) - THE OVERRIDES
        ws_p.write(1, 0, "BUDGET THEORIQUE", styles['budget'])
        for c_idx, cluster in enumerate(view.clusters):
            ws_p.write_number(1, c_idx + 1, view.get_budget(cluster), styles['budget'])

        # 4. Render Data Grid with Conditional Coloring & Hyperlinks to Ledger
        for r_idx, cycle in enumerate(view.cycles):
            ws_p.write(r_idx + 2, 0, cycle, styles['neutral'])
            for c_idx, cluster in enumerate(view.clusters):
                val = view.get_amount(cycle, cluster)
                limit = view.get_budget(cluster)
                
                # Logic for coloring based on BudgetView thresholds
                fmt = self._determine_color(val, limit, cluster, styles)

                cell_row = r_idx + 2
                cell_col = c_idx + 1
                
                # Link cell to the specific group in the Ledger sheet
                target_ldr = ledger_links.get((str(cycle), str(cluster)))
                if target_ldr and val > 0:
                    ws_p.write_url(cell_row, cell_col, 
                                   f"internal:{target_ldr}", 
                                   cell_format=fmt)
                    ws_p.write_number(cell_row, cell_col, val, fmt)
                else:
                    ws_p.write_number(r_idx + 2, c_idx + 1, val, fmt)

    def _create_named_ranges(self, wb, df, sheet, prefix, start_row, group_cols='master_cluster'):
        links = {}
        curr_row = start_row + 1 # Offset for header
        for key, group in df.groupby(group_cols, sort=False):
            lookup_key = tuple(map(str, key)) if isinstance(key, tuple) else str(key)
            range_id = f"{prefix}_{abs(hash(lookup_key))}"
            wb.define_name(range_id, f"='{sheet}'!$A${curr_row}:$G${curr_row + len(group) - 1}")
            links[lookup_key] = range_id
            curr_row += len(group)
        return links

    def _determine_color(self, val: float, limit: float, cluster: str, styles: dict):
        return styles[get_budget_status(val, limit, cluster).value]

    def _get_styles(self, wb) -> Dict[str, Any]:
        """Restored original high-fidelity styling."""
        fmt_base = {'underline': 1, 'num_format': '# ##0.00', 'border': 1}
        header_fmt = wb.add_format({
            'bold': True, 'align': 'center', 'bg_color': '#D9D9D9', 'border': 1
        })
        return {
            'header': header_fmt,
            'dark_green': wb.add_format({**fmt_base, 'bg_color': '#548235', 'font_color': '#FFFFFF'}),
            'light_green': wb.add_format({**fmt_base, 'bg_color': "#50BE5B", 'font_color': '#FFFFFF'}),
            'orange': wb.add_format({**fmt_base, 'bg_color': '#ED7D31', 'font_color': '#FFFFFF'}),
            'red': wb.add_format({**fmt_base, 'bg_color': '#C00000', 'font_color': '#FFFFFF'}),
            'neutral': wb.add_format({'num_format': '# ##0.00', 'border': 1}),
            'budget': wb.add_format({
                'num_format': '# ##0.00', 'italic': True, 'font_color': '#0000FF', 
                'bg_color': '#F2F2F2', 'border': 1, 'bold': True
            })
        }
