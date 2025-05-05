# Development Notes

When implementing getters and setters for parameters that are arrays, there is often
inconsistencies where EwE indexes the array as one based or zero-based. In fact, due to the
way arrays are declared in Visual Basic, there is often an unused element at the beginning
or end of arrays. This is notable in the shape forcing functions where one may define a
forcing function by a list of values, and then view it in the GUI, the first element is
missing as EwE treats it as an a one based array. Similar, problems occur for output
variables when they are `memmoved` from dot net to python, where the first or last slice of
each dimension is completely unused.

**Decisions should be made to replicate what would be expected if parameters were set via the
GUI.**

## Ecotracer Concentration and Concentration Biomass outputs

Visual Basic defines arrays as follows

```vb
Dim var(n, m) as integer
```

This constructs an array os shape `(n + 1, m + 1)`. Visual basic array declaration defines
the largest index possible, not the size of the dimension.

## Ecotracer Forcing

### Environmental Inflow Forcing
The Environmental inflow forcing function as seen at the top of the Ecotracer inputs page
can be loaded by defining a forcing function or csv.

The forcing shape manager indexs forcing shapes using a zero based index, whilst the index
stored in the shape objects is one based.

Before the forcing values are added to the core, the value 1.0 is added as padding to the
beginning of the vector as EwE treats the forcing function shape as a one-based index.


### Contaminent concentration driver file
Contaminant concentration driver file refers to the spatial temporal frame work with
ecospace.
