#!/usr/bin/env python

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup


AUTHOR_NAME = "André F. Rendeiro"
PUBS_TEX = {"_cv.tex": "cv.tex", "_lop.tex": "lop.tex"}
INDENT = "        "
GRANTS_AWARDS_FORMAT = (
    r"""\cventry{{{time}}}{{{title}}},{{{entity}}}{{{role}}}{{}}{{}}"""
)
grant_fields = [
    "time",
    "outcome",
    "title",
    "entity",
    "role",
    "amount",
    "comment",
]
PUB_FORMAT = """\\item {authors}. \\textbf{{{title}}}. {journal} ({year}).\n"""
PUB_FORMAT += """{indent}\\href{{https://dx.doi.org/{doi}}}{{doi:{doi}}}"""
PUBS_CSV = Path("data/publications.csv")
GRANTS_CSV = Path("data/grants.csv")
TEACHING_CSV = Path("data/teaching.csv")
SUPERVISION_CSV = Path("data/supervision.csv")
COURSES_CSV = Path("data/courses_attended.csv")
ADMIN_CSV = Path("data/administrative.csv")
SOFTWARE_CSV = Path("data/software.csv")
PATENTS_CSV = Path("data/patents.csv")
TALKS_CSV = Path("data/talks.csv")
POSTERS_CSV = Path("data/posters.csv")
INPUT_DIR = Path("source")
OUTPUT_DIR = Path("source")
DATE = datetime.now().isoformat().split("T")[0]
GOOGLE_SCHOLAR_ID = "lj17pqEAAAAJ"
LAST_AUTHOR_SIGN = r"$^\\Omega$"
main_pub_types = ["journal", "review"]
preprint_types = ["preprint"]
alt_pub_types = ["opinion"]


def main() -> int:
    pubs = pd.read_csv(PUBS_CSV, comment="#").query("publication_type != 'unpublished'")
    missing = pubs.loc[~pubs["authors"].str.contains(AUTHOR_NAME)]
    join = "    - ".join(missing["title"])
    reason = f"Some publications authors field missing including '{AUTHOR_NAME}': \n    - {join}"
    assert missing.empty, reason

    grants_awards = (
        pd.read_csv(GRANTS_CSV, comment="#")
        .query("applicant == @AUTHOR_NAME")
        .replace(pd.NA, "")
    ).sort_values("year_applied", ascending=False)
    grants_awards["time"] = (
        grants_awards["year_start"].astype(pd.Int64Dtype()).astype(str)
    )
    s = grants_awards["year_end"].notna()
    grants_awards.loc[s, "time"] = (
        grants_awards.loc[s, "year_start"].astype(pd.Int64Dtype()).astype(str)
        + " - "
        + grants_awards.loc[s, "year_end"].astype(pd.Int64Dtype()).astype(str)
    )
    s = grants_awards["year_start"].isna()
    grants_awards.loc[s, "time"] = grants_awards.loc[s, "year_applied"].astype(str)

    grants_awards_list = list()
    for _, g in grants_awards.iterrows():
        p = GRANTS_AWARDS_FORMAT.format(
            **g[grant_fields].to_dict(), indent=INDENT
        ).replace("},{", "}{")
        grants_awards_list.append(p)

    pub_list = list()
    for _, pub in pubs.query("publication_type.isin(@main_pub_types)").iterrows():
        p = PUB_FORMAT.format(**pub.to_dict(), indent=INDENT)
        p = p.replace(AUTHOR_NAME, f"\\underline{{{AUTHOR_NAME}}}")
        pub_list.append(p)

    preprint_list = list()
    for _, pub in pubs.query("publication_type.isin(@preprint_types)").iterrows():
        p = PUB_FORMAT.format(**pub.to_dict(), indent=INDENT)
        p = p.replace(AUTHOR_NAME, f"\\underline{{{AUTHOR_NAME}}}")
        preprint_list.append(p)

    alt_list = list()
    for _, pub in pubs.query("publication_type.isin(@alt_pub_types)").iterrows():
        p = PUB_FORMAT.format(**pub.to_dict(), indent=INDENT)
        p = p.replace(AUTHOR_NAME, f"\\underline{{{AUTHOR_NAME}}}")
        alt_list.append(p)

    metrics = get_google_scholar_metrics()
    n_preprints = pubs.query("publication_type.isin(@preprint_types)").shape[0]
    n_peer_reviewed = pubs.query("publication_type.isin(@main_pub_types)").shape[0]
    ff = AUTHOR_NAME + r"\*"
    n_first_author = pubs.query(
        f"authors.str.startswith(@AUTHOR_NAME) | authors.str.contains('{ff}')"
    ).shape[0]
    ll = AUTHOR_NAME + LAST_AUTHOR_SIGN
    n_last_author = pubs.query(f"authors.str.contains('{ll}', regex=False)").shape[0]

    teaching_list = format_teaching()
    supervision_list = format_supervision()
    courses_list = format_courses()
    admin_list = format_administrative()
    software_list = format_software()
    patents_list = format_patents()
    talks_list = format_talks()
    posters_list = format_posters()

    phrases = [
        f"Publications: {pubs.shape[0]} ({n_peer_reviewed} peer reviewed, {n_preprints} preprints, {n_first_author} first-author, {n_last_author} last-author)",
        f"Citations: {metrics['citations']} (last 5 years: {metrics['citations_5_years']})",
        f"h-index: {metrics['h_index']} (last 5 years: {metrics['h_index_5_years']})",
        f"Google Scholar Profile: \\href{{https://scholar.google.com/citations?user={GOOGLE_SCHOLAR_ID}}}{{https://scholar.google.com/citations?user={GOOGLE_SCHOLAR_ID}}}",
    ]
    metrics_text = "    ".join([f"\\cvitem{{}}{{\n{INDENT}{ph}}}\n" for ph in phrases])

    for input_file, output_file in PUBS_TEX.items():
        with open(INPUT_DIR / input_file, "r") as handle:
            content = (
                handle.read()
                .replace(
                    "{{grants_awards_go_here}}",
                    ("\n" + INDENT).join(grants_awards_list),
                )
                .replace("{{publications_go_here}}", ("\n\n" + INDENT).join(pub_list))
                .replace("{{preprints_go_here}}", ("\n\n" + INDENT).join(preprint_list))
                .replace("{{alt_pubs_go_here}}", ("\n\n" + INDENT).join(alt_list))
                .replace("{{metrics_go_here}}", metrics_text)
                .replace("{{teaching_go_here}}", teaching_list)
                .replace("{{supervision_go_here}}", supervision_list)
                .replace("{{courses_go_here}}", courses_list)
                .replace("{{administrative_go_here}}", admin_list)
                .replace("{{software_go_here}}", software_list)
                .replace("{{patents_go_here}}", patents_list)
                .replace("{{talks_go_here}}", talks_list)
                .replace("{{posters_go_here}}", posters_list)
                .replace("{{current_date}}", DATE)
            )

        with open(OUTPUT_DIR / output_file, "w") as handle:
            handle.write(content)

    return 0


