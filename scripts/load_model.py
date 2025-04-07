from decom_py import EwE

ewe = EwE(r'C:\Program Files\Ecopath with Ecosim 40 years 6.7.0.18865_64-bit')
core = ewe.core()

model_file = r'C:\Users\dtan\data\Decommissioning\Past_Ecopath\NorthSea\North Sea.eweaccdb'
ewe.load_model(model_file)

ewe.run_ecopath()
ewe.load_ecosim_scenario(0)
ewe.load_ecotracer_scenario(0)

ewe.run_ecosim()

ewe.save_ecopath_results('Outputs/ecopath_outputs.csv')
ewe.save_ecosim_results("Outputs/ecosim_outputs.csv")

core.CloseModel()
