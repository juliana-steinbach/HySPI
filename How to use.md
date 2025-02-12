This repository provides comprehensive instructions for setting up the required environments to host the necessary libraries for each stage of web app development. It includes:

- The code used to extract databases from Premise;
- Inventories for Hydrogen systems using PEM and AEC technologies;
- Inventory data for the French electricity modeling using a market from neighboring countries;
- The integration code linking the computational LCA (Life Cycle Assessment) model with the Streamlit-based web interface to enhance usability.

Additionally, a simplified version of the web app is available as Jupyter Notebooks, offering an alternative approach to generating results using parameterized values instead of user selections.

How to use this repo:

There are several steps to be completed before lauching this webapp. Three environments are required to complete the steps needed to run all the functionalities available in this repo. The environment creation can be found here

```bash
conda env create -f environment_premise.yml
```
```bash
conda env create -f environment_lca_algebraic.yml
```
```bash
conda env create -f environment_streamlit.yml
```

First you need to create a brightway project. This can be done using brightway2, which is installed alongside the two libraries required in this repo, premise and lca_algebraic. Here we will demonstrate how to create the project using premise environment:

Activate your premise environment:

```bash
conda activate environment_premise
```


Once ecoinvent is loeaded into your project you can transform the database according to the IAM scenarios available in Premise. To do this transformation you can use the same notebook used previously




Once the project is created databases can be loaded into the project before execution. The first database needed is ecoinvent, 
