# Analyse détaillée du notebook `04_EDA_sentiment_2020_2022.ipynb`

> Document de travail — PFE Finance Actuarielle
> Objet : audit cellule par cellule de l'EDA, correction de 3 bugs, et cadrage des notebooks 05 à 09.

---

## 0. Verdict en 6 lignes

Ton EDA est **bonne**. Elle démontre proprement le point central du mémoire : le sentiment nocturne
prédit le **gap d'ouverture** et ne prédit **pas** la séance.

Mais il y a **3 bugs** qui, si un jury les repère, coûtent cher :

1. Un **bug de tri** qui fait apparaître des corrélations **négatives** par ticker (`ρ = -0.5`) alors que
   la vraie valeur est **+0.9 à +1.0**. C'est le plus grave : ton propre notebook a l'air de contredire ta conclusion.
2. Une **p-value fantaisiste** (`p = 1.4e-24` sur 5 points) qu'il faut supprimer.
3. Un tableau de corrélations qui **mélange du prédictif et du contemporain** sans le dire — c'est de la
   fuite d'information déguisée (`mu_mkt → ret_oc = 0.208` n'est **pas** un signal exploitable).

Et il manque **2 choses** avant de modéliser : la normalisation par ticker, et le découpage train/test temporel.

---

# PARTIE 1 — LECTURE CELLULE PAR CELLULE

---

## Cellule 1 — Imports

```python
import pandas as pd, numpy as np, matplotlib.pyplot as plt
from scipy import stats
plt.style.use('seaborn-v0_8-whitegrid')
```

**Ce que ça fait :** rien de statistique, juste le décor.

**Remarque :** `warnings.filterwarnings('ignore')` est pratique pendant le développement mais
**dangereux** dans un mémoire. Pandas t'avertit quand une opération est ambiguë (ex. `SettingWithCopyWarning`).
En les masquant, tu perds le seul mécanisme qui te dirait « attention, tu écris dans une copie, ta
modification est perdue ». Garde-le pour la version finale propre, retire-le pendant que tu débugges.

---

## Cellule 2 — Chargement du panel

```
Shape : (2740, 76)
Tickers : AAPL AMZN META NVDA TSLA
Période : 2020-01-02 → 2022-03-04
548 jours par ticker
```

**Ce que ça veut dire concrètement.**

Tu as un tableau **panel** : chaque ligne = un couple (une action, un jour de bourse).
5 actions × 548 jours = 2 740 lignes. C'est bien : NVDA est maintenant présent (le problème de prix
manquants a été réglé), et les 5 tickers ont **exactement** le même nombre de jours, donc le panel est
**équilibré** (balanced panel). C'est important : ça veut dire qu'aucun ticker ne va peser plus lourd
qu'un autre dans les statistiques poolées.

**548 jours ouvrés**, ça fait environ **2 ans et 2 mois** de bourse (≈ 252 jours ouvrés par an).

**Le point de vigilance n° 1 pour ton jury :** 2 740 lignes, c'est **petit** pour du machine learning.
Et surtout, ces lignes ne sont pas indépendantes : les 5 tickers bougent ensemble le même jour (ils sont
tous tech, tous dans le Nasdaq). Ton **nombre effectif d'observations** est donc plus proche de
**548 que de 2 740**. Retiens ce chiffre : il conditionne tout le reste (il interdit les réseaux de
neurones profonds, il impose la validation walk-forward, et il rend les intervalles de confiance larges).

---

## Cellule 3 — Statistiques descriptives

```
                        AAPL      AMZN      META      NVDA      TSLA
gap           mean    0.00066   0.00124  -0.00025   0.00219   0.00402
              std     0.01540   0.01417   0.01872   0.01926   0.02978
ret_oc        mean    0.00107  -0.00017   0.00056   0.00084   0.00129
              std     0.01704   0.01687   0.01827   0.02674   0.03627
mu_night_full mean    0.09338   0.11572   0.11163   0.16001   0.04444
              std     0.04235   0.04947   0.06803   0.07873   0.03230
n_night_full  mean     703.5     318.7     198.5     169.8    1474.4
              std      642.1     534.5     603.2    1449.8    1449.8
```

Ce tableau est **le plus riche du notebook**. Prenons-le ligne par ligne.

### 3.1 — `gap` : le saut de la nuit

Le **gap** est le rendement entre la clôture de la veille et l'ouverture du jour :

```
gap_t = (Open_t / Close_{t-1}) - 1
```

C'est le mouvement de prix qui se produit **pendant que le marché est fermé**. Personne ne peut trader
dessus au moment où il se forme : il « apparaît » d'un coup à 9h30.

- **Moyenne** : entre −0.03 % (META) et +0.40 % (TSLA) par nuit. TSLA gagne **0.4 % chaque nuit en moyenne**
  sur la période — c'est énorme, c'est la bulle Tesla 2020.
