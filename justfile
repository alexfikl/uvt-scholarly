PYTHON := 'python -X dev'

_default:
    @just --list

# {{{ formatting

alias fmt: format

[doc('Reformat all source code')]
format: isort black pyproject justfmt

[doc('Run ruff isort fixes over the source code')]
isort:
    ruff check --fix --select=I src tests
    ruff check --fix --select=RUF022 src tests
    @echo -e "\e[1;32mruff isort clean!\e[0m"

[doc('Run ruff format over the source code')]
black:
    ruff format src tests
    @echo -e "\e[1;32mruff format clean!\e[0m"

[doc('Run pyproject-fmt over the configuration')]
pyproject:
    {{ PYTHON }} -m pyproject_fmt \
        --indent 4 --max-supported-python '3.14' \
        pyproject.toml
    @echo -e "\e[1;32mpyproject clean!\e[0m"

[doc('Run just --fmt over the justfile')]
justfmt:
    just --unstable --fmt
    @echo -e "\e[1;32mjust --fmt clean!\e[0m"

# }}}
# {{{ linting

[doc('Run all linting checks over the source code')]
lint: typos reuse ruff ty

[doc('Run typos over the source code and documentation')]
typos:
    typos --sort
    @echo -e "\e[1;32mtypos clean!\e[0m"

[doc('Check REUSE license compliance')]
reuse:
    {{ PYTHON }} -m reuse lint
    @echo -e "\e[1;32mREUSE compliant!\e[0m"

[doc('Run ruff checks over the source code')]
ruff:
    ruff check src tests
    @echo -e "\e[1;32mruff clean!\e[0m"

[doc('Run ty checks over the source code')]
ty:
    ty check src tests
    @echo -e "\e[1;32mty clean!\e[0m"

# }}}
# {{{ pin

REQUIREMENTS_DIR := ".ci"

[private]
requirements_build_txt:
    uv pip compile --upgrade --universal --python-version "3.11" \
        -o {{ REQUIREMENTS_DIR }}/requirements-build.txt \
        {{ REQUIREMENTS_DIR }}/requirements-build.in

[private]
requirements_test_txt:
    uv pip compile --upgrade --universal --python-version '3.11' \
        --group test --group plotting \
        -o {{ REQUIREMENTS_DIR }}/requirements-test.txt \
        pyproject.toml

[private]
requirements_txt:
    uv pip compile --upgrade --universal --python-version '3.11' \
        -o requirements.txt pyproject.toml

[doc('Pin dependency versions to requirements.txt')]
pin: requirements_txt requirements_test_txt requirements_build_txt

# }}}
# {{{ develop

[doc("Editable install using pinned dependencies from requirements-test.txt")]
ci-install venv=".venv":
    #!/usr/bin/env bash

    # build a virtual environment
    if [[ ! -d "{{ venv }}" ]]; then
        python -m venv {{ venv }}
        source {{ venv }}/bin/activate
        echo -e "\e[1;32mvenv created: '{{ venv }}'!\e[0m"
    fi

    # install build dependencies (need to be first due to  --no-build-isolation)
    {{ PYTHON }} -m pip install --requirement {{ REQUIREMENTS_DIR }}/requirements-build.txt

    # install all other pinned dependencies
    {{ PYTHON }} -m pip install \
        --verbose \
        --requirement {{ REQUIREMENTS_DIR }}/requirements-test.txt \
        --no-build-isolation \
        --editable .

    echo -e "\e[1;32mvenv setup completed: '{{ venv }}'!\e[0m"

[doc("Run pytest tests")]
test:
    {{ PYTHON }} -m pytest -rswx -v -s --durations=25 tests

[doc("Remove various build artifacts")]
clean:
    rm -rf *.png
    rm -rf build dist
    rm -rf docs/build.sphinx

[doc("Remove various temporary files and caches")]
purge: clean
    rm -rf .ruff_cache .pytest_cache tags

[doc("Regenerate ctags")]
ctags:
    ctags --recurse=yes \
        --tag-relative=yes \
        --exclude=.git \
        --exclude=docs \
        --python-kinds=-i \
        --language-force=python

# }}}
