from decom_py import EwE

ewe = EwE(r'C:\Program Files\Ecopath with Ecosim 40 years 6.7.0.18865_64-bit', 'Outputs/')
core = ewe.core()

model_file = r'C:\Users\dtan\data\Decommissioning\Past_Ecopath\NorthSea\North Sea.eweaccdb'
ewe.load_model(model_file)

ewe.run_ecopath()
ewe.load_ecosim_scenario(1)
ewe.load_ecotracer_scenario(1)

if not ewe.run_ecosim():
    print("Failed to run ecosim.")

ewe.save_ecopath_results()
if not ewe.save_ecosim_results('Outputs/ecosim_res'):
    print("Failed to save ecosim results.")

core.CloseModel()