def get_google_scholar_metrics():
    """
    Get metrics from Google Scholar profile
    """
    url = f"https://scholar.google.at/citations?user={GOOGLE_SCHOLAR_ID}&hl=en"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(executable_path="/usr/bin/chromedriver")
    with webdriver.Chrome(service=service, options=options) as driver:
        driver.get(url)
        html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    metrics = soup.find_all("td", class_="gsc_rsb_std")
    citations = metrics[0].text
    citations_5_years = metrics[1].text
    h_index = metrics[2].text
    h_index_5_years = metrics[3].text
    return pd.Series(
        [citations, citations_5_years, h_index, h_index_5_years],
        ["citations", "citations_5_years", "h_index", "h_index_5_years"],
    )


def format_teaching():
    df = pd.read_csv(TEACHING_CSV, comment="#").replace(pd.NA, "")
    items = []
    for _, row in df.iterrows():
        year = str(row.get("year", ""))
        recurring = " - present" if pd.notna(row.get("recurring")) else ""
        desc = row.get("name", "").replace("_", r"\_")
        items.append(f"\\cvitem{{{year}{recurring}}}{{{desc}}}")
    return INDENT + ("\n" + INDENT).join(items)


def format_supervision():
    df = pd.read_csv(SUPERVISION_CSV, comment="#").replace(pd.NA, "")
    items = []
    for _, row in df.iterrows():
        start = str(row.get("year_start", ""))
        end = str(row.get("year_end", ""))
        time_range = f"{start} - {end}" if end else f"{start} - "
        name = row.get("name", "").replace("_", r"\_")
        role = row.get("role", "").replace("_", r"\_")
        inst = row.get("institution", "").replace("_", r"\_")
        items.append(f"\\cvitem{{{time_range}}}{{{name}, {role} - {inst}}}")
    return INDENT + ("\n" + INDENT).join(items)


def format_courses():
    df = pd.read_csv(COURSES_CSV, comment="#").replace(pd.NA, "")
    items = []
    for _, row in df.iterrows():
        year = str(row.get("year", ""))
        name = row.get("name", "").replace("_", r"\_")
        org = row.get("organizer", "").replace("_", r"\_")
        loc = row.get("location", "")
        loc_str = f" - {loc}" if loc else ""
        items.append(f"\\cvitem{{{year}}}{{{name} - {org}{loc_str}}}")
    return INDENT + ("\n" + INDENT).join(items)


