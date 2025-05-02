import pandas as pd
import numpy as np
import re

df = pd.read_csv('2025_03_31_ga_voting_corr1.csv', low_memory=False)
df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True)
df['year'] = df['date_parsed'].dt.year

country_codes = {
    "CHN": "China", "IRN": "Iran", "SAU": "Saudi Arabia", "ARE": "UAE",
    "IRQ": "Iraq", "QAT": "Qatar", "BHR": "Bahrain", "KWT": "Kuwait",
    "OMN": "Oman", "KOR": "South Korea", "ISR": "Israel"
}
manual_me_terms = [
    "Iran", "Iraq", "Syria", "Lebanon", "Israel", "Palestine", "Jordan", "Saudi Arabia",
    "Yemen", "Oman", "UAE", "United Arab Emirates", "Qatar", "Bahrain", "Kuwait", "Egypt", "Turkey",
    "Gaza", "abu nidal", "al-aqsa", "al-nusra", "al-qaeda", "aqi", "aqap", "aqim",
    "arab league", "badr organization", "fatah", "fatah al-islam", "free syrian army",
    "hamas", "harakat al-nujaba", "hay'at tahrir al-sham", "hezbollah", "houthis",
    "islamic jihad", "islamic state", "isis", "isil", "daesh", "jaish al-islam",
    "jaish al-mahdi", "kataib hezbollah", "kataib al-imam ali", "kurdistan freedom falcons",
    "krg", "kurdistan regional government", "pkk", "liwa al-tawhid", "muqtada al-sadr",
    "plo", "palestinian authority", "popular mobilization forces", "pmf", "hashd al-shaabi",
    "popular resistance committees", "al-shabaab", "sdf", "syrian democratic forces",
    "tahrir al-sham", "taliban", "ypg", "zahran alloush"
]

combined_terms = set(term.lower() for term in manual_me_terms)
me_pattern = '|'.join(re.escape(term) for term in combined_terms)
me_resolutions = df[df['title'].str.lower().str.contains(me_pattern, na=False)]['resolution'].unique()

def compute_metrics(subset_df):
    if subset_df.empty:
        return None
    total = len(subset_df)

    counts = subset_df.groupby(['ms_vote_1', 'ms_vote_2']).size().to_dict()
    get = lambda a, b: counts.get((a, b), 0)

    agree_yes = get('Y', 'Y')
    agree_no = get('N', 'N')
    agree_abs = get('A', 'A')
    opp_yn = get('Y', 'N')
    opp_ny = get('N', 'Y')

    identical_votes = agree_yes + agree_no + agree_abs
    P_o = identical_votes / total

    P_1Y = (get('Y','Y') + get('Y','N') + get('Y','A')) / total
    P_1N = (get('N','N') + get('N','Y') + get('N','A')) / total
    P_1A = (get('A','A') + get('A','Y') + get('A','N')) / total
    P_2Y = (get('Y','Y') + get('N','Y') + get('A','Y')) / total
    P_2N = (get('N','N') + get('Y','N') + get('A','N')) / total
    P_2A = (get('A','A') + get('Y','A') + get('N','A')) / total

    P_e = P_1Y * P_2Y + P_1N * P_2N + P_1A * P_2A
    kappa = (P_o - P_e) / (1 - P_e) if P_e != 1 else None

    s_map = {'Y': 1, 'A': 2, 'N': 3}
    try:
        numeric_votes = subset_df[['ms_vote_1', 'ms_vote_2']].map(s_map.get)
        vote_diffs = abs(numeric_votes['ms_vote_1'] - numeric_votes['ms_vote_2'])
        s_score = 1 - (2 * vote_diffs.mean() / 2) if not vote_diffs.empty else None
    except:
        s_score = None

    return {
        'total_votes': total,
        'agree_pct': 100 * P_o,
        'chance_pct': 100 * P_e,
        'kappa': kappa,
        'S_score': s_score
    }

def compute_all_metrics(df, c1, c2, subset_name, resolutions_filter=None):
    v1 = df[df['ms_code'] == c1]
    v2 = df[df['ms_code'] == c2]
    merged = pd.merge(v1, v2, on="resolution", suffixes=("_1", "_2"))
    merged = merged[(merged['ms_vote_1'] != 'X') & (merged['ms_vote_2'] != 'X')]
    merged['year'] = pd.to_datetime(merged['date_parsed_1'], errors='coerce').dt.year
    if resolutions_filter is not None:
        merged = merged[merged['resolution'].isin(resolutions_filter)]

    results = []
    for year, group in merged.groupby('year'):
        metrics = compute_metrics(group)
        if metrics:
            metrics.update({'year': year, 'interval': str(year), 'country_1': c1, 'country_2': c2, 'subset': subset_name})
            results.append(metrics)
    for start in range(1946, 2026, 5):
        end = start + 4
        mask = (merged['year'] >= start) & (merged['year'] <= end)
        group = merged[mask]
        metrics = compute_metrics(group)
        if metrics:
            metrics.update({'year': start, 'interval': f'{start}-{end}', 'country_1': c1, 'country_2': c2, 'subset': subset_name})
            results.append(metrics)
    return results

pairs = [
    ("CHN", "IRN"), ("CHN", "ARE"), ("CHN", "SAU"),
    ("CHN", "IRQ"), ("CHN", "QAT"), ("CHN", "BHR"),
    ("CHN", "KWT"), ("CHN", "OMN"), ("CHN", "ISR"),
    ("IRN", "KOR")
]

all_results = []
for c1, c2 in pairs:
    all_results.extend(compute_all_metrics(df, c1, c2, "All Votes"))
    all_results.extend(compute_all_metrics(df, c1, c2, "Middle East Votes", resolutions_filter=me_resolutions))

df_all = pd.DataFrame(all_results)
df_all['country_1'] = df_all['country_1'].map(country_codes)
df_all['country_2'] = df_all['country_2'].map(country_codes)

df_all.to_csv("china_iran_gulf_alignment_extended.csv", index=False)