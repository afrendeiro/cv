#!/usr/bin/env python

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from joblib import Memory


CACHE_DIR = Path("build/.cache")
CACHE_TTL_DAYS = 30
memory = Memory(CACHE_DIR, verbose=0)


def main() -> int:
    config = load_config()
    author = config["author"]
    data_paths = config["data_paths"]
    indent = "        "

    pubs = pd.read_csv(Path(data_paths["publications"]), comment="#").query(
        "publication_type != 'unpublished'"
    )
    missing = pubs.loc[~pubs["authors"].str.contains(author["name"])]
    assert missing.empty, (
        f"Some publications authors field missing including '{author['name']}':\n    - "
        + "\n    - ".join(missing["title"])
    )

    grants_df = (
        pd.read_csv(Path(data_paths["grants"]), comment="#")
        .query("applicant == @author['name']")
        .replace(pd.NA, "")
    ).sort_values("year_applied", ascending=False)
    grants_df["time"] = grants_df["year_start"].astype(pd.Int64Dtype()).astype(str)
    s = grants_df["year_end"].notna()
    grants_df.loc[s, "time"] = (
        grants_df.loc[s, "year_start"].astype(pd.Int64Dtype()).astype(str)
        + " - "
        + grants_df.loc[s, "year_end"].astype(pd.Int64Dtype()).astype(str)
    )
    s = grants_df["year_start"].isna()
    grants_df.loc[s, "time"] = grants_df.loc[s, "year_applied"].astype(str)

    grant_fields = ["time", "outcome", "title", "entity", "role", "amount", "comment"]
    grants_awards_list = [
        rf"\cventry{{{g['time']}}}{{{g['title']}}},{{{g['entity']}}}{{{g['role']}}}{{}}{{}}".replace(
            "},{", "}{"
        )
        for _, g in grants_df.iterrows()
    ]

    pub_format = r"\item {authors}. \textbf{{{title}}}. {journal} ({year}).\n"
    pub_format += r"{indent}\href{{https://dx.doi.org/{doi}}}{{doi:{doi}}}"

    main_pub_types = ["journal", "review"]
    preprint_types = ["preprint"]
    alt_pub_types = ["opinion"]

    author_name = author["name"]
    author_name_underline = f"\\underline{{{author_name}}}"

    pub_list = [
        pub_format.format(**pub.to_dict(), indent=indent).replace(
            author_name, author_name_underline
        )
        for _, pub in pubs.query("publication_type.isin(@main_pub_types)").iterrows()
    ]
    preprint_list = [
        pub_format.format(**pub.to_dict(), indent=indent).replace(
            author_name, author_name_underline
        )
        for _, pub in pubs.query("publication_type.isin(@preprint_types)").iterrows()
    ]
    alt_list = [
        pub_format.format(**pub.to_dict(), indent=indent).replace(
            author_name, author_name_underline
        )
        for _, pub in pubs.query("publication_type.isin(@alt_pub_types)").iterrows()
    ]

    metrics = get_google_scholar_metrics(author["google_scholar"])
    n_preprints = pubs.query("publication_type.isin(@preprint_types)").shape[0]
    n_peer_reviewed = pubs.query("publication_type.isin(@main_pub_types)").shape[0]
    ff = author["name"] + r"\*"
    n_first_author = pubs.query(
        f"authors.str.startswith(@author['name']) | authors.str.contains('{ff}')"
    ).shape[0]
    n_last_author = pubs.query(
        f"authors.str.contains('{author['name']}$^\\\\Omega$', regex=False)"
    ).shape[0]

    phrases = [
        f"Publications: {pubs.shape[0]} ({n_peer_reviewed} peer reviewed, {n_preprints} preprints, {n_first_author} first-author, {n_last_author} last-author)",
        f"Citations: {metrics['citations']} (last 5 years: {metrics['citations_5_years']})",
        f"h-index: {metrics['h_index']} (last 5 years: {metrics['h_index_5_years']})",
        f"Google Scholar Profile: \\href{{https://scholar.google.com/citations?user={author['google_scholar']}}}{{https://scholar.google.com/citations?user={author['google_scholar']}}}",
    ]
    metrics_text = "    ".join([rf"\cvitem{{}}{{\n{indent}{ph}}}\n" for ph in phrases])

    input_dir = Path(config["input_dir"])
    output_dir = Path(config["output_dir"])
    date = datetime.now().isoformat().split("T")[0]

    replacements = {
        "{{firstname}}": author["firstname"],
        "{{familyname}}": author["familyname"],
        "{{title}}": author["title"],
        "{{subtitle}}": author["subtitle"],
        "{{email}}": author["email"],
        "{{homepage}}": author["homepage"],
        "{{orcid}}": author["orcid"],
        "{{github}}": author["github"],
        "{{twitter}}": author["twitter"],
        "{{grants_awards_go_here}}": ("\n" + indent).join(grants_awards_list),
        "{{publications_go_here}}": ("\n\n" + indent).join(pub_list),
        "{{preprints_go_here}}": ("\n\n" + indent).join(preprint_list),
        "{{alt_pubs_go_here}}": ("\n\n" + indent).join(alt_list),
        "{{metrics_go_here}}": metrics_text,
        "{{teaching_go_here}}": format_teaching(config),
        "{{supervision_go_here}}": format_supervision(config),
        "{{courses_go_here}}": format_courses(config),
        "{{administrative_go_here}}": format_administrative(config),
        "{{software_go_here}}": format_software(config),
        "{{patents_go_here}}": format_patents(config),
        "{{talks_go_here}}": format_talks(config),
        "{{posters_go_here}}": format_posters(config),
        "{{current_positions_go_here}}": format_current_positions(config),
        "{{past_positions_go_here}}": format_past_positions(config),
        "{{key_research_go_here}}": format_key_research(config),
        "{{current_date}}": date,
    }

    for input_file, output_file in {"_cv.tex": "cv.tex", "_lop.tex": "lop.tex"}.items():
        content = (input_dir / input_file).read_text()
        for old, new in replacements.items():
            content = content.replace(old, new)
        (output_dir / output_file).write_text(content)

    return 0


