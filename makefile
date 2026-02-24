# Best settings I found:
RAW_DIR := data
ANALYZED_DIR := data_out
IMG_DIR := images
ANALYZE_OPTIONS := --mode subtract --bandgap 1.5 3 --window 1
ANALYZE_OPTIONS_DIV := --mode divide --bandgap 1.5 3 --window 1
FILE:=""
# number of parallel workers: 0 = as many as possible; replace with 4 to limit
PARALLEL := 0

graph:
	@find "$(ANALYZED_DIR)" -type f -name '*' -print0 | \
	xargs -0 -P $(PARALLEL) -I{} sh -c 'QT_QPA_PLATFORM=wayland ./graph.py "$$1"' _ {}

save_graphs: | $(IMG_DIR)
	@find "$(ANALYZED_DIR)" -type f -name '*' -print0 | \
	xargs -0 -P $(PARALLEL) -I{} sh -c 'QT_QPA_PLATFORM=wayland ./graph.py -o $(IMG_DIR) "$$1"' _ {}

analyze:
	./analyze.py $(RAW_DIR) $(ANALYZED_DIR) $(ANALYZE_OPTIONS)

analyze-div:
	./analyze.py $(RAW_DIR) $(ANALYZED_DIR) $(ANALYZE_OPTIONS_DIV)

plot:
	QT_QPA_PLATFORM=wayland ./compare.py -m plot $(ANALYZED_DIR)

correlate:
	QT_QPA_PLATFORM=wayland ./compare.py -m correlate -s skill $(ANALYZED_DIR)


edit:
	@./view.py "$(FILE)"
	@./snirf-edit.py "$(FILE)"

$(IMG_DIR):
	mkdir -p "$(IMG_DIR)"

.PHONY: run save
