#!/usr/bin/env python

# /// script
# dependencies = [
#   "beautifulsoup4",
#   "lxml",
#   "matplotlib",
#   "numpy",
#   "pandas",
#   "requests",
#   "seaborn",
# ]
# ///

import sys
import time
from datetime import datetime
from pathlib import Path

import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


DEPLOY_URL = "https://andre-rendeiro.com/"
AUTHOR_NAME = "André F. Rendeiro"
SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_DIR = SCRIPT_DIR.parent

DATA_DIR = REPO_DIR / "data"
OUTPUT_DIR = REPO_DIR / "viz"

PUBS_CSV = DATA_DIR / "publications.csv"
TALKS_CSV = DATA_DIR / "talks.csv"
GRANTS_CSV = DATA_DIR / "grants.csv"
SUPERVISION_CSV = DATA_DIR / "supervision.csv"
SOFTWARE_CSV = DATA_DIR / "software.csv"

DATE = datetime.now().isoformat().split("T")[0]
CURRENT_YEAR = int(DATE.split("-")[0])

OUTPUT_DIR.mkdir(exist_ok=True)

figkws = dict(dpi=300, bbox_inches="tight")

plt.rcParams["text.usetex"] = False
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["font.family"] = "DejaVu Sans"


def load_publications():
    pubs = pd.read_csv(PUBS_CSV, comment="#").set_index("doi")
    missing = pubs.loc[~pubs["authors"].str.contains(AUTHOR_NAME)]
    if not missing.empty:
        join = "    - ".join(missing["title"])
        reason = f"Some publications authors field missing including '{AUTHOR_NAME}': \n    - {join}"
        assert missing.empty, reason

    pubs["years_old"] = CURRENT_YEAR - pubs["year"]
    pubs["is_first_author"] = pubs["authors"].str.split(",").str[0].str.contains(AUTHOR_NAME)
    pubs["is_last_author"] = pubs["authors"].str.split(",").str[-1].str.contains(AUTHOR_NAME)
    pubs["is_corresponding"] = pubs["authors"].str.contains(r"\*|\$\^\\Omega\$")
    pubs["is_preprint"] = pubs["publication_type"].str.lower().str.contains("preprint")
    pubs["is_review"] = pubs["publication_type"].str.lower().str.contains("review")
    pubs["is_journal"] = ~pubs["is_preprint"] & ~pubs["is_review"] & pubs["publication_type"].str.lower().str.contains("journal")
    pubs["is_opinion"] = pubs["publication_type"].str.lower().str.contains("opinion")

    pubs["total_authors"] = pubs["authors"].str.count(",") + 1

    def get_author_position(authors_str):
        clean = authors_str.replace("*", "").replace("$\\Omega$", "")
        authors_list = [a.strip() for a in clean.split(",")]
        try:
            return authors_list.index(AUTHOR_NAME) + 1
        except ValueError:
            return -1

    pubs["author_absolute_position"] = pubs["authors"].apply(get_author_position)
    pubs["author_relative_position"] = (pubs["author_absolute_position"] - 1) / (pubs["total_authors"] - 1)
    pubs["author_role"] = np.where(pubs["is_first_author"], "first",
                      np.where(pubs["is_last_author"], "last",
                      np.where(pubs["author_relative_position"] > 0.5, "senior", "middle")))

    return pubs


def load_talks():
    talks = pd.read_csv(TALKS_CSV, comment="#")
    talks["year"] = pd.to_datetime(talks["date"]).dt.year
    talks["is_online"] = talks["location"].str.lower().str.contains("online")
    talks["event_type"] = talks["event_type"].str.lower()
    return talks


