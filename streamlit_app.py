import streamlit as st
import pandas as pd

def process_file(uploaded_file, start_date, end_date):
    try:
        # Lire le fichier
        data = pd.read_excel(uploaded_file, engine='pyxlsb')

        # Diviser les colonnes
        data_split = data.iloc[:, 0].str.split(',', expand=True)
        data_split.rename(columns={0: "Date"}, inplace=True)

        # Convertir la colonne "Date" en datetime
        data_split["Date"] = pd.to_datetime(data_split["Date"], errors="coerce")
        data_cleaned = data_split.dropna(subset=["Date"])

        # Filtrer les données selon la plage de dates
        data_filtered = data_cleaned[(data_cleaned["Date"] >= start_date) & (data_cleaned["Date"] <= end_date)]

        # Convertir toutes les autres colonnes en numériques
        for col in data_filtered.columns[1:]:
            data_filtered[col] = pd.to_numeric(data_filtered[col], errors="coerce")

        # Ajouter une colonne "Month"
        data_filtered["Month"] = data_filtered["Date"].dt.to_period("M")

        # Sélectionner uniquement les colonnes numériques
        numeric_columns = data_filtered.select_dtypes(include=["number"])

        # Grouper par mois et calculer les totaux
        monthly_totals = numeric_columns.groupby(data_filtered["Month"]).sum()
        return monthly_totals

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")
        return None

# Titre de l'application
st.title("Analyse des Données Mensuelles avec Filtres")

# Charger un fichier
uploaded_file = st.file_uploader("Chargez votre fichier Excel", type=["xlsb"])

if uploaded_file:
    # Lire un aperçu pour déterminer les plages de dates
    data_preview = pd.read_excel(uploaded_file, engine='pyxlsb')
    data_preview["Date"] = pd.to_datetime(data_preview.iloc[:, 0].str.split(',', expand=True)[0], errors="coerce")

    # Afficher les premières lignes pour vérifier la structure
    st.write("### Aperçu des Données")
    st.dataframe(data_preview.head())

    # Déterminer les dates min et max dans le fichier
    min_date = data_preview["Date"].min()
    max_date = data_preview["Date"].max()

    # Sélection des dates de début et de fin
    st.write("### Sélectionnez une plage de dates")
    start_date = st.date_input("Date de début", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("Date de fin", value=max_date, min_value=min_date, max_value=max_date)

    # Assurez-vous que la date de début est avant la date de fin
    if start_date > end_date:
        st.error("La date de début doit être antérieure ou égale à la date de fin.")
    else:
        # Appeler la fonction de traitement
        results = process_file(uploaded_file, pd.Timestamp(start_date), pd.Timestamp(end_date))
        if results is not None:
            st.write("### Résultats par Mois")
            st.dataframe(results)
            st.write("### Graphique des Totaux Mensuels")
            st.bar_chart(results)
