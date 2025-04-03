# decom_py

A tool using [Ecopath with Ecosim](https://ecopath.org/), to explore a wide range of
decomissioning scenarios.

## Example

```python
from decom_py import EwE

ewe = EwE("path to EwE dll directory.")
core = ewe.core()

model_file = "path to model file"
core.LoadModel(model_file)
core.CloseModel()

```
