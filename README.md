# Objective
To build a Flask user-interface which will act as a workbench for future machine learning applications.

## How do I contribute?

### Conda

To save a Conda environment to an environment.yml file, you can use: `conda env export > environment.yml`. This command allows you to export the details of a Conda environment, including all installed packages and their versions, into a YAML file. Note: to exclude build details, use `conda env export | grep -v "^prefix: " > environment.yml`.

To use the environment, firstly create with `conda env create -f environment.yml` then activate as normal.

### Flask

To kill flask application when testing, type command in terminal:  
- `lsof -i :5000`  

Use the below command to kill PID(s):
- `kill -9 PID`  

Note: PID is always numeric. Ex:- kill -9 2882.

### Build Customers dataset

- Navigate to root directory
- Run `python experiments/create_customers_data.py`

### Variable Names

'db_registration_number'
'db_renewal'
'db_payment_frequency'
'db_total_annual_subs' # wrong
'db_arrears' # wrong
'db_financial_distress' # not included
'db_mf_last_year' # wrong
'db_mf_this_year' # wrong
'db_segment' # wrong
'db_claims_paid'
'db_intermediary'

'user-registration-number'
'user-renewal-date'
'user-payment-frequency'
'user-annual-subs'
'user-months-arrears'
'user-months-free-last'
'user-months-free-this'
'user-color-segment'
'user-claims-paid'
'user-intermediary'
'user-intermediary-advisor'



## Date
Created in 2024Q2.