#!/usr/bin/env python

import sys

import pandas as pd


AUTHOR_NAME = "André F. Rendeiro"
PUBS_CSV = "publications.csv"
PUBS_TEX_INPUT = "_cv.tex"
PUBS_TEX_OUTPUT = "cv.tex"
INDENT = "        "
PUB_FORMAT = """\\item {authors}. \\textbf{{{title}}}. {journal} ({year}).\n{indent}\\href{{https://dx.doi.org/{doi}}}{{doi:{doi}}}"""


def main() -> int:
    pubs = pd.read_csv(PUBS_CSV)

    pub_list = list()
    for _, pub in pubs.query("publication_type == 'journal'").iterrows():
        p = PUB_FORMAT.format(**pub.to_dict(), indent=INDENT)
        p = p.replace(AUTHOR_NAME, f"\\underline{{{AUTHOR_NAME}}}")
        pub_list.append(p)

    preprint_list = list()
    for _, pub in pubs.query("publication_type == 'preprint'").iterrows():
        p = PUB_FORMAT.format(**pub.to_dict(), indent=INDENT)
        p = p.replace(AUTHOR_NAME, f"\\underline{{{AUTHOR_NAME}}}")
        preprint_list.append(p)

    with open(PUBS_TEX_INPUT, "r") as handle:
        content = handle.read()
        content = content.replace(
            "{{publications_go_here}}", ("\n\n" + INDENT).join(pub_list)
        )
        content = content.replace(
            "{{preprints_go_here}}", ("\n\n" + INDENT).join(preprint_list)
        )

    with open(PUBS_TEX_OUTPUT, "w") as handle:
        handle.write(content)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
