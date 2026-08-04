

all:
	@uv run -m src.label 
	@uv run -m src.analyze
	@uv run -m src.template
	@uv run -m src.show_correlation

clean:
	@rm -f data/{labeled,analyzed,templates}/*
label:
	@uv run -m src.label --no-strict

analyze:
	@uv run -m src.analyze 