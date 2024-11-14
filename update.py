#!/usr/bin/env python

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


AUTHOR_NAME = "André F. Rendeiro"
PUBS_TEX = {"_cv.tex": "cv.tex", "_lop.tex": "lop.tex"}
INDENT = "        "
GRANTS_AWARDS_FORMAT = (
    """\cventry{{{time}}}{{{description}}},{{{funding_body}}}{{{role}}}{{}}{{}}"""
)
grant_fields = [
    "time",
    "outcome",
    "description",
    "funding_body",
    "role",
    "ammount",
    "comment",
]
PUB_FORMAT = """\\item {authors}. \\textbf{{{title}}}. {journal} ({year}).\n"""
PUB_FORMAT += """{indent}\\href{{https://dx.doi.org/{doi}}}{{doi:{doi}}}"""
PUBS_CSV = Path("publications.csv")
GRANTS_CSV = Path("grants.csv")
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

    #
    grants_awards = (
        pd.read_csv(GRANTS_CSV, comment="#")
        .query("applicant == @AUTHOR_NAME")
        .replace(pd.NA, "")
    ).sort_values("year_applied", ascending=False)
    grants_awards["time"] = (
        grants_awards["award_start"].astype(pd.Int64Dtype()).astype(str)
        + " - "
        + grants_awards["award_end"].astype(pd.Int64Dtype()).astype(str)
    )
    s = grants_awards["award_start"].isnull()
    grants_awards.loc[s, "time"] = grants_awards.loc[s, "year_applied"]

    grants_awards_list = list()
    for _, g in grants_awards.iterrows():
        p = (
            GRANTS_AWARDS_FORMAT.format(**g[grant_fields].to_dict(), indent=INDENT)
            # .replace("nan", "")
            .replace("},{", "}{")
        )
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

    # Publication metrics
    metrics = get_google_scholar_metrics()
    n_preprints = pubs.query("publication_type.isin(@preprint_types)").shape[0]
    n_peer_reviewed = pubs.query("publication_type.isin(@main_pub_types)").shape[0]
    ff = AUTHOR_NAME + r"\*"
    n_first_author = pubs.query(
        f"authors.str.startswith(@AUTHOR_NAME) | authors.str.contains('{ff}')"
    ).shape[0]
    ll = AUTHOR_NAME + LAST_AUTHOR_SIGN
    n_last_author = pubs.query(
        f"authors.str.endswith(@AUTHOR_NAME) | authors.str.contains('{ll}', regex=False)"
    ).shape[0]

    phrases = [
        f"Publications: {pubs.shape[0]} ({n_peer_reviewed} peer reviewed, {n_preprints} preprints, {n_first_author} first-author, {n_last_author} last-author)",
        f"Citations: {metrics['citations']} ({metrics['citations_5_years']} last 5 years)",
        f"h-index: {metrics['h_index']} ({metrics['h_index_5_years']} last 5 years)",
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
                .replace("{{current_date}}", DATE)
            )

        with open(OUTPUT_DIR / output_file, "w") as handle:
            handle.write(content)

    return 0


def get_google_scholar_metrics():
    """
    Get metrics from Google Scholar profile
    """
    # import requests
    from selenium import webdriver
    from bs4 import BeautifulSoup

    url = f"https://scholar.google.at/citations?user={GOOGLE_SCHOLAR_ID}&hl=en"
    # req = requests.get(url)
    # req.raise_for_status()
    # soup = BeautifulSoup(req.content, "html.parser")
    ops = webdriver.FirefoxOptions()
    ops.add_argument("--headless")
    with webdriver.Firefox(options=ops) as driver:
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


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
