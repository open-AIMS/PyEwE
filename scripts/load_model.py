import warnings
from decom_py import EwE, EwEState

ewe = EwE(r'C:\Program Files\Ecopath with Ecosim 40 years 6.7.0.18865_64-bit', 'Outputs/')
core = ewe.core()
state = EwEState(core)

CORE = ewe._get_core_module()
UTIL = ewe._get_util_module()

model_file = r'C:\Users\dtan\data\Decommissioning\Past_Ecopath\GippslandBasin\East Bass Strait.eweaccdb'
ewe.load_model(model_file)
state.print_summary()

ewe.load_ecosim_scenario(1)

if not ewe.load_ecotracer_scenario(1):
    print("Failed to load ecotracer scenario.")
if not core.ActiveEcotracerScenarioIndex == 1:
    print("Didn't load ecotracer scenarios.")

if not ewe.run_ecosim():
    print("Failed to run ecosim.")
state.print_summary()

print(core.EcosimModelParameters.ContaminantTracing)

print(core.nEcosimYears)
print(core.EcotracerModelParameters.CZero)

ewe.save_ecopath_results()
ewe.save_ecosim_results('Outputs/ecosim_res')

if not ewe.save_ecotracer_results():
    print("Failed to save ecotracer results.")

core.CloseModel()
