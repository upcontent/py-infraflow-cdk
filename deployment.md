### Uploading to PYPI
==========================

Create/edit ~/.pypirc
```rc
[testpypi]
username = __token__
password = <API_KEY>

[pypi]
username = __token__
password = <API_KEY>
```
---

start a venv

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

Standard username/password pypirc config is deprecated - need an API key
As long as the .pypirc is configured properly to point to pypi account, the upload should now work.