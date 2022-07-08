
# First thing you do upon installing this git repository
# make install
install:
	@pip install -r requirements/requirements.txt 

# make compile && make sync to re-install dependencies ONLY (without editable)
compile:
	@rm -rf requirements/requirements*.txt
	@pip-compile requirements/requirements.in

sync:
	@pip-sync requirements/requirements*.txt

# make refresh shortcut for make compile && make sync
refresh:
	@make compile && make sync
	@pip install -e .

# Run the clean up before committing
# make clean
clean:
	@./scripts/bash/run_mypy.sh
	@./scripts/bash/run_vulture.sh
	@./scripts/bash/run_isort.sh
	@./scripts/bash/run_black.sh
	@./scripts/bash/run_flake8.sh

test:
	@pytest .

coverage:
	@coverage run --source=src -m pytest tests
	@coverage report -m

serve-docs:
	@mkdocs serve

doc-format:
	@mdformat .
