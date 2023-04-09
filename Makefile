up:
	docker-compose up

run:
	python3 HeGel2/main.py

lint:
	flake8 HeGel2/

format:
	autoflake HeGel2 && isort HeGel2





