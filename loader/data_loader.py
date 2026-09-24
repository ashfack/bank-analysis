from io import StringIO
import os
from typing import Dict, List
import pandas as pd
from config.config import (
    CSV_SEP, ENCODING, COL_RAW_DATE, COL_RAW_AMOUNT, 
    COL_RAW_CATEGORY, COL_RAW_CLUSTER, COL_RAW_OVERRIDE, DOMAIN_DATE
)
from model.models import Transaction

class DataLoader:

    @staticmethod
    def load_category_cluster_map(path: str) -> Dict[str, str]:
        if not os.path.exists(path): return {}
        
        df = pd.read_csv(path, sep=CSV_SEP, encoding=ENCODING)
        
        # Use constants to zip the mapping
        if COL_RAW_CATEGORY in df.columns and COL_RAW_CLUSTER in df.columns:
            duplicated_categories = df.loc[
                df[COL_RAW_CATEGORY].duplicated(keep=False),
                COL_RAW_CATEGORY,
            ].dropna().astype(str).unique()
            if duplicated_categories.size:
                duplicates = ", ".join(sorted(duplicated_categories))
                raise ValueError(f"Duplicate category mappings: {duplicates}")
            return dict(zip(df[COL_RAW_CATEGORY], df[COL_RAW_CLUSTER]))
        return {}
    
    @staticmethod
    def load_budget_overrides(path: str) -> Dict[str, str]:
        if not os.path.exists(path): return {}
        
        valid_rows = []
        with open(path, 'r', encoding=ENCODING) as f:
            for line in f:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith('#'):
                    valid_rows.append(clean_line)
        
        if not valid_rows: return {}
        
        try:
            df = pd.read_csv(StringIO("\n".join(valid_rows)), sep=CSV_SEP)
            
            if COL_RAW_CATEGORY in df.columns and COL_RAW_OVERRIDE in df.columns:
                return dict(zip(df[COL_RAW_CATEGORY], df[COL_RAW_OVERRIDE]))
        except Exception as e:
            # Line 42: This is the line that was 'Missing'
            print(f"⚠️ Error parsing overrides: {e}")
            
        return {}
    
    @staticmethod
    def prepare_transaction_data(path: str) -> List[Transaction]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Input data not found at {path}")
            
        df = pd.read_csv(path, sep=CSV_SEP, encoding=ENCODING)
        
        # Validation using constants
        required = {COL_RAW_DATE, COL_RAW_AMOUNT}
        if not required.issubset(df.columns):
            missing = required - set(df.columns)
            raise ValueError(f"File at {path} missing required columns: {missing}")

        # European Cleaning Logic
        df[COL_RAW_AMOUNT] = (df[COL_RAW_AMOUNT].astype(str)
                              .str.replace(r'[\xa0 ]', '', regex=True)
                              .str.replace(',', '.')
                              .astype(float))
        
        # Domain Mapping: Technical -> Domain
        df[DOMAIN_DATE] = pd.to_datetime(df[COL_RAW_DATE])
        
        # 2. Conversion: DataFrame -> List[Transaction]
        # This is where we enforce the 'Contract'
        transactions = [
            Transaction(
                dateOperation=row[DOMAIN_DATE],
                label=str(row.get('label', 'Unknown')), # Assume 'label' is a standard
                amount=row[COL_RAW_AMOUNT],
                category=row[COL_RAW_CATEGORY]
            )
            for _, row in df.iterrows()
        ]
        
        # Sort by date before returning
        return sorted(transactions, key=lambda x: x.dateOperation)
