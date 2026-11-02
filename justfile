# CV generation and build system
# Usage: just [target]

set dotenv-load

# Default target
default: pdf

# Generate CV from CSVs and config.yaml
update:
    uv run --with pyyaml --with requests --with beautifulsoup4 --with joblib python build.py


# Install system-level TeX Live packages (requires sudo)
install-tex-system:
    sudo pacman -S --needed texlive-latex texlive-latexextra || true

# Install required LaTeX packages (user-tree mode)
install-tex-packages:
    tlmgr init-usertree || true
    tlmgr --usermode install lm academicons fontawesome5 etaremune || echo "Packages may already be installed"
    @echo "✓ LaTeX setup complete"

# Build PDF from LaTeX (run `just install-tex` once beforehand)
pdf: clean update
    mkdir -p build/pdf
    lualatex -interaction=nonstopmode -output-directory=build/pdf source/cv.tex || true
    lualatex -interaction=nonstopmode -output-directory=build/pdf source/cv.tex || true
    cp build/pdf/cv.pdf ./

# Clean build artifacts
clean:
    rm -rf viz
    rm -f source/cv*.tex
    rm -f source/lop*.tex
    rm -f build/pdf/*.aux
    rm -f build/pdf/*.log
    rm -f build/pdf/*.out

# Generate visualizations
viz: clean-viz
    uv run python scripts/viz.py

clean-viz:
    rm -rf viz

# Copy CV PDF to website (publications there are synced from the lab repo, not from here)
copy: pdf
    cp build/pdf/cv.pdf ../afrendeiro.github.io/

# Update website
web: copy
    cd ../afrendeiro.github.io/ && just web

# Git commit and push changes
up: copy
    git add \
        data/* \
        cv.pdf
    git commit -m 'update publications'
    git push origin main

# Install all LaTeX packages (system + user tree)
install-tex: install-tex-system install-tex-packages

# Help
help:
    @echo "Available targets:"
    @just --list