- **Écart-type** : de 1.4 % (AMZN) à 3.0 % (TSLA). TSLA est **deux fois plus volatile** qu'AAPL sur la nuit.

**Conséquence méthodologique directe :** tu ne peux **pas** mettre les gaps bruts de TSLA et d'AMZN dans
le même modèle sans les normaliser. Un gap de +2 % est un événement banal pour TSLA et un choc majeur pour
AMZN. Un modèle entraîné sur les valeurs brutes va simplement apprendre « TSLA bouge beaucoup » — ce qui
n'a aucune valeur prédictive. → **Il faut standardiser par ticker.** C'est le point n° 1 du notebook 05.

### 3.2 — `ret_oc` : la séance

```
ret_oc_t = (Close_t / Open_t) - 1
```

C'est le rendement **pendant** la séance, de l'ouverture à la clôture. C'est le seul morceau du rendement
sur lequel on peut réellement trader en continu.

Remarque : `std(ret_oc) > std(gap)` pour tous les tickers. La séance bouge plus que la nuit en amplitude
totale — logique, elle dure 6h30 contre quelques heures de pré-marché — mais on va voir qu'elle est
**beaucoup moins prévisible**.

### 3.3 — `mu_night_full` : le sentiment nocturne — **et le piège**

`mu_night_full` = sentiment FinBERT moyen des messages postés entre la clôture de la veille (16h) et
l'ouverture du jour (9h30).

Regarde bien les moyennes :

| Ticker | Sentiment moyen | Écart-type |
|--------|-----------------|------------|
| NVDA   | **0.160**       | 0.079      |
| AMZN   | 0.116           | 0.049      |
| META   | 0.112           | 0.068      |
| AAPL   | 0.093           | 0.042      |
| TSLA   | **0.044**       | 0.032      |

**NVDA a un sentiment moyen presque 4× supérieur à TSLA.**

Est-ce que ça veut dire que la foule aime 4× plus NVDA que TSLA ? **Non.** Ça veut dire que la *manière
d'écrire* diffère selon la communauté. Les tweets TSLA sont plus polémiques, plus chargés en vocabulaire
que FinBERT classe en négatif ou en neutre ; les tweets NVDA sont plus « techniques/enthousiastes ».
C'est un **biais de niveau propre au ticker**, pas un signal.

**Conséquence directe et cruciale :** quand la cellule 8 fait des quintiles **poolés** (tous tickers
mélangés), le quintile Q5 (« très positif ») est mécaniquement rempli de jours **NVDA et AMZN**, et le
quintile Q1 (« très négatif ») de jours **TSLA**. Le résultat poolé mélange donc deux choses :

- un vrai effet *temporel* (« quand le sentiment de NVDA est haut **pour NVDA**, NVDA gappe up »),
- et un artefact *transversal* (« NVDA a un sentiment haut et NVDA monte beaucoup en 2020-2021 »).

C'est pour ça que les tableaux **par ticker** de la cellule 8 sont tes vrais résultats, et que le résultat
poolé doit être **recalculé sur des quintiles intra-ticker**. (Corrigé dans le notebook 05.)

### 3.4 — `n_night_full` : la densité de messages — la vraie victoire

| Ticker | Messages/nuit (moyenne) |
|--------|-------------------------|
| TSLA   | 1 474                   |
| AAPL   | 704                     |
| AMZN   | 319                     |
| META   | 198                     |
| NVDA   | 170                     |

**Compare avec ton ancien corpus 2023-2026 : médiane de 2 messages par jour et par ticker.**

Tu es passé de 2 à ~170-1 474. C'est un facteur **×100 à ×700**.

Pourquoi ça change tout : le sentiment moyen d'un jour est une **moyenne d'échantillon**. Son bruit décroît
en `1/√n`. Avec n = 2, ton `mu` était essentiellement du bruit pur : deux tweets au hasard, et ta variable
explicative saute de −1 à +1 sans aucun rapport avec l'opinion du marché. Avec n = 500, l'erreur type de
la moyenne est divisée par ~16 par rapport à n = 2. **C'est la raison n° 1 pour laquelle la phase 5
échouait et pour laquelle elle va marcher maintenant.** C'est un argument à mettre noir sur blanc dans ton
mémoire.

**Attention à un détail :** les écarts-types de `n_night_full` sont **du même ordre que les moyennes**
(TSLA : moyenne 1 474, écart-type 1 450). La distribution est donc **très asymétrique** (log-normale) :
la plupart des nuits sont calmes, quelques nuits explosent (résultats trimestriels, tweets d'Elon Musk,
squeeze). C'est exactement pour ça que tu as construit `nlog_night_full` (log) et `nabn_night_full`
(attention anormale = volume rapporté à sa moyenne mobile). Ces deux variables sont **mieux
conditionnées** que `n` brut et c'est elles qu'il faut donner aux modèles, pas `n`.

