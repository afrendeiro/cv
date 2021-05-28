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
	pdflatex --output-format pdf cv.tex;
	pdflatex --output-format pdf cv.tex

clean:
	rm cv.aux cv.out cv.log

all: requirements pdf

.PHONY: requirements pdf clean
