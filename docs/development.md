# Development Notes

## Ecotracer Concentration and Concentration Biomass outputs

Visual Basic defines arrays as follows

```vb
Dim var(n, m) as integer
```

This constructs an array os shape `(n + 1, m + 1)`. Visual basic array declaration defines
the largest index possible, not the size of the dimension.
