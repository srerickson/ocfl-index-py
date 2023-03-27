.PHONY: proto
proto:
	which buf # is buf installed?
	rm -rf proto/ocfl
	rm -rf ocflindex/ocfl
	buf export buf.build/srerickson/ocfl -o proto
	buf mod update proto
	buf lint proto
	buf generate proto

clean:
	rm -rf dist
	rm -rf *.egg-info

.PHONY: build
build: clean
	python -m build