.PHONY: all clean test

docker:
	docker build -t markusressel/image-match .

test:
	cd tests; pytest