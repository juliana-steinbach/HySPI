This repository provides comprehensive instructions for setting up the required environments to host the necessary libraries for each stage of web app development. It includes:

- The code used to extract databases from Premise;
- Inventories for Hydrogen systems using PEM and AEC technologies;
- Inventory data for the French electricity modeling using a market from neighboring countries;
- The integration code linking the computational LCA (Life Cycle Assessment) model with the Streamlit-based web interface to enhance usability.

Additionally, a simplified version of the web app is available as Jupyter Notebooks, offering an alternative approach to generating results using parameterized values instead of user selections.

How to use this repo:

There are several steps to be completed before lauching this webapp. Three environments are required to complete the steps needed to run all the functionalities available in this repo. The .yml files are available in this repo and the environments can be created by:

```bash
conda env create -f environment_premise.yml
```
```bash
conda env create -f environment_lca_algebraic.yml
```
```bash
conda env create -f environment_streamlit.yml
```

1) The First step you need to follow is activating your premise environment and opening a Jupyter notebook.

```bash
activate environment_premise
```
```bash
jupyter notebook
```
2) In Jupyter notebook open the file 'Premise scenarios.ipynb'. This file contains instructions to:

- Create a brightway project
- Load the ecoinvent 3.9.1 on it
- Load the biosphere database
- Load the databases according to Image, Tiam-UCL or any IAMs you find relevant for your project
- Load a Premise inventory without applying IAM (Premise no updates)
- Load the LCI used in the foreground containing stacks and balance of plant data (AEC/PEM)
- Load the database that adapts RTE scenarios using ecoinvent and Premise inventories (RTE scenarios neighbouring imports)
- Check the databases
- Delete any database if needed

4) Once all databases have been loaded into the project we recommend that you get familiarized with the LCA calculation before diving into the web app. For this you will have to activate your Lca_algebraic environment and open jupyter notebook:

```bash
activate environment_lca_algebraic
```
```bash
jupyter notebook
```
5) In Jupyter Notebook, open the file "Parametrized model and LCA.ipynb". This notebook features a parameterized Life Cycle Assessment (LCA) for both the foreground and background systems. It provides the necessary components to construct an OAT matrix and perform Global Sensitivity Analysis (GSA) using Monte Carlo simulations, available with the lca_algebraic library. Additionally, it includes a similar code implementation to that used in the web application for LCA assessment, integrating a photovoltaic plant into the hydrogen system and generating an LCA results matrix based on various RTE scenario models and IAM applications, as well as different PV credit allocation.
   
6) Once you are familiar with the LCA process, you can explore how the assessment has been adapted for the Streamlit web app. We recommend using PyCharm to run the Streamlit code.

- Open PyCharm and navigate to the file Home.py.
- Ensure it is connected to the correct environment that includes Streamlit and all necessary dependencies by following these steps:
   - Go to Settings > Project: Home.py > Python Interpreter
   - Click Add Interpreter > Select Existing
   - Choose Type: Conda and select the appropriate environment (environment_streamlit)

You can also open Calculator.py, utils.py, and settings.py to understand their roles in the app.

- Ensure that the PyCharm terminal is in the correct project directory. If not, navigate to it using:

```bash
cd path_to_project_file
```
Once in the correct directory, start Streamlit by running:

```bash
streamlit run Home.py
```
And voilà! 🚀 Your web app should now be up and running.
