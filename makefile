# Best settings I found:
# make save_graphs BANDGAP_FREQ=1.5 BANDGAP_Q=3 FILTER_WINDOW=1
# make compare BANDGAP_FREQ=1.5 BANDGAP_Q=3 FILTER_WINDOW=1
XML_DIR := data
IMG_DIR := images

# number of parallel workers: 0 = as many as possible; replace with 4 to limit
PARALLEL := 0

graph:
	@find "$(XML_DIR)" -type f -name '*' -print0 | \
	xargs -0 -P $(PARALLEL) -I{} sh -c './graph.py "$$1"' _ {}

save_graphs: | $(IMG_DIR)
	@find "$(XML_DIR)" -type f -name '*' -print0 | \
	EXPORT_DIR="$(IMG_DIR)" \
	xargs -0 -P $(PARALLEL) -I{} sh -c 'EXPORT_DIR="$$EXPORT_DIR" ./graph.py "$$1"' _ {}

compare:
	@bash -c '\
		readarray -d "" FILES < <(find "$(XML_DIR)" -type f -name "*" -print0); \
		./compare.py "$${FILES[@]}"; \
	'
$(IMG_DIR):
	mkdir -p "$(IMG_DIR)"

.PHONY: run save
