# SPEC — Corrections du projet PFE Fintech

> **À coller dans Claude Code.** Ce document est une spécification exécutable : chaque tâche indique le
> fichier, l'ancre de recherche exacte, le code avant/après et le critère d'acceptation.

---

# 0. Mission

Tu interviens sur un projet de mémoire de fin d'études en finance actuarielle. Le projet prédit le signe
du gap d'ouverture d'actions américaines à partir du sentiment exprimé sur StockTwits pendant la nuit.

Un audit a identifié **un défaut majeur et dix défauts secondaires**. Ta mission est d'appliquer les
37 corrections décrites ci-dessous, dans l'ordre, en modifiant les notebooks Jupyter existants et en
créant un nouveau notebook.

## 0.1 — Le défaut majeur, en trois phrases

La variable `z_mu_pre` (sentiment de la fenêtre minuit → 9h30) porte **81 % du pouvoir prédictif** du
modèle. Or cette fenêtre recouvre la séance de pré-ouverture américaine, qui ouvre à **4h00** heure de
New York et pendant laquelle le prix d'ouverture se forme réellement. Les messages qui s'y écrivent ne
prédisent donc pas le gap : ils le décrivent.

Conséquence : l'AUC de 0,79 et le ratio de Sharpe de 11,5 sont des artefacts. Le test anti-fuite T1 du
notebook 05 le détecte déjà (`[ÉCHEC] z_mu_pre |rho| = 0.450`), mais l'export se poursuit malgré tout.

## 0.2 — Objectif des corrections

1. Rendre le blocage effectif quand un test anti-fuite échoue.
2. **Mesurer** empiriquement l'heure à laquelle le sentiment cesse d'anticiper (nouveau notebook 03bis).
3. Reconstruire le panel avec une fenêtre nocturne coupée avant l'ouverture du pré-marché.
4. Produire trois spécifications comparables (stricte / minuit / complète).
5. Corriger dix défauts secondaires (colinéarité, n effectif, bootstrap, purges, etc.).
6. Ajouter deux sections nouvelles à forte valeur (VaR du gap overnight, tableau 2×2 des backtests).

---

# 1. Environnement

```
RACINE = C:\Users\semy4\OneDrive\Bureau\Fintech_project

RACINE\src\notebooks\notebooks\
    03_Construction_Panel_1.ipynb
    04_EDA_Sentiment_Market.ipynb
    05_Features_et_Split.ipynb
    06_Modeling_M1_Gap.ipynb
    07_Modeling_M2_M3.ipynb
    08_Backtest.ipynb
    08_Backtest_Lag1.ipynb
    09_Backtest_Strategies_Lag1.ipynb
    09_Synthese_Memoire.ipynb

RACINE\data\processed\      <- CSV intermédiaires, config_modelisation.json
RACINE\docs\                <- CSV et PNG de résultats
```

Chaque notebook définit en première cellule :
`PROJET = r"C:\Users\semy4\OneDrive\Bureau\Fintech_project"`

Python 3, pandas, numpy, scikit-learn, statsmodels, scipy, matplotlib, yfinance.

---

# 2. Règles absolues

**R1 — Ne jamais deviner une ancre.** Chaque tâche donne une chaîne de recherche. Si tu ne la trouves pas
exactement, **arrête-toi et signale-le** au lieu d'appliquer la modification ailleurs.

**R2 — Ne jamais réordonner les cellules.** Les modifications sont locales : remplacement de bloc, ajout
d'une cellule immédiatement après une cellule identifiée, ou suppression d'une cellule identifiée.

**R3 — L'ordre des tâches est un ordre de dépendance.** T08 modifie un fichier que T11 lit. Applique les
tâches dans l'ordre numérique.

**R4 — Ne pas exécuter les notebooks sans instruction explicite.** L'exécution est demandée à la phase
finale (T37). Avant cela, tu ne fais qu'éditer.

**R5 — Ne pas modifier le bloc de test.** Le §9 du notebook 06 ne doit être réexécuté qu'une seule fois,
et seulement à T37.

**R6 — Conserver les sorties existantes** des cellules non modifiées. Pour une cellule modifiée, vider ses
outputs (`outputs: []`, `execution_count: null`).

**R7 — Encodage UTF-8 partout.** Les notebooks contiennent des accents et des caractères de dessin de
tableaux (`─`, `═`, `╔`). Lis et écris toujours en `encoding="utf-8"`.

**R8 — Ne rien supprimer d'irrécupérable.** T00 crée une archive ; ne la modifie jamais ensuite.

---

# 3. Méthode d'édition des notebooks

Un `.ipynb` est un JSON. Utilise le module `nbformat` si disponible, sinon `json` directement.

## 3.1 — Utilitaires à créer d'abord

Crée `RACINE\tools\nbtools.py` :

```python
"""Utilitaires d'édition de notebooks pour les corrections du PFE."""
import json, io, os, shutil, datetime as dt


def charger(chemin):
    with io.open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)


def sauver(nb, chemin):
    """Écrit le notebook après avoir fait une copie .bak horodatée."""
    if os.path.exists(chemin):
        bak = f"{chemin}.{dt.datetime.now():%Y%m%d_%H%M%S}.bak"
        shutil.copy2(chemin, bak)
    with io.open(chemin, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
        f.write("\n")


def src(cell):
    """Source d'une cellule sous forme de chaîne unique."""
    s = cell.get("source", [])
    return s if isinstance(s, str) else "".join(s)


def trouver(nb, ancre, type_cellule="code", occurrence=0):
    """Index de la cellule contenant `ancre`. Lève une exception si absente ou ambiguë."""
    hits = [i for i, c in enumerate(nb["cells"])
            if c["cell_type"] == type_cellule and ancre in src(c)]
    if not hits:
        raise LookupError(f"ANCRE INTROUVABLE : {ancre!r}")
    if len(hits) <= occurrence:
        raise LookupError(f"ANCRE trouvée {len(hits)}x, occurrence {occurrence} demandée : {ancre!r}")
    return hits[occurrence]


def remplacer_source(nb, idx, nouveau_code):
    """Remplace intégralement la source d'une cellule et vide ses sorties."""
    c = nb["cells"][idx]
    c["source"] = nouveau_code.splitlines(keepends=True)
    if c["cell_type"] == "code":
        c["outputs"] = []
        c["execution_count"] = None


def remplacer_bloc(nb, idx, ancien, nouveau):
    """Remplace un fragment de texte à l'intérieur d'une cellule. Exige une occurrence unique."""
    c = nb["cells"][idx]
    s = src(c)
    n = s.count(ancien)
    if n != 1:
        raise ValueError(f"Fragment trouvé {n} fois (1 attendu) dans la cellule {idx}")
    remplacer_source(nb, idx, s.replace(ancien, nouveau))


def inserer_apres(nb, idx, code, type_cellule="code"):
    """Insère une nouvelle cellule juste après l'index donné."""
    cellule = {"cell_type": type_cellule, "metadata": {},
               "source": code.splitlines(keepends=True)}
    if type_cellule == "code":
        cellule["outputs"] = []
        cellule["execution_count"] = None
    nb["cells"].insert(idx + 1, cellule)
    return idx + 1


def supprimer(nb, idx):
    del nb["cells"][idx]
```

## 3.2 — Modèle de script par tâche

Chaque tâche s'applique par un script du type :

```python
import sys; sys.path.insert(0, r"C:\Users\semy4\OneDrive\Bureau\Fintech_project\tools")
from nbtools import *

NB = r"C:\Users\semy4\OneDrive\Bureau\Fintech_project\src\notebooks\notebooks\05_Features_et_Split.ipynb"
nb = charger(NB)
i = trouver(nb, "ANCRE")
remplacer_bloc(nb, i, "ANCIEN", "NOUVEAU")
sauver(nb, NB)
print("OK")
```

Après chaque tâche, affiche `[T##] OK` ou `[T##] ÉCHEC : <raison>`.

---

# 4. Les tâches

Notation :
- **F** = fichier
- **A** = ancre de recherche (chaîne exacte présente dans la source de la cellule)
- **ACT** = action
- **AC** = critère d'acceptation

---

## T00 — Archiver l'état actuel

**ACT.** Crée `RACINE\archive_v1\` et copie dedans :
- tous les `.ipynb` de `src\notebooks\notebooks\`
- tous les `.csv` de `data\processed\`
- tous les `.csv` de `docs\`

**AC.** `archive_v1` contient 9 fichiers `.ipynb`. Le fichier `archive_v1\08_Backtest.ipynb` contient la
chaîne `11.509` dans ses sorties.

**Ne modifie plus jamais ce dossier.** Il contient le résultat non corrigé (Sharpe 11,5), qui deviendra
une annexe pédagogique du mémoire.

---

## T01 — Bloquer l'export quand un test anti-fuite échoue

**F.** `05_Features_et_Split.ipynb`
**A.** `AUCUNE FUITE DÉTECTÉE`

**ACT.** Dans cette cellule, remplace le bloc final :

```python
print("\n" + "=" * 70)
print("AUCUNE FUITE DÉTECTÉE — on peut modéliser." if not echecs
      else "ÉCHECS :\n  - " + "\n  - ".join(echecs))
print("=" * 70)
```

par :

```python
print("\n" + "=" * 70)
if echecs:
    print("ÉCHECS :\n  - " + "\n  - ".join(echecs))
    print("=" * 70)
    raise RuntimeError(
        "Tests anti-fuite en échec — export bloqué.\n"
        "Corriger la liste de variables avant de poursuivre :\n  - "
        + "\n  - ".join(echecs)
        + "\n\nUne variable qui échoue à T1 corrèle trop fortement avec la cible"
          " du même jour : elle contient l'information qu'on prétend prédire."
    )
