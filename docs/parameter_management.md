# Parameter Management

Currently, the parameter management object only supports Ecotracer. However, can be extended
by defining an Ecosim factory method similar to the Ecotracer implementation. The parameter
managers using the naming of parameters passed to the managers to decide which setter
functions to call and for which functional group it shoould be set.

## Parameter Naming

Ecotracer parameters are split into two groups, environmental parameters and group
parameters. EwE-py using different naming conventions for each with environmantal parameters
being much simpler.

### Environmental Parameters

Environmantal Parameters are named as follows,

- `env_init_c`: Initial environmental contaminant concentration.
- `env_base_inflow_r`: Base contaminant infrow rate.
- `env_decay_r`: Environmental contaminant decay rate.
- `base_vol_ex_loss`: Base environmental volume exchange loss.
- `env_inflow_forcing_idx`: Index of the inflow forcing function to use.

### Group Ecotracer Parameters

There are six types of ecotracer group parameters with the following prefixes,

- `init_c`: Group initial contaminant concentration.
- `immig_c`: Group immigration contaminant concentration
- `direct_abs_r`: Group direct absorption rate.
- `phys_decay_rate`: Physical decay rate.
- `meta_decay_r`: Metabolic decay rate.
- `excretion_r`: Excretion rate.

Then the full name of a ecotracer is structered as follows,

`<prefix>_<group_index>_<group_name>`.

For example, if `Baleen Whale` is the first functional group in the model and there is
between 10 and 100 functional groups, then the parameter for the Baleen Whale's initial 
contaminant concentration would be `init_c_01_Baleen Whale`.

## Management
