#!/usr/bin/env python

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


AUTHOR_NAME = "André F. Rendeiro"
PUBS_TEX = {"_cv.tex": "cv.tex", "_lop.tex": "lop.tex"}
INDENT = "        "
AWARDS_FORMAT = """\cventry{{{year_applied}, {outcome}}}{{{description}}},{{{funding_body}}}{{{role}}}{{{ammount}}}{{}}{{{comment}}}"""
grant_fields = [
    "year_applied",
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
main_pub_types = ["journal", "review"]
preprint_types = ["preprint"]
alt_pub_types = ["opinion"]


def main() -> int:
    pubs = pd.read_csv(PUBS_CSV).query("publication_type != 'unpublished'")
    grants = (
        pd.read_csv(GRANTS_CSV).query("applicant == @AUTHOR_NAME").replace(pd.NA, "")
    ).sort_values("year_applied", ascending=False)

    awards_list = list()
    for _, g in grants.iterrows():
        p = AWARDS_FORMAT.format(**g[grant_fields].to_dict(), indent=INDENT)
        awards_list.append(p)

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

    for input_file, output_file in PUBS_TEX.items():
        with open(INPUT_DIR / input_file, "r") as handle:
            content = (
                handle.read()
                .replace("{{awards_go_here}}", ("\n" + INDENT).join(awards_list))
                .replace("{{publications_go_here}}", ("\n\n" + INDENT).join(pub_list))
                .replace("{{preprints_go_here}}", ("\n\n" + INDENT).join(preprint_list))
                .replace("{{alt_pubs_go_here}}", ("\n\n" + INDENT).join(alt_list))
                .replace("{{current_date}}", DATE)
            )

        with open(OUTPUT_DIR / output_file, "w") as handle:
            handle.write(content)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
