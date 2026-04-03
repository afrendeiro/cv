# CV

Personal CV using LaTeX (ModernCV), with data sourced from CSV files.

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