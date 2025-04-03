PHONY: all clean test

docker:
	docker build -t image-match .

test:
	pytest