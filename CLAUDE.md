# Projet : Copilote d'anesthésie – prédiction de l'hypotension peropératoire

## Qui je suis
Nicolas Sales, Data Scientist (consultant chez Davidson Consulting depuis sept. 2026).
Ancien infirmier anesthésiste (IADE, 2017-2023), infirmier, pompier de Paris.
Mastère IA & Management (IA School, major de promo). Stage INSERM : analyse EEG (MNE).
Expérience : NLP Hugging Face chez Europcar (189 K€ d'économies), RAG multimodal (PyMuPDF, CLIP, RAGAS).
Stack maîtrisée : Python, scikit-learn, XGBoost, TensorFlow/Keras, Hugging Face, LangChain/LangGraph,
FastAPI, Streamlit, Docker, MLflow, DVC, Airflow, AWS (ECS Fargate, ECR, S3), GitHub Actions, Evidently.
Je veux un projet à fort impact, où j'apprends des choses nouvelles : DL sur signaux physiologiques,
modèles de fondation pour séries temporelles, évaluation clinique rigoureuse, temps réel.
Explique-moi les concepts nouveaux au fil de l'eau, en français.

## But du projet
Prédire l'hypotension peropératoire (PAM < 65 mmHg pendant ≥ 1 min) 5, 10 et 15 min à l'avance,
à partir des signaux du moniteur, puis l'afficher dans un écran temps réel type moniteur de bloc :
courbes qui défilent (PAM, ECG, pléthysmographie, FC, SpO2, EtCO2, BIS), jauge de risque avec incertitude,
et un bot LLM qui EXPLIQUE la prédiction (facteurs SHAP + contexte : médicaments, phase opératoire).
Le bot propose des éléments à considérer, jamais des prescriptions.

Angle de recherche : l'outil commercial HPI (Edwards) fait à peine mieux qu'une baseline « PAM seule ».
Objectif : battre HONNÊTEMENT cette baseline, avec un protocole sans fuite de données
(split par patient, pas d'échantillons déjà en hypotension, horizon de prédiction strict).
Livrables : repo GitHub propre, démo temps réel (rejeu de chirurgies enregistrées), article technique / preprint.

## Données : VitalDB (https://vitaldb.net/dataset)
6 388 chirurgies non cardiaques, Seoul National University Hospital. API publique : api.vitaldb.net,
package Python `vitaldb` (vitaldb.load_case(caseid, tracks, interval)).
Citer : Lee HC et al., Sci Data 2022;9:279. Respecter le Data Use Agreement.

### Déjà validé (à recréer)
1. `src/data/cohort.py` : catalogue via https://api.vitaldb.net/cases et /trks. Filtres : ane_type == "General",
   age >= 18, pistes SNUADC/ART ET Solar8000/ART_MBP présentes, (aneend - anestart) >= 60 min.
   Résultat : 3 558 chirurgies -> data/cohort.csv.
2. `src/data/download.py` : un parquet par cas, reprise si interrompu, téléchargement parallèle (4 threads).
   - data/numerics/{caseid}.parquet à 1 Hz (~160 Ko/cas) : Solar8000/ART_MBP, ART_SBP, ART_DBP, NIBP_MBP, HR,
     PLETH_SPO2, ETCO2, BT ; BIS/BIS ; Primus/MAC, PEEP_MBAR, TV ; Orchestra/PPF20_CE, RFTN20_CE, PHEN_RATE, NEPI_RATE.
   - option --waveforms : daSNUADC/ART, ECG_II, PLETHta/waveforms/{caseid}.parquet à 100 Hz (~10 Mo/cas, ~35 Go au total) :
     .
   - `load_numerics()` : ffill(limit=4) car Solar8000 mesure toutes les ~2 s (50 % de NaN à 1 Hz sinon),
     PAM hors [20, 200] mise à NaN (artefacts rinçage/prélèvement).

### Constats du contrôle qualité (test sur 5 cas)
- Certains cas listent la piste ART mais elle est vide (ex. cas 3) -> filtre qualité à ajouter :
  PAM disponible sur ≥ 70 % de la durée d'anesthésie.
- Épisodes d'hypotension bien présents (6 à 11 par cas sur 3 des 5 cas).
- Vasopresseurs en perfusion rares (< 5 % des cas) ; les bolus d'éphédrine/phényléphrine ne sont qu'en totaux
  dans cases (intraop_eph, intraop_phe) -> limite à documenter.

## Prochaines étapes
1. Environnement : .venv + requirements.txt (vitaldb, pandas, pyarrow, numpy, matplotlib).
2. Recréer cohort.py et download.py, télécharger les constantes de toute la cohorte, ajouter le filtre qualité.
3. Définir les étiquettes (événement, horizons 5/10/15 min, exclusions) et le split train/val/test par patient.
4. Baselines : PAM seule (dernière valeur, pente), puis régression logistique / XGBoost sur features de fenêtre.
5. Écran de rejeu temps réel (FastAPI + WebSocket, front React + uPlot) branché sur la baseline.
6. Modèles deep sur ondes 100 Hz + modèles de fondation (Chronos, MOMENT), calibration, prédiction conforme.
7. Évaluation clinique : AUC, délai d'anticipation, fausses alarmes/heure, anti-fatigue d'alarme.
8. Couche LLM explicative, puis rédaction ou couche agentique (voir section dédiée) : agent enquêteur, puis débriefing, avec son évaluation. Puis rédaction.

## Couche agentique (LangGraph)
Principe : l'agent ne prédit JAMAIS. Le risque vient du modèle ML (déterministe, calibré, mesuré).
L'agent enquête, explique et documente. Il tourne hors de la boucle temps réel (asynchrone).

### Agent 1 : enquêteur d'alerte (priorité)
Déclenché quand le risque dépasse le seuil (avec délai minimal entre deux alertes).
Outils :
- get_risk() : risque + intervalle d'incertitude à 5/10/15 min
- get_shap_factors() : facteurs qui poussent vers l'alerte
- get_drug_timeline() : bolus et concentrations (propofol, remifentanil, curares) des dernières minutes
- get_surgical_phase() : induction, incision, pneumopéritoine, fermeture…
- get_trends() : pentes PAM / FC / BIS, variabilité de pression pulsée
- search_guidelines() : RAG sur recommandations publiques (SFAR, ESAIC), avec citation des sources
Sortie : message court (3 lignes max), sourcé, en « éléments à considérer », jamais de prescription
(ni médicament, ni dose).

### Agent 2 : débriefing post-opératoire
En fin de chirurgie : nombre d'épisodes, durée cumulée sous 65 mmHg, alertes anticipées / manquées /
fausses, contexte de chaque épisode. Export en compte rendu.

### Agent 3 (optionnel) : chercheur sur la cohorte
Question en langage naturel -> écrit et exécute l'analyse pandas sur VitalDB -> chiffres + graphique.

### Évaluation de la couche agentique (obligatoire, c'est le point différenciant)
- Fidélité : chaque affirmation du message doit être vérifiable dans les sorties d'outils
  (contrôle automatique, zéro hallucination tolérée).
- Pertinence clinique : jeu de ~50 alertes annotées par moi (IADE), puis LLM-as-judge calibré
  sur mes annotations (mesurer l'accord).
- Latence : message affiché en < 5 s après l'alerte.
- Traçabilité : logger chaque appel d'outil (LangSmith ou équivalent).

### Ordre
Modèle ML + écran temps réel d'abord. Ensuite agent 1, puis agent 2, puis agent 3.

## Conventions
- Code et commentaires simple et lisible. Modules lancés avec `python -m src....`.
- Ne jamais committer data/ (ajouter au .gitignore).
- Windows + PowerShell.