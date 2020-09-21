#!/bin/bash

pushd "${VIRTUAL_ENV}/.." > /dev/null

python -m black -l 100 appcenter/*.py tests/*.py
python -m pylint --rcfile=pylintrc appcenter tests
python -m mypy --ignore-missing-imports appcenter/ tests/

popd > /dev/null

