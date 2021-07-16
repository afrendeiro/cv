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

pdf: clean
	python -u update_pubs.py
	pdflatex --output-format pdf cv.tex;
	pdflatex --output-format pdf cv.tex;
	cp cv.pdf ../afrendeiro.github.io/

	pdflatex --output-format pdf resume.tex;
	pdflatex --output-format pdf resume.tex

	pdflatex --output-format pdf resume_long.tex;
	pdflatex --output-format pdf resume_long.tex

	pdflatex --output-format pdf lop.tex;
	pdflatex --output-format pdf lop.tex

	pdflatex --output-format pdf pub_highlight.tex;
	pdflatex --output-format pdf pub_highlight.tex

	pdflatex --output-format pdf references.tex;
	pdflatex --output-format pdf references.tex

	pdflatex --output-format pdf cover_letter.tex;
	pdflatex --output-format pdf cover_letter.tex

	make clean

clean:
	-rm cv.aux cv.out cv.log cv.tex
	-rm resume.aux resume.out resume.log
	-rm resume.aux resume.out resume_long.log
	-rm lop.aux lop.out lop.log lop.tex
	-rm pub_highlight.aux pub_highlight.out pub_highlight.log
	-rm references.aux references.out references.log
	-rm cover_letter.aux cover_letter.out cover_letter.log

all: requirements pdf

.PHONY: requirements pdf clean
