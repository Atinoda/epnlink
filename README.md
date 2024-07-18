# epnlink
Python interface to [EnergyPLAN - Advanced energy system analysis computer model](https://www.energyplan.eu).

## Description
This project provides python input-output parsers for the EnergyPLAN energy system modelling software, with data managed using `pandas` dataframes. It includes a descriptive `key:value` map of the GUI fields. It is intended for simulation automation using [command line calls](https://www.energyplan.eu/training/faqs/#eleven), and is confirmed to work correctly with EnergyPLAN 16.2. running under WINE.

## Functionality
- Map GUI fields to configuration `key:value` pairs
- Read and write EnergyPLAN simulation input files
- Read and parse EnergyPLAN ascii output files

## Installation
Install from pypi with `pip install epnlink`

## Usage
Please refer to the docstrings in the code for detailed usage. While this library can be used to fully specify simulations, the recommended workflow is to build base simulations using the GUI and leverage this library for sensitivity testing or optimisation.

**Quick-start example:**

```python
import epnlink as ep

# Create a template file
df_tmp = ep.utilities.get_ep_template()

# Initialise the template to zeros
df_tmp = ep.utilities.initialise_settings(df_tmp)

# Or, read an existing file that was saved by EnergyPLAN
fpath_raw = "/home/EnergyPLAN/input.txt"
df = ep.utilities.load_settings_file(fpath_raw, raw=True)

# Modify the capacity of renewable generation technology 1
df.loc['input_RES1_capacity', 'value'] = 42

# Save the modified file
fpath_mod = "/home/EnergyPLAN/input-mod.txt"
df_out = df.dropna(subset='value')
ep.utilities.save_settings_file(df, fpath_mod)

# Readback the modified file as a demonstration - notice that raw=False
df_mod = ep.utilities.load_settings_file(fpath_mod, raw=False)

# < RUN A SIMULATION VIA CLI - e.g., subprocess.run() >
# "energyPLAN.exe -i input-mod.txt -ascii results.ascii"

# Parse the simulation results to dict of dataframes
fpath_results = "/home/EnergyPLAN/results.ascii"
results = ep.results.read_ascii_file(fpath_results)

# Examine annual fuel balance dataframe
df_fb = results['annual_fuel_balance']
```

### Working with EnergyPLAN input .txt files
EnergyPLAN input files are in `.txt` format. If the files are produced directly from EnergyPLAN, they will be encoded as `cp1252`. If they have been saved by this library they will use `utf-8` encoding. EnergyPLAN can work with either format, but it defaults to `cp1252`.

#### Creating input files
Create a template input file with `df = ep.utilities.get_ep_template()` and initialise it with `df = ep.utilities.initialise_settings(df)`. The template contains the descriptive mapping between GUI fields and parameter `key:value` pairs.

#### Reading input files
Load an existing EnergyPLAN input file with `ep.utilities.load_settings_file(fpath, raw=True)`. If the file has been produced by this library, set `raw=False`. *If in doubt - try each setting!*

#### Writing input files
Save an input file for EnergyPLAN with `ep.utilities.save_settings_file(df, fpath)`, where `df` contains the EnergyPLAN settings, and `fpath` is the absolute or relative path to save the file.

### Working with EnergyPLAN output .ascii files
This library parses the `.ascii` files that EnergyPLAN outputs when called from the command line interface. When used from the GUI, EnergyPLAN can also output files to the screen as tabulated plaintext or to the clipboard for pasting into spreadsheet software - these workflows are not supported by `epnlink`.

#### Parsing .ascii results
Parse the results into a dict of dataframes with `ep.results.read_ascii_file(fpath)` containing:

| Results key                       | Contents                                                       |
| --------------------------------- | -------------------------------------------------------------- |
| annual_costs                      | Costs - total, variable, and components                        |
| annual_emissions                  | Emissions - SO2, PM2.5, NOx, CH4, N2O                          |
| annual_emissions_co2              | CO2 emissions                                                  |
| annual_fuel_balance               | Fuel balance across applications                               |
| annual_fuel_consumption           | Fuel consumption – total and households                        |
| annual_investment_costs           | Investment costs – Total, Annual, and Fixed O&M                |
| annual_share_of_res               | Share of renewable energy – PES, Electricity, Total production |
| application_annual_avg_max_min_mw | Application demand - Average, Max, and Min                     |
| application_annual_total_twh      | Application demand – Total TWh                                 |
| application_hourlies_mw           | Application hourly demand                                      |
| application_monthly_avg_mw        | Application monthly averages                                   |
| calculation_time                  | Simulation calculation time (invalid)                          |
| sim_parameters                    | Copy of the simulation input settings                          |

# Citation
If you find this library useful in your work, we would appreciate it if you cite the following paper:

**C. Cameron, A. Foley, H. Lund, and S. McLoone, *‘A soft-linking method for responsive modelling of decarbonisation scenario costs’*, International Journal of Sustainable Energy Planning and Management, 2024, [https://doi.org/10.54337/ijsepm.8234](https://doi.org/10.54337/ijsepm.8234)**

Bibtex:
```bibtex
@article{cameron_2024,
	title = {A soft-linking method for responsive modelling of decarbonisation scenario costs},
	doi = {10.54337/ijsepm.8234},
	author = {Cameron, Ché and Foley, Aoife and Lund, Henrik and McLoone, Seán},
}
```
