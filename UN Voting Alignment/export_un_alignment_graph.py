import pandas as pd

df_all = pd.read_csv("china_iran_gulf_alignment_extended.csv")

output_path = "china_alignment_graph_data_with_intervals.xlsx"

metrics = {
    "agree_pct": "Raw Agreement %",
    "chance_pct": "Chance Agreement %",
    "kappa": "Cohen's Kappa",
    "S_score": "S-Score"
}

def get_china_subset(df, subset_label, use_interval=False):
    df = df[
        (df['country_1'] == 'China') &
        (df['year'] >= 1971) &
        (df['year'] <= 2024) &
        (df['subset'] == subset_label)
    ]
    if not use_interval:
        df = df[df['interval'].astype(str) == df['year'].astype(str)]
    else:
        df = df[df['interval'].astype(str) != df['year'].astype(str)]
    return df

with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
    for subset_label, prefix in [("All Votes", "All"), ("Middle East Votes", "ME")]:
        
        china_df_yearly = get_china_subset(df_all, subset_label, use_interval=False)
        for metric, sheet_title in metrics.items():
            pivot = china_df_yearly.pivot(index="year", columns="country_2", values=metric)
            sheet_name = f"{prefix}_Y_{sheet_title}"[:31]
            pivot.to_excel(writer, sheet_name=sheet_name)
        
        china_df_interval = get_china_subset(df_all, subset_label, use_interval=True)
        for metric, sheet_title in metrics.items():
            pivot = china_df_interval.pivot(index="interval", columns="country_2", values=metric)
            sheet_name = f"{prefix}_5Y_{sheet_title}"[:31]
            pivot.to_excel(writer, sheet_name=sheet_name).