---

## Cellule 4 — Histogrammes de densité

Rien à corriger. Cette figure sert **un but rhétorique précis dans ton mémoire** : c'est la preuve visuelle
que le corpus 2020-2022 est exploitable là où le corpus 2023-2026 ne l'était pas.

**Suggestion :** ajoute `axes[i].set_xscale('log')`. Avec une distribution aussi asymétrique, l'histogramme
en échelle linéaire est écrasé contre l'axe des ordonnées et on ne voit rien de la structure.

---

## Cellule 5 — Prix vs sentiment (double axe)

Figure descriptive, correcte.

**Piège à connaître (et à ne pas commettre à l'oral) :** superposer un **prix** (variable en niveau, qui
tendance) et un **sentiment** (variable stationnaire, centrée) donne toujours une impression de lien fort
qui n'existe pas statistiquement. Deux séries qui montent ensemble sont corrélées même sans relation
causale (corrélation fallacieuse / *spurious regression*, Granger & Newbold 1974).

**Correction recommandée :** trace le **rendement cumulé** ou le prix en log, et mets en face le
**sentiment lissé** (moyenne mobile 5 jours). Ou mieux : superpose le sentiment au **gap cumulé**, puisque
c'est ça que tu prétends prédire.

---

## Cellule 6 — Corrélations par fenêtre — **LA CELLULE À CORRIGER EN PRIORITÉ**

```
Fenêtre            gap    ret_oc   ret_cc
mu_mkt          0.0672   0.2081   0.2025
mu_night_full   0.1651  -0.0100   0.0986
mu_open30       0.0623   0.1021   0.1186
mu_overnight    0.1010  -0.0296   0.0426
mu_post         0.0626   0.1699   0.1703
mu_pre          0.1816   0.0128   0.1265
```

Ce tableau contient à la fois **ton meilleur résultat** et **ton plus gros piège**. Il faut absolument
séparer les deux.

### 6.1 — La règle : une corrélation n'est un signal que si la cause précède l'effet

Pour chaque case, pose-toi une seule question : **au moment où la fenêtre de texte se ferme, la cible
est-elle déjà connue ou pas encore ?**

| Fenêtre | Se ferme à | `gap` (formé à 9h30) | `ret_oc` (formé 9h30→16h) | `ret_cc` (veille 16h → 16h) |
|---------|-----------|----------------------|---------------------------|------------------------------|
| `mu_overnight` (16h→minuit) | minuit | ✅ **prédictif** | ✅ prédictif | ✅ prédictif |
| `mu_pre` (minuit→9h30) | 9h30 | ✅ **prédictif** (limite) | ✅ prédictif | ✅ prédictif |
| `mu_night_full` (= overnight + pre) | 9h30 | ✅ **prédictif** | ✅ prédictif | ✅ prédictif |
| `mu_open30` (9h30→10h) | 10h | ❌ gap déjà passé | ⚠️ **contemporain** | ⚠️ contemporain |
| `mu_mkt` (10h→16h) | 16h | ❌ | ❌ **contemporain** | ❌ contemporain |
| `mu_post` (16h→minuit) | minuit du jour J | ❌ | ❌ **postérieur** | ❌ postérieur |

### 6.2 — Ce qu'il faut donc lire

**Les 3 chiffres qui comptent (colonne `gap`, lignes prédictives) :**

- `mu_pre → gap` : **ρ = +0.182**
- `mu_night_full → gap` : **ρ = +0.165**
- `mu_overnight → gap` : **ρ = +0.101**

Interprétation : plus on **approche** de l'ouverture, plus le sentiment est informatif. `mu_pre` (les
messages postés entre minuit et 9h30) bat `mu_overnight` (16h → minuit) : logique, l'information la plus
fraîche est la plus pertinente. C'est un **résultat de microstructure** cohérent avec la littérature
(Tetlock 2007, Bollen et al. 2011) et c'est un très bon paragraphe de mémoire.

**Les 3 chiffres qu'il ne faut SURTOUT PAS présenter comme un signal :**

- `mu_mkt → ret_oc = +0.208` ← le plus élevé du tableau, et **le plus inutile**
- `mu_post → ret_cc = +0.170`
- `mu_post → ret_oc = +0.170`

Pourquoi ils sont inutiles : `mu_mkt` agrège les messages **de 10h à 16h**, c'est-à-dire **pendant** que
`ret_oc` se forme. La corrélation dit simplement : *« quand le prix monte pendant la séance, les gens
tweetent positivement pendant la séance »*. C'est une **réaction**, pas une **prédiction**. Pour
l'exploiter, il te faudrait connaître les tweets de 16h à 15h59 — impossible.