def load_grants():
    grants = pd.read_csv(GRANTS_CSV, comment="#")
    grants["year_applied"] = grants["year_applied"].astype(int)
    grants["outcome"] = grants["outcome"].str.lower().fillna("pending")

    def parse_amount(amount_str):
        if pd.isna(amount_str) or amount_str == "":
            return 0.0
        amount_str = str(amount_str).upper()
        multiplier = 1_000_000 if "M" in amount_str else 1_000 if "K" in amount_str else 1
        try:
            return float("".join(c for c in amount_str if c.isdigit() or c == ".")) * multiplier
        except ValueError:
            return 0.0

    grants["amount_euro"] = grants["amount"].apply(parse_amount)
    grants["is_awarded"] = grants["outcome"] == "awarded"
    grants["is_rejected"] = grants["outcome"] == "rejected"
    grants["grant_type"] = grants["type"].str.lower()

    return grants


def load_supervision():
    sup = pd.read_csv(SUPERVISION_CSV, comment="#")

    def parse_year_range(year_str):
        if pd.isna(year_str):
            return CURRENT_YEAR
        if "/" in str(year_str):
            return int(str(year_str).split("/")[0])
        return int(year_str)

    sup["year_start"] = sup["year_start"].apply(parse_year_range)
    sup["year_end"] = sup["year_end"].apply(parse_year_range)
    sup["duration_years"] = sup["year_end"] - sup["year_start"]
    sup["student_role"] = sup["role"].fillna("unknown")
    sup["my_role"] = sup["level"].fillna("sole").replace("", "sole")
    sup["is_co_supervisor"] = sup["my_role"].str.lower().str.contains("co")
    sup["is_sole"] = ~sup["is_co_supervisor"] & (sup["my_role"].str.lower() == "sole")

    return sup


def load_software():
    sw = pd.read_csv(SOFTWARE_CSV, comment="#")
    sw["is_author"] = sw["role"].str.lower() == "author"
    sw["is_contributor"] = sw["role"].str.lower() == "contributor"
    sw["category"] = sw["category"].str.lower()
    return sw


def crawl_form_metrics(pubs_df: pd.DataFrame):
    import urllib.parse

    metrics = dict()
    
    for i, doi in enumerate(pubs_df.index):
        if pd.isna(doi) or doi == "":
            metrics[doi] = dict(citations=0, altmetrics=0)
            continue
        try:
            url = f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(doi, safe='')}"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                citations = data.get("cited_by_count", 0)
                altmetrics = data.get("altmetrics_score", 0) if data.get("altmetrics") else 0
                metrics[doi] = dict(citations=citations, altmetrics=altmetrics)
            else:
                metrics[doi] = dict(citations=0, altmetrics=0)
        except Exception:
            metrics[doi] = dict(citations=0, altmetrics=0)
        
        if i < len(pubs_df) - 1:
            time.sleep(0.12)
    
    quant = pd.DataFrame(metrics).T.rename_axis(index="doi")
    return quant


def plot_publications(df: pd.DataFrame):
    """Publication trends: counts by year, stratified by type"""
    w = 2.5

    fig, axes = plt.subplots(1, 3, figsize=(3 * w * 2, 1 * w))

    g = df.groupby("year").size().rename("count").reset_index()
    sns.barplot(data=g, x="year", y="count", ax=axes[0])
    axes[0].set(xlabel="Year", ylabel="Publications")
    axes[0].tick_params(axis="x", rotation=45)

    cumulative = g.copy()
    cumulative["cumulative"] = g["count"].cumsum()
    sns.barplot(data=cumulative, x="year", y="cumulative", ax=axes[1])
    axes[1].set(xlabel="Year", ylabel="Publications (cumulative)")
    axes[1].tick_params(axis="x", rotation=45)

    type_counts = df.groupby(["year", "publication_type"]).size().reset_index(name="count")
    sns.barplot(data=type_counts, x="year", y="count", hue="publication_type", ax=axes[2])
    axes[2].set(xlabel="Year", ylabel="Publications by type")
    axes[2].tick_params(axis="x", rotation=45)

    fig.savefig(OUTPUT_DIR / "01_publications.svg", **figkws)
    plt.close()


