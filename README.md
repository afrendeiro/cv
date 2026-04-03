# CV

Personal CV using LaTeX (ModernCV), with data sourced from CSV files and config.yaml.

A Python script (`build.py`) reads data files and fills placeholders in TeX template files.

Uses [just](https://just.systems/) as the build system.

## Quick Start

```bash
# Build PDF (default)
just

# Just update the TeX files from data (publications, grants, etc.)
just update

# Build PDF only
just pdf
```

## Data

### [config.yaml](data/config.yaml)

Main configuration file with:
- Author info (name, title, email, ORCID, social links)
- Current positions
- Past positions and education
- Key research publications

### CSV files in `data/`

- [publications.csv](data/publications.csv) - Publication list
- [grants.csv](data/grants.csv) - Grants and awards
- [teaching.csv](data/teaching.csv) - Teaching experience
- [supervision.csv](data/supervision.csv) - Supervision/mentoring
- [courses_attended.csv](data/courses_attended.csv) - Professional development courses
- [administrative.csv](data/administrative.csv) - Administrative roles
- [software.csv](data/software.csv) - Software/tools developed
- [patents.csv](data/patents.csv) - Patents
- [talks.csv](data/talks.csv) - Conference talks
- [posters.csv](data/posters.csv) - Conference posters

Edit data files and run `just update` to regenerate the TeX files.

## Scripts

- [build.py](build.py) - Main build script that reads data and generates TeX

## Requirements

- [just](https://just.systems/) - Build tool
- Python 3.12+ with uv - For running build.py
- TeX Live (lualatex) - For PDF generation
- Chrome/Chromium + chromedriver - For scraping Google Scholar metrics
- LaTeX packages: moderncv, fontawesome5, etaremune, academicons, lm-math

## Build Outputs

Generated TeX files (in `source/`, not git tracked):
- `cv.tex` - Main CV
- `lop.tex` - List of publications
- `resume.tex` - Resume version