`mu_post` est encore pire : il agrège des messages postés **après** la clôture, donc **après** que
`ret_oc` et `ret_cc` soient définitivement fixés. La causalité va franchement à l'envers.

> **À écrire textuellement dans ton mémoire :**
> « Les corrélations les plus fortes du tableau (μ_mkt→ret_oc = 0.208 ; μ_post→ret_cc = 0.170) sont
> contemporaines ou postérieures à la formation du rendement. Elles mesurent la réaction du sentiment au
> prix et non l'inverse ; elles ne constituent pas un signal exploitable et sont exclues de l'espace de
> features. Seules les fenêtres se clôturant avant 9h30 sont retenues. »

Ce paragraphe-là vaut des points. Il montre que tu as compris la différence entre corrélation et
prédictibilité, ce que 80 % des mémoires sur le sentiment ratent.

### 6.3 — Deux défauts techniques de la cellule

**a) Il manque le test par ticker.** La corrélation poolée mélange l'effet transversal (niveaux différents
par ticker) et l'effet temporel. Il faut calculer ρ **par ticker** puis rapporter la moyenne et la
dispersion.

**b) La p-value de Pearson est fausse ici.** `stats.pearsonr` suppose des observations **i.i.d.**. Tes
observations sont autocorrélées (le sentiment est persistant d'un jour à l'autre) et corrélées en coupe
(les 5 tickers bougent ensemble). La vraie p-value est donc **beaucoup plus grande** que celle affichée.
→ Il faut un **bootstrap par blocs** (on rééchantillonne des blocs de ~20 jours consécutifs plutôt que
des jours isolés). C'est implémenté dans le notebook 05.

---

## Cellule 7 — Heatmap de corrélation

Correcte et utile, mais elle sert **deux buts** qu'il faut expliciter dans le mémoire :

1. **Voir le signal** (colonne `gap`).
2. **Détecter la multicolinéarité entre features.** Regarde le bloc `mu_night_full` / `mu_pre` /
   `mu_overnight` : par construction `night_full = overnight + pre`, donc ces trois variables sont
   fortement corrélées entre elles. Si tu les mets **toutes les trois** dans une régression logistique,
   les coefficients deviennent instables et ininterprétables (variance gonflée).

**Règle à appliquer au notebook 06 :** soit tu gardes `mu_night_full` seul (agrégé), soit tu gardes
`mu_overnight` + `mu_pre` (décomposé), **jamais les trois**. Et tu vérifies avec un **VIF**
(Variance Inflation Factor) : au-dessus de 5, tu retires.

---

## Cellule 8 — Quintiles — **le cœur du mémoire**

### 8.1 — Résultat poolé

```
quintile    n   gap_moyen  %gap_pos  seance_moy  %seance_pos  cc_moyen
Q1        548     -0.51 %    42.2 %     +0.20 %      53.1 %    -0.32 %
Q2        547     +0.27 %    55.9 %     +0.10 %      50.1 %    +0.36 %
Q3        547     +0.28 %    62.9 %     -0.06 %      47.7 %    +0.23 %
Q4        547     +0.23 %    63.1 %     +0.01 %      51.0 %    +0.24 %
Q5        547     +0.52 %    70.4 %     +0.11 %      50.8 %    +0.63 %
```

**Comment lire ça, en français simple.**

On trie les 2 740 jours du plus négatif au plus positif en sentiment nocturne, on les coupe en 5 paquets
égaux, et on regarde ce que le marché a fait.

- **Colonne `%gap_pos`** : dans le paquet le plus négatif, seulement **42.2 %** des jours ont ouvert en
  hausse. Dans le paquet le plus positif, **70.4 %**. **Écart = 28.2 points.**
  C'est **massif**. À titre de comparaison : la plupart des signaux publiés en finance quantitative sur
  données journalières se battent pour 2 à 4 points d'écart.
- **Colonne `%seance_pos`** : 53.1 %, 50.1 %, 47.7 %, 51.0 %, 50.8 %. **Aucune structure.** Ça oscille
  autour de 50 % sans direction. C'est exactement ce qu'on attend d'un pile ou face.

**Ces deux colonnes côte à côte SONT ton mémoire.** La même variable explicative, les mêmes jours, deux
cibles différentes : l'une est prévisible, l'autre non. Ce n'est pas un échec, c'est un **résultat**, et
il a un nom en théorie financière : **l'efficience semi-forte de Fama (1970)**. L'information publique
(les tweets de la nuit) est **incorporée dans le prix à l'ouverture**, en une seule fois, et il n'en reste
rien pour la séance.

### 8.2 — La monotonie n'est pas parfaite, et il faut le dire

