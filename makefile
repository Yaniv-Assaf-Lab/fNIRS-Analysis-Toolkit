RAW_DIR := data
ANALYZED_DIR := data_out
IMG_DIR := images
ANALYZE_OPTIONS := --bandgap 1.5 3 --window 1
FILE:=""
# number of parallel workers: 0 = as many as possible; replace with 4 to limit
PARALLEL := 0

# On Ubuntu, if this script does not work for you, add the line:
# export QT_QPA_PLATFORM=wayland
# To your ~/.bashrc file, and reload the terminal

graph:
	@find "$(ANALYZED_DIR)" -type f -name '*' -print0 | \
	xargs -0 -P $(PARALLEL) -I{} sh -c ' ./graph.py "$$1"' _ {}

save-graphs: | $(IMG_DIR)
	@find "$(ANALYZED_DIR)" -type f -name '*' -print0 | \
	xargs -0 -P $(PARALLEL) -I{} sh -c ' ./graph.py -o $(IMG_DIR) "$$1"' _ {}


analyze:
	./analyze.py $(RAW_DIR) $(ANALYZED_DIR) $(ANALYZE_OPTIONS)

analyze-sub:
	./analyze.py $(RAW_DIR) $(ANALYZED_DIR) $(ANALYZE_OPTIONS) --transform subtract

analyze-div:
	./analyze.py $(RAW_DIR) $(ANALYZED_DIR) $(ANALYZE_OPTIONS) --transform divide

correlate:
	./correlate.py -s skill $(ANALYZED_DIR)

correlate-split:
	./correlate.py -s skill --split $(ANALYZED_DIR) --save $(IMG_DIR)

correlate-blck:
	./correlate.py -s skill -f belt blck $(ANALYZED_DIR)

correlate-brwn:
	./correlate.py -s skill -f belt brwn $(ANALYZED_DIR)

correlate-prpl:
	./correlate.py -s skill -f belt prpl $(ANALYZED_DIR)

correlate-blue:
	./correlate.py-s skill -f belt blue $(ANALYZED_DIR)

correlate-whte:
	./correlate.py -s skill -f belt whte $(ANALYZED_DIR)

edit:
	@./view.py "$(FILE)"
	@./snirf-edit.py "$(FILE)"

$(IMG_DIR):
	mkdir -p "$(IMG_DIR)"

clean:
	rm -rf $(ANALYZED_DIR)

.PHONY: clean