def plot_citations(df: pd.DataFrame, quant: pd.DataFrame):
    """Citation trends"""
    w = 2.5

    df_full = df.join(quant)
    df_full[quant.columns] = df_full[quant.columns].fillna(0) + 1

    fig, axes = plt.subplots(1, 3, figsize=(3 * w * 2, 1 * w))

    g = df_full.groupby("year")["citations"].sum().reset_index()
    sns.barplot(data=g, x="year", y="citations", ax=axes[0])
    axes[0].set(xlabel="Year", ylabel="Citations")
    axes[0].tick_params(axis="x", rotation=45)

    g_cum = df_full.groupby("year")["citations"].sum().cumsum().reset_index()
    sns.barplot(data=g_cum, x="year", y="citations", ax=axes[1])
    axes[1].set(xlabel="Year", ylabel="Citations (cumulative)")
    axes[1].tick_params(axis="x", rotation=45)

    c = axes[2].scatter(df_full["years_old"], df_full["citations"],
                       c=df_full["year"], cmap="inferno", alpha=0.6, edgecolor="black")
    axes[2].set(xlabel="Paper age (years)", ylabel="Citations", yscale="log")
    axes[2].set_ylim(bottom=0.9)
    plt.colorbar(c, ax=axes[2], label="Year")

    fig.savefig(OUTPUT_DIR / "02_citations.svg", **figkws)
    plt.close()


def plot_author_positions(df: pd.DataFrame, quant: pd.DataFrame):
    """Author position trends"""
    w = 2.5

    df_full = df.join(quant)

    fig, axes = plt.subplots(1, 3, figsize=(3 * w * 2, 1 * w))

    axes[0].scatter(df_full["year"], df_full["author_relative_position"],
                   c=df_full["year"], cmap="inferno", alpha=0.6, edgecolor="black")
    axes[0].set(xlabel="Year", ylabel="Relative author position")
    axes[0].invert_yaxis()

    role_counts = df_full.groupby(["year", "author_role"]).size().reset_index(name="count")
    sns.barplot(data=role_counts, x="year", y="count", hue="author_role", ax=axes[1])
    axes[1].set(xlabel="Year", ylabel="Count by role")
    axes[1].tick_params(axis="x", rotation=45)

    senior_papers = df_full[(df_full["author_role"] == "first") | (df_full["author_role"] == "last")]
    role_pct = senior_papers.groupby("year").size() / df_full.groupby("year").size() * 100
    role_pct = role_pct.reset_index(name="percentage")
    sns.barplot(data=role_pct, x="year", y="percentage", ax=axes[2])
    axes[2].set(xlabel="Year", ylabel="Lead author papers (%)")
    axes[2].tick_params(axis="x", rotation=45)

    fig.savefig(OUTPUT_DIR / "03_author_positions.svg", **figkws)
    plt.close()


def plot_talks(talks: pd.DataFrame):
    """Talk/presentation trends"""
    w = 2.5

    fig, axes = plt.subplots(1, 3, figsize=(3 * w * 2, 1 * w))

    g = talks.groupby("year").size().reset_index(name="count")
    sns.barplot(data=g, x="year", y="count", ax=axes[0])
    axes[0].set(xlabel="Year", ylabel="Number of talks")
    axes[0].tick_params(axis="x", rotation=45)

    type_counts = talks.groupby(["year", "event_type"]).size().reset_index(name="count")
    sns.barplot(data=type_counts, x="year", y="count", hue="event_type", ax=axes[1])
    axes[1].set(xlabel="Year", ylabel="Talks by type")
    axes[1].tick_params(axis="x", rotation=45)

    online_counts = talks.groupby("is_online").size().reset_index(name="count")
    sns.barplot(data=online_counts, x="is_online", y="count", ax=axes[2])
    axes[2].set(xlabel="Online", ylabel="Number of talks")

    fig.savefig(OUTPUT_DIR / "04_talks.svg", **figkws)
    plt.close()


