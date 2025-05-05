# Development Notes

## Ecotracer Concentration and Concentration Biomass outputs

Visual Basic defines arrays as follows

```vb
Dim var(n, m) as integer
```

This constructs an array os shape `(n + 1, m + 1)`. Visual basic array declaration defines
the largest index possible, not the size of the dimension.

## Ecotracer Forcing

The Environmental inflow forcing function as seen at the top of the Ecotracer inputs page
can be loaded by defining a forcing function or csv.

Contaminant concentration driver file refers to the spatial temporal frame work with
ecospace.
