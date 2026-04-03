# CV

Personal CV using LaTeX (ModernCV), with data sourced from CSV files.

A Python script (`update.py`) reads CSV files and fills placeholders in TeX template files.

Uses [just](https://just.systems/) as the build system.

## Quick Start

```bash
# Build PDF (default)
just

# Just update the TeX files from CSV (publications, etc.)
just update

# Build PDF only
just pdf

# Generate visualizations
just viz

# Copy to info to personal website (afrendeiro.github.io)
just copy
```

## Data

CSV files in `data/`:
- `publications.csv` - Publication list
- `grants.csv` - Grants and awards
- `publication_resources.csv` - Links to code/data for publications
- `experience.csv`, `skills.csv`, `software.csv`, `talks.csv`, `posters.csv`, `patents.csv`

Edit CSV files and run `just update` to regenerate the TeX files.

## Requirements

- [just](https://just.systems/) - Build tool
- Python 3.12+ with uv - For running update.py
- TeX Live (lualatex) - For PDF generation
- Chrome/Chromium + chromedriver - For scraping Google Scholar metrics
- LaTeX packages: moderncv, fontawesome5, etaremune, academicons, lm-math