def plot_supervision(sup: pd.DataFrame):
    """Mentorship tracking"""
    w = 2.5

    sup = sup.copy()
    sup["year_end"] = sup["year_end"].fillna(CURRENT_YEAR)
    max_year = max(CURRENT_YEAR, sup["year_end"].max())
    min_year = sup["year_start"].min()
    years = list(range(min_year, max_year + 1))

    yearly_active = []
    yearly_started = []
    yearly_exited = []
    for year in years:
        active_this_year = sup[(sup["year_start"] <= year) & (sup["year_end"] >= year)]
        started_this_year = sup[sup["year_start"] == year]
        exited_this_year = sup[(sup["year_end"] == year) & (sup["year_end"] < CURRENT_YEAR)]
        
        yearly_active.append({"year": year, "count": len(active_this_year)})
        yearly_started.append({"year": year, "count": len(started_this_year)})
        yearly_exited.append({"year": year, "count": len(exited_this_year)})
    
    active_df = pd.DataFrame(yearly_active)
    started_df = pd.DataFrame(yearly_started)
    exited_df = pd.DataFrame(yearly_exited)

    ongoing = sup[sup["year_end"] >= CURRENT_YEAR - 1]

    fig, axes = plt.subplots(2, 3, figsize=(3 * w * 2, 2 * w))

    sns.barplot(data=active_df, x="year", y="count", ax=axes[0, 0])
    axes[0, 0].set(xlabel="Year", ylabel="People supervised")
    axes[0, 0].tick_params(axis="x", rotation=45)

    sns.barplot(data=started_df, x="year", y="count", ax=axes[0, 1])
    axes[0, 1].set(xlabel="Year", ylabel="Started")
    axes[0, 1].tick_params(axis="x", rotation=45)

    sns.barplot(data=exited_df, x="year", y="count", ax=axes[0, 2])
    axes[0, 2].set(xlabel="Year", ylabel="Exited")
    axes[0, 2].tick_params(axis="x", rotation=45)

    role_counts = sup.groupby("student_role").size().reset_index(name="count")
    sns.barplot(data=role_counts, x="student_role", y="count", ax=axes[1, 0])
    axes[1, 0].set(xlabel="Student role", ylabel="Total count")
    axes[1, 0].tick_params(axis="x", rotation=45)

    active_counts = ongoing.groupby("student_role").size().reset_index(name="count")
    sns.barplot(data=active_counts, x="student_role", y="count", ax=axes[1, 1])
    axes[1, 1].set(xlabel="Currently active", ylabel="Count")
    axes[1, 1].tick_params(axis="x", rotation=45)

    net_change = pd.DataFrame({
        "year": years,
        "net": [len(sup[sup["year_start"] == y]) - len(sup[(sup["year_end"] == y) & (sup["year_end"] < CURRENT_YEAR)]) for y in years]
    })
    sns.barplot(data=net_change, x="year", y="net", ax=axes[1, 2])
    axes[1, 2].set(xlabel="Year", ylabel="Net change")
    axes[1, 2].axhline(0, color="black", linestyle="--", alpha=0.3)
    axes[1, 2].tick_params(axis="x", rotation=45)

    fig.savefig(OUTPUT_DIR / "05_supervision.svg", **figkws)
    plt.close()


def plot_grants(grants: pd.DataFrame):
    """Grant progression"""
    w = 2.5

    fig, axes = plt.subplots(1, 3, figsize=(3 * w * 2, 1 * w))

    applied = grants.groupby("year_applied").size().reset_index(name="applied")
    awarded = grants[grants["is_awarded"]].groupby("year_applied").size().reset_index(name="awarded")
    combined = pd.merge(applied, awarded, on="year_applied", how="left").fillna(0)
    combined_m = combined.melt(id_vars="year_applied", var_name="outcome", value_name="count")
    sns.barplot(data=combined_m, x="year_applied", y="count", hue="outcome", ax=axes[0])
    axes[0].set(xlabel="Year applied", ylabel="Grant applications")
    axes[0].legend(title="Outcome")
    axes[0].tick_params(axis="x", rotation=45)

    awarded_amounts = grants[grants["is_awarded"]].groupby("year_applied")["amount_euro"].sum().reset_index()
    sns.barplot(data=awarded_amounts, x="year_applied", y="amount_euro", ax=axes[1])
    axes[1].set(xlabel="Year", ylabel="Funding (EUR)")
    axes[1].tick_params(axis="x", rotation=45)

    type_counts = grants[grants["is_awarded"]].groupby("grant_type").size().reset_index(name="count")
    sns.barplot(data=type_counts, x="grant_type", y="count", ax=axes[2])
    axes[2].set(xlabel="Grant type", ylabel="Awarded grants")

    fig.savefig(OUTPUT_DIR / "06_grants.svg", **figkws)
    plt.close()