def format_administrative():
    df = pd.read_csv(ADMIN_CSV, comment="#").replace(pd.NA, "")
    items = []
    for _, row in df.iterrows():
        start = str(row.get("year_start", ""))
        end = str(row.get("year_end", ""))
        time_range = f"{start} - {end}" if end else f"{start} - "
        name = row.get("name", "").replace("_", r"\_")
        inst = row.get("institution", "").replace("_", r"\_")
        loc = row.get("location", "")
        loc_str = f", {loc}" if loc else ""
        items.append(f"\\cvitem{{{time_range}}}{{{name}, {inst}{loc_str}}}")
    return INDENT + ("\n" + INDENT).join(items)


def format_software():
    df = pd.read_csv(SOFTWARE_CSV, comment="#").replace(pd.NA, "")
    items = []
    for _, row in df.iterrows():
        name = row.get("name", "").replace("_", r"\_")
        desc = row.get("description", "").replace("_", r"\_")
        url = row.get("github_url", "").replace("_", r"\_")
        items.append(f"\\cvitem{{{name}}}{{{desc}\\newline\\href{{{url}}}{{{url}}}}}")
    return INDENT + ("\n" + INDENT).join(items)


def format_patents():
    df = pd.read_csv(PATENTS_CSV, comment="#").replace(pd.NA, "")
    if df.empty:
        return ""
    items = []
    for _, row in df.iterrows():
        title = row.get("title", "").replace("_", r"\_")
        office = row.get("office", "").replace("_", r"\_")
        status = row.get("status", "")
        date = row.get("date", "")[:7] if pd.notna(row.get("date")) else ""
        comment = row.get("comment", "")
        status_pretty = {
            "approval_pending": "Approval pending",
            "granted": "Granted",
        }.get(status, status)
        items.append(f"\\textbf{{{title}}}. \\textit{{{office}}}, {date}. {comment}")
    content = ("\n        \\item ").join(items)
    return (
        "\\cvitem{\\underline{"
        + status_pretty
        + "}}{}\n"
        + "    \\begin{etaremune}[leftmargin=1.0cm, itemindent=0pt, topsep=10pt, itemsep=2pt, partopsep=0pt, parsep=0pt]\n"
        + "        \\item "
        + content
        + "\n"
        + "    \\end{etaremune}"
    )


def format_talks():
    df = pd.read_csv(TALKS_CSV, comment="#").replace(pd.NA, "")
    if df.empty:
        return ""
    df = df.sort_values("date", ascending=False)
    items = []
    for _, row in df.iterrows():
        title = row.get("title", "").replace("_", r"\_")
        event = row.get("event", "").replace("_", r"\_")
        location = row.get("location", "")
        date = row.get("date", "")[:7] if pd.notna(row.get("date")) else ""
        items.append(f"\\textbf{{{title}}}. \\textit{{{event}}}, {date}. {location}")
    content = ("\n        \\item ").join(items)
    return (
        "\\cvitem{\\underline{Conference talks}}{}\n"
        + "    \\begin{etaremune}[leftmargin=1.0cm,itemindent=0pt,topsep=10pt,itemsep=2pt,partopsep=0pt,parsep=0pt]\n"
        + "        \\item "
        + content
        + "\n"
        + "    \\end{etaremune}"
    )


def format_posters():
    df = pd.read_csv(POSTERS_CSV, comment="#").replace(pd.NA, "")
    if df.empty:
        return ""
    df = df.sort_values("date", ascending=False)
    items = []
    for _, row in df.iterrows():
        title = row.get("title", "").replace("_", r"\_")
        event = row.get("event", "").replace("_", r"\_")
        location = row.get("location", "")
        date = row.get("date", "")[:7] if pd.notna(row.get("date")) else ""
        doi = row.get("doi", "")
        doi_str = f" \\href{{https://doi.org/{doi}}}{{doi:{doi}}}" if doi else ""
        comment = row.get("comment", "")
        comment_str = f" \\textbf{{{comment}}}" if comment else ""
        items.append(
            f"\\textbf{{{title}}}. \\textit{{{event}}}, {date}. {location}.{doi_str}{comment_str}"
        )
    content = ("\n        \\item ").join(items)
    return (
        "\\cvitem{\\underline{Conference posters}}{}\n"
        + "    \\begin{etaremune}[leftmargin=1.0cm,itemindent=0pt,topsep=10pt,itemsep=2pt,partopsep=0pt,parsep=0pt]\n"
        + "        \\item "
        + content
        + "\n"
        + "    \\end{etaremune}"
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
