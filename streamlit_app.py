import streamlit as st
import pandas as pd
import zipfile
import os

def extract_csv_from_zip(zip_file, keyword="1DAY.csv"):
    """Extrait un fichier CSV spécifique d'un fichier ZIP."""
    with zipfile.ZipFile(zip_file, 'r') as z:
        for file_name in z.namelist():
            if keyword in file_name:
                z.extract(file_name, path="extracted_files/")
                return os.path.join("extracted_files", file_name)
    return None

def process_file(csv_path, start_date, end_date):
    """Traite le fichier CSV, filtre par plage de dates, et calcule les totaux mensuels."""
    try:
        # Charger les données
        data = pd.read_csv(csv_path)
        data.rename(columns={"Time Bucket (Europe/Budapest)": "Date"}, inplace=True)
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        data.replace("No CT", pd.NA, inplace=True)
        
        # Supprimer les colonnes vides (ou contenant uniquement des NaN)
        data = data.dropna(axis=1, how="all")
        
        # Convertir les colonnes en numériques
        for col in data.columns:
            if col != "Date":
                data[col] = pd.to_numeric(data[col], errors="coerce")
        
        # Filtrer par plage de dates
        filtered_data = data[(data["Date"] >= start_date) & (data["Date"] <= end_date)]
        filtered_data["Month"] = filtered_data["Date"].dt.to_period("M")
        
        # Calculer les totaux mensuels
        numeric_columns = filtered_data.select_dtypes(include=["number"])
        monthly_totals = numeric_columns.groupby(filtered_data["Month"]).sum()
        
        # Ajouter un total par mois (somme de toutes les colonnes pour chaque mois)
        monthly_totals["Total Mois"] = monthly_totals.sum(axis=1)

        # Calculer un total global pour la période sélectionnée
        total_period = monthly_totals["Total Mois"].sum()

        # Éclater les données : chaque colonne devient une ligne
        exploded_data = monthly_totals.reset_index().melt(id_vars=["Month"], var_name="Colonne", value_name="Valeur")

        return monthly_totals, exploded_data, total_period
    except Exception as e:
        st.error(f"Erreur lors du traitement des données : {e}")
        return None, None, None

# Titre de l'application
st.title("Analyse des Données Énergétiques")

# Charger un fichier ZIP
uploaded_zip = st.file_uploader("Chargez un fichier ZIP contenant le CSV 1DAY", type=["zip"])

if uploaded_zip:
    # Extraire le fichier contenant 1DAY.csv
    csv_path = extract_csv_from_zip(uploaded_zip, "1DAY.csv")
    
    if csv_path:
        st.success(f"Fichier trouvé et extrait : {csv_path}")
        
        # Lire un aperçu des données pour déterminer les plages de dates
        data_preview = pd.read_csv(csv_path)
        data_preview.rename(columns={"Time Bucket (Europe/Budapest)": "Date"}, inplace=True)
        data_preview["Date"] = pd.to_datetime(data_preview["Date"], errors="coerce")
        
        st.write("### Aperçu des données")
        st.dataframe(data_preview.head())
        
        # Obtenir les plages de dates
        min_date = data_preview["Date"].min()
        max_date = data_preview["Date"].max()
        
        # Sélecteurs de plage de dates
        st.write("### Sélectionnez une plage de dates")
        start_date = st.date_input("Date de début", value=min_date, min_value=min_date, max_value=max_date)
        end_date = st.date_input("Date de fin", value=max_date, min_value=min_date, max_value=max_date)
        
        if start_date > end_date:
            st.error("La date de début doit être antérieure ou égale à la date de fin.")
        else:
            # Traiter les données et afficher les résultats
            monthly_totals, exploded_data, total_period = process_file(csv_path, pd.Timestamp(start_date), pd.Timestamp(end_date))
            if monthly_totals is not None and exploded_data is not None:
                st.write("### Résultats par Mois (Tableau Agrégé)")
                st.dataframe(monthly_totals)
                
                st.write(f"### Total pour la période sélectionnée : **{total_period:.2f}** kWh")
                
                st.write("### Résultats par Mois et par Colonne (Tableau Éclaté)")
                st.dataframe(exploded_data)
                
                st.write("### Graphique des Totaux Mensuels")
                st.bar_chart(monthly_totals["Total Mois"])
    else:
        st.error("Le fichier 1DAY.csv n'a pas été trouvé dans l'archive ZIP.")
