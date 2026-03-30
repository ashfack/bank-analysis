from typing import List, Dict, Any
import pandas as pd
from config.config import DOMAIN_DATE
from model.models import ProcessedCategory, Transaction

class ExcelArchitect:
    def __init__(self, transactions: List[Transaction], processed_results: List[ProcessedCategory], output_path: str):
        # Store full transactions to preserve all columns (like dateOperation)
        self.df = pd.DataFrame([t.__dict__ for t in transactions])
        self.mapping_df = pd.DataFrame([p.__dict__ for p in processed_results])
        self.output_path = output_path

    def generate(self, enriched_data: List[dict]):
        """Main entry point to orchestrate file creation."""
        # 1. Data Preparation
        summary = self._prepare_summary(enriched_data)
        pivot = self._create_pivot(summary)
        budget_line = self._calculate_budget_line(pivot.columns)
        
        details = summary.sort_values(['cycle', 'master_cluster', DOMAIN_DATE]).reset_index(drop=True)
        mapping_sorted = self.mapping_df.sort_values(
            ['master_cluster', 'total_actual_spending'], 
            ascending=[True, False]
        ).reset_index(drop=True)

        # 2. File Writing
        with pd.ExcelWriter(self.output_path, engine='xlsxwriter') as writer:
            # startrow=0 allows Headers on Row 0
            pivot.to_excel(writer, sheet_name='Pilotage', startrow=0)
            mapping_sorted.to_excel(writer, sheet_name='Mapping', index=False)
            details.to_excel(writer, sheet_name='Details', index=False)
            
            self._apply_styles(writer, pivot, budget_line, mapping_sorted, details)
            
            for s in writer.sheets.values(): 
                s.set_column(0, 25, 20)

    def _prepare_summary(self, enriched_data: List[dict]) -> pd.DataFrame:
        """Merges cycle labels into the full transaction dataframe safely."""
        enriched_df = pd.DataFrame(enriched_data)
        
        if self.df.empty:
            summary = enriched_df.copy()
        else:
            summary = self.df.copy()
            if not enriched_df.empty and len(enriched_df) == len(summary):
                summary['cycle'] = enriched_df['cycle'].values

        if 'cycle' not in summary.columns:
            summary['cycle'] = 'Unknown'

        if 'category' not in summary.columns:
            return pd.DataFrame(columns=['category', 'cycle', 'master_cluster', 'amount'])

        return summary.merge(self.mapping_df[['category', 'master_cluster']], on='category', how='left')

    def _create_pivot(self, summary: pd.DataFrame) -> pd.DataFrame:
        return summary.pivot_table(
            index='cycle', columns='master_cluster', values='amount', 
            aggfunc=lambda x: x.abs().sum()
        ).fillna(0).round(2)

    def _calculate_budget_line(self, columns: pd.Index) -> pd.Series:
        return self.mapping_df.groupby('master_cluster')['theoretical_budget'].sum().reindex(columns, fill_value=0).round(2)

    def _apply_styles(self, writer, pivot, budget_line, mapping_df, details):
        wb, ws_p = writer.book, writer.sheets['Pilotage']
        styles = self._get_excel_styles(wb)

        # 1. Create Named Ranges for Mapping and Details
        map_links = self._create_named_ranges(wb, mapping_df, "Mapping", "MAP", 2)
        detail_links = self._create_named_ranges(wb, details, "Details", "DTL", 2, 
                                                group_cols=['cycle', 'master_cluster'])

        # 2. Header Navigation (Row 0)
        # Link the Cluster names to the Mapping tab
        ws_p.write(0, 0, "cycle", styles['header']) # Top-left corner
        for c_idx, cluster in enumerate(pivot.columns):
            target_map = map_links.get(str(cluster))
            if target_map:
                ws_p.write_url(0, c_idx + 1, f"internal:{target_map}", 
                               cell_format=styles['header'], string=str(cluster))
            else:
                ws_p.write(0, c_idx + 1, str(cluster), styles['header'])

        # 3. Write the Budget Line at Row 1
        ws_p.write(1, 0, "BUDGET THEORIQUE", styles['budget'])
        for c_idx, cluster in enumerate(pivot.columns):
            limit = float(budget_line.get(cluster, 0))
            ws_p.write_number(1, c_idx + 1, limit, styles['budget'])

        # 4. Style the Dashboard Data (Starting at Row 2)
        for r_idx, cycle in enumerate(pivot.index):
            ws_p.write(r_idx + 2, 0, str(cycle), styles['neutral'])
            for c_idx, cluster in enumerate(pivot.columns):
                val = float(pivot.loc[cycle, cluster])
                limit = float(budget_line.get(cluster, 0))
                st = self._determine_color(val, limit, cluster, styles)
                
                target_dtl = detail_links.get((str(cycle), str(cluster)))
                self._write_smart_cell(ws_p, r_idx + 2, c_idx + 1, val, st, target_dtl)

    def _create_named_ranges(self, wb, df, sheet, prefix, start_row, group_cols='master_cluster'):
        links = {}
        curr_row = int(start_row)
        
        for key, group in df.groupby(group_cols, sort=False):
            lookup_key = tuple(map(str, key)) if isinstance(key, tuple) else str(key)
            range_id = f"{prefix}_{abs(hash(lookup_key))}"
            
            group_len = len(group)
            end_row = curr_row + group_len - 1
            range_string = f"='{sheet}'!$A${curr_row}:$G${end_row}"
            
            wb.define_name(range_id, range_string)
            links[lookup_key] = range_id
            curr_row += group_len
            
        return links

    def _get_excel_styles(self, wb) -> Dict[str, Any]:
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

    def _determine_color(self, val: float, limit: float, cluster: str, styles: dict):
        if "0." in cluster or val == 0: 
            return styles['dark_green'] if val > 0 else styles['neutral']
        if val <= limit: 
            return styles['light_green'] if val > limit * 0.5 else styles['dark_green']
        return styles['orange'] if val <= limit * 1.5 else styles['red']

    def _write_smart_cell(self, sheet, row, col, val, fmt, target=None):
        if target and val > 0:
            sheet.write_url(row, col, f"internal:{target}", cell_format=fmt, string=str(round(val, 2)))
        else:
            sheet.write_number(row, col, val, fmt)