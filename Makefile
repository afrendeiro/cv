.DEFAULT_GOAL := pdf

# Practical notes on installing packages from texlive:
# # `tlmgr` is the package manager.
# # In order to use it as a normal user, run on the current directory:
# # $ tlmgr init-usertree
# # The year version of the texlive installation must match the package year version.
# # So if textlive installation is from a different year than the current, change the
# # source of the packages to be get:
# # $ tlmgr repository add ftp://tug.org/historic/systems/texlive/2021/tlnet-final
# # $ tlmgr repository remove http://mirror.ctan.org/systems/texlive/tlne
# # $ tlmgr option repository ftp://tug.org/historic/systems/texlive/2021/tlnet-final

requirements:
	sudo apt install texlive; \
	sudo apt install texlive-latex-extra; \
	tlmgr init-usertree; \
	tlmgr install \
		etaremune \
		fontawesome5

FILES = cv resume lop pub_highlight references # cover_letter resume_long teaching_strategy

python-requirements:
	uv pip install -r requirements.txt

update: python-requirements
	@echo `uv run python --version`
	uv run python update.py

pdf: clean update
	mkdir -p build/pdf
	$(foreach \
		file, $(FILES), \
		lualatex --output-dir build/pdf source/$(file).tex \
	;)
	# -interaction nonstopmode to run through errors

	# # Run twice to fix list ordering with etanumer :/
	$(foreach \
		file, $(FILES), \
		lualatex --output-dir build/pdf source/$(file).tex \
	;)
	cp build/pdf/cv.pdf ./
	make clean

copy:
	# Copy changes to website
	cp build/pdf/cv.pdf ./
	cp build/pdf/cv.pdf ../afrendeiro.github.io/
	cp publications.csv ../afrendeiro.github.io/
	cp publication_resources.csv ../afrendeiro.github.io/
	cd ../afrendeiro.github.io/; \

up: copy
	# Upload changes
	git add \
		publications.csv \
		publication_resources.csv \
		source/_cv.tex \
		cv.pdf
	git commit -m 'update publications'
	git push origin main

web: pdf copy
	# Update website: "afrendeiro.github.io"
	cd ../afrendeiro.github.io/; \
	$(MAKE) web

clean_viz:
	-rm -r viz

viz: clean_viz
	uv run python viz.py

clean:
	-rm -r viz
	-rm source/cv*.tex
	-rm source/lop*.tex
	-rm build/pdf/*.aux
	-rm build/pdf/*.log
	-rm build/pdf/*.out

all: requirements pdf

.PHONY: requirements pdf clean web