def plot_software(sw: pd.DataFrame):
    """Software metrics"""
    w = 2.5

    fig, axes = plt.subplots(1, 2, figsize=(2 * w * 2, 1 * w))

    role_counts = sw.groupby("role").size().reset_index(name="count")
    sns.barplot(data=role_counts, x="role", y="count", ax=axes[0])
    axes[0].set(xlabel="Role", ylabel="Number of tools")

    cat_counts = sw.groupby("category").size().reset_index(name="count")
    sns.barplot(data=cat_counts, x="category", y="count", ax=axes[1])
    axes[1].set(xlabel="Category", ylabel="Number of tools")
    axes[1].tick_params(axis="x", rotation=45)

    fig.savefig(OUTPUT_DIR / "07_software.svg", **figkws)
    plt.close()


def plot_annual_summary(df: pd.DataFrame, talks: pd.DataFrame,
                       grants: pd.DataFrame, sup: pd.DataFrame):
    """Annual summary dashboard"""
    w = 3

    years = sorted(df["year"].unique())
    max_year = max(years) if years else CURRENT_YEAR
    min_year = min(years) if years else CURRENT_YEAR - 5
    year_range = list(range(min_year, max_year + 1))

    sup = sup.copy()
    sup["year_end"] = sup["year_end"].fillna(CURRENT_YEAR)

    summary = []
    for year in year_range:
        n_pubs = len(df[df["year"] == year])
        n_talks = len(talks[talks["year"] == year])
        n_grants = len(grants[(grants["year_applied"] == year) & grants["is_awarded"]])
        n_supervised = len(sup[(sup["year_start"] <= year) & (sup["year_end"] >= year)])
        summary.append({
            "year": year,
            "publications": n_pubs,
            "talks": n_talks,
            "grants_awarded": n_grants,
            "people_supervised": n_supervised
        })

    summary_df = pd.DataFrame(summary)

    fig, axes = plt.subplots(2, 2, figsize=(2 * w, 2 * w))

    for ax, col in zip(axes.flat, summary_df.columns[1:]):
        sns.barplot(data=summary_df, x="year", y=col, ax=ax)
        ax.set(xlabel="Year", ylabel=col.replace("_", " ").title())
        ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "08_annual_summary.svg", **figkws)
    plt.close()

    summary_df.to_csv(OUTPUT_DIR / "annual_summary.csv", index=False)


