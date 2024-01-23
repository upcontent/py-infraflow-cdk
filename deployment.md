### upload to PYPI
==========================

create ~/.pypirc
```rc
[testpypi]
username = **token**
password = <API_KEY>

[pypi]
username = **token**
password = <API_KEY>
start a venv
```
```shell
pip install build twin
```

```shell
python -m build
```

optional: `twine check dist/*`

if testing
```shell
twine upload -r testpypi dist/*
```
OR 
```shell
twine upload dist/*
```

user/pass id deprecated - need API key

should just work if .pypirc is configured properly to point to pypi account
(edited)