print("AUCUNE FUITE DÉTECTÉE — on peut modéliser.")
print("=" * 70)
```

**AC.** La cellule contient `raise RuntimeError` et ne contient plus l'expression ternaire
`if not echecs\n      else`.

**NOTE.** À ce stade, exécuter le notebook 05 lèvera une exception. C'est voulu. Elle disparaîtra à T13.

---

## T02 — Retirer `ret_cc_lag1` à la source

**F.** `05_Features_et_Split.ipynb`
**A.** `CONTROLES = ["ret_cc_lag1"`

**ACT.** Juste après la ligne de définition de `CONTROLES`, insère dans la **même cellule** :

```python

# --------------------------------------------------------------------------
# RETRAIT D'UNE REDONDANCE EXACTE
# ret_cc = gap composé avec ret_oc, donc ret_cc ≈ gap + ret_oc à 1e-4 près.
# Les trois versions décalées dans le même modèle créent une quasi-dépendance
# linéaire : VIF(ret_cc_lag1) = 1516, soit R² = 99,93 % avec les autres.
# On retire ICI, à la source, pour que config_modelisation.json soit la
# seule vérité et que les notebooks 06 à 09 utilisent tous la même liste.
# --------------------------------------------------------------------------
CONTROLES = [c_ for c_ in CONTROLES if c_ != "ret_cc_lag1"]
print(f"CONTROLES après retrait de la redondance : {len(CONTROLES)} variables")
print("  ", CONTROLES)
```

**AC.** La cellule contient `c_ != "ret_cc_lag1"`.

---

## T03 — Supprimer le retrait local dans le notebook 06

**F.** `06_Modeling_M1_Gap.ipynb`
**A.** `Contrôle des features :`

**ACT.** Supprime **la cellule entière**. Le retrait est désormais fait par T02.

**AC.** La chaîne `ret_cc_lag1 in FEATURES` n'apparaît plus dans le notebook 06.

---

## T04 — Nommer les deux purges séparément

**F.** `05_Features_et_Split.ipynb`
**A.** `def assigner_bloc(d):`

**ACT.** Remplace la fonction et le tableau récapitulatif qui suit :

```python
def assigner_bloc(d):
    """Affecte chaque date à un bloc. Les deux embargos sont nommés séparément
    pour que le tableau récapitulatif reste lisible : sous une étiquette unique,
    l'agrégation affichait un intervalle de cinq mois pour cinq jours réels."""
    if d <= FIN_TRAIN:                                    return "train"
    if d <= FIN_TRAIN + pd.Timedelta(days=PURGE_JOURS):   return "purge_1"
    if d <= FIN_VALID:                                    return "valid"
    if d <= FIN_VALID + pd.Timedelta(days=PURGE_JOURS):   return "purge_2"
    return "test"

df["bloc"] = df["Date"].apply(assigner_bloc)

resume = df.groupby("bloc").agg(
    n_lignes=("Date", "size"), n_jours=("Date", "nunique"),
    debut=("Date", "min"), fin=("Date", "max"), pct_gap_pos=("y_gap", "mean"),
).reindex(["train", "purge_1", "valid", "purge_2", "test"])
resume["pct_gap_pos"] = (resume["pct_gap_pos"] * 100).round(1)
print(resume.to_string())
```

**ACT COMPLÉMENTAIRE.** Dans **tous** les notebooks 06, 07, 08, 08bis, 09str, 09syn, remplace chaque
occurrence de :

| ancien | nouveau |
|---|---|
| `["train", "valid"]` (dans un `.isin`) | `["train", "purge_1", "valid"]` si le contexte est un entraînement final ; **sinon laisser** |
| `== "purge"` | `.isin(["purge_1", "purge_2"])` |
| `"purge"` dans un `reindex([...])` | `"purge_1", "purge_2"` |

**AC.** `grep -c '"purge"' *.ipynb` renvoie 0 pour les six notebooks (hors chaînes `purge_1`/`purge_2`).

---

## T05 — Supprimer le code mort du notebook 05

**F.** `05_Features_et_Split.ipynb`
**A.** `FEATURES_SENT = [c_ for c_ in df.columns`

**ACT.** Remplace les deux affectations successives de `FEATURES_SENT` (la première est écrasée par la
seconde et contient un piège de priorité `and`/`or`) par :

```python
FEATURES_SENT = sorted([c_ for c_ in df.columns if c_.startswith(("z_", "rk_"))])
FEATURES = FEATURES_SENT + CONTROLES
FEATURES = [c_ for c_ in FEATURES if df[c_].notna().sum() > 500]

ecartees = [c_ for c_ in FEATURES_SENT + CONTROLES if c_ not in FEATURES]
if ecartees:
    print(f"ATTENTION — {len(ecartees)} variables écartées (< 500 valeurs) : {ecartees}")
```

**AC.** La chaîne `and "night" in c_ or` n'apparaît plus dans le fichier.

---

## T06 — Signaler les features manquantes dans les notebooks aval

**F.** `06`, `07`, `08`, `08_Backtest_Lag1`, `09_Backtest_Strategies_Lag1`, `09_Synthese_Memoire`
**A.** `CFG["features"] if c in df.columns` (ou `cfg["features"]` pour le 09 stratégies)

**ACT.** Après la ligne qui construit `FEATURES` (ou `features`), insère dans la même cellule :

```python
_absentes = [c for c in CFG["features"] if c not in df.columns]
if _absentes:
    raise KeyError(f"{len(_absentes)} features déclarées dans config_modelisation.json "
                   f"sont absentes du CSV : {_absentes}\nRéexécuter le notebook 05.")
```

Adapte `CFG` → `cfg` pour `09_Backtest_Strategies_Lag1.ipynb`.

**AC.** Les six notebooks contiennent `_absentes`.

---

## T07 — Exporter les messages horodatés depuis le notebook 03

**F.** `03_Construction_Panel_1.ipynb`
**A.** `CONTRÔLE 3 — night_full = overnight + pre`

**ACT.** Insère une **nouvelle cellule de code** juste après celle contenant l'ancre :

```python
# --------------------------------------------------------------------------
# EXPORT DES MESSAGES HORODATÉS
# Le notebook 03bis a besoin du détail message par message pour construire la
# courbe rho(heure de coupure). Le format parquet se relit en quelques secondes
# contre plusieurs minutes pour le CSV d'origine.
# --------------------------------------------------------------------------
cols_export = [c for c in ["Ticker", "ts_ny", "score", "fen_nuit"] if c in m.columns]
m[cols_export].to_parquet(
    os.path.join(DATA, "MESSAGES_HORODATES.parquet"), index=False)
print(f"Messages horodatés exportés : {len(m):,} lignes, colonnes {cols_export}")

# Le calendrier de bourse est également nécessaire au 03bis
pd.DataFrame({"Date": CALENDRIER}).to_parquet(
    os.path.join(DATA, "CALENDRIER_BOURSE.parquet"), index=False)
print(f"Calendrier exporté : {len(CALENDRIER)} jours de bourse")
```

**PRÉCAUTION.** Si `pyarrow` n'est pas installé, utilise `.to_pickle()` et adapte T08 en conséquence.
Vérifie avec `python -c "import pyarrow"`.

**AC.** La cellule existe et contient `MESSAGES_HORODATES`.

---

## T08 — Créer le notebook 03bis (découpage horaire)

**F.** Nouveau fichier `src\notebooks\notebooks\03bis_Decoupage_Horaire.ipynb`

**ACT.** Crée un notebook contenant les cellules suivantes, dans l'ordre.

### Cellule 1 — markdown

```markdown
# 03bis — Où le sentiment cesse d'anticiper et commence à décrire

**La question.** À quelle heure de la nuit le sentiment cesse-t-il de prédire le gap d'ouverture pour se
mettre à le décrire ?

**L'hypothèse.** La séance de pré-ouverture américaine ouvre à **4h00** heure de New York. Avant cette
heure, il ne se négocie quasiment rien (l'*after-hours* s'arrête à 20h00). Après, les prix bougent
réellement et le prix d'ouverture de 9h30 commence à se former.

**Le test.** On calcule la corrélation entre le sentiment cumulé depuis 16h00 et le gap d'ouverture, pour
une série d'heures de coupure. Si l'hypothèse est vraie, la courbe est plate jusqu'à 4h00 puis décolle.

**L'enjeu.** Ce notebook détermine la coupure retenue pour l'ensemble du mémoire. Ce choix devient
**mesuré** au lieu d'être conventionnel.
```

### Cellule 2 — code : chargement

```python
PROJET = r"C:\Users\semy4\OneDrive\Bureau\Fintech_project"

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

DATA = os.path.join(PROJET, "data", "processed")
DOCS = os.path.join(PROJET, "docs")
os.makedirs(DOCS, exist_ok=True)
pd.set_option("display.width", 170); pd.set_option("display.max_columns", 40)
plt.style.use("seaborn-v0_8-whitegrid"); plt.rcParams["figure.figsize"] = (13, 6)

m = pd.read_parquet(os.path.join(DATA, "MESSAGES_HORODATES.parquet"))
m["ts_ny"] = pd.to_datetime(m["ts_ny"])
CALENDRIER = pd.read_parquet(os.path.join(DATA, "CALENDRIER_BOURSE.parquet"))["Date"].values
CALENDRIER = np.sort(CALENDRIER.astype("datetime64[ns]"))

PANEL = os.path.join(DATA, "PANEL_SENTIMENT_WINDOWS_2020_2022_v2.csv")
prix = pd.read_csv(PANEL, usecols=["Date", "Ticker", "gap", "ret_oc", "ret_cc"])
prix["Date"] = pd.to_datetime(prix["Date"])

print(f"{len(m):,} messages | {len(CALENDRIER)} jours de bourse | {len(prix):,} lignes de panel")
```

### Cellule 3 — markdown

```markdown
## 1 — Rattacher chaque message à sa nuit cible

Un message appartient à la nuit qui précède le **prochain jour de bourse dont l'ouverture suit le
message**. Un message du vendredi 18h00 appartient donc à la nuit du lundi : c'est ce lundi-là que son
information sera incorporée au prix d'ouverture.
```

### Cellule 4 — code : affectation

```python
ts = m["ts_ny"].values.astype("datetime64[ns]")

OUVERTURES = CALENDRIER + np.timedelta64(9 * 60 + 30, "m")   # 9h30
CLOTURES   = CALENDRIER + np.timedelta64(16 * 60, "m")       # 16h00

# Premier jour de bourse dont l'ouverture est STRICTEMENT après le message
idx = np.searchsorted(OUVERTURES, ts, side="right")
valide = idx < len(CALENDRIER)
m = m.loc[valide].copy()
idx = idx[valide]

m["date_cible"]   = CALENDRIER[idx]
m["cloture_prec"] = np.where(idx > 0, CLOTURES[np.maximum(idx - 1, 0)],
                             np.datetime64("NaT"))

# On ne garde que les messages NOCTURNES
m = m[m["ts_ny"] > m["cloture_prec"]].copy()

# Heures écoulées depuis MINUIT du jour cible (négatif = veille au soir / week-end)
m["h_rel"] = (m["ts_ny"] - m["date_cible"]).dt.total_seconds() / 3600.0

print(f"Messages nocturnes retenus : {len(m):,}")
print(f"Plage de h_rel : {m['h_rel'].min():.1f} h  ->  {m['h_rel'].max():.1f} h\n")

BORNES = [-200, -8, -4, -2, 0, 2, 4, 6, 8, 9.5]
NOMS   = ["week-end / avant 16h", "16h-20h", "20h-22h", "22h-minuit", "minuit-2h",
          "2h-4h", "4h-6h", "6h-8h", "8h-9h30"]
tr = pd.cut(m["h_rel"], bins=BORNES, labels=NOMS)
rep = tr.value_counts().sort_index().to_frame("messages")
rep["part"] = (rep["messages"] / rep["messages"].sum() * 100).round(1)
print("RÉPARTITION PAR TRANCHE HORAIRE")
print(rep.to_string())
print("""
VÉRIFICATION : le total doit être proche de 1 715 650, le chiffre imprimé par
le notebook 03 pour la fenêtre night_full. Un écart important signale une
erreur d'affectation.

À OBSERVER : un creux entre 2h et 4h suivi d'une REMONTÉE après 4h00 indique
que l'activité de la foule suit l'ouverture du pré-marché.
""")
```

### Cellule 5 — markdown

```markdown
## 2 — La courbe des coupures

Pour chaque heure de coupure `t`, on ne garde que les messages postés avant `t`, on agrège par
(titre, jour), et on mesure la corrélation avec le gap.

La corrélation **intra-titre** (moyenne de chaque titre retirée) est la version défendable : elle élimine
le biais de niveau entre communautés.

La corrélation avec la **séance** sert de contrôle : elle doit rester plate et nulle à toutes les heures.
```

### Cellule 6 — code : la courbe

```python
COUPURES = [-6, -4, -2, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9.0, 9.5]
ETIQ = {-6: "18h00", -4: "20h00", -2: "22h00", 0: "minuit", 1: "01h00", 2: "02h00",
        3: "03h00", 4: "04h00", 5: "05h00", 6: "06h00", 7: "07h00", 8: "08h00",
        9.0: "09h00", 9.5: "09h30"}

lignes = []
for t in COUPURES:
    sub = m[m["h_rel"] <= t]
    if len(sub) < 1000:
        continue
    agg = (sub.groupby(["Ticker", "date_cible"])["score"]
              .agg(mu="mean", n="size").reset_index()
              .rename(columns={"date_cible": "Date"}))
    agg["Date"] = pd.to_datetime(agg["Date"])
    j = prix.merge(agg, on=["Ticker", "Date"], how="inner").dropna(subset=["mu", "gap"])

    for c_ in ["mu", "gap", "ret_oc"]:
        j[c_ + "_c"] = j[c_] - j.groupby("Ticker")[c_].transform("mean")

    lignes.append(dict(
        coupure_h=t, heure=ETIQ[t],
        n_messages=len(sub), n_lignes=len(j),
        msg_par_nuit=round(agg["n"].mean(), 1),
        rho_gap_brut=round(j["mu"].corr(j["gap"]), 4),
        rho_gap_intra=round(j["mu_c"].corr(j["gap_c"]), 4),
        rho_seance_intra=round(j["mu_c"].corr(j["ret_oc_c"]), 4),
    ))

C = pd.DataFrame(lignes)
C["gain_rho"] = C["rho_gap_intra"].diff().round(4)
print(C.to_string(index=False))
C.to_csv(os.path.join(DOCS, "03bis_courbe_coupures.csv"), index=False)
print("""
LES TROIS CHOSES À REGARDER
  1. gain_rho : l'apport de chaque tranche. Doit être petit et décroissant
     entre 22h et 4h, puis REMONTER après 4h00 -> c'est la bascule.
  2. rho_seance_intra : doit rester plat et proche de zéro PARTOUT.
     C'est le contrôle : la séance n'est prévisible à aucune heure.
  3. La valeur à 04h00 : c'est le nouveau chiffre de référence du mémoire.
""")
```

### Cellule 7 — code : la figure

```python
fig, axes = plt.subplots(1, 2, figsize=(15, 5.8))

ax = axes[0]
ax.plot(C["coupure_h"], C["rho_gap_intra"], "o-", color="#2f6f9f", lw=2.4,
        markersize=7, label="corrélation avec le GAP")
ax.plot(C["coupure_h"], C["rho_seance_intra"], "s--", color="#b8b8b8", lw=1.8,
        markersize=5, label="corrélation avec la SÉANCE (contrôle)")
ax.axhline(0, color="black", lw=0.8)
ax.axvspan(4, 9.5, color="crimson", alpha=0.11)
ax.axvline(4, color="crimson", ls="--", lw=2)
y1 = ax.get_ylim()[1]
ax.text(6.7, y1 * 0.55, "PRÉ-MARCHÉ\nOUVERT\n(4h00 - 9h30)", ha="center",
        fontsize=10.5, color="#8a1f1f", fontweight="bold")
ax.text(-1.0, y1 * 0.16, "aucun marché ouvert", ha="center", fontsize=10,
        color="#3a5f7f", style="italic")
ax.set_xticks(C["coupure_h"]); ax.set_xticklabels(C["heure"], rotation=45, ha="right", fontsize=9)
ax.set_xlabel("Heure de coupure de la fenêtre nocturne (début fixe : 16h00)")
ax.set_ylabel("Corrélation intra-titre avec le gap")
ax.set_title("Où le sentiment cesse d'anticiper et commence à décrire",
             fontweight="bold", fontsize=12.5)
ax.legend(loc="upper left", fontsize=9.5)

ax = axes[1]
c2 = C.dropna(subset=["gain_rho"])
cols = ["#c05c4a" if h > 4 else "#2f6f9f" for h in c2["coupure_h"]]
ax.bar(range(len(c2)), c2["gain_rho"], color=cols, edgecolor="white", width=0.72)
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(range(len(c2))); ax.set_xticklabels(c2["heure"], rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Gain de corrélation apporté par la tranche")
ax.set_title("Apport marginal de chaque tranche horaire\n"
             "bleu = marché fermé, rouge = pré-marché ouvert",
             fontweight="bold", fontsize=12.5)

plt.tight_layout()
plt.savefig(os.path.join(DOCS, "03bis_fig_courbe_coupures.png"), dpi=180, bbox_inches="tight")
plt.show()
```

### Cellule 8 — code : quantification

```python
def _v(t, col="rho_gap_intra"):
    return C.loc[C["coupure_h"] == t, col].iloc[0]

r0, r4, r95 = _v(0), _v(4), _v(9.5)
n4, n95 = _v(4, "n_messages"), _v(9.5, "n_messages")

print("=" * 78)
print("DÉCOMPOSITION DU SIGNAL PAR PHASE DE MARCHÉ")
print("=" * 78)
print(f"""
  16h00 -> minuit   (marché fermé)      rho = {r0:+.4f}
  16h00 -> 04h00    (marché fermé)      rho = {r4:+.4f}
  16h00 -> 09h30    (pré-marché inclus) rho = {r95:+.4f}

  PART ANTICIPATRICE (jusqu'à 4h00) ... {r4:+.4f}   soit {r4/r95*100:5.1f} % du total
  PART CONTEMPORAINE (4h00 -> 9h30) ... {r95-r4:+.4f}   soit {(r95-r4)/r95*100:5.1f} % du total

  Messages avant 4h00 : {n4:,.0f} sur {n95:,.0f}  ({n4/n95*100:.1f} %)

  LECTURE : la tranche 4h00-9h30 représente {100-n4/n95*100:.0f} % des messages mais apporte
  {(r95-r4)/r95*100:.0f} % de la corrélation. Cette disproportion est la signature d'une
  information CONTEMPORAINE et non ANTICIPATRICE.
""")
print("=" * 78)

with open(os.path.join(DOCS, "03bis_synthese.txt"), "w", encoding="utf-8") as f:
    f.write(f"rho_minuit={r0:.4f}\nrho_4h={r4:.4f}\nrho_9h30={r95:.4f}\n"
            f"part_anticipatrice={r4/r95:.4f}\npart_contemporaine={(r95-r4)/r95:.4f}\n"
            f"messages_avant_4h={n4:.0f}\nmessages_total={n95:.0f}\n")
```

### Cellule 9 — code : robustesse par titre

```python
lignes = []
for tk in sorted(m["Ticker"].unique()):
    for t in [0, 4, 9.5]:
        sub = m[(m["h_rel"] <= t) & (m["Ticker"] == tk)]
        agg = (sub.groupby("date_cible")["score"].mean()
                  .rename("mu").reset_index().rename(columns={"date_cible": "Date"}))
        agg["Date"] = pd.to_datetime(agg["Date"])
        j = prix[prix["Ticker"] == tk].merge(agg, on="Date").dropna(subset=["mu", "gap"])
        lignes.append(dict(Ticker=tk, coupure=ETIQ[t], n=len(j),
                           rho=round(j["mu"].corr(j["gap"]), 4)))

R = pd.DataFrame(lignes).pivot(index="Ticker", columns="coupure", values="rho")
R = R[["minuit", "04h00", "09h30"]]
R["gain_4h_930"] = (R["09h30"] - R["04h00"]).round(4)
print("CORRÉLATION AVEC LE GAP, PAR TITRE ET PAR COUPURE")
print(R.round(4).to_string())
R.to_csv(os.path.join(DOCS, "03bis_coupures_par_ticker.csv"))
print(f"""
gain_4h_930 positif sur {int((R['gain_4h_930'] > 0).sum())} titres sur {len(R)}.
Si c'est 5 sur 5, la contamination par le pré-marché est un phénomène général
et non l'artefact d'une action particulière.
""")
```

**AC.** Le fichier existe, contient 9 cellules, et `json.load` le parse sans erreur.

---

## T09 — Ajouter les fenêtres `night_safe` et `premkt` au notebook 03

**F.** `03_Construction_Panel_1.ipynb`
**A.** `Affectation B — nocturne`

**ACT 1.** Dans la cellule d'affectation, après le code existant, ajoute :

```python

# --------------------------------------------------------------------------
# NOUVELLES FENÊTRES : coupure à l'ouverture du pré-marché américain.
# Justification empirique : notebook 03bis, courbe rho(heure de coupure).
# --------------------------------------------------------------------------
HEURE_COUPURE = 4.0

_ouv = CALENDRIER + np.timedelta64(9 * 60 + 30, "m")
_idx = np.searchsorted(_ouv, m["ts_ny"].values.astype("datetime64[ns]"), side="right")
_ok = _idx < len(CALENDRIER)
m["_date_cible"] = pd.NaT
m.loc[_ok, "_date_cible"] = CALENDRIER[_idx[_ok]]
m["h_rel"] = (m["ts_ny"] - m["_date_cible"]).dt.total_seconds() / 3600.0

msk_nuit = m["fen_nuit"].notna()
m["fen_nuit2"] = np.nan
m.loc[msk_nuit & (m["h_rel"] <= HEURE_COUPURE), "fen_nuit2"] = "night_safe"
m.loc[msk_nuit & (m["h_rel"] >  HEURE_COUPURE), "fen_nuit2"] = "premkt"

print("\nNOUVELLES FENÊTRES (coupure à {}h00) :".format(int(HEURE_COUPURE)))
print(m["fen_nuit2"].value_counts(dropna=False).to_string())
assert m["fen_nuit2"].notna().sum() == msk_nuit.sum(), \
    "Des messages nocturnes ont été perdus dans le nouveau découpage"
print(f"Contrôle OK : night_safe + premkt = night_full = {msk_nuit.sum():,}")
```

**ACT 2.** Localise la cellule d'agrégation par fenêtre (ancre : `night_full   :` dans une chaîne de
`print`, ou la liste des fenêtres traitées). Ajoute `night_safe` et `premkt` à la liste des fenêtres, en
utilisant `fen_nuit2` comme colonne d'affectation pour ces deux-là.

Si l'agrégation est écrite avec une liste explicite, elle doit devenir :

```python
FENETRES = [("overnight",  "fen_nuit"),
            ("pre",        "fen_nuit"),
            ("night_full", None),          # union, recalculée sur tous les messages nocturnes
            ("night_safe", "fen_nuit2"),   # NOUVEAU
            ("premkt",     "fen_nuit2"),   # NOUVEAU
            ("open30",     "fen_jour"),
            ("mkt",        "fen_jour"),
            ("post",       "fen_jour")]
```

**IMPORTANT.** Les statistiques `sd`, `p10`, `p90` doivent être recalculées **depuis les messages** pour
chaque fenêtre (elles ne s'agrègent pas). Le notebook le fait déjà pour `night_full` ; applique la même
méthode.

**AC.** Le panel exporté contient les colonnes `n_night_safe`, `mu_night_safe`, `sd_night_safe`,
`pos_night_safe`, `neg_night_safe`, `nlog_night_safe`, `nabn_night_safe`, `disp_night_safe`, et les
équivalents `_premkt`.

---

## T10 — Variables dérivées sur la fenêtre propre

**F.** `03_Construction_Panel_1.ipynb`
**A.** `mu_night_ma3`

**ACT.** Dans la cellule qui calcule `dmu_night`, `mu_night_ma3`, `mu_night_z20`, ajoute leurs équivalents
sur `night_safe` :

```python

# --- Versions SAFE : aucune ne dépend de la fenêtre premkt ---
_g = df.sort_values(["Ticker", "Date"]).groupby("Ticker")
df["dmu_safe"]    = df["mu_night_safe"] - _g["mu_night_safe"].shift(1)
df["mu_safe_ma3"] = _g["mu_night_safe"].transform(
                        lambda s: s.rolling(3, min_periods=2).mean())
df["mu_safe_z20"] = _g["mu_night_safe"].transform(
    lambda s: (s - s.rolling(20, min_periods=10).mean().shift(1))
              / s.rolling(20, min_periods=10).std().shift(1))
print("\nVariables dérivées SAFE :")
print(df[["dmu_safe", "mu_safe_ma3", "mu_safe_z20"]].describe().T.round(4).to_string())
```

**AC.** Les trois colonnes existent dans le panel exporté.

---

## T11 — Huitième contrôle qualité

**F.** `03_Construction_Panel_1.ipynb`
**A.** `TOUS LES CONTRÔLES PASSENT`

**ACT.** Avant le message final, ajoute un contrôle :

```python
# CONTRÔLE 8 — night_full = night_safe union premkt
_ns = df["n_night_safe"].fillna(0)
_pm = df["n_premkt"].fillna(0)
_nf = df["n_night_full"].fillna(0)
_err = float((_ns + _pm - _nf).abs().max())
_ok = _err < 1e-9
controles.append(_ok)
print(f"  [{'OK   ' if _ok else 'ÉCHEC'}] n_night_full = n_night_safe + n_premkt "
      f"— erreur max {_err:.2e}")
```

Adapte le nom de la liste d'accumulation des contrôles à celui utilisé dans le notebook.

**AC.** La sortie affiche 8 contrôles.

---

## T12 — Mettre à jour la liste blanche du notebook 05

**F.** `05_Features_et_Split.ipynb`
**A.** `CONNUE_A = {`

**ACT.** Remplace la cellule entière par :

```python
# --------------------------------------------------------------------------
# LÉGALITÉ TEMPORELLE : heure (depuis minuit du jour J) à laquelle chaque
# famille de variables devient connue.
# --------------------------------------------------------------------------
CONNUE_A = {
    "_overnight":   0.0,    # 16h(J-1) -> minuit
    "_night_safe":  4.0,    # 16h(J-1) -> 4h00              <-- NOUVEAU
    "_pre":         9.5,    # minuit   -> 9h30
    "_night_full":  9.5,    # union overnight + pre
    "_premkt":      9.5,    # 4h00     -> 9h30 (PRÉ-MARCHÉ) <-- NOUVEAU
    "_open30":     10.0,
    "_mkt":        16.0,
    "_post":       24.0,
}
DEBUT_CIBLE = {"gap": 9.5, "ret_oc": 9.5, "ret_cc": 9.5}

INTERDITES_TOUJOURS = ["Open", "High", "Low", "Close", "Adj Close", "Volume",
                       "gap", "ret_oc", "ret_cc", "y_gap", "y_oc", "y_cc",
                       "amplitude", "abs_gap", "regime", "gap_mkt", "gap_excess"]

# --------------------------------------------------------------------------
# LÉGALITÉ ÉCONOMIQUE : au-delà de la légalité temporelle, on exige qu'AUCUN
# marché ne soit ouvert pendant la fenêtre. Le pré-marché américain ouvre à
# 4h00 (heure de New York) : au-delà, le prix d'ouverture se forme déjà, et un
# message qui le commente le DÉCRIT au lieu de le PRÉDIRE.
# Mesuré au notebook 03bis : la corrélation avec le gap est plate jusqu'à 4h00
# puis décolle.
# --------------------------------------------------------------------------
OUVERTURE_PREMARCHE = 4.0
FENETRES_CONTAMINEES = ("_pre", "_night_full", "_premkt")

def est_legale(col, cible="gap", strict=True):
    """True si `col` peut servir à prédire `cible`.

    strict=True  : exige en outre qu'aucun marché ne soit ouvert pendant la
                   fenêtre. Spécification retenue pour le mémoire.
    strict=False : légalité temporelle seule. Spécification de comparaison,
                   reportée en annexe.
    """
    if col in INTERDITES_TOUJOURS or col in ("Date", "Ticker", "bloc"):
        return False
    for suf, h in CONNUE_A.items():
        if col.endswith(suf):
            if strict and suf in FENETRES_CONTAMINEES:
                return False
            return h <= DEBUT_CIBLE[cible]
    return None

legales_strict = [c_ for c_ in df.columns if est_legale(c_, "gap", True) is True]
legales_large  = [c_ for c_ in df.columns if est_legale(c_, "gap", False) is True]
a_traiter      = [c_ for c_ in df.columns if est_legale(c_, "gap", True) is None]

print(f"LÉGALES — spécification STRICTE ({len(legales_strict)}) :")
for x in legales_strict: print("   ", x)
print(f"\nLÉGALES — spécification LARGE (annexe) : {len(legales_large)}")
print(f"Écart : {len(legales_large) - len(legales_strict)} variables exclues par le critère économique")
print(f"\nÀ EXAMINER au cas par cas ({len(a_traiter)}) : {a_traiter}")
```

**AC.** La cellule contient `FENETRES_CONTAMINEES` et `OUVERTURE_PREMARCHE`.

---

## T13 — Mettre à jour la normalisation

**F.** `05_Features_et_Split.ipynb`
**A.** `A_NORMALISER = [c_ for c_ in [`

**ACT.** Remplace la liste et la boucle par :

```python
A_NORMALISER = [c_ for c_ in [
    # --- fenêtres PROPRES : aucun marché ouvert ---
    "mu_night_safe", "sd_night_safe", "nlog_night_safe", "nabn_night_safe",
    "pos_night_safe", "neg_night_safe", "dmu_safe", "mu_safe_ma3",
    "mu_overnight",  "sd_overnight",
    # --- fenêtres CONTAMINÉES : conservées pour la spécification C (annexe) ---
    "mu_premkt", "sd_premkt", "mu_pre", "sd_pre",
    "mu_night_full", "sd_night_full", "nlog_night_full", "nabn_night_full",
    "pos_night_full", "neg_night_full", "dmu_night", "mu_night_ma3",
] if c_ in df.columns]

print("Variables normalisées :")
for col in A_NORMALISER:
    df[f"z_{col}"] = df.groupby("Ticker")[col].transform(zscore_glissant)
    print(f"   z_{col}")

for col in ["mu_night_safe", "nabn_night_safe"]:
    if col in df.columns:
        df[f"rk_{col}"] = df.groupby("Ticker")[col].transform(rang_glissant)
        print(f"   rk_{col}  (rang percentile)")

print("\nCONTRÔLE — moyenne de mu_night_safe par ticker AVANT / APRÈS :")
print(pd.DataFrame({
    "avant": df.groupby("Ticker")["mu_night_safe"].mean(),
    "apres": df.groupby("Ticker")["z_mu_night_safe"].mean(),
}).round(4).to_string())
```

**AC.** La cellule contient `mu_night_safe` et `rk_mu_night_safe`.

---

## T14 — Définir les trois spécifications

**F.** `05_Features_et_Split.ipynb`
**A.** `FEATURES_SENT = sorted(` (issue de T05)

**ACT.** Remplace la définition simple de `FEATURES` par :

```python
# ==========================================================================
#  LES TROIS SPÉCIFICATIONS DU MÉMOIRE
#    A — STRICTE   : fenêtres fermées avant 4h00. Aucun marché ouvert.
#                    -> RÉSULTAT PRINCIPAL.
#    B — MINUIT    : coupure à minuit (la convention naïve).
#                    -> test de sensibilité au choix de coupure.
#    C — COMPLÈTE  : toute la nuit, pré-marché inclus.
#                    -> ANNEXE : ce qu'on obtient sans contrôle économique.
# ==========================================================================

def _norm(noms):
    """Versions normalisées existantes (z_ et rk_) des variables données."""
    out = []
    for n in noms:
        for p in ("z_", "rk_"):
            if p + n in df.columns:
                out.append(p + n)
    return sorted(set(out))

SENT_A = _norm(["mu_night_safe", "sd_night_safe", "nlog_night_safe", "nabn_night_safe",
                "mu_overnight", "sd_overnight", "dmu_safe", "mu_safe_ma3"])
SENT_B = _norm(["mu_overnight", "sd_overnight", "nlog_night_full", "nabn_night_full"])
SENT_C = _norm(["mu_night_full", "sd_night_full", "mu_pre", "sd_pre", "mu_premkt",
                "mu_overnight", "sd_overnight", "nlog_night_full", "nabn_night_full",
                "pos_night_full", "neg_night_full", "dmu_night", "mu_night_ma3"])

def _filtrer(l):
    return [c_ for c_ in l if c_ in df.columns and df[c_].notna().sum() > 500]

FEATURES_A = _filtrer(SENT_A) + CONTROLES
FEATURES_B = _filtrer(SENT_B) + CONTROLES
FEATURES_C = _filtrer(SENT_C) + CONTROLES

# La spécification par défaut de TOUS les notebooks aval est la STRICTE.
FEATURES_SENT = _filtrer(SENT_A)
FEATURES = FEATURES_A

# --- Garde-fou : aucune variable dérivée d'une fenêtre contaminée dans A ---
# Ce test attrape le défaut du "jeu conservateur" de la version précédente :
# z_dmu_night et z_mu_night_ma3 traversaient un filtre par sous-chaîne alors
# qu'ils dérivent tous deux de mu_night_full, donc de mu_pre.
MOTIFS_INTERDITS = ("premkt", "_pre", "night_full", "dmu_night", "night_ma3")
for f in FEATURES_A:
    assert not any(k in f for k in MOTIFS_INTERDITS), \
        f"Variable contaminée dans la spécification STRICTE : {f}"

print(f"A — STRICTE  : {len(FEATURES_A)} variables "
      f"({len(_filtrer(SENT_A))} sentiment + {len(CONTROLES)} contrôles)")
print(f"B — MINUIT   : {len(FEATURES_B)} variables")
print(f"C — COMPLÈTE : {len(FEATURES_C)} variables (annexe)")
print("\nSpécification A retenue par défaut :")
for f in FEATURES_A: print("   ", f)
```

**AC.** La cellule contient `MOTIFS_INTERDITS` et l'`assert`.

---

## T15 — Exporter les trois configurations

**F.** `05_Features_et_Split.ipynb`
**A.** `config = {`

**ACT.** Remplace le dictionnaire `config` et l'export :

```python
config = {
    "specification_retenue": "A_stricte",
    "heure_coupure": 4.0,
    "justification_coupure": "ouverture du pré-marché américain ; voir notebook 03bis",

    "features":            FEATURES_A,
    "features_sentiment":  [f for f in FEATURES_A if f.startswith(("z_", "rk_"))],
    "features_B_minuit":   FEATURES_B,
    "features_C_complete": FEATURES_C,
    "controles":           CONTROLES,

    "fin_train": str(FIN_TRAIN.date()),
    "fin_valid": str(FIN_VALID.date()),
    "purge_jours": PURGE_JOURS,
    "seuil_zone_morte_bp": SEUIL_BP,
    "fenetre_zscore": FENETRE_Z,
}
with open(os.path.join(DATA, "config_modelisation.json"), "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

BRUTES = [c_ for c_ in df.columns
          if c_.endswith(("_overnight", "_pre", "_night_full", "_night_safe", "_premkt"))
          and not c_.startswith(("z_", "rk_"))]

garder = (META + sorted(set(FEATURES_A + FEATURES_B + FEATURES_C))
          + BRUTES + [c_ for c_ in CIBLES if c_ in df.columns])
garder = [c_ for c_ in dict.fromkeys(garder) if c_ in df.columns]

out = df[garder].copy()
out.to_csv(os.path.join(DATA, "DATASET_MODELISATION_2020_2022.csv"), index=False)

print(f"Écrit : {out.shape[0]:,} lignes x {out.shape[1]} colonnes")
print(f"        A={len(FEATURES_A)} | B={len(FEATURES_B)} | C={len(FEATURES_C)}")
print("\nRépartition par bloc :")
print(out["bloc"].value_counts()
        .reindex(["train", "purge_1", "valid", "purge_2", "test"]).to_string())
```

**AC.** Le JSON contient les clés `features_B_minuit` et `features_C_complete`.

---

## T16 — Verrouiller le bloc de test dans le walk-forward

**F.** `06_Modeling_M1_Gap.ipynb`, `07_Modeling_M2_M3.ipynb`, `08_Backtest.ipynb`,
`08_Backtest_Lag1.ipynb`, `09_Backtest_Strategies_Lag1.ipynb`
**A.** `d_wf = df.dropna(subset=[CIBLE]).copy()` (notebook 06) ;
`d = df.dropna(subset=[cible]).copy()` ou `d = df.dropna(subset=["y_gap", "gap"]).copy()` (autres)

**ACT (notebook 06).** Remplace par :

```python
# --------------------------------------------------------------------------
# Le walk-forward NE DOIT PAS toucher le bloc de test, sinon l'évaluation
# finale du §9 n'est plus en aveugle. Dans la version précédente, le pli 4
# (2021-12-08 -> 2022-03-04) recouvrait le bloc test (2021-12-06 -> 2022-03-04)
# à deux jours près.
# --------------------------------------------------------------------------
d_wf = (df[df["bloc"].isin(["train", "purge_1", "valid"])]
          .dropna(subset=[CIBLE]).copy())

plis = plis_walk_forward(d_wf["Date"], n_plis=6, taille_test=60, min_train=200)

_dernier = pd.Timestamp(plis[-1][1][-1])
_premier = df.loc[df["bloc"] == "test", "Date"].min()
print(f"Walk-forward : {len(plis)} plis")
for i, (a, b) in enumerate(plis, 1):
    print(f"  Pli {i} : train {pd.Timestamp(a[0]).date()} -> {pd.Timestamp(a[-1]).date()} "
          f"({len(a):3d} j)  |  test {pd.Timestamp(b[0]).date()} -> "
          f"{pd.Timestamp(b[-1]).date()} ({len(b)} j)")
print(f"\nDernier jour du walk-forward : {_dernier.date()}")
print(f"Premier jour du bloc test    : {_premier.date()}")
assert _dernier < _premier, \
    "Le walk-forward empiète sur le bloc de test : le §9 ne serait plus en aveugle."
print("[OK] Le bloc de test est intact.")
```

**ACT (autres notebooks).** Applique la même restriction `bloc.isin(["train","purge_1","valid"])` et le
même `assert`, en adaptant les noms de variables.

**AC.** Les cinq notebooks contiennent `Le bloc de test est intact` ou l'`assert` correspondant.

**ATTENDU.** Le nombre de plis passe de 4 à 3.

---

## T17 — Comparer les trois spécifications

**F.** `06_Modeling_M1_Gap.ipynb`
**A.** `DÉCOMPOSITION DU POUVOIR PRÉDICTIF`

**ACT.** Insère une nouvelle cellule de code **après** celle contenant l'ancre :

```python
# ==========================================================================
#  TABLEAU CENTRAL DU CHAPITRE DE RÉSULTATS
# ==========================================================================
from sklearn.base import clone

SPECS = {
    "A — stricte (coupée 4h00)":  CFG["features"],
    "B — coupée minuit":          CFG["features_B_minuit"],
    "C — nuit complète (annexe)": CFG["features_C_complete"],
    "Contrôles de marché seuls":  CFG["controles"],
}

lignes = []
for nom, feats in SPECS.items():
    feats = [f for f in feats if f in d_wf.columns]
    if not feats:
        continue
    m_, s_, k_ = auc_walkforward(feats, proto=pipeline_logit(1.0))
    mod = clone(pipeline_logit(1.0)).fit(tr[feats], tr[CIBLE])
    r = evaluer(va[CIBLE], mod.predict_proba(va[feats])[:, 1], nom=nom)
    r.update(n_features=len(feats), AUC_wf=round(m_, 4),
             AUC_wf_std=round(s_, 4), plis=k_)
    lignes.append(r)

T = afficher(lignes)
print("=" * 108)
print("COMPARAISON DES TROIS SPÉCIFICATIONS")
print("=" * 108)
print(T[["modele", "n_features", "AUC", "AUC_wf", "AUC_wf_std", "plis",
         "MCC", "Brier", "gain_vs_naif"]].to_string(index=False))
T.to_csv(os.path.join(DOCS, "06_comparaison_specifications.csv"), index=False)

_a = T.loc[T["modele"].str.startswith("A"), "AUC_wf"].iloc[0]
_c = T.loc[T["modele"].str.startswith("C"), "AUC_wf"].iloc[0]
print(f"""
DÉCOMPOSITION DU POUVOIR PRÉDICTIF
  A — part ANTICIPATRICE (aucun marché ouvert) ..... {_a:.4f}
  C — mesure brute (pré-marché inclus) ............. {_c:.4f}
  Écart = part CONTEMPORAINE ....................... {_c - _a:+.4f}
          soit {(_c-_a)/max(_c-0.5, 1e-9)*100:.0f} % du signal apparent

Le chiffre du mémoire est {_a:.4f}. Le {_c:.4f} figure en annexe, accompagné de
son explication : il mesure une information disponible mais non actionnable.
""")
```

**AC.** Le fichier `docs\06_comparaison_specifications.csv` est produit à l'exécution.

---

## T18 — Nettoyer la colinéarité et rendre les coefficients interprétables

**F.** `06_Modeling_M1_Gap.ipynb`
**A.** `variance_inflation_factor`

**ACT.** À la fin de cette cellule, ajoute :

```python

SEUIL_VIF = 10.0
mauvais = vif[vif["VIF"] > SEUIL_VIF].sort_values("VIF", ascending=False)

if len(mauvais):
    print(f"\n{len(mauvais)} variables au-dessus de VIF={SEUIL_VIF} : "
          f"coefficients NON interprétables.")
    print(mauvais.round(2).to_string(index=False))
    print("""
  RÈGLE : on conserve mu (= pos - neg) et on écarte pos et neg ;
  on conserve la décomposition overnight/night_safe et on écarte l'union.
  Les PRÉDICTIONS changent à peine ; les COEFFICIENTS redeviennent lisibles.
""")
    restant = list(feats)
    while len(restant) > 4:
        X_ = pd.DataFrame(modele.named_steps["std"].transform(
                modele.named_steps["imp"].transform(tr[restant])), columns=restant)
        v_ = pd.Series([variance_inflation_factor(X_.values, i)
                        for i in range(len(restant))], index=restant)
        if v_.max() <= SEUIL_VIF:
            break
        pire = v_.idxmax()
        print(f"    retrait de {pire:26s} (VIF {v_.max():.1f})")
        restant.remove(pire)

    FEATURES_VIF = restant
    print(f"\n  Jeu non colinéaire : {len(FEATURES_VIF)} variables, VIF max = {v_.max():.2f}")

    m_ = clone(pipeline_logit(1.0)).fit(tr[FEATURES_VIF], tr[CIBLE])
    auc_ = roc_auc_score(va[CIBLE], m_.predict_proba(va[FEATURES_VIF])[:, 1])
    print(f"  AUC avec le jeu nettoyé : {auc_:.4f}")

    co = pd.DataFrame({"feature": FEATURES_VIF, "coef": m_.named_steps["clf"].coef_[0]})
    co["odds_ratio"] = np.exp(co["coef"])
    co = co.reindex(co["coef"].abs().sort_values(ascending=False).index)
    print("\n  COEFFICIENTS INTERPRÉTABLES :")
    print(co.round(4).to_string(index=False))
    co.to_csv(os.path.join(DOCS, "06_coefficients_interpretables.csv"), index=False)

    print("""
  VÉRIFICATION ATTENDUE : le coefficient de z_mu_overnight doit être POSITIF,
  cohérent avec sa corrélation de +0,216 avec le gap (notebook 04 §17).
  S'il reste négatif, il subsiste de la colinéarité.
""")
else:
    print(f"\n[OK] Tous les VIF sont sous {SEUIL_VIF} : coefficients interprétables.")
```

**AC.** La cellule contient `SEUIL_VIF` et `06_coefficients_interpretables.csv`.

---

## T19 — Bootstrap par blocs de jours

**F.** `06_Modeling_M1_Gap.ipynb`
**A.** `IC 95%` (dans le §9)

**ACT.** Remplace le bloc de bootstrap par :

```python
if meilleur_nom in proba_test:
    p = proba_test[meilleur_nom]
    y = te[CIBLE].values

    # --- version par LIGNES (trop étroite, conservée pour comparaison) ---
    rng = np.random.default_rng(0); a_lig = []
    for _ in range(2000):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) > 1:
            a_lig.append(roc_auc_score(y[i], p[i]))
    lo1, hi1 = np.percentile(a_lig, [2.5, 97.5])

    # --- version par BLOCS DE JOURS (correcte) ---
    jours = te["Date"].unique()
    idx_j = {d_: np.where(te["Date"].values == d_)[0] for d_ in jours}
    rng = np.random.default_rng(0); a_blk = []
    for _ in range(2000):
        tir = rng.choice(jours, size=len(jours), replace=True)
        idx = np.concatenate([idx_j[d_] for d_ in tir])
        if len(np.unique(y[idx])) > 1:
            a_blk.append(roc_auc_score(y[idx], p[idx]))
    lo2, hi2 = np.percentile(a_blk, [2.5, 97.5])

    print(f"\n{meilleur_nom} — AUC test = {roc_auc_score(y, p):.4f}")
    print(f"  IC 95 % par LIGNES         : [{lo1:.4f} ; {hi1:.4f}]  largeur {hi1-lo1:.4f}")
    print(f"  IC 95 % par BLOCS DE JOURS : [{lo2:.4f} ; {hi2:.4f}]  largeur {hi2-lo2:.4f}"
          f"   <-- À REPORTER")
    print(f"""
  Le second est {(hi2-lo2)/max(hi1-lo1,1e-9):.1f} fois plus large. C'est la version correcte : les
  cinq titres d'un même jour réagissent au même choc de marché et ne
  constituent donc pas cinq observations indépendantes. Le nombre
  d'observations effectivement indépendantes est de l'ordre de {len(jours)}, non {len(y)}.
""")
```

**AC.** La cellule contient `BLOCS DE JOURS`.

---

## T20 — Calibration évaluée hors échantillon

**F.** `06_Modeling_M1_Gap.ipynb`
**A.** `gb_cal = calibrer_modele_entraine(`

**ACT.** Remplace par :

```python
from sklearn.model_selection import train_test_split

# Découpage CHRONOLOGIQUE de la validation : shuffle=False impératif.
va_cal, va_ev = train_test_split(va, test_size=0.5, shuffle=False)
print(f"Calibration ajustée sur {len(va_cal)} lignes "
      f"({va_cal['Date'].min().date()} -> {va_cal['Date'].max().date()})")
print(f"Évaluée sur            {len(va_ev)} lignes "
      f"({va_ev['Date'].min().date()} -> {va_ev['Date'].max().date()})")

gb_cal = calibrer_modele_entraine(gb, va_cal[FEATURES], va_cal[CIBLE])

b_in_a  = brier_score_loss(va_cal[CIBLE], gb.predict_proba(va_cal[FEATURES])[:, 1])
b_in_p  = brier_score_loss(va_cal[CIBLE], gb_cal.predict_proba(va_cal[FEATURES])[:, 1])
b_out_a = brier_score_loss(va_ev[CIBLE],  gb.predict_proba(va_ev[FEATURES])[:, 1])
b_out_p = brier_score_loss(va_ev[CIBLE],  gb_cal.predict_proba(va_ev[FEATURES])[:, 1])

print(f"""
                        avant     après     gain
  DANS l'échantillon   {b_in_a:.4f}    {b_in_p:.4f}   {(b_in_a-b_in_p)/b_in_a*100:+5.1f} %
  HORS échantillon     {b_out_a:.4f}    {b_out_p:.4f}   {(b_out_a-b_out_p)/b_out_a*100:+5.1f} %  <-- À REPORTER

  Si le gain hors échantillon est nettement plus faible, la régression
  isotonique surajuste (elle peut créer autant de paliers que d'observations).
  Préférer alors method="sigmoid" (scaling de Platt), plus rigide mais plus
  stable sur petit échantillon.
""")

p_va = gb.predict_proba(va[FEATURES])[:, 1]
p_va_cal = gb_cal.predict_proba(va[FEATURES])[:, 1]
```

**AC.** La cellule contient `va_cal, va_ev = train_test_split`.

---

## T21 — Ajouter la cible `y_gap_excess`

**F.** `06_Modeling_M1_Gap.ipynb`
**A.** `LEAVE-ONE-TICKER-OUT`

**ACT.** Insère une nouvelle cellule de code **après** celle contenant l'ancre :

```python
print("=" * 92)
print("8.4 — LE SIGNAL EST-IL SPÉCIFIQUE À L'ACTION, OU EST-CE LE MARCHÉ ?")
print("=" * 92)
print("""
  gap_excess = gap du titre − moyenne des gaps du jour sur les 5 titres.

  Si le sentiment ne prédisait que le marché (le Nasdaq ouvre en hausse, les
  cinq titres ouvrent en hausse), le signal disparaîtrait sur cette cible.
  S'il survit, il est SPÉCIFIQUE au titre — un résultat bien plus fort.
""")

lignes = []
for cible, libelle in [("y_gap", "gap brut"),
                       ("y_gap_excess", "gap en excès du marché")]:
    if cible not in df.columns:
        print(f"  [ABSENT] {cible} — vérifier le notebook 05 §5")
        continue
    d_ = df[df["bloc"].isin(["train", "purge_1", "valid"])].dropna(subset=[cible]).copy()
    s_ = []
    for j_tr, j_te in plis:
        a = d_[d_["Date"].isin(j_tr)]; b = d_[d_["Date"].isin(j_te)]
        if len(a) < 200 or b[cible].nunique() < 2:
            continue
        mm = clone(pipeline_logit(1.0)).fit(a[FEATURES], a[cible])
        s_.append(roc_auc_score(b[cible], mm.predict_proba(b[FEATURES])[:, 1]))
    lignes.append(dict(Cible=libelle, taux_base=round(d_[cible].mean(), 3),
                       AUC_wf=round(np.mean(s_), 4), std=round(np.std(s_), 4),
                       plis=len(s_)))

E = pd.DataFrame(lignes)
print(E.to_string(index=False))
E.to_csv(os.path.join(DOCS, "06_cible_gap_excess.csv"), index=False)

if len(E) == 2:
    perte = E["AUC_wf"].iloc[1] - E["AUC_wf"].iloc[0]
    print(f"""
  Perte en passant au gap en excès : {perte:+.4f}

  INTERPRÉTATION
    perte < 0,02      -> signal ENTIÈREMENT spécifique au titre. Excellent.
    0,02 <= perte < 0,05 -> majoritairement spécifique, composante de marché.
    perte >= 0,05     -> une part importante est un effet de marché commun.
""")
```

**AC.** Le fichier `docs\06_cible_gap_excess.csv` est produit à l'exécution.

---

## T22 — Journal des exécutions du bloc de test

**F.** `06_Modeling_M1_Gap.ipynb`
**A.** `trva = d[d["bloc"].isin(`

**ACT.** Au **début** de cette cellule, avant tout le reste, insère :

```python
import datetime as _dt
_JOURNAL = os.path.join(DOCS, "JOURNAL_TEST.txt")
with open(_JOURNAL, "a", encoding="utf-8") as _f:
    _f.write(f"{_dt.datetime.now():%Y-%m-%d %H:%M:%S} | "
             f"spec={CFG.get('specification_retenue','?')} | "
             f"n_features={len(FEATURES)} | coupure={CFG.get('heure_coupure','?')}h\n")
print("Historique des exécutions du bloc de TEST :")
print(open(_JOURNAL, encoding="utf-8").read())
print("Chaque ligne consomme un 'regard' sur le test. Au-delà de deux, le\n"
      "chiffre annoncé n'a plus la valeur d'une évaluation en aveugle.\n")

```

Et remplace `trva = d[d["bloc"].isin(["train", "valid"])]` par :

```python
trva = d[d["bloc"].isin(["train", "purge_1", "valid"])]
```

**AC.** La cellule contient `JOURNAL_TEST.txt`.

---

## T23 — Corriger le n effectif

**F.** `07_Modeling_M2_M3.ipynb`
**A.** `n_eff = n * (1 - a1 * a2) / (1 + a1 * a2)`

**ACT.** Remplace **la cellule entière** par :

```python
def rho_minimal_detectable(n, alpha=0.05, puissance=0.80):
    """Plus petite corrélation détectable, via la transformation z de Fisher.
    Écart-type de z = 1/sqrt(n-3), indépendant de la vraie valeur de rho."""
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(puissance)
    return np.tanh((z_a + z_b) / np.sqrt(n - 3))

n_lignes = len(df)
n_jours  = df["Date"].nunique()
n_tick   = df["Ticker"].nunique()
VAR_SENT = "mu_night_safe" if "mu_night_safe" in df.columns else "mu_overnight"

print("=" * 80)
print("PUISSANCE STATISTIQUE — corrélation minimale détectable")
print("=" * 80)
print(f"""
  n brut ........ {n_lignes:,} observations titre-jour ({n_jours} jours x {n_tick} titres)
  n effectif .... {n_jours:,} jours

  JUSTIFICATION DU n EFFECTIF
  Les cinq titres d'un même jour sont de grandes capitalisations
  technologiques du même indice : leurs gaps sont fortement corrélés, un choc
  de marché les affectant simultanément. Les cinq lignes d'une même date ne
  constituent donc pas cinq informations indépendantes ; le nombre
  d'observations effectivement indépendantes est majoré par le nombre de jours.

  NB — une correction fondée sur la seule autocorrélation temporelle
  (facteur de Bartlett) est inadaptée : la dépendance dominante est
  TRANSVERSALE. Appliquée ici, elle produisait un n effectif SUPÉRIEUR au n
  brut (3 158 pour 2 736), ce qui est impossible par construction.
""")

seuil = rho_minimal_detectable(n_jours)
print(f"  Corrélation détectable à 80 % de puissance (alpha = 5 %) : {seuil:.4f}\n")
print(f"  {'Cible':10s} {'rho observé':>12s}   Verdict")
print("  " + "-" * 54)
for cible in ["gap", "ret_oc", "ret_cc"]:
    s = df[[VAR_SENT, cible]].dropna()
    rho = s[VAR_SENT].corr(s[cible])
    v = "SIGNAL DÉTECTÉ" if abs(rho) > seuil else "sous le seuil de détection"
    print(f"  {cible:10s} {rho:>+12.4f}   {v}")
print("=" * 80)
```

**AC.** La chaîne `(1 - a1 * a2)` n'apparaît plus dans le notebook 07.

---

## T24 — Faire tourner les variantes de M2

**F.** `07_Modeling_M2_M3.ipynb`
**A.** `échantillon insuffisant`

**ACT.** Remplace la fonction `ajouter` et son contexte par :

```python
MIN_TRAIN, TAILLE_TEST = 80, 40
BESOIN = MIN_TRAIN + PURGE + TAILLE_TEST

def auc_wf_souple(data, cible, feats, proto, min_train=MIN_TRAIN, taille_test=TAILLE_TEST):
    """Walk-forward avec des paramètres adaptés aux sous-échantillons.
    La version standard (min_train=250, taille_test=60) exige 315 jours
    distincts, que les sous-échantillons de quintile n'atteignent pas."""
    j = np.sort(pd.unique(data["Date"])); plis_, fin = [], len(j)
    for _ in range(6):
        d0 = fin - taille_test
        if d0 - PURGE < min_train:
            break
        plis_.append((j[:d0 - PURGE], j[d0:fin])); fin = d0
    plis_ = plis_[::-1]
    s = []
    for j_tr, j_te in plis_:
        a = data[data["Date"].isin(j_tr)]; b = data[data["Date"].isin(j_te)]
        if len(a) < 100 or b[cible].nunique() < 2:
            continue
        mm = clone(proto).fit(a[feats], a[cible])
        s.append(roc_auc_score(b[cible], mm.predict_proba(b[feats])[:, 1]))
    return (np.mean(s), np.std(s), len(s)) if s else (np.nan, np.nan, 0)

variantes = []

def ajouter(nom, sous, feats=None):
    """Ajoute une variante. Si l'échantillon est trop court, on le DIT au lieu
    de renvoyer un NaN muet qui se lirait comme un résultat nul."""
    feats = feats or FEAT_SENT
    n_j = sous["Date"].nunique()
    if n_j < BESOIN:
        variantes.append(dict(Variante=nom, n=len(sous), n_jours=n_j, AUC=np.nan,
                              note=f"IMPOSSIBLE : {n_j} jours < {BESOIN} requis"))
        return
    m_, s_, k_ = auc_wf_souple(sous, "y_oc", feats, logit())
    variantes.append(dict(Variante=nom, n=len(sous), n_jours=n_j,
                          AUC=round(m_, 4), note=f"{k_} plis"))
```

**ACT COMPLÉMENTAIRE.** À la fin de la cellule, après l'affichage de `V`, ajoute :

```python
n_ok = int(V["AUC"].notna().sum())
print(f"""
  {n_ok} variantes sur {len(V)} ont produit un résultat.

  CORRECTION POUR TESTS MULTIPLES (Bonferroni)
    seuil individuel .. 0,05
    seuil corrigé ..... {0.05/max(n_ok,1):.4f}   (0,05 / {n_ok})
    P(au moins un faux positif sans correction) = {1-0.95**max(n_ok,1):.1%}

  Toute variante qui ressort doit être traitée comme une HYPOTHÈSE à retester
  sur données indépendantes, et non comme un résultat.
""")
```

**AC.** La cellule contient `IMPOSSIBLE :` et `Bonferroni`.

---

## T25 — Erreurs-types groupées par date

**F.** `07_Modeling_M2_M3.ipynb`
**A.** `compare_f_test`

**ACT.** Insère une nouvelle cellule de code **après** celle contenant l'ancre :

```python
# ==========================================================================
#  ERREURS-TYPES GROUPÉES PAR DATE
#  Le test F suppose 2 391 résidus indépendants. Il y en a environ 478 (les
#  jours). Un p de 1e-38 n'est pas crédible en économie ; le regroupement par
#  date autorise une corrélation arbitraire entre les cinq titres d'un même
#  jour (Petersen, 2009).
# ==========================================================================
X_ = sm.add_constant(e[TK + VOL_PASSEE + SENT_RISQUE].astype(float))
y_ = e["log_ampl"].astype(float)
groupes = pd.factorize(e["Date"])[0]

m3_ols = sm.OLS(y_, X_).fit()
m3_clu = sm.OLS(y_, X_).fit(cov_type="cluster", cov_kwds={"groups": groupes})

cmp = pd.DataFrame({
    "coef":       m3_ols.params,
    "se_ols":     m3_ols.bse,
    "se_cluster": m3_clu.bse,
    "t_ols":      m3_ols.tvalues,
    "t_cluster":  m3_clu.tvalues,
    "p_cluster":  m3_clu.pvalues,
}).loc[VOL_PASSEE + SENT_RISQUE]
cmp["inflation"] = (cmp["se_cluster"] / cmp["se_ols"]).round(2)

print("COMPARAISON DES ERREURS-TYPES\n" + "-" * 88)
print(cmp.round(4).to_string())
cmp.to_csv(os.path.join(DOCS, "07_M3_erreurs_types_cluster.csv"))
print(f"""
  Inflation moyenne des erreurs-types : {cmp['inflation'].mean():.2f}x

  À REPORTER DANS LE MÉMOIRE : les colonnes t_cluster et p_cluster,
  jamais celles de la régression brute.
""")
```

**AC.** La cellule contient `cov_type="cluster"`.

---

## T26 — Retirer `rk_nabn` de M3

**F.** `07_Modeling_M2_M3.ipynb`
**A.** `SENT_RISQUE = [c for c in [`

**ACT.** Remplace la définition par :

```python
# rk_nabn RETIRÉE, pour deux raisons cumulées :
#   1) elle est redondante avec z_nabn (même quantité, z-score vs rang), ce qui
#      rendait z_nabn non significative (p = 0,61) par répartition arbitraire
#      du crédit entre deux variables colinéaires ;
#   2) son min_periods=60 ampute le calendrier de 60 jours par titre, soit un
#      pli entier de walk-forward (3 au lieu de 4).
SENT_RISQUE = [c for c in ["z_nabn_night_safe", "z_nlog_night_safe",
                           "z_sd_night_safe", "z_mu_night_safe",
                           "z_nabn_night_full", "z_nlog_night_full",
                           "z_sd_night_full", "z_mu_night_full"]
               if c in d.columns][:4]
print("SENT_RISQUE :", SENT_RISQUE)
```

**AC.** La chaîne `rk_nabn_night_full` n'apparaît plus dans `SENT_RISQUE`.
**ATTENDU.** Le nombre de plis de la section B.4 passe de 3 à 4.

---

## T27 — Test de Christoffersen

**F.** `07_Modeling_M2_M3.ipynb`
**A.** `def kupiec(depassements, n, alpha=NIVEAU):`

**ACT.** Insère une nouvelle cellule de code **après** la cellule contenant l'ancre :

```python
def christoffersen(depassements, alpha=0.05):
    """Test conjoint de couverture (Kupiec) et d'indépendance (Christoffersen 1998).

    Kupiec teste le NOMBRE de dépassements, pas leur REGROUPEMENT. Deux modèles
    avec 10 dépassements sur 200 jours reçoivent le même verdict, qu'ils soient
    dispersés ou groupés sur dix jours consécutifs — alors que le second fait
    faillite. Christoffersen ajoute le test manquant.

    depassements : série booléenne ORDONNÉE CHRONOLOGIQUEMENT, pour UN titre.
    """
    d_ = np.asarray(depassements).astype(int)
    n, x = len(d_), int(d_.sum())
    if x == 0 or x == n or n < 20:
        return dict(n=n, x=x, taux=np.nan, LR_uc=np.nan, p_uc=np.nan,
                    LR_ind=np.nan, p_ind=np.nan, LR_cc=np.nan, p_cc=np.nan)

    pi = x / n
    lr_uc = -2 * ((n - x) * np.log(1 - alpha) + x * np.log(alpha)
                  - (n - x) * np.log(1 - pi) - x * np.log(pi))

    n00 = int(((d_[:-1] == 0) & (d_[1:] == 0)).sum())
    n01 = int(((d_[:-1] == 0) & (d_[1:] == 1)).sum())
    n10 = int(((d_[:-1] == 1) & (d_[1:] == 0)).sum())
    n11 = int(((d_[:-1] == 1) & (d_[1:] == 1)).sum())
    if (n00 + n01) == 0 or (n10 + n11) == 0 or n11 == 0:
        lr_ind = 0.0
    else:
        p01 = n01 / (n00 + n01); p11 = n11 / (n10 + n11)
        p_  = (n01 + n11) / (n00 + n01 + n10 + n11)
        lr_ind = -2 * ((n00 + n10) * np.log(1 - p_) + (n01 + n11) * np.log(p_)
                       - n00 * np.log(1 - p01) - n01 * np.log(p01)
                       - n10 * np.log(1 - p11) - n11 * np.log(p11))

    lr_cc = lr_uc + lr_ind
    return dict(n=n, x=x, taux=round(x / n, 4),
                LR_uc=round(lr_uc, 3),  p_uc=round(1 - stats.chi2.cdf(lr_uc, 1), 4),
                LR_ind=round(lr_ind, 3), p_ind=round(1 - stats.chi2.cdf(lr_ind, 1), 4),
                LR_cc=round(lr_cc, 3),   p_cc=round(1 - stats.chi2.cdf(lr_cc, 2), 4))


# Application PAR TICKER : l'ordre chronologique doit être respecté à
# l'intérieur d'une série. Sur le panel empilé, les transitions
# « dernier jour d'AAPL -> premier jour d'AMZN » seraient absurdes.
lignes = []
for nom, col in [("inconditionnelle", "VaR_incond"), ("conditionnelle", "VaR_cond")]:
    for tk, g_ in O.sort_values("Date").groupby("Ticker"):
        r_ = christoffersen((g_["ret_cc"] < g_[col]).values)
        r_.update(VaR=nom, Ticker=tk)
        lignes.append(r_)

CH = pd.DataFrame(lignes)[["VaR", "Ticker", "n", "x", "taux",
                           "LR_uc", "p_uc", "LR_ind", "p_ind", "LR_cc", "p_cc"]]
print("TESTS DE COUVERTURE ET D'INDÉPENDANCE, PAR TITRE")
print(CH.to_string(index=False))
CH.to_csv(os.path.join(DOCS, "07_christoffersen.csv"), index=False)
print("""
  LECTURE
    p_uc  > 0,05 : le NOMBRE de dépassements est correct   (Kupiec)
    p_ind > 0,05 : les dépassements ne sont pas GROUPÉS    (Christoffersen)
    p_cc  > 0,05 : les deux à la fois                      (test conjoint)

  Une VaR qui passe p_uc mais échoue p_ind est dangereuse : elle a le bon
  nombre de dépassements, mais ils surviennent tous en même temps — c'est-à-dire
  pendant les crises, quand le capital est le plus nécessaire.
""")
```

**AC.** Le fichier `docs\07_christoffersen.csv` est produit à l'exécution.

---

## T28 — Corriger la lecture de la VaR moyenne

**F.** `07_Modeling_M2_M3.ipynb`
**A.** `même protection, moins de capital immobilisé`

**ACT.** Remplace le bloc de commentaire final de cette cellule par :

```python
    print(f"""
LECTURE
  - taux_observe doit être proche de 0,05. Trop haut = risque sous-estimé.
  - p_value de Kupiec > 0,05 = la couverture est acceptable.

  ATTENTION à l'argument du capital : dans nos résultats, la VaR
  conditionnelle est en moyenne LÉGÈREMENT PLUS LARGE que l'inconditionnelle
  ({K.loc[1,'VaR_moyenne_pct']:.3f} % contre {K.loc[0,'VaR_moyenne_pct']:.3f} %).
  Le gain n'est donc PAS dans le niveau moyen de capital immobilisé.

  Le gain est dans l'ALLOCATION TEMPORELLE, et il se mesure sur l'Expected
  Shortfall — la perte moyenne les jours où la VaR est dépassée :
     inconditionnelle : {K.loc[0,'ES_observe_pct']:.3f} %
     conditionnelle   : {K.loc[1,'ES_observe_pct']:.3f} %
     amélioration     : {(1 - K.loc[1,'ES_observe_pct']/K.loc[0,'ES_observe_pct'])*100:.1f} %

  L'Expected Shortfall est la mesure qui remplace la VaR dans le cadre FRTB de
  Bâle III, et qu'on retrouve en actuariat sous le nom de Tail-VaR. C'est
  l'argument à retenir : à capital équivalent, les dépassements sont MOINS
  GRAVES.
""")
```

**AC.** La chaîne `moins de capital immobilisé` n'apparaît plus.

---

## T29 — Nouvelle section : VaR du gap overnight

**F.** `07_Modeling_M2_M3.ipynb`
**ACT.** Ajoute **deux cellules à la fin du notebook**, avant la cellule de synthèse §C.

### Cellule markdown

```markdown
---
## §B.6 — Tarification du risque de gap d'ouverture

**Motivation actuarielle.** Le risque overnight est structurellement non couvrable : entre la clôture et
l'ouverture, aucun ordre ne s'exécute, et un stop-loss ne protège pas. C'est le segment de risque le plus
proche d'un sinistre assurantiel — une perte subie, non gérable, dont seule la tarification *ex ante*
peut protéger.

**La question.** L'attention sociale nocturne permet-elle de mieux tarifer ce risque qu'une approche
inconditionnelle ?

**Pourquoi ce résultat est robuste.** Les variables utilisées sont le **volume** et la **dispersion** des
messages, mesurés avant 4h00 — pas leur direction. Un volume de messages nocturne ne peut pas décrire
l'amplitude d'un gap qui ne se formera qu'à l'ouverture. Cette section est donc immunisée contre la
contamination par le pré-marché identifiée pour la prédiction directionnelle.
```

### Cellule code

```python
from sklearn.linear_model import RidgeCV

print("=" * 86)
print("§B.6 — TARIFICATION DU RISQUE DE GAP D'OUVERTURE")
print("=" * 86)

# ---------- 1. Cible : amplitude du gap ----------
r = df.copy()
r["abs_gap"]    = r["gap"].abs()
r["log_absgap"] = np.log(r["abs_gap"].clip(lower=1e-6))

_g = r.sort_values(["Ticker", "Date"]).groupby("Ticker")
r["lag_absgap_1"]    = _g["log_absgap"].shift(1)
r["lag_absgap_ma5"]  = _g["log_absgap"].transform(
                           lambda s: s.shift(1).rolling(5, min_periods=3).mean())
r["lag_absgap_ma20"] = _g["log_absgap"].transform(
                           lambda s: s.shift(1).rolling(20, min_periods=10).mean())

VOL_GAP  = ["lag_absgap_1", "lag_absgap_ma5", "lag_absgap_ma20", "vol_20"]
ATT_NUIT = [c for c in ["z_nabn_night_safe", "z_nlog_night_safe",
                        "z_sd_night_safe", "z_mu_night_safe",
                        "z_nabn_night_full", "z_nlog_night_full"]
            if c in r.columns][:4]
print(f"Variables d'attention retenues : {ATT_NUIT}\n")

r = pd.get_dummies(r, columns=["Ticker"], prefix="tk", drop_first=False)
TKD = [c for c in r.columns if c.startswith("tk_")][1:]     # drop_first manuel
rr = r.dropna(subset=["log_absgap", "gap"] + VOL_GAP + ATT_NUIT).copy()
print(f"n = {len(rr):,} observations | {rr['Date'].nunique()} jours\n")

# ---------- 2. Modèles emboîtés, erreurs-types groupées ----------
def _ols(cols, nom):
    X = sm.add_constant(rr[cols].astype(float))
    mm = sm.OLS(rr["log_absgap"].astype(float), X).fit(
            cov_type="cluster", cov_kwds={"groups": pd.factorize(rr["Date"])[0]})
    print(f"  {nom:54s} R2 = {mm.rsquared:.4f}")
    return mm

print("MODÈLES EMBOÎTÉS — cible : log |gap|")
g0 = _ols(TKD,                      "[G0] effets fixes titre")
g1 = _ols(TKD + VOL_GAP,            "[G1] + amplitude passée des gaps  <-- RÉFÉRENCE")
g2 = _ols(TKD + VOL_GAP + ATT_NUIT, "[G2] + attention sociale nocturne")
print(f"\n  Apport de l'attention (G2 - G1) : {g2.rsquared - g1.rsquared:+.4f}")
print("\n  Coefficients (erreurs-types groupées par date) :")
print(g2.summary2().tables[1].loc[VOL_GAP + ATT_NUIT].round(4).to_string())

# ---------- 3. VaR du gap en walk-forward ----------
NIVEAU_G = 0.05
plis_g = plis_wf(rr["Date"], n_plis=6, taille_test=60)
obs_g, feats_g = [], TKD + VOL_GAP + ATT_NUIT

for j_tr, j_te in plis_g:
    a = rr[rr["Date"].isin(j_tr)]; b = rr[rr["Date"].isin(j_te)].copy()
    if len(a) < 250 or len(b) < 30:
        continue
    mdl = RidgeCV(alphas=np.logspace(-3, 3, 25)).fit(
              a[feats_g].astype(float), a["log_absgap"].astype(float))

    # Correction de Jensen (smearing de Duan, 1983) : E[exp(X)] != exp(E[X]).
    # Sans elle, l'amplitude prévue est sous-estimée d'environ 7 %, donc la
    # VaR est trop étroite et les dépassements trop nombreux.
    resid   = a["log_absgap"].values - mdl.predict(a[feats_g].astype(float))
    facteur = float(np.mean(np.exp(resid)))

    ech_train = np.exp(mdl.predict(a[feats_g].astype(float))) * facteur
    b["ech_prevue"] = np.exp(mdl.predict(b[feats_g].astype(float))) * facteur

    # Quantile des gaps STANDARDISÉS, estimé sur le train, à la MÊME échelle
    a_ = a.copy(); a_["z_gap"] = a_["gap"].values / ech_train
    q = a_["z_gap"].quantile(NIVEAU_G)

    b["VaR_gap_cond"]   = q * b["ech_prevue"]
    b["VaR_gap_incond"] = a["gap"].quantile(NIVEAU_G)
    obs_g.append(b)

G = pd.concat(obs_g).dropna(subset=["gap", "VaR_gap_cond", "VaR_gap_incond"])
print(f"\nBacktest de VaR sur {len(G):,} observations ({G['Date'].nunique()} jours)")

lignes = []
for nom, col in [("VaR gap inconditionnelle", "VaR_gap_incond"),
                 ("VaR gap conditionnelle (attention)", "VaR_gap_cond")]:
    dep = int((G["gap"] < G[col]).sum()); n = len(G)
    lr, p = kupiec(dep, n)
    es = G.loc[G["gap"] < G[col], "gap"].mean()
    lignes.append(dict(Modele=nom, n=n, depassements=dep, taux=round(dep / n, 4),
                       LR_Kupiec=round(lr, 3), p_value=round(p, 4),
                       ES_pct=round(es * 100, 3),
                       VaR_moy_pct=round(G[col].mean() * 100, 3)))
KG = pd.DataFrame(lignes)
print("\n" + KG.to_string(index=False))
KG.to_csv(os.path.join(DOCS, "07_VaR_GAP.csv"), index=False)

# ---------- 4. Indépendance des dépassements ----------
tk_cols = [c for c in G.columns if c.startswith("tk_")]
G["_ticker"] = G[tk_cols].idxmax(axis=1) if tk_cols else "ALL"
print("\nTEST D'INDÉPENDANCE (Christoffersen) sur la VaR du gap :")
for nom, col in [("incond", "VaR_gap_incond"), ("cond", "VaR_gap_cond")]:
    for tk, gg in G.sort_values("Date").groupby("_ticker"):
        rr_ = christoffersen((gg["gap"] < gg[col]).values)
        print(f"  {nom:7s} {str(tk)[:8]:8s} : taux={rr_['taux']} "
              f"p_uc={rr_['p_uc']} p_ind={rr_['p_ind']} p_cc={rr_['p_cc']}")

print("""
PHRASE POUR LE MÉMOIRE
  « Le risque de gap d'ouverture, structurellement non couvrable puisqu'aucun
    ordre ne s'exécute pendant la fermeture des marchés, est tarifé
    conditionnellement à l'attention sociale nocturne. Le modèle conditionnel
    atteint un taux de dépassement de X % pour une cible de 5 %, contre Y %
    pour une VaR inconditionnelle, et réduit l'Expected Shortfall observé de
    Z %. L'attention sociale constitue ainsi un facteur de tarification du
    risque overnight, alors même qu'elle n'apporte aucun pouvoir prédictif
    directionnel. »
""")
```

**AC.** Le fichier `docs\07_VaR_GAP.csv` est produit à l'exécution.

---

## T30 — Corriger le turnover du notebook 08

**F.** `08_Backtest.ipynb`
**A.** `x["cout"] = x["position"].abs() * (cout_bp / 10_000)`

**ACT.** Remplace la fonction `backtest` par :

```python
def backtest(data, cout_bp=10.0, cible="gap"):
    """P&L d'une stratégie close-to-open.

    Le coût porte sur le TURNOVER (variation de position) et non sur la
    position brute : maintenir une position ne coûte rien, la retourner coûte
    deux fois. C'est la convention du notebook 09, adoptée ici pour que les
    deux soient comparables.
    """
    x = data.sort_values(["Ticker", "Date"]).copy()
    x["turnover"] = (x.groupby("Ticker")["position"].diff().abs()
                       .fillna(x["position"].abs()))
    x["pnl_brut"] = x["position"] * x[cible]
    x["cout"]     = x["turnover"] * (cout_bp / 10_000)
    x["pnl_net"]  = x["pnl_brut"] - x["cout"]

    j = x.groupby("Date").agg(
        pnl_brut=("pnl_brut", "sum"), pnl_net=("pnl_net", "sum"),
        cout=("cout", "sum"), turnover=("turnover", "sum"),
        expo=("position", lambda s: s.abs().sum()),
        n_pos=("position", lambda s: (s != 0).sum()))
    j["rendement"] = np.where(j["expo"] > 0, j["pnl_net"] / j["expo"], 0.0)
    j["equity"] = (1 + j["rendement"]).cumprod()
    return x, j
```

Applique **la même correction** dans `08_Backtest_Lag1.ipynb`.

**AC.** Les deux notebooks contiennent `x["turnover"] = (x.groupby("Ticker")`.

---

## T31 — Corriger le libellé « meilleur mois »

**F.** `08_Backtest.ipynb`
**A.** `pire = mois.idxmax()`

**ACT.** Remplace par :

```python
meilleur_mois = mois.idxmax()
Pm = P[P["Date"].dt.to_period("M") != meilleur_mois]
evaluer_variante(Pm, f"Sans le meilleur mois ({meilleur_mois})")
```

Vérifie que la ligne suivante utilise bien `meilleur_mois` et non `pire`.

**AC.** La chaîne `pire = mois.idxmax()` n'apparaît plus.

---

## T32 — Supprimer l'avertissement pandas du notebook 09 stratégies

**F.** `09_Backtest_Strategies_Lag1.ipynb`
**A.** `return x.groupby("Date", group_keys=False).apply(normalize)`

**ACT.** Remplace la fin de `make_positions` :

```python
    x["raw_position"] = raw
    # transform() au lieu de apply() : plus rapide, et sans FutureWarning sur
    # l'inclusion des colonnes de groupement.
    gross = x.groupby("Date")["raw_position"].transform(lambda s: s.abs().sum())
    x["position"] = np.where(gross > 0, x["raw_position"] / gross, 0.0)
    return x
```

Supprime aussi la fonction interne `normalize` devenue inutile.

**AC.** La chaîne `group_keys=False` n'apparaît plus dans ce notebook.

---

## T33 — Tableau 2×2 des backtests

**F.** `08_Backtest_Lag1.ipynb`
**ACT.** Ajoute une cellule de code **à la fin** :

```python
# ==========================================================================
#  LE TABLEAU 2 x 2 DU MÉMOIRE
#  Deux corrections INDÉPENDANTES, qui se cumulent :
#    - la spécification A retire l'information non ACTIONNABLE (pré-marché) ;
#    - le lag 1 retire l'information non DISPONIBLE au moment de la décision.
# ==========================================================================
resultats = []
for nom_spec, cle in [("A — stricte (4h00)",    "features"),
                      ("C — complète (annexe)", "features_C_complete")]:
    feats = [c for c in CFG.get(cle, []) if c in d.columns]
    if not feats:
        print(f"[IGNORÉ] {nom_spec} : clé {cle} absente du JSON")
        continue
    blocs = []
    for j_tr, j_te in plis:
        a = d[d["Date"].isin(j_tr)]; b = d[d["Date"].isin(j_te)].copy()
        if len(a) < 250 or b["y_gap"].nunique() < 2:
            continue
        mm = clone(logit()).fit(a[feats], a["y_gap"])
        b["proba"] = mm.predict_proba(b[feats])[:, 1]
        blocs.append(b)
    PP = pd.concat(blocs).sort_values(["Ticker", "Date"]).reset_index(drop=True)

    for lag in [0, 1]:
        Q = PP.copy()
        if lag:
            Q["proba"] = Q.groupby("Ticker")["proba"].shift(lag)
            Q = Q.dropna(subset=["proba"])
        auc_ = roc_auc_score(Q["y_gap"], Q["proba"])
        pos = construire_positions(Q, seuil=0.05, mode="proportionnel")
        _, jj = backtest(pos, cout_bp=10.0, cible="gap")
        mm_ = metriques(jj, nom=f"{nom_spec} | lag {lag}")
        mm_["AUC"] = round(auc_, 4)
        resultats.append(mm_)

R2 = pd.DataFrame(resultats)[["strategie", "AUC", "sharpe", "rendement_annuel",
                              "max_drawdown", "taux_reussite"]]
print("=" * 100)
print("TABLEAU 2 x 2 — spécification x décalage   (coût 10 bp)")
print("=" * 100)
print(R2.round(4).to_string(index=False))
R2.to_csv(os.path.join(DOCS, "08bis_tableau_2x2.csv"), index=False)
print("""
LECTURE EN CROIX
  C | lag 0 : la mesure naïve. Impressionnante et fausse.
  C | lag 1 : la même spécification, décalée du délai réellement imposé par
              la décision (à 16h00, les messages de la nuit n'existent pas).
  A | lag 0 : le signal propre, mesuré sans contamination par le pré-marché.
  A | lag 1 : le signal propre ET décalé. C'est ce qu'on peut effectivement
              négocier — le résultat économique du mémoire.
""")
```

**AC.** Le fichier `docs\08bis_tableau_2x2.csv` est produit à l'exécution.

---

## T34 — Garde-fou de fraîcheur dans la synthèse

**F.** `09_Synthese_Memoire.ipynb`
**A.** `INVENTAIRE DES RÉSULTATS`

**ACT.** Remplace la cellule entière par :

```python
import datetime as dt

fichiers = {
    "Comparaison spécifications (06)": "06_comparaison_specifications.csv",
    "Coefficients interprétables (06)": "06_coefficients_interpretables.csv",
    "Comparaison modèles M1 (06)":     "06_comparaison_modeles_valid.csv",
    "Walk-forward M1 (06)":            "06_walkforward_synthese.csv",
    "Ablations M1 (06)":               "06_ablations.csv",
    "Cible gap_excess (06)":           "06_cible_gap_excess.csv",
    "Résultats TEST M1 (06)":          "06_RESULTATS_TEST.csv",
    "Recherche signal M2 (07)":        "07_M2_recherche_signal.csv",
    "Variantes M2 (07)":               "07_M2_variantes.csv",
    "Résultats M3 (07)":               "07_M3_resultats.csv",
    "Erreurs-types cluster (07)":      "07_M3_erreurs_types_cluster.csv",
    "Backtest VaR ret_cc (07)":        "07_M3_backtest_VaR.csv",
    "Backtest VaR GAP (07)":           "07_VaR_GAP.csv",
    "Christoffersen (07)":             "07_christoffersen.csv",
    "Sensibilité aux coûts (08)":      "08_sensibilite_couts.csv",
    "Comparaison stratégies (08)":     "08_comparaison_strategies.csv",
    "Robustesse backtest (08)":        "08_robustesse.csv",
    "Tableau 2x2 (08bis)":             "08bis_tableau_2x2.csv",
    "Courbe des coupures (03bis)":     "03bis_courbe_coupures.csv",
    "Coupures par ticker (03bis)":     "03bis_coupures_par_ticker.csv",
}

REFERENCE = os.path.join(DATA, "DATASET_MODELISATION_2020_2022.csv")
t_ref = os.path.getmtime(REFERENCE)
print(f"Dataset de référence : {dt.datetime.fromtimestamp(t_ref):%Y-%m-%d %H:%M}\n")

print("INVENTAIRE DES RÉSULTATS\n" + "=" * 90)
dispo, perimes, manquants = {}, [], []
for nom, f in fichiers.items():
    p = os.path.join(DOCS, f)
    if not os.path.exists(p):
        manquants.append(nom)
        print(f"  [MANQUE ] {nom:38s} -> exécuter le notebook correspondant")
        continue
    age = os.path.getmtime(p)
    if age < t_ref:
        perimes.append(nom); marque = "PÉRIMÉ "
    else:
        dispo[nom] = pd.read_csv(p); marque = "OK     "
    print(f"  [{marque}] {nom:38s} ({dt.datetime.fromtimestamp(age):%Y-%m-%d %H:%M})")

print("=" * 90)
if perimes:
    raise RuntimeError(
        f"{len(perimes)} fichier(s) antérieur(s) au dataset — chiffres non fiables.\n"
        "Ce notebook alimente le manuscrit : un CSV périmé y ferait entrer un\n"
        "chiffre que les notebooks ne produisent plus.\nRéexécuter :\n  - "
        + "\n  - ".join(perimes))
if manquants:
    print(f"\nATTENTION : {len(manquants)} résultats manquants — synthèse incomplète.")
print(f"\n{len(dispo)} fichiers de résultats à jour.")
```

**AC.** La cellule contient `PÉRIMÉ` et `raise RuntimeError`.

---

## T35 — Mettre à jour la réponse au jury

**F.** `09_Synthese_Memoire.ipynb`
**A.** `Comment savez-vous qu'il n'y a pas de fuite`

**ACT.** Dans cette cellule markdown, remplace la section correspondante par :

```markdown
### « Comment savez-vous qu'il n'y a pas de fuite ? »

Cinq éléments, dont un négatif que nous reportons nous-mêmes.

**Ce qui est établi :**

1. **Test placebo** — le pipeline entraîné sur une cible aléatoirement permutée obtient une AUC de 0,479.
   Une fuite structurelle du code lui ferait trouver quelque chose même sur du bruit.
2. **Lags négatifs** — le sentiment du jour J+1 ne prédit pas le gap du jour J (0,096 contre 0,383). Un
   désalignement temporel se verrait immédiatement ici.
3. **Ablation par inversion** — inverser le signe du sentiment sur le seul jeu d'évaluation fait tomber
   l'AUC à 0,249, soit le complément à un de la valeur nominale à 1 % près. La performance dépend donc du
   contenu du signal, non d'un artefact.
4. **Règle codée** — l'appartenance d'une variable à l'espace des prédicteurs est décidée par une fonction
   (`est_legale`), et l'export du jeu de données est **bloqué par une exception** si l'un des tests échoue.

**Ce que nous avons trouvé et documenté :**

5. Le test de corrélation contemporaine a signalé que `z_mu_pre` — sentiment de la fenêtre minuit–9h30 —
   corrèle à 0,450 avec le gap, seule variable sur vingt-trois à dépasser le seuil. L'analyse d'importance
   par permutation lui attribuait 81 % du pouvoir prédictif.

   Un découpage horaire de la fenêtre nocturne (notebook 03bis) localise la rupture à **4h00 du matin**,
   heure d'ouverture de la séance de pré-ouverture américaine. Au-delà, les messages décrivent un prix
   déjà en formation sur un marché ouvert.

   La spécification retenue pour l'ensemble des résultats restreint donc la fenêtre nocturne aux messages
   antérieurs à 4h00. Elle conserve une AUC de [A_REMPLIR], contre [C_REMPLIR] pour la spécification non
   contrôlée, qui figure en annexe à titre de comparaison.
```

**AC.** La cellule contient `notebook 03bis`.

---

## T36 — Corrections mineures du notebook 04

**F.** `04_EDA_Sentiment_Market.ipynb`

**ACT 36a.** Ancre : `fois supérieur`. Le message imprime « environ 1 fois supérieur », résultat d'un
arrondi. Remplace la ligne de `print` par une formulation en pourcentage :

```python
print(f"LECTURE : NVDA a un sentiment moyen environ {(ratio-1)*100:.0f} % supérieur à TSLA.")
```

en définissant `ratio = niveaux.max() / niveaux.min()` juste avant (adapte le nom de la série).

**ACT 36b.** Ancre : `PRÉDICTIVE (limite)`. Ajoute un troisième niveau de statut :

```python
def statut(fenetre, rho, seuil_contamination=0.40):
    """Statut d'une fenêtre vis-à-vis d'une cible.

    Trois niveaux :
      PRÉDICTIVE                    : fenêtre close avant l'ouverture du pré-marché
      CONTAMINÉE PRÉ-MARCHÉ         : fenêtre recouvrant 4h00-9h30 ET rho élevé
      CONTEMPORAINE / POSTÉRIEURE   : fenêtre du jour même
    """
    if fenetre in ("mu_open30", "mu_mkt", "mu_post"):
        return "CONTEMPORAINE / POSTÉRIEURE"
    if fenetre in ("mu_pre", "mu_night_full", "mu_premkt"):
        return ("CONTAMINÉE PRÉ-MARCHÉ (exclure)" if abs(rho) > seuil_contamination
                else "PRÉDICTIVE (limite)")
    return "PRÉDICTIVE"
```

**ACT 36c.** Ancre : `VERDICT AUTOMATIQUE`. Étends le verdict aux trois cibles et commente le pic au
lag −1 :

```python
print("VERDICT AUTOMATIQUE")
for cible in ["gap", "ret_cc", "ret_oc"]:
    r0 = T.loc[0, cible]
    rneg = T.loc[T.index < 0, cible].abs().max()
    print(f"  {cible:7s} : lag0 = {r0:+.4f} | max|lag<0| = {rneg:.4f} "
          f"| ratio = {rneg/max(abs(r0), 1e-9):.2f}")
print("""
  Le pic au lag -1 sur ret_oc et ret_cc n'est PAS une fuite. La fenêtre
  nocturne qui suit le jour J s'ouvre à 16h00 le jour J, après la clôture :
  les messages qui s'y écrivent COMMENTENT la séance écoulée. La causalité va
  donc du rendement vers le sentiment, dans le bon sens du temps. C'est une
  VALIDATION de l'alignement temporel, pas un problème.

  Seule la colonne gap importe pour le verdict de fuite : elle affiche un
  ratio bien inférieur à 0,5, ce qui confirme que le signal est ponctuel et
  correctement orienté.
""")
```

**AC.** Le notebook contient `CONTAMINÉE PRÉ-MARCHÉ`.

---

## T37 — Exécution de la chaîne et rapport

**ACT.** Dans cet ordre exact, exécute chaque notebook et **arrête-toi à la première exception** :

```
1.  03_Construction_Panel_1.ipynb
2.  03bis_Decoupage_Horaire.ipynb
3.  05_Features_et_Split.ipynb
4.  06_Modeling_M1_Gap.ipynb
5.  07_Modeling_M2_M3.ipynb
6.  08_Backtest.ipynb
7.  08_Backtest_Lag1.ipynb
8.  09_Backtest_Strategies_Lag1.ipynb
9.  09_Synthese_Memoire.ipynb
10. 04_EDA_Sentiment_Market.ipynb     (peut être exécuté à tout moment après 03)
```

Commande suggérée :

```powershell
cd "C:\Users\semy4\OneDrive\Bureau\Fintech_project\src\notebooks\notebooks"
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 03_Construction_Panel_1.ipynb
```

**POINTS DE CONTRÔLE.**

| Après | Vérifier |
|---|---|
| 03 | 8 contrôles qualité affichés, tous OK ; panel > 95 colonnes ; `MESSAGES_HORODATES.parquet` existe |
| 03bis | `03bis_courbe_coupures.csv` produit ; `rho_seance_intra` plat ; noter `rho_gap_intra` à 04h00 |
| 05 | **T1 PASSE** ; `AUCUNE FUITE DÉTECTÉE` ; JSON avec 3 clés de features |
| 06 | `assert` du walk-forward passe ; 3 plis ; `JOURNAL_TEST.txt` a une ligne de plus |
| 07 | Pas de `n_effectif > n_brut` ; `07_VaR_GAP.csv` et `07_christoffersen.csv` produits |
| 08/08bis | `08bis_tableau_2x2.csv` produit |
| 09syn | Aucun `PÉRIMÉ` |

**SI UNE EXCEPTION SURVIENT.** Ne la contourne pas. Rapporte : le notebook, la cellule, le message
complet, et ton hypothèse sur la cause. Attends une instruction.

---

# 5. Rapport attendu

À la fin, produis `RACINE\docs\RAPPORT_CORRECTIONS.md` contenant :

```markdown
# Rapport d'application des corrections

Date : ...

## Tâches appliquées
| ID | Fichier | Statut | Note |
|----|---------|--------|------|
| T00 | (archive) | OK | 9 notebooks, 23 CSV |
| T01 | 05 | OK | |
| ... | | | |

## Tâches en échec ou partielles
(détail : ancre introuvable, ambiguïté, exception)

## Chiffres clés après correction
| Grandeur | Avant | Après | Source |
|---|---|---|---|
| rho(sentiment, gap) | 0,3307 | ... | nb04 §17 |
| rho à la coupure 4h00 | — | ... | nb03bis |
| Part contemporaine | — | ... % | nb03bis |
| AUC validation (spec A) | 0,7753 | ... | nb06 |
| AUC walk-forward (spec A) | 0,7604 | ... | nb06 |
| AUC test (spec A) | 0,7912 | ... | nb06 §9 |
| IC 95 % par blocs | — | [... ; ...] | nb06 §9 |
| Nombre de plis | 4 | ... | nb06 |
| VIF maximum | 204,6 | ... | nb06 |
| Sharpe lag 0, 10 bp | 9,72 | ... | nb08 |
| Sharpe lag 1, 10 bp | −0,97 | ... | nb08bis |
| Break-even lag 1 | 4,8 bp | ... | nb08bis |
| M3 R2 hors échantillon | 0,5278 | ... | nb07 |
| M3 plis | 3 | ... | nb07 |
| VaR ret_cc — Kupiec p | 0,781 | ... | nb07 |
| VaR gap — Kupiec p | — | ... | nb07 §B.6 |

## Questions ouvertes
(tout choix que tu as dû faire faute d'instruction explicite)
```

---

# 6. Ce que tu ne dois PAS faire

- **Ne pas** supprimer le notebook 08 ni ses résultats à Sharpe 11,5 : ils deviennent une annexe
  pédagogique du mémoire.
- **Ne pas** réexécuter le §9 du notebook 06 plus d'une fois.
- **Ne pas** ajuster les hyperparamètres pour améliorer un résultat.
- **Ne pas** ajouter de modèles (LSTM, XGBoost réglé finement) : quatre spécifications donnent déjà des
  performances statistiquement indiscernables (écart de 0,011 pour une barre d'erreur de 0,023), la
  relation est linéaire.
- **Ne pas** remplacer une exception par un `try/except` silencieux : les exceptions ajoutées sont des
  garde-fous délibérés.
- **Ne pas** modifier `archive_v1\`.
- **Ne pas** deviner une ancre introuvable : signale et attends.

---

# 7. Contexte chiffré, pour référence

État **avant** corrections, mesuré sur les sorties exécutées :

```
Panel        : 2 740 lignes x 81 colonnes | 548 jours x 5 titres | 2020-01-02 -> 2022-03-04
Corpus       : 3 711 333 messages StockTwits (TSLA 51 %, AAPL 24 %)
FinBERT      : masse neutre moyenne 0,384 ; 36 % de messages neutres à plus de 90 %

Corrélations avec le gap (notebook 04 §17) :
  mu_pre         0,4007      <- fenêtre minuit-9h30, contaminée
  mu_night_full  0,3307      <- l'union
  mu_overnight   0,2156      <- fenêtre 16h-minuit, propre

Blocs        : train 1885 (59,5 % gaps +) | purge 25 | valid 520 (60,6 %) | test 310 (51,0 %)

Notebook 06  : R4 (1 variable, sans apprentissage) AUC 0,6983
               L-ctrl 0,4828 | L-sent 0,7733 | L-tout 0,7753 | GB 0,7845
               walk-forward 0,7604 | test 0,7912 IC [0,7391 ; 0,8390]
               VIF max 204,6 (z_mu_night_full) ; z_mu_overnight coef NÉGATIF (−0,48)
               permutation : z_mu_pre 0,1721 sur 0,2127 = 81 %
               ablations : sans sentiment 0,4979 | conservateur 0,6879
                           inversé 0,2485 | placebo 0,4942

Notebook 07  : séance 6 configurations, 0,490 à 0,522 (contrôle positif OK)
               n_effectif 3 158 > n brut 2 736  <- BUG
               4 variantes sur 7 en NaN         <- BUG
               M3 R2 0,4856 | R2_oos 0,5278 | QLIKE 0,3898 | 3 plis
               z_mu_night_full −0,0296 (t=−3,11) : effet de levier, Black 1976
               VaR : 43 dépassements / 896 = 4,80 % | Kupiec p 0,7812 | ES −5,255 %

Notebook 08  : Sharpe 11,509 (0 bp) | 9,722 (10 bp) | break-even INFINI
               drawdown −1,37 % | réussite 76,7 %
Notebook 08bis : Sharpe −0,969 (10 bp) | drawdown −16,94 % | réussite 46,4 %
                 break-even 4,1 à 4,8 bp
Notebook 09str : long_only_055 : 0,757 (5 bp) | 0,000 (10 bp) | −1,503 (20 bp)
                 p-value du rendement moyen : 0,4616 (NON significatif)
                 benchmark « acheter chaque soir » : 0,637 à 10 bp
                 SPY overnight : 0,434 | par ticker : 1 sur 5 au-dessus de 0,5
Notebook 09syn : lit des CSV périmés (affiche Sharpe 6,037 au lieu de 9,722)
```

**Vérifications arithmétiques déjà effectuées, toutes cohérentes** (donc aucun bug de calcul à chercher) :
rho 0,3307 → AUC 0,690 vs 0,6983 mesurée ; AUC 0,76 → 76,7 % de journées gagnantes ; break-even théorique
48 bp ; Sharpe × vol = rendement annuel ; AUC inversée = 1 − AUC.
