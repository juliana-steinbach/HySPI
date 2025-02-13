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
2) In Jupyter notebook open the file 'Project creation + biosphere + ecoinvent.ipynb'. This file contains instructions to:

- Create a brightway project
- Load the ecoinvent 3.9.1 on it
- Load the biosphere database
- Check the databases
- Load the database that adapts RTE scenarios using ecoinvent
- Load the LCI used in the foreground containing stacks and balance of plant data

3) Once ecoinvent and biosphere were loaded into the project, it is time to load the databases that modelled the RTE scenarios using AIMs. Open the file 'Premise scenarios.ipynb'. This file contains instructions to:

- Open the brightway project created previously
- Load the databases according to Image, Tiam-UCL or any IAMs you find relevant for your project
- Check the databases
- Delete any database if needed

4) Once all databases have been loaded into the project we recommend that you get familiarized with the LCA calculation before diving into the web app. For this you will have to activate your LCA_algebraic environment and open jupyter notebook:

```bash
activate environment_lca_algebraic
```
```bash
jupyter notebook
```
5) In jupyter notebook open the file Parametrized assessment.ipynb. This file contains the same sequence of code used in the web app for the LCA calculation. Run the code adapting project and database names. This LCA calculation provides a parametrized view of the results, and this can give you an idea regarding the uncerntainties of the model and which activities play the most and the least important role in the assessment.
   
6) Once you are familirized with the LCA part, you can see how the assessment was adapated to the streamlit web app. We recommend the use of Pycharm to run the streamlit code. In pycharm, open the file Home.py and make sure it is conected to the environment that contains streamlite and the other dependencies, this can be done by:

- Opening the file Home.py and go into Settings >> Project: Home.py >> Python interpreter >> add interpreter >> Select existing >> Type: Conda >> Choose the environment_streamlit.
- You can also open the files Calculator.py, utils.py and settings.py.
- To run the web app make sure the pycharm terminal is in the same directory that you project is locates, in case it is not use:

```bash
cd path_to_project_file
```
Once you are in the right directory you can run streamlit by typing Streamlit run Home.py

and voile la!
