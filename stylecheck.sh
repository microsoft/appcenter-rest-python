#!/bin/bash

pushd "${VIRTUAL_ENV}" > /dev/null

python -m black -l 100 appcenter/*.py tests/*.py

python -m pylint --rcfile=pylintrc appcenter
python -m mypy --ignore-missing-imports appcenter/

python -m pylint --rcfile=pylintrc tests
python -m mypy --ignore-missing-imports tests/

popd > /dev/null