Regarde `gap_moyen` : −0.51 %, puis +0.27 %, +0.28 %, +0.23 %, +0.52 %.
Q2, Q3, Q4 sont quasi **plats**. Le signal n'est pas linéaire : il vient presque entièrement des
**extrêmes**, surtout de Q1.

**C'est une information capitale pour la modélisation, pas un défaut.** Elle te dit deux choses :

1. Un modèle **linéaire** (régression logistique sur `mu` brut) va sous-performer parce que la relation
   n'est pas linéaire. → Les **arbres** (Random Forest, XGBoost) sont mieux adaptés, ou il faut donner le
   **rang/quintile** comme feature plutôt que la valeur brute.
2. Une stratégie de trading ne doit **pas** trader tous les jours. Elle doit trader **uniquement Q1 et
   Q5** et rester neutre au milieu. C'est le design du backtest du notebook 08.

**Et surtout : l'asymétrie.** Q1 (sentiment très négatif) donne −0.51 % de gap moyen, Q5 donne +0.52 %.
Mais la moyenne inconditionnelle de tous les jours est **positive** (marché haussier 2020-2021). Donc
**relativement à la moyenne**, le signal négatif est **beaucoup plus fort** que le signal positif. Le
pessimisme nocturne informe plus que l'optimisme. C'est cohérent avec la littérature sur l'asymétrie des
mauvaises nouvelles (Hong & Stein 1999) → excellent point de discussion.

### 8.3 — Le tableau par ticker : ton vrai test de robustesse

En triant proprement (voir bug §9 ci-dessous), voici ce que donne `% Gap positif` de Q1 à Q5 :

| Ticker | Q1 | Q2 | Q3 | Q4 | Q5 | Écart Q5−Q1 |
|--------|----|----|----|----|----|-------------|
| AAPL   | 31.8 | 50.5 | 64.5 | 64.2 | 72.7 | **+40.9 pts** |
| AMZN   | 40.0 | 58.7 | 69.1 | 63.3 | 71.8 | **+31.8 pts** |
| META   | 40.0 | 56.9 | 55.5 | 57.8 | 65.5 | **+25.5 pts** |
| NVDA   | 46.4 | 49.5 | 67.0 | 69.7 | 74.5 | **+28.1 pts** |
| TSLA   | 38.5 | 47.7 | 65.1 | 70.6 | 80.7 | **+42.2 pts** |

**Les 5 tickers vont dans le même sens, sans exception.** C'est bien plus convaincant que le chiffre poolé,
parce que ça exclut l'explication « c'est juste un artefact de mélange entre tickers ». Ce tableau doit
être **dans ton mémoire**, poolé ou pas.

### 8.4 — Petit bug cosmétique

Les lignes `NVDA / NaN / n=0` et `TSLA / NaN / n=0` viennent de `sub['quintile'].unique()` qui, sur une
variable catégorielle avec des `NaN` (jours sans message nocturne), renvoie aussi `NaN`. Corrigé en
ajoutant `.dropna()`.

---

## Cellule 9 — Test de Spearman — **BUG MAJEUR**

### Ce que ton notebook affiche

```
Spearman (quintile vs % gap positif) : rho = 1.000, p = 1.4043e-24
Par ticker :
  AAPL: rho = -0.500
  AMZN: rho = -0.100
  META: rho = -0.200
  NVDA: rho = -0.500
  TSLA: rho = -0.700
```

**Tel quel, ce résultat détruit ta conclusion.** Un lecteur lit : « effet global positif parfait, mais
effet négatif sur les 5 actions individuelles ». C'est le paradoxe de Simpson dans sa version la plus
suspecte — un jury va immédiatement penser que ton résultat poolé est un artefact.

### Or c'est faux. Voici le bug.

Dans la cellule 8 tu construis `quintile_df` avec :

```python
for q in sub['quintile'].unique():      # ← ORDRE D'APPARITION, PAS ORDRE Q1→Q5
```

`.unique()` sur une série renvoie les valeurs **dans l'ordre où elles apparaissent dans les données**, pas
dans l'ordre logique des catégories. Pour AAPL, l'ordre obtenu est **Q5, Q2, Q3, Q1, Q4**.

Ensuite, en cellule 9, tu fais :

```python
spearmanr([1, 2, 3, 4, 5], sub_t['% Gap positif'].values)
```

