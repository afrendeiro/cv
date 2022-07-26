.DEFAULT_GOAL := pdf

# Practical notes on installing packages from texlive:
# # `tlmgr` is the package manager.
# # In order to use it as a normal user, run on the current directory:
# # $ tlmgr init-usertree
# # The year version of the texlive installation must match the package year version.
# # So if textlive installation is from a different year than the current, change the
# # source of the packages to be get:
# # $ tlmgr repository add ftp://tug.org/historic/systems/texlive/2020/tlnet-final
# # $ tlmgr repository remove http://mirror.ctan.org/systems/texlive/tlne
# # $ tlmgr option repository ftp://tug.org/historic/systems/texlive/2020/tlnet-final

requirements:
	sudo apt install texlive; \
	sudo apt install texlive-latex-extra; \
	tlmgr init-usertree; \
	tlmgr install \
		etaremune \
		fontawesome5; \
	wget -O source/fontawesome5.sty https://raw.githubusercontent.com/JanHendrikDolling/latex-fontawesome5/master/fontawesome5.sty

FILES = cv resume lop pub_highlight references # cover_letter resume_long teaching_strategy

pdf: clean
	mkdir -p build/pdf
	python -u update_pubs.py
	$(foreach \
		file, $(FILES), \
		pdflatex --output-dir build/pdf --output-format pdf source/$(file).tex \
	;)
	# # Run twice to fix list ordering with etanumer :/
	$(foreach \
		file, $(FILES), \
		pdflatex --output-dir build/pdf --output-format pdf source/$(file).tex \
	;)
	cp build/pdf/cv.pdf ./
	make clean

clean:
	-rm source/cv*.tex;
	-rm source/lop*.tex;
	-rm build/pdf/*.aux;
	-rm build/pdf/*.log;
	-rm build/pdf/*.out

copy:
	cp build/pdf/cv.pdf ../afrendeiro.github.io/
	cp publications.csv ../afrendeiro.github.io/
	cp publication_resources.csv ../afrendeiro.github.io/
	cd ../afrendeiro.github.io/; \
	python update_publications_resources.py

web: pdf copy
	cd ../afrendeiro.github.io/; \
	python update_publications_resources.py; \
	git add \
		publications.csv \
		publication_resources.csv \
		cv.pdf \
		index.md; \
	git commit -m 'update publications'; \
	git push origin gh-pages

up: web
	git add \
		publications.csv \
		publication_resources.csv \
		source/_cv.tex \
		cv.pdf
	git commit -m 'update publications'
	git push origin main

all: requirements pdf

.PHONY: requirements pdf clean web
