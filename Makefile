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
	tlmgr install etaremune

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
	make clean

clean:
	-rm source/cv*.tex;
	-rm source/lop*.tex;
	-rm build/pdf/*.aux;
	-rm build/pdf/*.log;
	-rm build/pdf/*.out

web: pdf
	cp build/pdf/cv.pdf ../afrendeiro.github.io/
	cd ../afrendeiro.github.io/; \
	git add cv.pdf; \
	git commit -m 'update publications'; \
	git push origin gh-pages

all: requirements pdf

.PHONY: requirements pdf clean web
