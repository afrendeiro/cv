# CV generation and build system
# Usage: just [target]

set dotenv-load

# Default target
default: pdf

# Generate CV from CSVs and config.yaml
update:
    uv run --with pyyaml --with requests --with beautifulsoup4 --with joblib python build.py


# Install required LaTeX packages (user-tree mode)
install-tex-packages:
    tlmgr init-usertree || true
    tlmgr --usermode install fontawesome5 etaremune || echo "Packages may already be installed"
    @echo "✓ LaTeX setup complete"

# Build PDF from LaTeX
pdf: install-tex-packages clean update
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
    uv run python viz.py

clean-viz:
    rm -rf viz

# Copy to website
copy: pdf
    cp build/pdf/cv.pdf ./
    cp build/pdf/cv.pdf ../afrendeiro.github.io/
    cp publications.csv ../afrendeiro.github.io/
    cp publication_resources.csv ../afrendeiro.github.io/

# Update website
web: copy
    cd ../afrendeiro.github.io/ && just web

# Git commit and push changes
up: copy
    git add \
        publications.csv \
        publication_resources.csv \
        source/_cv.tex \
        cv.pdf
    git commit -m 'update publications'
    git push origin main

# Install LaTeX packages (requires tlmgr)
install-tex:
    sudo apt install texlive texlive-latex-extra
    tlmgr init-usertree
    tlmgr install etaremune fontawesome5

# Help
help:
    @echo "Available targets:"
    @just --list