Tu compares donc le vecteur `[1,2,3,4,5]` (qui suppose l'ordre Q1→Q5) au vecteur
`[72.7, 50.5, 64.5, 31.8, 64.2]` (qui est dans l'ordre Q5,Q2,Q3,Q1,Q4). **Tu compares des choux et des
carottes.** D'où le −0.5.

### Le vrai résultat, une fois trié

```
AAPL : rho = +0.900   (p = 0.037)
AMZN : rho = +0.900   (p = 0.037)
META : rho = +0.900   (p = 0.037)
NVDA : rho = +1.000
TSLA : rho = +1.000
```

**Les 5 tickers sont entre +0.90 et +1.00.** Ta conclusion n'est pas seulement sauvée, elle est
**renforcée** : l'effet est monotone croissant sur les 5 actions prises séparément.

### Le correctif (une ligne)

```python
ORDRE = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']
sub_t = (quintile_df[quintile_df['Ticker'] == ticker]
         .dropna(subset=['Quintile'])
         .assign(q=lambda d: d['Quintile'].astype(str).str[:2])
         .set_index('q').reindex(ORDRE))          # ← LE TRI EXPLICITE
rho_t, p_t = spearmanr([1, 2, 3, 4, 5], sub_t['% Gap positif'].values)
```

**Le même bug affecte le graphique `ax2` de la cellule 10** (les lignes par ticker sont tracées dans le
désordre, ce qui donne des courbes en zigzag qui ne veulent rien dire). Même correctif.

### Deuxième problème : la p-value `1.4e-24`

Elle est **absurde** et il faut la supprimer. Avec **n = 5 points**, le nombre de permutations possibles
est 5! = 120. La plus petite p-value atteignable par un test exact est donc **1/120 ≈ 0.0083**. Une
p-value de 10⁻²⁴ est mathématiquement impossible : elle vient du fait que scipy utilise une approximation
en t de Student, et quand ρ = 1 exactement, la statistique t = ρ·√((n−2)/(1−ρ²)) **explose à l'infini**
(division par zéro).

**De toute façon, ce test n'a pas de sens ici** : il teste la monotonie de 5 moyennes **déjà agrégées**,
en traitant les quintiles comme 5 observations indépendantes. Il ignore complètement les 2 740
observations sous-jacentes.

**Ce qu'il faut faire à la place :** une **régression sur le rang**, ou plus simplement le test de
Jonckheere-Terpstra, ou — le plus lisible pour un mémoire — un **test de différence de proportions entre
Q1 et Q5** :

```python
from statsmodels.stats.proportion import proportions_ztest
succ  = [nb_gaps_positifs_Q5, nb_gaps_positifs_Q1]
nobs  = [n_Q5, n_Q1]
z, p = proportions_ztest(succ, nobs)     # sur ~1100 observations réelles, pas 5
```

Avec 70.4 % contre 42.2 % sur ~547 observations chacun, ce test sera écrasant (z ≈ 9-10, p < 10⁻¹⁸) et,
lui, il sera **honnête**.

---

## Cellule 10 — Graphique des quintiles

Le graphe de gauche (poolé) est excellent, c'est **la figure principale de ton mémoire**. Le contraste
visuel bleu (gap) / corail (séance) raconte l'histoire sans un mot.

Le graphe de droite souffre du **même bug de tri** que la cellule 9.

**Trois améliorations pour la figure de gauche :**
1. Ajouter les **intervalles de confiance à 95 %** sur chaque barre (`yerr = 1.96·√(p(1−p)/n)`). Avec
   n ≈ 547, l'IC fait environ ±4 points — ce qui montre que l'écart de 28 points est bien au-delà du bruit.
2. Annoter la ligne des 50 % avec le texte « hasard ».
3. Titrer explicitement : « Le sentiment nocturne prédit le gap, pas la séance ».

---

## Cellule 11 — Nuages de points

Bonne figure de robustesse (elle montre que la corrélation n'est pas due à quelques points aberrants).

**Deux améliorations :**
- Trace aussi une **régression robuste** (Huber ou quantile) en plus de `np.polyfit`, pour montrer que le
  résultat ne dépend pas des outliers.
- Ajoute la **moyenne de `gap` par décile de sentiment** en points rouges par-dessus le nuage : c'est
  beaucoup plus lisible qu'une droite au milieu de 548 points.

---

## Cellule 12 — Effet des lags — **excellente idée, à mieux exploiter**

Tu testes `mu_night_full` décalé de 1, 2, 3, 5 jours contre les cibles du jour J. Le titre de la figure
dit : *« Le signal est contemporain (Lag 0) — il disparaît aux lags suivants »*.

**Pourquoi c'est le test le plus important du notebook.**

C'est ta **preuve d'absence de fuite de données**. Voilà le raisonnement :

- Si le signal était un artefact statistique (surajustement, corrélation fallacieuse, tendance commune),
  il persisterait aux lags 1, 2, 3, 5 — parce qu'une tendance commune ne disparaît pas en un jour.
- Si le signal est une **vraie information incorporée immédiatement**, il doit être **fort au lag 0 et
  nul dès le lag 1** — parce qu'un marché efficient ne laisse pas traîner une information exploitable
  pendant 24 h.

Ton résultat (fort à lag 0, nul ensuite) est donc **exactement la signature d'un marché semi-efficient**.
C'est un argument très fort, et il faut le formuler comme ça dans le mémoire.

**Précision de vocabulaire importante :** « lag 0 » chez toi n'est **pas** contemporain au sens de la
fuite. `mu_night_full` du jour J se ferme à 9h30 et `gap` du jour J se forme à 9h30. La relation est
« juste avant → juste après ». Ce n'est pas de la fuite, c'est de la prédiction à très court horizon.
**Écris-le explicitement**, sinon un lecteur pressé va croire à un problème.

**Amélioration à faire :** ajoute des lags **négatifs** (le sentiment de J+1 contre le gap de J).
Si ρ(J+1 → gap_J) est **aussi grand** que ρ(J → gap_J), tu as un problème de construction de fenêtres
(désalignement de timezone, par exemple). Si c'est ~0, ta construction est validée. C'est un test de
falsification en 4 lignes et il rassure énormément un jury.

---

## Cellule 13 — Régimes de marché — **définitions à corriger**

```python
if date <= '2020-03-23':   return 'COVID Crash (jan-mar 2020)'
elif date <= '2021-01-28': return 'Rallye Liquidity (avr 2020 - jan 2021)'
elif date <= '2021-02-28': return 'Meme Stocks (jan 2021)'
else:                      return 'Bear Market (2022)'
```

**Trois problèmes.**

1. **Le régime « Meme Stocks » est mal daté.** La cascade `if/elif` fait que ce régime couvre en réalité
   **du 29 janvier au 28 février 2021**, alors que le squeeze GameStop a eu lieu **du 22 au 28 janvier
   2021** — donc entièrement dans le régime précédent. Le label « (jan 2021) » ment sur son propre contenu.
   Et 1 mois × 5 tickers = ~100 lignes : c'est trop peu pour une corrélation stable de toute façon.

2. **Le régime « Bear Market (2022) » couvre de mars 2021 à mars 2022.** Or mars-décembre 2021 était un
   marché **haussier** (le S&P a fait +27 % en 2021). Tu appelles « bear market » une période dont 10 mois
   sur 12 sont haussiers. Un jury qui connaît les marchés va tiquer immédiatement.

3. **Les régimes sont définis *ex post*, sur des dates que tu connais.** C'est acceptable pour une analyse
   descriptive, mais il faut l'écrire : « les régimes sont définis ex post à des fins descriptives ; ils
   ne sont pas utilisés comme variable explicative dans les modèles » — sinon c'est de la fuite.

**Découpage proposé (plus défendable) :**

| Régime | Période | Justification |
|--------|---------|---------------|
| Krach COVID | 2020-01-02 → 2020-03-23 | jusqu'au plus bas du S&P 500 |
| Reprise / liquidité | 2020-03-24 → 2020-12-31 | QE massif, rebond en V |
| Euphorie retail | 2021-01-01 → 2021-06-30 | meme stocks, pic de participation retail |
| Plateau / rotation | 2021-07-01 → 2021-12-31 | fin du rallye, rotation sectorielle |
| Resserrement | 2022-01-01 → 2022-03-04 | pivot Fed, début de correction |

Et surtout : **ne calcule pas une corrélation sur moins de ~60 observations par groupe**. En dessous,
l'intervalle de confiance sur ρ est tellement large que le chiffre ne veut rien dire. Ajoute une colonne
`IC 95 %` (transformation de Fisher) pour le montrer.

---

## Cellule 14 — Attention anormale vs amplitude — **la piste la plus prometteuse**

Tu croises `nabn_night_full` (volume de messages anormal) avec `|gap|` et avec l'amplitude
`(High − Low)/Open`.

**C'est le début du modèle M3 (risque), et c'est probablement le meilleur résultat que tu vas obtenir.**

Le raisonnement, en une phrase : **prédire la direction est difficile (le marché est efficient sur la
direction), prédire l'amplitude est beaucoup plus facile (la volatilité est fortement persistante et
réagit à l'attention).**

C'est un fait empirique bien établi : la volatilité se prédit (modèles GARCH, R² de 0.3 à 0.6), le signe
du rendement ne se prédit presque pas (R² de 0.001 à 0.01). Et un pic d'attention sociale est un
**prédicteur avancé de volatilité** documenté dans la littérature (Da, Engelberg & Gao 2011 sur Google
Trends ; Antweiler & Frank 2004 sur les forums boursiers).

**Améliorations :**
- Passe en **log-log** ou en **rangs** : `nabn` et `|gap|` sont tous les deux très asymétriques, une
  corrélation de Pearson dessus est dominée par quelques points extrêmes. Utilise **Spearman**.
- Ajoute la **vraie cible** du modèle M3 : `amplitude_{t}` prédite par `nabn_{t}` **et**
  `amplitude_{t-1}` (le prédicteur de référence). La question qui compte n'est pas « nabn corrèle-t-il
  avec la volatilité ? » (oui, trivialement) mais **« nabn apporte-t-il quelque chose EN PLUS de la
  volatilité de la veille ? »**. C'est un test d'**incrément de R²**, et c'est ça qui fait un résultat
  publiable.

---

## Cellule 15 — Résumé

Bon résumé. Deux ajouts :

- Reporte le nombre d'observations et un **intervalle de confiance** sur chaque ρ.
- Ajoute la phrase clé : *« l'absence de prédictibilité de la séance est un résultat, pas un échec :
  elle est cohérente avec l'efficience semi-forte au sens de Fama (1970) »*.

---

# PARTIE 2 — CE QU'IL FAUT AJOUTER AVANT DE MODÉLISER

Deux manques bloquants avant le notebook 06.

## Manque 1 — La normalisation par ticker

Vu au §3.3 : `mu_night_full` vaut 0.16 en moyenne pour NVDA et 0.044 pour TSLA. Un modèle entraîné sur les
valeurs brutes apprend l'identité du ticker, pas le signal.

**Solution : le z-score glissant intra-ticker.**

```python
def zscore_glissant(s, fenetre=60, minp=20):
    mu = s.rolling(fenetre, min_periods=minp).mean().shift(1)   # shift(1) = ANTI-FUITE
    sd = s.rolling(fenetre, min_periods=minp).std().shift(1)
    return (s - mu) / sd.replace(0, np.nan)

df['z_mu_night'] = df.groupby('Ticker')['mu_night_full'].transform(zscore_glissant)
```

Le `.shift(1)` est **essentiel** : sans lui, la moyenne mobile du jour J inclut la valeur du jour J
elle-même, et tu utilises de l'information du futur pour normaliser. C'est la fuite la plus fréquente et
la plus sournoise en finance quantitative.

**Interprétation :** `z_mu_night = +2` ne veut plus dire « sentiment positif dans l'absolu » mais
**« sentiment anormalement positif pour cette action, comparé à ses 60 derniers jours »**. C'est ça, le
vrai signal.

## Manque 2 — Le découpage temporel

Il n'y a nulle part dans le notebook 04 de séparation train/test. Avant tout modèle, il faut :

```
Train      : 2020-01-02 → 2021-06-30   (~370 jours)
Validation : 2021-07-01 → 2021-11-30   (~105 jours)
Test       : 2021-12-01 → 2022-03-04   (~65 jours, JAMAIS TOUCHÉ)
```

**Règles non négociables :**
- Découpage **par date**, jamais aléatoire (`train_test_split(shuffle=True)` est une faute grave sur des
  séries temporelles : ça met des jours futurs dans le train).
- Le test est **verrouillé** : on ne le regarde qu'**une seule fois**, à la toute fin. Chaque coup d'œil
  supplémentaire est du surajustement déguisé.
- Tous les paramètres estimés (moyennes de normalisation, seuils, hyperparamètres) le sont **uniquement**
  sur le train.

---

# PARTIE 3 — LES NOTEBOOKS RESTANTS

| Notebook | Titre | Question à laquelle il répond |
|----------|-------|-------------------------------|
| **04bis** | Corrections de l'EDA | Les 3 bugs sont-ils corrigés ? |
| **05** | Features & split anti-fuite | Quelles variables, normalisées comment, découpées comment ? |
| **06** | Modèle M1 — direction du gap | Peut-on prédire le **signe** du gap ? *(oui — c'est le résultat principal)* |
| **07** | Modèles M2 (séance) & M3 (risque) | La séance est-elle imprévisible ? *(oui — résultat d'efficience)* L'attention prédit-elle la volatilité ? *(oui — meilleur R²)* |
| **08** | Backtest avec coûts | Le signal survit-il aux frais de transaction ? *(c'est là que ça se joue)* |
| **09** | Synthèse | Que retenir, et quelles limites ? |

Ces notebooks sont fournis, entièrement commentés en français, dans le dossier `notebooks/`.

---

## Le point le plus important de tout ce document

Ton mémoire ne doit **pas** être présenté comme « j'ai construit un modèle qui bat le marché ».
Il doit être présenté comme :

> **« J'ai testé si le sentiment social prédit le prix. La réponse est : oui pour le gap d'ouverture
> (ρ = 0.17, écart de 28 points entre quintiles extrêmes, effet monotone sur les 5 actions), non pour la
> séance (ρ = −0.01). Cette asymétrie n'est pas un échec : c'est une confirmation empirique de
> l'efficience semi-forte de Fama. Et une fois les coûts de transaction intégrés, la fraction du gap
> réellement capturable est [résultat du notebook 08]. »**

Un résultat négatif bien démontré vaut plus qu'un résultat positif mal contrôlé. C'est ce qui distingue
un mémoire de recherche d'un projet de data science.