def load_config() -> dict:
    with open(Path("data/config.yaml")) as f:
        return yaml.safe_load(f)


def _cache_is_expired() -> bool:
    import time

    cache_joblib = CACHE_DIR / "joblib"
    if not cache_joblib.exists():
        return True
    mtime = cache_joblib.stat().st_mtime
    age_days = (time.time() - mtime) / 86400
    return age_days > CACHE_TTL_DAYS


@memory.cache
def _fetch_google_scholar_metrics(google_scholar_id: str) -> dict:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from bs4 import BeautifulSoup

    url = f"https://scholar.google.at/citations?user={google_scholar_id}&hl=en"

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
    return {
        "citations": metrics[0].text,
        "citations_5_years": metrics[1].text,
        "h_index": metrics[2].text,
        "h_index_5_years": metrics[3].text,
    }


def get_google_scholar_metrics(google_scholar_id: str) -> dict:
    if _cache_is_expired():
        memory.clear()
    return _fetch_google_scholar_metrics(google_scholar_id)


def format_teaching(config: dict) -> str:
    df = pd.read_csv(Path(config["data_paths"]["teaching"]), comment="#").replace(
        pd.NA, ""
    )
    indent = "        "
    items = []
    for _, row in df.iterrows():
        year = str(row.get("year", ""))
        recurring = " - present" if pd.notna(row.get("recurring")) else ""
        desc = row.get("name", "").replace("_", r"\_")
        items.append(f"\\cvitem{{{year}{recurring}}}{{{desc}}}")
    return indent + ("\n" + indent).join(items)


def format_supervision(config: dict) -> str:
    df = pd.read_csv(Path(config["data_paths"]["supervision"]), comment="#").replace(
        pd.NA, ""
    )
    indent = "        "
    items = []
    for _, row in df.iterrows():
        start = str(row.get("year_start", ""))
        end = str(row.get("year_end", ""))
        time_range = f"{start} - {end}" if end else f"{start} - "
        name = row.get("name", "").replace("_", r"\_")
        role = row.get("role", "").replace("_", r"\_")
        inst = row.get("institution", "").replace("_", r"\_")
        items.append(f"\\cvitem{{{time_range}}}{{{name}, {role} - {inst}}}")
    return indent + ("\n" + indent).join(items)


def format_courses(config: dict) -> str:
    df = pd.read_csv(Path(config["data_paths"]["courses"]), comment="#").replace(
        pd.NA, ""
    )
    indent = "        "
    items = []
    for _, row in df.iterrows():
        year = str(row.get("year", ""))
        name = row.get("name", "").replace("_", r"\_")
        org = row.get("organizer", "").replace("_", r"\_")
        loc = row.get("location", "")
        loc_str = f" - {loc}" if loc else ""
        items.append(f"\\cvitem{{{year}}}{{{name} - {org}{loc_str}}}")
    return indent + ("\n" + indent).join(items)


def format_administrative(config: dict) -> str:
    df = pd.read_csv(Path(config["data_paths"]["administrative"]), comment="#").replace(
        pd.NA, ""
    )
    indent = "        "
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
    return indent + ("\n" + indent).join(items)


