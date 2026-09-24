import streamlit as st

from model.models import DataQualityReport


def render_quality_panel(quality: DataQualityReport) -> None:
    if not quality.alert_count:
        return

    with st.expander(
        f"⚠️ Qualité des données — {quality.alert_count} point(s) à vérifier"
    ):
        if quality.duplicate_transaction_count:
            st.warning(
                f"{quality.duplicate_transaction_count} ligne(s) d'opération "
                "strictement identique(s) ont été détectée(s). Elles restent "
                "incluses dans les calculs."
            )
        if quality.auto_classified_categories:
            st.warning(
                f"{len(quality.auto_classified_categories)} catégorie(s) sans "
                "mapping manuel ont été classées automatiquement."
            )
            st.write(", ".join(quality.auto_classified_categories))
        if quality.unused_budget_targets:
            st.warning(
                f"{len(quality.unused_budget_targets)} entrée(s) de budget ne "
                "correspondent à aucune catégorie ni aucun cluster et n'ont "
                "donc aucun effet."
            )
            st.write(", ".join(quality.unused_budget_targets))
