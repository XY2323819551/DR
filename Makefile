.PHONY: clean

clean:
	rm -rf dist
	rm -rf build
	rm -rf *.spec
	rm -rf *.pyc
	rm -rf **/*.pyc
	rm -rf **/**/*.pyc
	rm -rf **/**/**/*.pyc
	rm -rf **/**/**/**/*.pyc
	rm -rf *.egg-info;
	rm -rf **/*.egg-info;
	rm -rf **/**/*.egg-info;
	find . -type d -name "__pycache__" -exec rm -rf {} +
