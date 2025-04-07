# decom_py

A tool using [Ecopath with Ecosim](https://ecopath.org/), to explore a wide range of
decomissioning scenarios.

## Example

```python
from decom_py import EwE

ewe = EwE("path to EwE dll directory.", "path to result save dir")

model_file = "path to model file"
ewe.load_model(model_file)

ewe.run_ecopath()
ewe.load_ecosim_scenario(0)
ewe.load_ecotracer_scenario(0)

ewe.run_ecosim()

ewe.save_ecopath_results()
ewe.save_ecosim_results()

ewe.core().CloseModel()

```
