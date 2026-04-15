RAW_DIR := data
ANALYZED_DIR := analyzed_data
ANALYZED_FILE := $(ANALYZED_DIR)/analyzed.npz
TEMPLATE_FILE := $(ANALYZED_DIR)/template.npz
IMG_DIR := images
ANALYZE_OPTIONS := --bandgap 1.5 3 --window 1
FILE:=""
# number of parallel workers: 0 = as many as possible; replace with 4 to limit
PARALLEL := 0

# On Ubuntu, if this script does not work for you, add the line:
# export QT_QPA_PLATFORM=wayland
# To your ~/.bashrc file, and reload the terminal
all: 
	$(MAKE) clean
	$(MAKE) analyze
	$(MAKE) template
	$(MAKE) analyze
	$(MAKE) correlate
	
graph:
	@find "$(ANALYZED_DIR)" -type f -name '*' -print0 | \
	xargs -0 -P $(PARALLEL) -I{} sh -c ' ./graph.py "$$1"' _ {}

save-graphs: | $(IMG_DIR)
	@find "$(ANALYZED_DIR)" -type f -name '*' -print0 | \
	xargs -0 -P $(PARALLEL) -I{} sh -c ' ./graph.py -o $(IMG_DIR) "$$1"' _ {}

template: 
	./template.py $(ANALYZED_FILE) $(TEMPLATE_FILE)

template-show: 
	./template.py --show $(ANALYZED_FILE) $(TEMPLATE_FILE)

analyze:
	./analyze.py $(RAW_DIR) $(ANALYZED_FILE) $(ANALYZE_OPTIONS)

analyze-sub:
	./analyze.py $(RAW_DIR) $(ANALYZED_FILE) $(ANALYZE_OPTIONS) --transform subtract

analyze-div:
	./analyze.py $(RAW_DIR) $(ANALYZED_FILE) $(ANALYZE_OPTIONS) --transform divide

correlate:
	./correlate.py -s belt $(ANALYZED_FILE)

correlate-no-offset:
	./correlate.py -s belt $(ANALYZED_FILE) --no-offset

correlate-split:
	./correlate.py -s skill --split $(ANALYZED_FILE) --save $(IMG_DIR)

correlate-group:
	./correlate.py -s skill --group belt $(ANALYZED_FILE)

correlate-blck:
	./correlate.py -s skill -f belt blck $(ANALYZED_FILE)

correlate-brwn:
	./correlate.py -s skill -f belt brwn $(ANALYZED_FILE)

correlate-prpl:
	./correlate.py -s skill -f belt prpl $(ANALYZED_FILE)

correlate-blue:
	./correlate.py -s skill -f belt blue $(ANALYZED_FILE)

correlate-whte:
	./correlate.py -s skill -f belt whte $(ANALYZED_FILE)

edit:
	@./view.py "$(FILE)"
	@./snirf-edit.py "$(FILE)"

$(IMG_DIR):
	mkdir -p "$(IMG_DIR)"

clean:
	rm -rf $(ANALYZED_DIR)

.PHONY: clean
