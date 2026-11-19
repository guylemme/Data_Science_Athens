# Air Quality Monitoring in Athens — Programming for Data Science

Final project for the **Programming for Data Science** course at **ESILV**.  
This project applies the KDD process to explore, analyze, and visualize multidimensional air quality and meteorological data from Athens, Greece.

---

## 👥 Team Members

* **Guilhem LE DU**
* **Anais KAMTCHOUANG NONO**
* **Yutong CAO**
* **Soukaina BAHAMI**

---

## 📊 Dataset Description

* **Source:** [Air Quality Monitoring in European Cities (Kaggle)](https://www.kaggle.com/datasets/yekenot/air-quality-monitoring-in-european-cities)
* **Subset used:** `athens_data.csv` (**1,726,464 rows** × **19 columns**, hourly observations starting May 2020)
* **Multidimensional structure:**
  * **Temporal dimension:** `Date` (`YYYY-MM-DD HH:MM:SS`, hourly resolution)
  * **Spatial dimension:** `Latitude`, `Longitude`, `station_name`, `code`, `id`
  * **Analytical dimension:**
    * *Air pollutants (`µg/m³`):* `PM10`, `PM2.5`, `NO2`, `O3`
    * *Meteorological & environmental variables:* `Wind-Speed (U)`, `Wind-Speed (V)`, `Temp`, `Dewpoint Temp`, `Soil Temp`, `Total Percipitation`, `Relative Humidity`, `Vegitation (High)`, `Vegitation (Low)`

---

## 🎯 Project Objectives & Queries

1. **Data Exploration & Preprocessing (`Task 1`):**
   * Load the dataset, inspect data types, missing values, and variable ranges.
2. **Information Building (`Task 2`):**
   * **Query 1**
   * **Query 2**
   * **Query 3a**
   * **Query 3b**
3. **Interactive Dashboard (`Task 3`):**

---

## ⚙️ Installation & Usage

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/<your-repository-name>.git
cd <your-repository-name>
```

### 2. Set up the Python environment
Using Conda :
```bash
conda create -n air_quality_ds python=3.11 -y
conda activate air_quality_ds
pip install pandas numpy matplotlib seaborn scikit-learn mlxtend dash plotly kagglehub jupyter
```

### 3. Download the dataset (if not included in `data/`)
```python
import kagglehub
path = kagglehub.dataset_download("yekenot/air-quality-monitoring-in-european-cities")
print("Dataset downloaded to:", path)
```

### 4. Run the Notebook & Dashboard
Open `familyNameLeader_notebook.ipynb` in Jupyter Notebook or VS Code and run all cells. The `__main__` block executes the full pipeline (data loading, exploration, indicator computation, and Dash dashboard launch).

---

## 📝 Code Conventions & Academic Requirements

* Every processing step is encapsulated in a dedicated Python function (`def ...`) with explicit `# Input:` and `# Output:` documentation.
* All functions are orchestrated from the `if __name__ == "__main__":` entry point.
* Every analytical indicator is documented in Markdown with its calculation formula, meaning, and interpretation.
