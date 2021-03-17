.PHONY: test

test:
	mys build && cd test && python3 test.py
