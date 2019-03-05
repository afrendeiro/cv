.DEFAULT_GOAL := pdf

requirements:
	sudo apt install texlive; sudo apt install texlive-latex-extra

pdf:
	pdflatex --output-format pdf cv.tex

clean:
	rm cv.aux cv.out cv.log

all: requirements pdf

.PHONY: requirements pdf clean