def format_software(config: dict) -> str:
    df = pd.read_csv(Path(config["data_paths"]["software"]), comment="#").replace(
        pd.NA, ""
    )
    indent = "        "
    items = []
    for _, row in df.iterrows():
        name = row.get("name", "").replace("_", r"\_")
        desc = row.get("description", "").replace("_", r"\_")
        url = row.get("github_url", "").replace("_", r"\_")
        items.append(f"\\cvitem{{{name}}}{{{desc}\\newline\\href{{{url}}}{{{url}}}}}")
    return indent + ("\n" + indent).join(items)


def format_patents(config: dict) -> str:
    df = pd.read_csv(Path(config["data_paths"]["patents"]), comment="#").replace(
        pd.NA, ""
    )
    indent = "        "
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
        rf"\cvitem{{\underline{{{status_pretty}}}}}# }}"
        + "\n"
        + r"    \begin{etaremune}[leftmargin=1.0cm, itemindent=0pt, topsep=10pt, itemsep=2pt, partopsep=0pt, parsep=0pt]"
        + "\n"
        rf"        \item {content}" + "\n"
        "    \\end{etaremune}"
    ).replace("}# }", "}{}")


def format_talks(config: dict) -> str:
    df = pd.read_csv(Path(config["data_paths"]["talks"]), comment="#").replace(
        pd.NA, ""
    )
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
        "    \\begin{etaremune}[leftmargin=1.0cm,itemindent=0pt,topsep=10pt,itemsep=2pt,partopsep=0pt,parsep=0pt]\n"
        f"        \\item {content}\n"
        "    \\end{etaremune}"
    )


def format_posters(config: dict) -> str:
    df = pd.read_csv(Path(config["data_paths"]["posters"]), comment="#").replace(
        pd.NA, ""
    )
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
        "    \\begin{etaremune}[leftmargin=1.0cm,itemindent=0pt,topsep=10pt,itemsep=2pt,partopsep=0pt,parsep=0pt]\n"
        f"        \\item {content}\n"
        "    \\end{etaremune}"
    )


def format_current_positions(config: dict) -> str:
    indent = "        "
    items = []
    for pos in config.get("current_positions", []):
        start = pos.get("start_date", "")[:7].replace("-", "/")
        time_str = start + " - "
        position = pos.get("position", "").replace("_", r"\_")
        institution = pos.get("institution", "").replace("_", r"\_")
        location = pos.get("location", "")
        items.append(
            f"\\cventry{{{time_str}}}{{{position}}}{{\\newline{institution}}}{{{location}}}{{}}{{}}"
        )
    return indent + ("\n" + indent).join(items)


def format_past_positions(config: dict) -> str:
    indent = "        "
    items = []
    for pos in config.get("past_positions", []):
        start = pos.get("start_date", "")[:7].replace("-", "/")
        end = (
            pos.get("end_date", "")[:7].replace("-", "/") if pos.get("end_date") else ""
        )
        time_str = f"{start} - {end}" if end else f"{start} - "
        position = pos.get("position", "").replace("_", r"\_")
        institution = pos.get("institution", "").replace("_", r"\_")
        location = pos.get("location", "")
        supervisor = pos.get("supervisor", "")
        supervisor_str = f"Supervisor: {supervisor}" if supervisor else ""
        items.append(
            f"\\cventry{{{time_str}}}{{{position}}}{{{institution}}}{{{location}}}{{}}{{{supervisor_str}}}"
        )
    return indent + ("\n" + indent).join(items)


def format_key_research(config: dict) -> str:
    indent = "        "
    items = []
    for pub in sorted(
        config.get("key_research", []), key=lambda x: x.get("order", 999)
    ):
        doi = pub.get("doi", "")
        authors = pub.get("authors_short", "").replace("_", r"\_")
        title = pub.get("title", "").replace("_", r"\_")
        journal = pub.get("journal", "")
        year = pub.get("year", "")
        last_author = r" $\Omega$" if pub.get("last_author", False) else ""
        doi_str = f" \\href{{https://doi.org/{doi}}}{{doi:{doi}}}" if doi else ""
        order_num = pub.get("order", "")
        items.append(
            f"\\cvitem{{{order_num}.}}{{{authors}{last_author} \\textbf{{{title}}}. {journal} ({year}).{doi_str}}}"
        )
    items.append(
        r"\cvitem{}{$\Omega$ \textit{corresponding author}; * \textit{first-author}}"
    )
    return ("\n" + indent).join(items)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
