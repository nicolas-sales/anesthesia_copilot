# Copilote d'anesthésie – prédiction de l'hypotension peropératoire

Prédire l'hypotension peropératoire (PAM < 65 mmHg pendant ≥ 1 min) 5, 10 et 15 min à l'avance
à partir des signaux du moniteur, avec un écran de rejeu temps réel.

Données : [VitalDB](https://vitaldb.net/dataset) – Lee HC et al., *Sci Data* 2022;9:279.
Les données ne sont pas versionnées (`data/` est dans le `.gitignore`), conformément au Data Use Agreement.

## Lancer

```powershell
conda activate .\venvcop
pip install -r requirements.txt
python -m src.data.cohort      # -> data/cohort.csv
```

## Cohorte (diagramme de flux)

| Étape | Chirurgies |
|---|---|
| VitalDB | 6 388 |
| Anesthésie générale | 6 043 |
| Âge ≥ 18 ans | 5 989 |
| Pistes `SNUADC/ART` **et** `Solar8000/ART_MBP` présentes | 3 575 |
| Durée d'anesthésie ≥ 60 min | **3 558** (3 427 patients) |

---

# Dictionnaire des données

## Convention de temps

Tous les temps sont en **secondes relatives au début de l'enregistrement** (`casestart = 0`).
Une valeur négative signifie « avant le début de l'enregistrement »
(ex. `anestart = -552` : l'anesthésie a commencé 9 min avant que le moniteur n'enregistre).

---

## 1. `cases` – informations cliniques (API `/cases`, 1 ligne par chirurgie, 74 colonnes)

Colonne **Usage** :
- **Feature** : variable préopératoire utilisable par le modèle
- **Option** : à tester plus tard (ablation)
- **Méta** : nécessaire au pipeline, mais pas comme feature
- **Interdit** : connu seulement en fin de chirurgie ou après → **fuite de données** si utilisé comme feature
- **Exclu** : non pertinent ou trop de valeurs manquantes

### Identifiants et temps

| Colonne | Description | Unité | Usage |
|---|---|---|---|
| `caseid` | Identifiant de la chirurgie | – | Méta |
| `subjectid` | Identifiant du **patient** (un patient peut avoir plusieurs chirurgies) → clé du split | – | Méta |
| `casestart` | Début de l'enregistrement (toujours 0) | s | Méta |
| `caseend` | Fin de l'enregistrement | s | Méta |
| `anestart` | Début de l'anesthésie | s | Méta |
| `aneend` | Fin de l'anesthésie (cas 4476 corrompu : −3,69 × 10⁹) | s | Méta |
| `opstart` | Début de la chirurgie (incision) | s | Méta |
| `opend` | Fin de la chirurgie (inconnue en temps réel : jamais comme feature) | s | Méta |
| `adm` | Admission à l'hôpital | s | Exclu |
| `dis` | Sortie de l'hôpital | s | Interdit |
| `icu_days` | Durée de séjour en réanimation postopératoire | jours | Interdit |
| `death_inhosp` | Décès pendant l'hospitalisation (0/1) | – | Interdit |

### Démographie et contexte opératoire

| Colonne | Description | Unité | Usage |
|---|---|---|---|
| `age` | Âge (min 0,3 : enfants présents avant filtre) | ans | Feature |
| `sex` | Sexe (M/F) | – | Feature |
| `height` | Taille | cm | Option |
| `weight` | Poids | kg | Feature |
| `bmi` | Indice de masse corporelle | kg/m² | Feature |
| `asa` | Score ASA (1 à 6), 133 NaN | – | Feature |
| `emop` | Chirurgie en urgence (0/1) | – | Feature |
| `department` | Spécialité (General surgery, Thoracic surgery, Urology, Gynecology) | – | Feature |
| `optype` | Type d'intervention (Colorectal, Stomach, Biliary/Pancreas…) | – | Feature |
| `dx` | Diagnostic (texte libre, espaces parasites → `.str.strip()`) | – | Exclu |
| `opname` | Nom de l'intervention (texte libre) | – | Exclu |
| `approach` | Voie d'abord (Open, Videoscopic, Robotic) | – | Feature |
| `position` | Position opératoire (Supine, Lithotomy, Reverse Trendelenburg, Prone…) | – | Feature |
| `ane_type` | Type d'anesthésie (General, Spinal, Sedationalgesia) | – | Méta (filtre) |

### Antécédents et bilan préopératoire

| Colonne | Description | Unité | Usage |
|---|---|---|---|
| `preop_htn` | Hypertension artérielle (0/1) | – | Feature |
| `preop_dm` | Diabète (0/1) | – | Feature |
| `preop_ecg` | ECG préopératoire (texte : Normal Sinus Rhythm, Atrial fibrillation…) | – | Option (indicateur FA) |
| `preop_pft` | Explorations fonctionnelles respiratoires | – | Exclu |
| `preop_hb` | Hémoglobine | g/dL | Feature |
| `preop_plt` | Plaquettes | ×10³/µL | Exclu |
| `preop_pt` | Taux de prothrombine | % | Exclu |
| `preop_aptt` | TCA | s | Exclu |
| `preop_na` | Sodium | mmol/L | Feature |
| `preop_k` | Potassium | mmol/L | Exclu |
| `preop_gluc` | Glycémie | mg/dL | Option |
| `preop_alb` | Albumine | g/dL | Feature |
| `preop_ast` | ASAT | UI/L | Exclu |
| `preop_alt` | ALAT | UI/L | Exclu |
| `preop_bun` | Urée sanguine | mg/dL | Option |
| `preop_cr` | Créatinine | mg/dL | Feature |
| `preop_ph` | pH artériel (~91 % NaN) | – | Exclu |
| `preop_hco3` | Bicarbonates (~91 % NaN) | mmol/L | Exclu |
| `preop_be` | Excès de base (~91 % NaN) | mmol/L | Exclu |
| `preop_pao2` | PaO2 (~91 % NaN) | mmHg | Exclu |
| `preop_paco2` | PaCO2 (~91 % NaN) | mmHg | Exclu |
| `preop_sao2` | SaO2 (~91 % NaN) | % | Exclu |

### Voies aériennes et abords vasculaires

| Colonne | Description | Unité | Usage |
|---|---|---|---|
| `cormack` | Grade de Cormack-Lehane (I à IV) | – | Exclu |
| `airway` | Voie d'intubation (Oral, Nasal, Tracheostomy) | – | Exclu |
| `tubesize` | Diamètre interne de la sonde d'intubation | mm | Exclu |
| `dltubesize` | Sonde double lumière (ex. Left-35) | Fr | Exclu |
| `lmasize` | Taille du masque laryngé | – | Exclu |
| `iv1`, `iv2` | Sites des voies veineuses périphériques | – | Exclu |
| `aline1`, `aline2` | Sites du cathéter artériel (radial, fémoral…) | – | Méta (contrôle qualité) |
| `cline1` | Site de la voie veineuse centrale (IJV, sous-clavière…) | – | Option (indicateur VVC) |
| `cline2` | 2ᵉ voie veineuse centrale | – | Exclu |

### Totaux peropératoires (fin de chirurgie → **jamais comme features**)

Utiles pour la Table 1 de l'article et pour l'agent de débriefing post-opératoire.

| Colonne | Description | Unité | Usage |
|---|---|---|---|
| `intraop_ebl` | Pertes sanguines estimées | mL | Interdit |
| `intraop_uo` | Diurèse | mL | Interdit |
| `intraop_rbc` | Culots globulaires transfusés | unités | Interdit |
| `intraop_ffp` | Plasma frais congelé transfusé | unités | Interdit |
| `intraop_crystalloid` | Cristalloïdes | mL | Interdit |
| `intraop_colloid` | Colloïdes | mL | Interdit |
| `intraop_ppf` | Propofol en bolus | mg | Interdit |
| `intraop_mdz` | Midazolam | mg | Interdit |
| `intraop_ftn` | Fentanyl | µg | Interdit |
| `intraop_rocu` | Rocuronium | mg | Interdit |
| `intraop_vecu` | Vécuronium | mg | Interdit |
| `intraop_eph` | Éphédrine (total, pas d'horodatage des bolus) | mg | Interdit |
| `intraop_phe` | Phényléphrine (total, pas d'horodatage des bolus) | µg | Interdit |
| `intraop_epi` | Adrénaline | µg | Interdit |
| `intraop_ca` | Chlorure de calcium | mg | Interdit |

---

## 2. `trks` – liste des pistes (API `/trks`, 1 ligne par signal enregistré)

| Colonne | Description |
|---|---|
| `caseid` | Identifiant de la chirurgie |
| `tname` | Nom de la piste, au format `Appareil/Signal` (ex. `Solar8000/ART_MBP`) |
| `tid` | Identifiant de la piste → `https://api.vitaldb.net/{tid}` renvoie ses valeurs (`Time`, valeur) |

Appareils : `Solar8000` (moniteur patient), `SNUADC` (ondes 500 Hz), `Primus` (respirateur),
`BIS` (profondeur d'anesthésie), `Orchestra` (pousse-seringues AIVOC).

---

## 3. `labs` – biologie (API `/labs`, 1 ligne par résultat)

| Colonne | Description |
|---|---|
| `caseid` | Identifiant de la chirurgie |
| `dt` | Heure du prélèvement, en s relatives à `casestart` (de −90 à +90 jours environ) |
| `name` | Nom de l'examen |
| `result` | Valeur |

Examens disponibles : `alb`, `alt`, `ammo`, `aptt`, `ast`, `be`, `bun`, `ccr`, `cl`, `cr`, `crp`, `esr`, `fib`,
`gfr`, `gluc`, `hb`, `hco3`, `hct`, `ica`, `k`, `lac`, `na`, `p`, `pco2`, `ph`, `plt`, `po2`, `pt%`, `ptinr`,
`ptsec`, `sao2`, `tbil`, `tprot`, `wbc`.

⚠️ **Fuite de données** : un résultat n'est utilisable à l'instant *t* que si `dt < t`.
Non utilisé pour l'instant.

---

## 4. `data/cohort.csv` – cohorte retenue

Produit par `python -m src.data.cohort`. Mêmes 74 colonnes que `cases`, filtrées à 3 558 chirurgies
(critères dans le diagramme de flux ci-dessus).

---

## 5. `data/numerics/{caseid}.parquet` – constantes à 1 Hz *(à venir : `download.py`)*

1 ligne par seconde, ~160 Ko par cas.

| Piste | Description | Unité |
|---|---|---|
| `Solar8000/ART_MBP` | PAM invasive (**cible**) | mmHg |
| `Solar8000/ART_SBP` | PA systolique invasive | mmHg |
| `Solar8000/ART_DBP` | PA diastolique invasive | mmHg |
| `Solar8000/NIBP_MBP` | PAM non invasive (brassard) | mmHg |
| `Solar8000/HR` | Fréquence cardiaque | bpm |
| `Solar8000/PLETH_SPO2` | SpO2 | % |
| `Solar8000/ETCO2` | CO2 expiré | mmHg |
| `Solar8000/BT` | Température | °C |
| `BIS/BIS` | Index bispectral | 0–100 |
| `Primus/MAC` | Concentration alvéolaire minimale d'halogéné | – |
| `Primus/PEEP_MBAR` | PEEP | mbar |
| `Primus/TV` | Volume courant | mL |
| `Orchestra/PPF20_CE` | Propofol, concentration au site effet (AIVOC) | µg/mL |
| `Orchestra/RFTN20_CE` | Rémifentanil, concentration au site effet (AIVOC) | ng/mL |
| `Orchestra/PHEN_RATE` | Phényléphrine en perfusion, débit | mL/h |
| `Orchestra/NEPI_RATE` | Noradrénaline en perfusion, débit | mL/h |

Nettoyage prévu (`load_numerics()`) :
- Le Solar8000 mesure toutes les ~2 s → `ffill(limit=4)` (sinon 50 % de NaN à 1 Hz).
- PAM hors [20, 200] mmHg → NaN (capteur non branché ou en cours de zéro, rinçage, prélèvement).
  Exemple : cas 1, PAM à −8 / −9 mmHg en début d'enregistrement.

## 6. `data/waveforms/{caseid}.parquet` – ondes à 100 Hz *(à venir, option `--waveforms`)*

~10 Mo par cas, ~35 Go au total. Enregistrées à 500 Hz par `SNUADC`, rééchantillonnées à 100 Hz.

| Piste | Description | Unité |
|---|---|---|
| `SNUADC/ART` | Courbe de pression artérielle invasive | mmHg |
| `SNUADC/ECG_II` | ECG, dérivation II | mV |
| `SNUADC/PLETH` | Courbe de pléthysmographie | – |

---

## Limites connues des données

- Certains cas listent la piste ART mais elle est vide → filtre qualité à ajouter (PAM valide ≥ 70 % de la durée).
- La ligne artérielle est souvent posée après l'induction → la phase d'induction est mal couverte.
- Bolus de vasopresseurs (éphédrine, phényléphrine) disponibles seulement en totaux, sans horodatage.
- Vasopresseurs en perfusion rares (< 5 % des cas).
