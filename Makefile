.PHONY: proto
proto:
	rm -rf proto/ocfl
	buf export buf.build/srerickson/ocfl -o proto
	buf mod update proto
	buf lint proto
	buf generate proto
