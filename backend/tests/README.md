To verify that everything works, run:
```sh
python -m pytest -s tests/
```
and check the output for any errors.

You can also run a specific test file or function:
```sh
python -m pytest -s tests/test_t2sql.py::test_sql2t
```