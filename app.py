import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Pants Matcher", page_icon="👖", layout="centered")

# --- CHARGEMENT ET PATCH ---
@st.cache_data
def load_data():
    if not os.path.exists("MASTER_CLEAN.csv"): return None
    df = pd.read_csv("MASTER_CLEAN.csv", sep=",")
    
    # === LE PATCH DE RÉPARATION ===
    # 1. On s'assure que c'est des chiffres
    df['W_LABEL'] = pd.to_numeric(df['W_LABEL'], errors='coerce')
    
    # 2. Si la taille est > 50 (ex: 300), on divise par 10
    mask_x10 = df['W_LABEL'] > 50
    if mask_x10.sum() > 0:
        df.loc[mask_x10, 'W_LABEL'] = df.loc[mask_x10, 'W_LABEL'] / 10
        
    # 3. On nettoie pour l'affichage (enlève les .0 moches)
    df['W_LABEL'] = df['W_LABEL'].fillna(0).astype(int)
    
    return df

df = load_data()

if df is None:
    st.error("🚨 Fichier introuvable.")
    st.stop()

# --- HEADER ---
st.title("👖 Pants Matcher")
st.markdown("Comparateur de tailles intelligent : **Levi's** vs **Uniqlo**")
st.divider()

# --- INTERFACE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔵 Je possède")
    
    # 1. MARQUE
    marques = sorted(list(df['MARQUE'].astype(str).unique()))
    ma_marque = st.selectbox("Marque", marques)
    
    # 2. MODÈLE
    df_m = df[df['MARQUE'] == ma_marque]
    modeles = sorted(list(df_m['MODÈLE'].astype(str).unique()))
    mon_modele = st.selectbox("Modèle", modeles)
    
    # 3. TAILLE (Maintenant corrigée !)
    df_mod = df_m[df_m['MODÈLE'] == mon_modele]
    tailles = sorted(df_mod['W_LABEL'].unique())
    ma_taille = st.selectbox("Taille (W)", tailles)
    
    # REF
    try:
        ref = df_mod[df_mod['W_LABEL'] == ma_taille].iloc[0]
        st.success(f"**Votre Jean :**\n\nCeinture : {ref['WAIST_CM']:.1f} cm\n\nCuisse : {ref['REAL_THIGH']:.1f} cm")
    except:
        st.warning("Donnée manquante.")
        st.stop()

with col2:
    st.subheader("🟠 Je cherche chez")
    cibles = [m for m in marques if m != ma_marque]
    if not cibles:
        st.error("Pas d'autre marque dispo !")
        st.stop()
    marque_cible = st.selectbox("Marque Cible", cibles)
    st.write("") 
    st.write("")
    
    lancer = st.button("🔍 COMPARER", type="primary", use_container_width=True)

st.divider()

# --- RÉSULTATS ---
if lancer:
    st.subheader(f"Résultats chez {marque_cible}")
    
    candidats = df[df['MARQUE'] == marque_cible].copy()
    
    # 1. FILTRE CEINTURE
    candidats = candidats[
        (candidats['WAIST_CM'] >= ref['WAIST_CM'] - 2.5) & 
        (candidats['WAIST_CM'] <= ref['WAIST_CM'] + 2.5)
    ]
    
    if candidats.empty:
        st.warning(f"Aucun équivalent trouvé pour ce tour de taille ({ref['WAIST_CM']:.0f} cm).")
    else:
        # 2. COMPARAISON CUISSE
        candidats['DIFF'] = candidats['REAL_THIGH'] - ref['REAL_THIGH']
        candidats['ABS_DIFF'] = candidats['DIFF'].abs()
        top = candidats.sort_values('ABS_DIFF').head(5)
        
        for i, row in top.iterrows():
            diff = row['DIFF']
            
            if abs(diff) <= 2:
                color = "green"; icon = "✅"; txt = "CONFORT IDENTIQUE"
            elif diff > 2:
                color = "blue"; icon = "ℹ️"; txt = f"PLUS LARGE (+{diff:.1f} cm)"
            else:
                color = "orange"; icon = "⚠️"; txt = f"PLUS SERRÉ ({diff:.1f} cm)"
            
            with st.container():
                c1, c2 = st.columns([0.7, 0.3])
                c1.markdown(f"**{row['MODÈLE']}** (W{row['W_LABEL']})")
                c1.caption(f"Coupe : {row['COUPE']}")
                c2.markdown(f":{color}[**{icon} {txt}**]")
                st.divider()