def plot_contrast(df: pd.DataFrame, talks: pd.DataFrame, grants: pd.DataFrame, sup: pd.DataFrame, quant: pd.DataFrame):
    """Contrast visualizations comparing different metrics"""
    w = 2.5

    df_full = df.join(quant).copy()
    sup_full = sup.copy()
    sup_full["year_end"] = sup_full["year_end"].fillna(CURRENT_YEAR)
    grants_full = grants.copy()

    fig, axes = plt.subplots(2, 3, figsize=(3 * w * 2, 2 * w))

    year_summary = []
    for year in sorted(df_full["year"].unique()):
        year_summary.append({
            "year": year,
            "publications": len(df_full[df_full["year"] == year]),
            "citations": df_full[df_full["year"] == year]["citations"].sum()
        })
    year_sum = pd.DataFrame(year_summary)
    ax = axes[0, 0]
    ax.bar(year_sum["year"] - 0.2, year_sum["publications"], width=0.4, label="Papers", color="steelblue", alpha=0.7)
    ax.bar(year_sum["year"] + 0.2, year_sum["citations"] / 50, width=0.4, label="Citations/50", color="coral", alpha=0.7)
    ax.set(xlabel="Year", ylabel="Count")
    ax.set_title("Papers vs Citations", fontsize=10)
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=45)

    grants_full["year_applied"] = grants_full["year_applied"].astype(int)
    grants_year = grants_full.groupby(["year_applied", "outcome"]).size().reset_index(name="count")
    grants_year = grants_year[grants_year["year_applied"] >= 2018]
    ax = axes[0, 1]
    sns.barplot(data=grants_year, x="year_applied", y="count", hue="outcome", ax=ax)
    ax.set(xlabel="Year applied", ylabel="Grants")
    ax.set_title("Grant applications", fontsize=10)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(fontsize=8, loc="upper left")

    type_cites = df_full.groupby("publication_type")["citations"].sum().reset_index()
    ax = axes[0, 2]
    sns.barplot(data=type_cites, x="publication_type", y="citations", ax=ax, palette="viridis")
    ax.set(xlabel="Publication type", ylabel="Total citations")
    ax.set_title("Citations by type", fontsize=10)
    ax.tick_params(axis="x", rotation=45)

    role_cites = df_full.groupby("author_role")["citations"].agg(["sum", "mean", "count"]).reset_index()
    ax = axes[1, 0]
    x = np.arange(len(role_cites))
    width = 0.25
    ax.bar(x - width, role_cites["sum"], width, label="Total", color="steelblue", alpha=0.7)
    ax.bar(x, role_cites["mean"] * 10, width, label="Mean*10", color="coral", alpha=0.7)
    ax.bar(x + width, role_cites["count"], width, label="Count", color="seagreen", alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(role_cites["author_role"], rotation=45)
    ax.set(xlabel="Author role", ylabel="Count")
    ax.set_title("Citations by role", fontsize=10)
    ax.legend(fontsize=8)

    yearly_sup = []
    for year in sorted(df_full["year"].unique()):
        active = len(sup_full[(sup_full["year_start"] <= year) & (sup_full["year_end"] >= year)])
        pubs = len(df_full[df_full["year"] == year])
        yearly_sup.append({"year": year, "supervised": active, "publications": pubs})
    sup_pub = pd.DataFrame(yearly_sup)
    ax = axes[1, 1]
    ax.scatter(sup_pub["supervised"], sup_pub["publications"], c=sup_pub["year"], cmap="viridis", s=60, alpha=0.7)
    for _, row in sup_pub.iterrows():
        ax.annotate(str(int(row["year"])), (row["supervised"], row["publications"]), fontsize=7)
    ax.set(xlabel="People supervised", ylabel="Publications")
    ax.set_title("Supervision vs Productivity", fontsize=10)

    activity = []
    for year in sorted(df_full["year"].unique()):
        activity.append({
            "year": year,
            "publications": len(df_full[df_full["year"] == year]),
            "talks": len(talks[talks["year"] == year]),
            "supervised": len(sup_full[(sup_full["year_start"] <= year) & (sup_full["year_end"] >= year)])
        })
    act_df = pd.DataFrame(activity)
    ax = axes[1, 2]
    act_m = act_df.melt(id_vars="year", var_name="metric", value_name="count")
    sns.barplot(data=act_m, x="year", y="count", hue="metric", ax=ax, palette="viridis")
    ax.set(xlabel="Year", ylabel="Count")
    ax.set_title("Activity overview", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "09_contrast.svg", **figkws)
    plt.close()


def main() -> int:
    pubs = load_publications()
    talks = load_talks()
    grants = load_grants()
    sup = load_supervision()
    software = load_software()

    quant = crawl_form_metrics(pubs)

    plot_publications(pubs)

    plot_citations(pubs, quant)

    plot_author_positions(pubs, quant)

    plot_talks(talks)

    plot_supervision(sup)

    plot_grants(grants)

    plot_software(software)

    plot_annual_summary(pubs, talks, grants, sup)

    plot_contrast(pubs, talks, grants, sup, quant)

    pubs_joined = pubs.join(quant)
    pubs_joined[quant.columns] = pubs_joined[quant.columns].fillna(0) + 1
    pubs_joined.to_csv(OUTPUT_DIR / "publication_stats.csv")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)