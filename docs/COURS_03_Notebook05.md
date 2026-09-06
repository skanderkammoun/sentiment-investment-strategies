# Cours 3 — Notebook 05 : les variables et le découpage anti-fuite

**Le notebook le plus important du mémoire — celui qui décide si tes résultats sont vrais**

*Cours détaillé, chapitre par chapitre. Chaque transformation : la notion, la formule, la valeur ajoutée
mesurée. Chaque test : ce qu'il prouve, et pourquoi il est construit ainsi.*

---

## Table des matières

| # | Chapitre | Notion enseignée |
|---|---|---|
| 0 | Pourquoi ce notebook est le plus important | taxonomie des fuites |
| 1 | L'inventaire et les valeurs manquantes | lire un tableau de NaN |
| 2 | La liste blanche codée | règle exécutable |
| 3 | Le z-score glissant | **standardisation causale** ⭐ |
| 4 | Le rang percentile | transformation robuste |
| 5 | Les variables de contrôle | **variable de confusion** ⭐ |
| 6 | Les cibles dérivées | gap en excès, zone morte |
| 7 | Le découpage temporel | **train / valid / test** ⭐ |
| 8 | Le purge et le walk-forward | embargo, fenêtre extensible |
| 9 | T1 — la corrélation anormale | contrôle de bon sens |
| 10 | T2 — l'ordre chronologique | contrôle structurel |
| 11 | T3 — le sentiment futur | falsification |
| 12 | T4 — le test placebo | **contrôle négatif** ⭐ |
| 13 | L'export et la reproductibilité | source unique de vérité |
| 14 | Trois points à corriger | esprit critique |
| 15 | Récapitulatif | les 12 idées à retenir |

---

# Chapitre 0 — Pourquoi ce notebook est le plus important

## 0.1 — L'asymétrie fondamentale

Voici la phrase à comprendre avant tout le reste :

> **Un modèle mal réglé donne un mauvais résultat — qu'on voit, et qu'on corrige.
> Une fuite d'information donne un excellent résultat — qu'on ne voit pas.**

C'est une asymétrie brutale :

| Type d'erreur | Symptôme | Détection |
|---|---|---|
| Mauvais hyperparamètres | AUC = 0,52 | immédiate, on corrige |
| Modèle inadapté | AUC = 0,51 | immédiate |
| **Fuite d'information** | **AUC = 0,85** | **aucune — on est content** |

Une fuite ne provoque **aucune erreur**. Le code tourne, les graphiques sont beaux, les chiffres sont
excellents. On rédige, on soutient — et un membre du jury pose la bonne question.

**D'où la stratégie de ce notebook :** rendre la fuite **impossible par construction**, puis le **prouver**
par quatre tests automatiques.

## 0.2 — La taxonomie des fuites

Il en existe plusieurs types. Les connaître, c'est savoir où regarder.

### Type 1 — Fuite de cible (*target leakage*)

Une variable explicative contient, directement ou indirectement, la réponse.

> **Exemple médical classique.** On prédit si un patient a un cancer. Parmi les variables : « le patient
> a-t-il reçu une chimiothérapie ? ». Le modèle atteint 99 % — et il est inutile, car on ne prescrit une
> chimiothérapie qu'**après** le diagnostic.

**Ici :** mettre `Close` du jour J pour prédire `ret_oc` du jour J. C'est le rôle du test **T1**.

### Type 2 — Fuite temporelle (*look-ahead bias*)

On utilise de l'information qui n'existait pas encore au moment de la décision.

**Ici :** trois sources possibles —
- les fenêtres `mkt` et `post` du jour J (réglé par la liste blanche, ch. 2) ;
- une moyenne mobile non décalée (réglé par le `.shift(1)`, ch. 3) ;
- un découpage aléatoire au lieu de chronologique (réglé au ch. 7, testé par **T2**).

### Type 3 — Fuite de prétraitement (*preprocessing leakage*)

La plus vicieuse : on normalise, on impute ou on sélectionne des variables **sur l'ensemble des données**,
avant de découper.

> **Exemple.** Tu standardises toutes tes variables avec la moyenne calculée sur 2020-2022, puis tu
> découpes. La moyenne du train contient alors de l'information de 2022. La fuite est minuscule mais
> réelle, et elle gonfle systématiquement les performances.

**Ici :** réglé par le z-score **glissant** (ch. 3), qui ne regarde que le passé à chaque date.

### Type 4 — Fuite par contamination de groupe

Deux observations du même « groupe » se retrouvent l'une dans le train et l'autre dans le test.

**Ici :** deux jours consécutifs partagent 59 des 60 jours de leur fenêtre de normalisation. C'est le rôle
du **purge** (ch. 8).

---

# Chapitre 1 — L'inventaire et les valeurs manquantes

```
Dimensions : 2,740 lignes x 81 colonnes
Période    : 2020-01-02 -> 2022-03-04

Valeurs manquantes :
y_gap_net          382
mu_night_z20       106
nabn_night_full     50
nabn_open30         50
nabn_mkt            50
nabn_post           50
sd_open30           25
mu_open30           13   (et p10, p90, pos, neg, disp : 13 aussi)
sd_post_lag1        11
mu_post_lag1        10
dmu_night           10
mu_mkt_lag1          8
sd_post              8
mu_post              7
```

## 1.1 — Pourquoi regarder les NaN en premier

**Un tableau de valeurs manquantes est un diagnostic.** Chaque nombre raconte quelque chose sur la
construction des données. Si un chiffre ne s'explique pas, il y a un problème.

## 1.2 — Décoder chaque ligne

| Colonne | NaN | Explication |
|---|---|---|
| `y_gap_net` | **382** | volontaire : les gaps dans la zone morte de ±15 bp sont neutralisés (13,9 %) |
| `mu_night_z20` | **106** | il faut 20 jours d'historique → ~21 premiers jours × 5 titres |
| `nabn_*` | **50** | il faut 10 jours d'historique (`min_periods=10`) → 10 × 5 titres |
| `sd_open30` | **25** | 25 jours où la fenêtre 9h30-10h contenait 0 ou 1 message |
| `mu_open30` | **13** | 13 jours sans **aucun** message entre 9h30 et 10h |
| `dmu_night` | **10** | une différence a besoin d'un jour précédent → 2 × 5 titres |
| `mu_post` | **7** | 7 soirées sans aucun message après la clôture |

**Tout s'explique.** Aucun NaN n'est inattendu.

## 1.3 — Le raisonnement qui compte

Regarde la relation entre `mu_open30` (13 NaN) et `sd_open30` (25 NaN).

```
mu manquant  ->  0 message           (13 jours)
sd manquant  ->  0 ou 1 message      (25 jours)
```

Il y a donc **12 jours** avec **exactement un** message entre 9h30 et 10h : la moyenne existe (c'est la
valeur de ce message), mais l'écart-type est indéfini — on ne calcule pas une dispersion sur un point.

**Cette cohérence interne est une validation.** Si `sd` avait eu *moins* de NaN que `mu`, il y aurait eu
une erreur quelque part.

## 1.4 — La règle générale

> **Un NaN inexpliqué est un bug jusqu'à preuve du contraire.**
>
> Et un NaN **honnête** vaut toujours mieux qu'une valeur inventée. Remplacer un écart-type indéfini
> par 0 revient à affirmer « la dispersion était nulle » — ce qui est faux, on ne sait pas.

---

# Chapitre 2 — La liste blanche codée

```python
CONNUE_A = {
    "_overnight":   0.0,    # connu à minuit
    "_pre":         9.5,    # connu à l'ouverture
    "_night_full":  9.5,
    "_open30":     10.0,
    "_mkt":        16.0,
    "_post":       24.0,
}
DEBUT_CIBLE = {"gap": 9.5, "ret_oc": 9.5, "ret_cc": 9.5}

def est_legale(col, cible="gap"):
    ...
    return h <= DEBUT_CIBLE[cible]
```

```
LÉGALES pour prédire le gap (24)
INTERDITES (43)
À EXAMINER au cas par cas (14)
```

## 2.1 — La notion : transformer une règle en code

**La règle** : une variable est utilisable si elle est connue avant que la cible ne commence à se former.

**Le problème** : appliquée à la main sur 81 colonnes, cette règle sera mal appliquée. Pas par
incompétence — par fatigue, par distraction, ou parce qu'on ajoute une colonne trois semaines plus tard
sans y repenser.

**La solution** : encoder la règle dans une fonction. Trois avantages :

| Avantage | Pourquoi |
|---|---|
| **Elle ne s'oublie pas** | toute nouvelle colonne est classée automatiquement |
| **Elle est vérifiable** | on peut la relire, la tester, la discuter |
| **Elle est documentable** | le dictionnaire `CONNUE_A` *est* la documentation |

> **C'est un principe général en science des données :** chaque fois qu'une règle méthodologique doit être
> appliquée de façon répétée, il faut l'écrire en code plutôt que la garder en tête. Le code est un
> **contrat** qui survit à la fatigue et au temps.

## 2.2 — Les trois catégories, et pourquoi la troisième existe

```
LÉGALES (24)     : toutes les colonnes _overnight, _pre, _night_full
INTERDITES (43)  : les prix du jour + toutes les colonnes _open30, _mkt, _post
À EXAMINER (14)  : prev_close, vol_20d, dmu_night, mu_night_z20, *_lag1, y_gap_net...
```

La troisième catégorie renvoie `None` — « je ne sais pas ». C'est **volontaire**.

Ces 14 colonnes ne portent pas de suffixe de fenêtre : ce sont des variables dérivées. La fonction ne peut
pas décider seule, elle **signale** qu'un jugement humain est nécessaire.

> **C'est une bonne pratique de conception :** un système automatique doit savoir dire « je ne sais pas »
> plutôt que deviner. En actuariat comme en médecine, un modèle qui signale son incertitude vaut mieux
> qu'un modèle qui tranche toujours.

## 2.3 — Le jugement sur les 14 restantes

| Colonne | Verdict | Raison |
|---|---|---|
| `prev_close`, `prev_volume`, `prev_ret_cc` | ✅ légale | décalées d'un jour |
| `vol_20d` | ✅ légale | fenêtre `.shift(1)` |
| `dmu_night`, `mu_night_ma3`, `mu_night_z20` | ✅ légale | dérivées de `night_full`, connues à 9h30 |
| `*_mkt_lag1`, `*_post_lag1` | ✅ légale | c'est **le but** du décalage (ch. 5) |
| `y_gap_net` | ❌ cible | c'est une cible, pas une variable |

## 2.4 — L'encadré sur `pre` : la nuance à retenir

La fenêtre `pre` se ferme **exactement** à l'ouverture. Statistiquement, elle est utilisable pour prédire
le gap. Mais deux régimes doivent être distingués :

| Usage | Fenêtres utilisables | Pourquoi |
|---|---|---|
| **Prédire** le prix d'ouverture | `overnight` + `pre` | tout est connu à 9h29 |
| **Trader** le gap | `overnight` seulement, décalé | la position se prend à 16h00 la veille |

**D'où le « jeu conservateur »** : un sous-ensemble coupé à minuit, testé au notebook 06 comme contrôle de
robustesse. Il donne AUC = 0,597 contre 0,664 pour le jeu complet.

*(Le chapitre 14 signale un défaut dans la construction de ce jeu conservateur.)*

---

# Chapitre 3 — Le z-score glissant ⭐

```python
def zscore_glissant(s, fenetre=60, minp=20):
    mu = s.rolling(fenetre, min_periods=minp).mean().shift(1)
    sd = s.rolling(fenetre, min_periods=minp).std().shift(1)
    return (s - mu) / sd.replace(0, np.nan)
```

## 3.1 — La notion : standardiser

**Standardiser** une variable, c'est la ramener à une échelle universelle :

```
              valeur observée  −  ce qui est normal
z  =  ────────────────────────────────────────────────
              de combien ça varie habituellement
```

Le résultat s'exprime **en écarts-types**. Un `z = +2` signifie « deux écarts-types au-dessus de la
normale » — et cette phrase a le même sens pour n'importe quelle variable, n'importe quelle unité.

> **L'analogie.** Un enfant mesure 1,30 m. Est-il grand ? Impossible à dire sans savoir son âge. Le
> carnet de santé n'affiche donc pas la taille brute, mais la **position par rapport à sa classe d'âge**.
> C'est exactement un z-score.

## 3.2 — Le problème résolu ici

```
Moyenne de mu_night_full par ticker :
  NVDA    0.1627
  AMZN    0.1170
  META    0.1139
  AAPL    0.0945
  TSLA    0.0449
```

Un sentiment de 0,12 vaut :

```
Pour NVDA :  (0,12 − 0,1627) / 0,0783  =  −0,55 écart-type   ->  MÉDIOCRE
Pour TSLA :  (0,12 − 0,0449) / 0,0323  =  +2,33 écarts-types ->  EXCEPTIONNEL
```

**Sans normalisation, un modèle nourri de valeurs brutes apprend l'identité du titre** : « quand `mu` est
élevé, c'est probablement NVDA, et NVDA a beaucoup monté ». Ce n'est pas un signal, c'est de la
mémorisation — et cela ne se généralise à aucun autre titre ni à aucune autre période.

## 3.3 — La preuve chiffrée que ça marche

```
AVANT normalisation (moyenne de mu_night_full par ticker) :
  AAPL 0.0945   AMZN 0.1170   META 0.1139   NVDA 0.1627   TSLA 0.0449

APRÈS normalisation (moyenne de z_mu_night_full par ticker) :
  AAPL -0.0063  AMZN -0.0720  META -0.1107  NVDA -0.1237  TSLA -0.0280
```

Les écarts passent d'un facteur **3,6** à des valeurs toutes proches de zéro.

### Et voici la preuve la plus convaincante

Compare ces deux corrélations, prises dans deux notebooks différents :

| Variable | Corrélation avec le gap | Source |
|---|---|---|
| `mu_night_full` (brut) | **+0,157** | notebook 04 |
| `z_mu_night_full` (normalisé) | **+0,257** | notebook 05, test T3 |

**La normalisation fait passer la corrélation de 0,157 à 0,257 — une amélioration de 64 %.**

**Pourquoi.** Le biais de niveau entre titres est un **bruit** qui dilue le signal. En le supprimant, on
révèle la relation qu'il masquait. Ce n'est pas de la magie : c'est simplement qu'on mesure enfin la bonne
chose — l'écart à la normale, et non le niveau absolu.

> **C'est un chiffre à mettre dans le mémoire.** Il justifie la normalisation par un gain mesuré, et non
> par un argument théorique.

## 3.4 — Le `.shift(1)` : le détail qui décide de tout

```python
mu = s.rolling(60).mean().shift(1)      # <-- SANS ce shift, c'est une fuite
```

**Sans `.shift(1)`,** la fenêtre de 60 jours **inclut le jour J**. On normalise donc `x_t` par une moyenne
qui contient déjà `x_t`.

**Quel est l'effet concret ?** Il paraît minuscule — 1/60 du poids. Mais il est **systématique** et il va
toujours dans le même sens : si `x_t` est très élevé, il tire sa propre moyenne de référence vers le haut,
donc le z-score est **sous-estimé**. Inversement pour les valeurs basses. Le résultat est une compression
artificielle des extrêmes… qui rend le signal plus « propre » qu'il ne l'est.

> **C'est l'erreur numéro un en finance quantitative appliquée.** Elle est présente dans une grande
> partie du code publié en ligne. Retiens la règle :
>
> **Toute fenêtre glissante utilisée comme variable explicative doit être décalée d'au moins un pas.**

## 3.5 — Pourquoi une fenêtre glissante et pas une moyenne globale

**Deux raisons.**

**1. La fuite.** Une moyenne calculée sur 2020-2022 entier utiliserait des données de 2022 pour normaliser
des jours de 2020. C'est la fuite de prétraitement (type 3, ch. 0).

**2. L'adaptation aux régimes.** Le niveau de bavardage sur TSLA en mars 2020 (panique COVID) n'a rien à
voir avec janvier 2022. Une référence fixe serait fausse dans les deux cas. La fenêtre glissante **suit**
le régime.

## 3.6 — Le choix des paramètres

```python
FENETRE_Z = 60      # ~3 mois de bourse
MIN_OBS   = 20      # au moins 1 mois avant de produire une valeur
```

**Pourquoi 60 jours ?** C'est un compromis classique :

| Fenêtre | Avantage | Inconvénient |
|---|---|---|
| courte (20 j) | s'adapte vite aux changements | référence bruitée |
| **moyenne (60 j)** | **équilibre** | — |
| longue (250 j) | référence stable | ne voit pas les changements de régime |

**Pourquoi `min_periods=20` ?** Pour ne pas produire un z-score sur 3 observations, qui serait absurde. En
dessous de 20, on renvoie `NaN` — d'où les 106 valeurs manquantes de `mu_night_z20`.

**Le `.replace(0, np.nan)` sur l'écart-type** évite une division par zéro : si les 60 derniers jours ont
tous exactement la même valeur, `sd = 0` et le z-score serait infini.

---

# Chapitre 4 — Le rang percentile

```python
def rang_glissant(s, fenetre=252, minp=60):
    return s.rolling(fenetre, min_periods=minp).apply(
        lambda w: (w[:-1] < w[-1]).mean(), raw=True)
```

## 4.1 — Ce que fait cette fonction

Pour chaque jour, elle répond à : *« parmi les 252 derniers jours, quelle proportion avait une valeur
inférieure à celle d'aujourd'hui ? »*

```
rk = 0,95  ->  aujourd'hui est plus élevé que 95 % de l'année écoulée
rk = 0,50  ->  aujourd'hui est dans la moyenne
rk = 0,02  ->  aujourd'hui est parmi les 2 % les plus bas
```

Le résultat est toujours entre **0 et 1**.

## 4.2 — Pourquoi en plus du z-score

Les deux normalisent, mais différemment :

| | z-score | rang percentile |
|---|---|---|
| Utilise | les **valeurs** | les **positions** |
| Sensible aux extrêmes | **oui** | non |
| Suppose une forme | plutôt symétrique | aucune |
| Interprétation | « x écarts-types » | « meilleur que y % » |

**Le problème que le rang résout.** Un seul jour extrême — un tweet d'Elon Musk qui multiplie l'activité
par 10 — fait exploser l'écart-type de la fenêtre. Tous les z-scores des 60 jours suivants sont alors
comprimés artificiellement. Le rang, lui, ne bouge pas : ce jour reste simplement « le plus élevé ».

**Le lien avec le notebook 04.** L'analyse par quintiles avait montré que l'effet est concentré dans les
**queues** (Q1 et Q5), pas au milieu. Or c'est précisément aux queues que le z-score est le plus fragile
et le rang le plus fiable. D'où son ajout.

## 4.3 — Le coût : la complétude

```
rk_nabn_night_full    81.7 %
rk_mu_night_full      84.4 %
z_nabn_night_full     92.0 %
z_mu_night_full       94.7 %
```

Le rang exige `min_periods=60` (contre 20 pour le z-score), donc il est disponible sur **moins de
lignes**. C'est le prix de la robustesse.

**C'est un arbitrage à assumer :** une variable plus fiable mais moins souvent disponible, contre une
variable toujours disponible mais plus fragile. Avoir les deux permet au modèle de choisir.

---

# Chapitre 5 — Les variables de contrôle ⭐

## 5.1 — L'objection à laquelle elles répondent

Imagine que tu présentes ton résultat. Un membre du jury dit :

> *« Votre sentiment est élevé **parce que** l'action a monté hier. Et une action qui a monté hier a
> tendance à ouvrir en hausse — c'est le momentum, un fait connu depuis 1993. Vous avez simplement
> redécouvert le momentum, en passant par les tweets. »*

**C'est une objection sérieuse, et on ne peut pas y répondre avec des mots.** Il faut des données.

## 5.2 — La notion : la variable de confusion

Une **variable de confusion** (*confounder*) est une variable qui influence **à la fois** la variable
explicative et la cible, créant une corrélation qui n'est pas causale.

```
        rendement d'hier  (Z)
              ╱        ╲
             ╱          ╲
            ▼            ▼
    sentiment (X)  ⋯⋯⋯>  gap (Y)
                  corrélation observée
                  mais peut-être non causale
```

**Si Z cause X et Z cause Y**, alors X et Y seront corrélés même sans lien direct.

> **L'exemple canonique.** Les ventes de glaces et les noyades sont fortement corrélées. La glace ne
> cause pas les noyades : la **chaleur** cause les deux. La température est la variable de confusion.

## 5.3 — La solution : contrôler

**Contrôler** une variable, c'est l'inclure dans le modèle pour neutraliser son effet. On demande alors :

> *« À rendement de la veille égal, le sentiment apporte-t-il encore quelque chose ? »*

Si oui, l'explication par le momentum est écartée.

## 5.4 — Les neuf contrôles

| Variable | Ce qu'elle capture | Objection qu'elle neutralise |
|---|---|---|
| `ret_cc_lag1` | rendement de la veille | « c'est du momentum » |
| `ret_oc_lag1` | séance de la veille | « c'est la fin de journée d'hier » |
| `gap_lag1`, `gap_lag2` | gaps précédents | « les gaps se suivent » |
| `vol_20` | régime de volatilité | « ça marche seulement en marché agité » |
| `ampl_lag1`, `ampl_ma5` | agitation de la veille | idem |
| `vol_dollar_z` | intensité de l'activité | « c'est le volume, pas le sentiment » |
| `dow` | jour de la semaine | « c'est un effet lundi/vendredi » |

## 5.5 — Les effets calendaires : pourquoi `dow` mérite d'être là

Les marchés présentent des **anomalies calendaires** documentées depuis les années 1970 :

- **l'effet week-end** (French, 1980) : les rendements du lundi sont historiquement plus faibles ;
- **l'effet janvier** : les petites capitalisations surperforment en janvier ;
- **l'effet fin de mois** : rééquilibrages institutionnels.

Dans ton cas, `dow` capture aussi une réalité mécanique : **le lundi, la fenêtre nocturne couvre 65 heures
au lieu de 8**. Si le modèle se comportait différemment le lundi, il faudrait le savoir.

## 5.6 — Le contrôle anti-fuite de cette cellule

```
VÉRIFICATION — corrélation de chaque contrôle avec la cible du MÊME jour :
   ret_cc_lag1      rho(gap) = +0.0508
   ret_oc_lag1      rho(gap) = +0.1029
   gap_lag1         rho(gap) = -0.0461
   gap_lag2         rho(gap) = +0.0706
   vol_20           rho(gap) = +0.0516
   ampl_lag1        rho(gap) = -0.0021
   ampl_ma5         rho(gap) = +0.0533
   vol_dollar_z     rho(gap) = -0.0147
   dow              rho(gap) = -0.0186
```

**Toutes les corrélations sont faibles (|ρ| ≤ 0,10).** C'est exactement ce qu'on attend : ces variables
sont décalées, elles ne peuvent pas contenir l'information du jour J.

**Si l'une avait valu 0,6**, cela aurait signalé un `shift` oublié — la variable contiendrait la cible.

### Le chiffre qui mérite un commentaire : `ret_oc_lag1` à +0,103

C'est le plus élevé des neuf. Est-ce inquiétant ?

**Non — et c'est même intéressant.** Il dit : *« quand la séance d'hier a bien fini, l'ouverture
d'aujourd'hui est un peu meilleure »*. C'est un effet de **continuation** documenté, lié à l'exécution
différée des ordres accumulés en fin de séance.

**Ce n'est pas une fuite** : `ret_oc_lag1` est entièrement connue à 16h00 la veille. C'est un vrai
prédicteur, faible mais légitime.

**Et c'est précisément pourquoi il faut le contrôler :** au notebook 06, le modèle « contrôles seuls »
obtient AUC = 0,498 — donc ces variables, ensemble, ne prédisent **rien**. Le sentiment apporte
**+0,17 point d'AUC** par-dessus. L'objection du momentum est démolie par les chiffres.

---

# Chapitre 6 — Les cibles dérivées

## 6.1 — Le gap en excès du marché

```python
df["gap_mkt"]    = df.groupby("Date")["gap"].transform("mean")
df["gap_excess"] = df["gap"] - df["gap_mkt"]
```

### La notion : séparer le marché du titre

Une partie du gap d'AAPL n'a rien à voir avec AAPL : si le Nasdaq ouvre en hausse, **les cinq titres**
ouvrent en hausse. C'est le **facteur commun** — le « marché » au sens du MEDAF (modèle d'évaluation des
actifs financiers).

```
gap(AAPL)  =  composante MARCHÉ  +  composante SPÉCIFIQUE à AAPL
```

**Prédire la composante marché, c'est prédire le marché** — un problème différent, et beaucoup plus
étudié. La contribution originale serait de prédire la composante **spécifique**.

### Comment on l'isole

En retirant, chaque jour, la moyenne des cinq titres. C'est une version simplifiée de la
**démarché-neutralisation** (*market-neutralization*) utilisée par les fonds quantitatifs.

**Pourquoi c'est un test plus exigeant.** Si le sentiment prédit encore `gap_excess`, alors le signal est
vraiment spécifique au titre. Une stratégie construite dessus serait **neutre au marché** — insensible à
la direction générale, donc bien moins risquée.

### Le résultat qui surprend

```
y_gap_excess : 0.472
```

**Moins de 50 %.** Comment le gap en excès peut-il être négatif plus souvent que positif, alors qu'il est
défini comme un écart à la moyenne ?

**Parce que la moyenne n'est pas la médiane.** TSLA a des gaps très positifs et très volatils : il tire la
moyenne du jour vers le haut. Résultat : **plus de la moitié des titres se retrouvent sous la moyenne**,
même si l'écart total se compense.

> **C'est une propriété générale des distributions asymétriques** : quand quelques valeurs très élevées
> tirent la moyenne, la majorité des observations passe en dessous.
>
> Exemple : dans un bar avec 9 personnes gagnant 2 000 € et une gagnant 100 000 €, le salaire moyen est
> de 11 800 €. **90 % des gens sont en dessous de la moyenne.**

**Une amélioration possible :** utiliser la **médiane** transversale plutôt que la moyenne, ce qui donnerait
mécaniquement 50 % de part et d'autre.

## 6.2 — La zone morte

```python
SEUIL_BP = 15                    # 15 points de base = 0,15 %
df["y_gap_net"] = np.where(df["gap"] > seuil, 1,
                    np.where(df["gap"] < -seuil, 0, np.nan))
```

```
Jours neutralisés : 382 (13.9 % du total)
y_gap_net : 0.599 (n = 2 358)
```

### Le problème

Un **point de base** (bp) vaut 0,01 %. Un gap de +0,013 % donne `y_gap = 1` — « hausse » — alors que ce
mouvement est **plusieurs fois plus petit que les frais de transaction**.

Le modèle est donc évalué sur des jours qu'il serait **impossible de trader**.

### Le passage d'une évaluation statistique à une évaluation décisionnelle

C'est un changement de perspective important, et très actuariel :

| Question | Type |
|---|---|
| « Le modèle a-t-il raison ? » | **statistique** |
| « Le modèle a-t-il raison **là où ça change quelque chose** ? » | **décisionnelle** |

En actuariat, on ne demande pas seulement si le modèle prédit bien la sinistralité — on demande s'il la
prédit bien **là où les montants sont significatifs**. Un modèle qui se trompe sur les petits sinistres et
a raison sur les gros vaut mieux que l'inverse, même si son taux d'erreur global est plus élevé.

**Le choix de 15 bp** correspond à l'ordre de grandeur des coûts de transaction à l'ouverture (5 à 20 bp).
C'est un paramètre à faire varier en analyse de sensibilité.

---

# Chapitre 7 — Le découpage temporel ⭐

## 7.1 — La règle absolue

> **Jamais** de `train_test_split(shuffle=True)` sur des séries temporelles.

### Pourquoi c'est catastrophique

Un découpage aléatoire met des jours de 2022 dans l'entraînement et des jours de 2020 dans le test. Le
modèle **apprend le futur pour prédire le passé**.

**Concrètement**, avec des données financières autocorrélées, si le 15 mars est dans le train et le
16 mars dans le test, le modèle a quasiment vu la réponse : les deux jours partagent le même régime, la
même volatilité, souvent la même actualité.

**Les scores obtenus sont excellents et entièrement faux.** C'est la faute la plus fréquente et la plus
rédhibitoire dans ce type de mémoire.

## 7.2 — Pourquoi trois blocs et pas deux

C'est une question qu'on pose souvent, et la réponse est subtile.

```
├──────────── TRAIN ────────────┼──── VALID ────┼──── TEST ────┤
2020-01-02              2021-06-30      2021-11-30      2022-03-04
```

| Bloc | À quoi il sert | Combien de fois on le regarde |
|---|---|---|
| **TRAIN** | ajuster les **paramètres** du modèle (les coefficients) | en continu |
| **VALIDATION** | choisir les **hyperparamètres** (C, profondeur, seuil) et le modèle final | autant qu'on veut |
| **TEST** | **estimer** la performance réelle | **une seule fois** |

### Le concept clé : le surajustement à la validation

Chaque fois qu'on regarde la validation pour prendre une décision, on lui **transmet un peu
d'information**. Après 50 essais d'hyperparamètres, le modèle choisi est celui qui marche le mieux **sur
cette validation précise** — pas nécessairement le meilleur en général.

> **L'analogie de l'examen.** Le **train**, ce sont les exercices d'entraînement. La **validation**, ce
> sont les annales que tu refais dix fois pour choisir ta méthode. Le **test**, c'est l'examen final.
>
> Si tu utilisais les annales comme examen, ta note serait flatteuse — tu les connais par cœur. Le test
> doit rester **inconnu**.

### La conséquence pratique

> **Chaque coup d'œil supplémentaire au test le transforme en validation.**
>
> Si tu regardes le test, modifies le modèle, puis regardes à nouveau — le chiffre annoncé n'a plus la
> signification qu'on lui prête. Il faut alors soit repartir d'un test neuf, soit annoncer honnêtement
> que l'évaluation repose sur la validation.

*(C'est exactement le point signalé dans le verdict général : la cellule de test du notebook 06 n'a jamais
été exécutée. Tous tes chiffres sont donc des chiffres de validation glissante — ce qui est déjà hors
échantillon et honnête, mais il faut le dire.)*

## 7.3 — Le résultat, et le point important à voir

```
       n_lignes  n_jours      debut        fin  pct_gap_pos
train      1885      377 2020-01-02 2021-06-30         59.5
purge        25        5 2021-07-01 2021-12-03         76.0
valid       520      104 2021-07-06 2021-11-30         60.6
test        310       62 2021-12-06 2022-03-04         51.0
```

### ⚠ Le taux de base chute dans le test : 59,5 % → 60,6 % → **51,0 %**

**C'est le chiffre le plus important de cette cellule, et il faut absolument le commenter dans le
mémoire.**

Le bloc de test (décembre 2021 → mars 2022) tombe dans un **régime de marché différent** : c'est le début
du resserrement monétaire de la Fed et la correction du Nasdaq. Les gaps y sont positifs seulement 51 % du
temps, contre ~60 % avant.

**Trois conséquences :**

1. **Il faut s'attendre à des performances plus faibles sur le test** — pour des raisons qui n'ont rien à
   voir avec la qualité du modèle.
2. **C'est aussi une bonne nouvelle** : si le modèle fonctionne encore dans un régime différent de celui
   sur lequel il a été entraîné, sa robustesse est démontrée. *(Et c'est le cas : au notebook 06, le
   régime « Resserrement Fed » donne l'AUC la plus élevée, 0,713.)*
3. **Il faut l'écrire soi-même**, plutôt que de subir la question.

> **La phrase pour le mémoire :** *« Le bloc de test correspond au début du resserrement monétaire de
> 2022 : la proportion de gaps positifs y chute de 60 % à 51 %. Le modèle y est donc évalué dans un
> régime différent de celui de son entraînement, ce qui constitue un test de robustesse plus exigeant
> qu'un découpage homogène. »*

---

# Chapitre 8 — Le purge et le walk-forward

## 8.1 — Le purge (ou embargo)

```python
PURGE_JOURS = 5
```

### Le problème qu'il résout

Tes variables utilisent des fenêtres glissantes de 60 jours. Donc :

```
Dernier jour du TRAIN     (30 juin 2021)  utilise les 60 jours précédents
Premier jour de la VALID  (1er juillet)   utilise les 60 jours précédents
```

**Ces deux fenêtres partagent 59 jours sur 60.** Le premier jour de la validation n'est donc pas
réellement « hors échantillon » — il est presque entièrement construit sur des données d'entraînement.

C'est la **fuite par contamination de groupe** (type 4, ch. 0).

### La solution

On retire quelques jours **entre** les blocs. C'est le **purge**, formalisé par **Marcos López de Prado**
dans *Advances in Financial Machine Learning* (2018) — l'ouvrage de référence sur ces questions.

```
├─── TRAIN ───┤ purge ├─── VALID ───┤ purge ├─── TEST ───┤
              ← 5 j →              ← 5 j →
```

**Coût :** 25 lignes sur 2 740, soit 0,9 %. **Bénéfice :** une frontière propre entre les blocs.

> **Note :** López de Prado recommande un purge de la taille de la fenêtre de features (ici, 60 jours).
> Cinq jours est un compromis pragmatique — il coupe le chevauchement le plus direct sans sacrifier 11 %
> des données. À mentionner comme limite.

### Une bizarrerie d'affichage à comprendre

```
purge        25        5 2021-07-01 2021-12-03         76.0
```

`debut = 2021-07-01` et `fin = 2021-12-03` : cinq mois d'écart pour seulement 5 jours ?

**Ce n'est pas un bug.** Il y a **deux purges** (une après le train, une après la validation), et
`groupby("bloc")` les regroupe sous la même étiquette. Le `min` prend la première date du premier purge,
le `max` la dernière date du second.

Les lignes sont bien exclues — seul l'affichage est trompeur. **Une amélioration serait de nommer les
purges séparément** (`purge_1`, `purge_2`).

*(Le `pct_gap_pos = 76 %` sur 25 lignes n'a aucune signification statistique : l'incertitude sur un
pourcentage calculé sur 25 observations est d'environ ±17 points.)*

## 8.2 — La validation glissante (walk-forward)

```
Walk-forward : 4 plis
  Pli 1 : train 2020-01-02 -> 2021-03-16 (303 j)  |  test 2021-03-24 -> 2021-06-17 (60 j)
  Pli 2 : train 2020-01-02 -> 2021-06-10 (363 j)  |  test 2021-06-18 -> 2021-09-13 (60 j)
  Pli 3 : train 2020-01-02 -> 2021-09-03 (423 j)  |  test 2021-09-14 -> 2021-12-07 (60 j)
  Pli 4 : train 2020-01-02 -> 2021-11-30 (483 j)  |  test 2021-12-08 -> 2022-03-04 (60 j)
```

### Le problème du découpage unique

Un score obtenu sur une seule période de validation dépend **de cette période**. Si juillet-novembre 2021
a été calme, le score sera flatteur ; s'il a été agité, pessimiste.

**Un seul chiffre ne dit rien de la stabilité.**

### Le principe

On entraîne sur tout le passé disponible, on teste sur la période suivante, on avance, on recommence.

```
Pli 1 :  [══════ train ══════]--purge--[test]
Pli 2 :  [════════ train ════════]--purge--[test]
Pli 3 :  [══════════ train ══════════]--purge--[test]
Pli 4 :  [════════════ train ════════════]--purge--[test]
```

**C'est la seule validation acceptable en finance**, parce que c'est la seule qui reproduit la situation
réelle : au 1ᵉʳ mars, on ne dispose que des données antérieures au 1ᵉʳ mars.

### Fenêtre extensible vs fenêtre glissante

Deux variantes existent :

| Type | Le train… | Avantage |
|---|---|---|
| **Extensible** (*expanding*) — utilisée ici | grandit à chaque pli (303 → 483 j) | plus de données à chaque fois |
| Glissante (*rolling*) | garde une taille fixe | s'adapte mieux aux changements de régime |

Le choix de l'extensible est justifié ici par la **rareté des données** : avec seulement 548 jours, on ne
peut pas se permettre d'en jeter.

### Ce qu'il faut regarder dans les résultats

Pas seulement la **moyenne** des AUC, mais aussi :

- l'**écart-type** entre plis — la stabilité ;
- le **nombre de plis au-dessus de 0,50** — la fiabilité.

Un modèle à AUC moyenne 0,60 obtenue par 0,75 / 0,48 / 0,52 / 0,65 n'est pas un bon modèle : c'est un
modèle qui a eu de la chance une fois. *(Le tien fait 4 plis sur 4 au-dessus de 0,50, avec un écart-type
de 0,022 — c'est très stable.)*

---

# Chapitre 9 — T1 : la corrélation anormale

```
T1 — Corrélation feature <-> cible du même jour
SEUIL_T1 = 0.40
  [OK] Aucune corrélation suspecte.
```

## Ce qu'il teste

Pour chaque variable explicative, on calcule sa corrélation avec la cible du **même jour**. Si l'une
dépasse 0,40, c'est une alerte.

## Pourquoi ce test attrape la fuite de cible

**Le raisonnement.** En finance journalière, aucune variable légitime ne peut atteindre |ρ| > 0,40 avec un
rendement futur. Si une variable y parvient, c'est presque certainement qu'elle **contient** la cible.

> **Exemple typique d'accident** : on garde `Close` du jour J dans les features pour prédire `ret_oc` du
> jour J. Comme `ret_oc = Close/Open − 1`, la corrélation serait énorme. Le test l'attraperait
> immédiatement.

## Pourquoi le seuil de 0,40

Il est **délibérément haut**. Le but n'est pas de détecter un signal faible — c'est de détecter une
**catastrophe**.

| Seuil | Effet |
|---|---|
| 0,20 | trop bas : déclencherait sur des variables légitimes |
| **0,40** | **détecte les fuites franches sans faux positifs** |
| 0,80 | trop haut : laisserait passer des fuites partielles |

**C'est un garde-fou, pas un test statistique.** Il attrape l'erreur grossière — celle qu'on commet en
étant fatigué à 2h du matin.

---

# Chapitre 10 — T2 : l'ordre chronologique

```
max(train) = 2021-06-30  <  min(valid) = 2021-07-06   -> OK
max(valid) = 2021-11-30  <  min(test)  = 2021-12-06   -> OK
```

## Ce qu'il teste

Que le dernier jour de chaque bloc soit **strictement antérieur** au premier jour du suivant.

## Pourquoi ce test est indispensable malgré sa simplicité

Il paraît trivial — on vient de construire les blocs par date, comment pourraient-ils se chevaucher ?

**Réponse : très facilement.** Trois manières classiques :

1. un `sort_values` oublié avant un `shift` ;
2. une fusion (`merge`) qui réordonne les lignes ;
3. une modification du découpage trois semaines plus tard, en oubliant qu'un bloc chevauche l'autre.

> **Le principe général : tester les invariants.** Un **invariant** est une propriété qui doit être vraie
> à tout moment. Le vérifier explicitement coûte trois lignes et attrape des erreurs qui, autrement,
> resteraient invisibles.
>
> C'est le même esprit que les contrôles comptables : on ne vérifie pas que le bilan s'équilibre parce
> qu'on doute du comptable, mais parce que l'erreur est possible et silencieuse.

**On observe aussi ici l'effet du purge** : 6 jours séparent le 30 juin du 6 juillet (5 jours d'embargo
plus un week-end).

---

# Chapitre 11 — T3 : le sentiment futur prédit-il le passé ?

```
rho(sentiment de J   -> gap de J) = +0.2572   <- le signal
rho(sentiment de J+1 -> gap de J) = +0.0993   <- doit être proche de 0
[OK] Le signal est bien orienté dans le temps.
```

## 11.1 — La logique du test

**Le sentiment de demain ne peut pas causer le gap d'aujourd'hui.** C'est logiquement impossible.

Donc si on trouvait une corrélation aussi forte à J+1 qu'à J, cela signifierait une **erreur
d'alignement** : décalage de fuseau, messages rattachés au mauvais jour, `shift` dans le mauvais sens.

**C'est un test de falsification** au sens de Popper : on cherche activement à réfuter son propre
résultat. S'il résiste, la confiance augmente considérablement.

## 11.2 — Pourquoi 0,0993 et pas 0,0000 ?

C'est **la question à laquelle il faut savoir répondre**, parce qu'un jury attentif la posera.

La réponse tient en un mot : **l'autocorrélation**.

### Le mécanisme, étape par étape

```
1.  Le sentiment est PERSISTANT :  correlation( mu(J+1) , mu(J) )  ≈  0,4
2.  Le sentiment de J prédit le gap de J :  correlation( mu(J) , gap(J) )  =  0,257
3.  Donc mu(J+1), qui « ressemble » à mu(J), hérite d'une partie de cette corrélation
```

**L'ordre de grandeur attendu** est le produit des deux : 0,4 × 0,257 ≈ **0,10**.

**On observe 0,0993.** C'est exactement la valeur prédite par ce raisonnement.

> **Ce n'est donc pas une fuite** — c'est une conséquence arithmétique de la persistance du sentiment.
> Si le sentiment d'un titre est élevé aujourd'hui, il a de bonnes chances de l'être demain ; la variable
> de demain est donc une version bruitée de celle d'aujourd'hui.

### Le critère de décision

```python
if abs(r1) > 0.5 * abs(r0):
    ECHEC
```

On échoue si le lag négatif dépasse **la moitié** du lag zéro. Ici : 0,0993 / 0,2572 = **0,386**. Le test
passe, avec une marge confortable.

**Pourquoi ce seuil de 0,5 ?** Parce qu'une vraie fuite d'alignement donnerait un ratio proche de **1**
(le décalage rendrait les deux corrélations quasi identiques), tandis que la contamination par
autocorrélation reste sous 0,5 tant que la persistance est modérée.

## 11.3 — Le chiffre caché : la preuve que la normalisation fonctionne

Regarde le chiffre `+0,2572`.

Au notebook 04, la corrélation de `mu_night_full` **brut** avec le gap était de **+0,157**.
Ici, avec `z_mu_night_full` **normalisé**, elle vaut **+0,257**.

**La normalisation intra-ticker a augmenté la corrélation de 64 %.**

C'est la **valeur ajoutée mesurée** du chapitre 3, et c'est un chiffre à citer dans le mémoire : la
normalisation n'est pas un choix esthétique, elle révèle un signal que le biais de niveau masquait.

---

# Chapitre 12 — T4 : le test placebo ⭐

```
AUC avec cible PERMUTÉE : 0.4719   (doit être ~0.50)
AUC avec cible RÉELLE   : 0.6557   (doit être nettement > 0.50)
[OK] Le pipeline n'apprend rien sur du bruit.
```

## 12.1 — La notion : le contrôle négatif

Un **contrôle négatif** est une expérience où l'on **sait** que le résultat doit être nul. Si l'instrument
produit un résultat non nul, c'est l'instrument qui est défaillant — pas le phénomène.

> **En médecine, c'est le placebo.** On donne à un groupe une pilule sans principe actif. Si ce groupe
> guérit autant que le groupe traité, le médicament ne fait rien. Le placebo ne teste pas le médicament :
> il teste **le protocole**.

## 12.2 — Comment il est construit ici

```python
y_bidon = rng.permutation(tr["y_gap"].values)   # on MÉLANGE la cible
pipe.fit(tr[FEATURES], y_bidon)                 # on entraîne sur du bruit
auc_bidon = roc_auc_score(te["y_gap"], ...)     # on évalue sur la VRAIE cible
```

**La permutation** garde exactement les mêmes valeurs de `y_gap` — même proportion de 1, même effectif —
mais **détruit le lien** entre chaque ligne et sa cible. La ligne du 3 mars reçoit la cible du 17 août.

Il ne reste donc **aucune information exploitable**. L'AUC attendue est **0,50**.

## 12.3 — Ce que ce test attrape, et que les autres ratent

C'est le test le plus puissant des quatre, parce qu'il vérifie **le pipeline entier**, pas une hypothèse
particulière.

| Problème | T1 | T2 | T3 | **T4** |
|---|---|---|---|---|
| Une feature contient la cible | ✅ | | | ✅ |
| Blocs qui se chevauchent | | ✅ | | ✅ |
| Décalage temporel | | | ✅ | ✅ |
| Imputation calculée sur tout le jeu | | | | ✅ |
| Sélection de variables faite avant le découpage | | | | ✅ |
| Bug d'indexation dans le code | | | | ✅ |

**T4 est un filet de sécurité global.** Si le pipeline apprend quoi que ce soit sur du bruit pur, quelque
chose est structurellement cassé — et on ne sait pas forcément quoi, mais on sait qu'il faut chercher.

## 12.4 — Pourquoi 0,4719 et pas exactement 0,50 ?

**Parce que 0,50 est une espérance, pas une certitude.**

Sur un échantillon fini, l'AUC calculée sur du bruit fluctue autour de 0,50. Son écart-type approximatif :

```
                    ┌─────────────────────┐
écart-type(AUC)  ≈  │  1 / (12 × n_eff)  │        avec n_eff ≈ min(n1, n0)
                   \└─────────────────────┘
```

Sur 520 observations de validation avec ~60 % de positifs, cela donne un écart-type d'environ **0,025**.

```
0,4719 est à  (0,50 − 0,4719) / 0,025  =  1,1 écart-type de 0,50
```

**C'est parfaitement normal.** Un écart de 1,1 écart-type arrive environ une fois sur quatre.

**Le seuil de tolérance du code** est `|AUC − 0,50| > 0,05`, soit environ 2 écarts-types. Bien calibré :
assez large pour tolérer le hasard, assez strict pour attraper une vraie fuite (qui donnerait 0,60 ou
plus).

## 12.5 — Le contraste, qui est le vrai résultat

```
Cible permutée : 0.4719      <- le pipeline n'apprend rien sur du bruit
Cible réelle   : 0.6557      <- le pipeline apprend beaucoup sur la vraie cible
```

**C'est la comparaison qui compte, pas les valeurs isolées.** Même code, mêmes variables, même découpage —
seule la cible change. L'écart de 0,18 point d'AUC ne peut venir que de l'information réellement contenue
dans les variables.

> **La phrase pour la soutenance :** *« En permutant aléatoirement la cible d'entraînement, le pipeline
> obtient une AUC de 0,47 — indiscernable du hasard. Avec la cible réelle, il obtient 0,66. Le pipeline
> n'apprend donc rien de structurel : ce qu'il capte vient bien des données. »*

---

# Chapitre 13 — L'export et la reproductibilité

```
Écrit : DATASET_MODELISATION_2020_2022.csv    2 740 lignes x 66 colonnes
Écrit : config_modelisation.json               23 features
```

## 13.1 — Pourquoi un fichier de configuration séparé

```json
{
  "features": [...23 noms...],
  "features_conservateur": [...],
  "features_sentiment": [...],
  "controles": [...],
  "fin_train": "2021-06-30",
  "fin_valid": "2021-11-30",
  "purge_jours": 5,
  "seuil_zone_morte_bp": 15,
  "fenetre_zscore": 60
}
```

**Le problème qu'il résout.** Les notebooks 06, 07 et 08 ont tous besoin de la même liste de variables et
des mêmes dates. Si chacun la redéfinit, ils finiront par diverger — et les résultats ne seront plus
comparables entre eux.

C'est le principe de la **source unique de vérité** (déjà vu au Cours 1, ch. 1), appliqué cette fois
**entre notebooks**.

## 13.2 — La notion de reproductibilité

Un travail de recherche doit pouvoir être **refait à l'identique** — par un jury, par un futur étudiant,
ou par toi-même dans six mois.

**Ce fichier JSON est la trace de tes choix.** Il documente :

- quelles variables ont été utilisées (et donc lesquelles ont été écartées) ;
- où passent les frontières temporelles ;
- quels paramètres ont été retenus (60 jours, 5 jours, 15 bp).

> **La crise de la reproductibilité.** Une étude de 2016 dans *Nature* a montré que plus de 70 % des
> chercheurs interrogés avaient échoué à reproduire les résultats d'un collègue, et plus de 50 % leurs
> propres résultats. La documentation des paramètres est le premier remède.

## 13.3 — Le détail des colonnes conservées

```
2 740 lignes x 66 colonnes
  dont 24 colonnes brutes conservées pour l'analyse descriptive
```

Le fichier ne garde pas que les 23 variables du modèle. Il conserve aussi :

- les **métadonnées** (Date, Ticker, bloc, prix) ;
- les **cibles** (y_gap, y_oc, log_ampl…) ;
- les **24 variables brutes** des fenêtres nocturnes.

**Pourquoi garder les brutes alors que les modèles utilisent les normalisées ?** Parce que les notebooks 07
et 09 en ont besoin pour des analyses **descriptives** — les figures, les statistiques par ticker, les
tableaux du mémoire. Les valeurs normalisées sont bonnes pour prédire, mauvaises pour décrire.

---

# Chapitre 14 — Trois points à corriger

*Un cours doit aussi apprendre à regarder son propre travail avec un œil critique. Voici trois défauts de
ce notebook.*

## 14.1 — ⚠ Le « jeu conservateur » n'est pas conservateur

```python
FEATURES_CONS = [f for f in FEATURES if "_pre" not in f and "night_full" not in f]
```

**L'intention :** ne garder que les variables issues de la fenêtre `overnight` (fermée à minuit), pour
tester si le signal survit sans les messages du petit matin.

**Le problème :** ce filtre laisse passer deux variables contaminées.

| Variable | Passe le filtre ? | Est-elle vraiment « coupée à minuit » ? |
|---|---|---|
| `z_mu_overnight` | oui | ✅ oui |
| `z_sd_overnight` | oui | ✅ oui |
| `z_dmu_night` | **oui** | ❌ **non** — dérivée de `mu_night_full` |
| `z_mu_night_ma3` | **oui** | ❌ **non** — moyenne mobile de `mu_night_full` |

`dmu_night = mu_night_full(t) − mu_night_full(t−1)` et `mu_night_ma3` est une moyenne de `mu_night_full`.
**Les deux contiennent donc l'information de la fenêtre `pre`** — celle qu'on voulait justement exclure.

**La conséquence.** Le test de robustesse du notebook 06 (« jeu conservateur », AUC = 0,597) n'est pas
aussi propre qu'annoncé. Le vrai jeu conservateur donnerait probablement un score un peu plus faible.

**Le correctif :**

```python
CONTAMINEES = ["z_dmu_night", "z_mu_night_ma3"]
FEATURES_CONS = [f for f in FEATURES
                 if "_pre" not in f and "night_full" not in f
                 and f not in CONTAMINEES]
```

> **La leçon générale :** filtrer par le **nom** d'une variable est fragile. Une variable dérivée peut
> porter un nom qui ne trahit pas son origine. Le filtre correct porterait sur la **provenance**, ce qui
> suppose de la déclarer explicitement à la construction.

## 14.2 — Du code mort

```python
FEATURES_SENT = [c_ for c_ in df.columns
                 if c_.startswith(("z_", "rk_")) and "night" in c_ or c_.startswith("z_mu_overnight")]
FEATURES_SENT = sorted(set([c_ for c_ in df.columns if c_.startswith(("z_", "rk_"))]))
```

La première ligne est **immédiatement écrasée** par la seconde. Elle ne sert à rien.

Pire : elle contient un piège classique de précédence des opérateurs. En Python, `and` est prioritaire sur
`or`, donc l'expression se lit :

```
( startswith(("z_","rk_")) AND "night" in c_ )  OR  ( startswith("z_mu_overnight") )
```

ce qui n'est probablement pas ce qui était voulu.

**Sans conséquence ici** (la ligne est écrasée), mais c'est le genre de code qui devient un vrai bug le
jour où quelqu'un supprime la ligne suivante. **À supprimer.**

## 14.3 — L'étiquette « purge » ambiguë

Comme vu au chapitre 8, les deux purges partagent la même étiquette, ce qui rend l'affichage `debut/fin`
trompeur (juillet → décembre pour 5 jours).

**Correctif :** nommer `purge_1` et `purge_2`.

---

# Chapitre 15 — Récapitulatif

## 15.1 — Les 12 idées à retenir

| # | Idée | Chapitre |
|---|---|---|
| **1** | **Une fuite donne un excellent résultat qu'on ne voit pas.** C'est ce qui la rend dangereuse. | 0 |
| **2** | **Il existe quatre types de fuites** : de cible, temporelle, de prétraitement, de groupe. Chacune a son remède. | 0 |
| **3** | **Un NaN inexpliqué est un bug** jusqu'à preuve du contraire — et un NaN honnête vaut mieux qu'une valeur inventée. | 1 |
| **4** | **Une règle méthodologique doit être codée**, pas gardée en tête. Le code survit à la fatigue. | 2 |
| **5** | **La normalisation intra-ticker fait passer ρ de 0,157 à 0,257.** Ce n'est pas cosmétique, c'est mesuré. ⭐ | 3, 11 |
| **6** | **Toute fenêtre glissante doit être décalée** (`.shift(1)`). L'erreur n° 1 du domaine. | 3 |
| **7** | **Une variable de confusion crée une corrélation non causale.** D'où les variables de contrôle. ⭐ | 5 |
| **8** | **Jamais de découpage aléatoire sur des séries temporelles.** | 7 |
| **9** | **Trois blocs, pas deux** : le test ne se regarde qu'une fois, sinon il devient une validation. ⭐ | 7 |
| **10** | **Le purge coupe le chevauchement** des fenêtres entre blocs. | 8 |
| **11** | **Le walk-forward mesure la stabilité**, pas seulement le niveau. | 8 |
| **12** | **Le test placebo vérifie le pipeline entier.** Si le code apprend sur du bruit, tout est faux. ⭐ | 12 |

## 15.2 — Les résultats du notebook 05, en une page

```
ENTRÉE   : 2 740 lignes x 81 colonnes
SORTIE   : 2 740 lignes x 66 colonnes  +  config_modelisation.json

Variables : 24 légales -> 14 normalisées (12 z_ + 2 rk_) + 9 contrôles = 23 features
Cibles    : y_gap 0,589 | y_oc 0,505 | y_cc 0,534 | y_gap_excess 0,472 | y_gap_net 0,599

Découpage : train 1 885 (377 j, 59,5 % gaps +)
            valid   520 (104 j, 60,6 %)
            test    310 ( 62 j, 51,0 %)   <- régime différent, à commenter
            walk-forward : 4 plis de 60 jours

TESTS ANTI-FUITE
  T1  corrélation anormale    : aucune > 0,40                      OK
  T2  ordre chronologique     : train < valid < test               OK
  T3  sentiment futur         : 0,099 vs 0,257  (ratio 0,39)       OK
  T4  placebo (cible permutée): AUC 0,472 vs 0,656 réelle          OK
```

## 15.3 — Les cinq phrases pour la soutenance

1. « L'appartenance d'une variable à l'espace des prédicteurs est décidée par une **fonction codée**, non
   par un jugement au cas par cas : la règle ne peut donc pas être oubliée quand on ajoute une colonne. »

2. « Les variables de sentiment sont normalisées par un **z-score glissant intra-titre, décalé d'un jour**.
   Cette normalisation fait passer la corrélation avec le gap de 0,157 à 0,257 — elle révèle un signal que
   le biais de niveau entre titres masquait. »

3. « Le découpage est **strictement chronologique**, avec un embargo de cinq jours entre blocs pour couper
   le chevauchement des fenêtres glissantes. Le bloc de test correspond au resserrement monétaire de 2022,
   où la proportion de gaps positifs chute de 60 % à 51 % : le modèle y est donc évalué dans un régime
   différent de celui de son entraînement. »

4. « Des **variables de contrôle de marché** — momentum, volatilité, volume, effets calendaires — sont
   incluses pour écarter l'objection selon laquelle le signal ne serait qu'un momentum déguisé. Utilisées
   seules, elles donnent une AUC de 0,498. »

5. « Un **test placebo** entraîne le pipeline sur une cible aléatoirement permutée. Il obtient 0,47 —
   indiscernable du hasard — contre 0,66 avec la cible réelle. Le pipeline n'apprend donc rien de
   structurel. »

---

## Références

- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. — purge, embargo, walk-forward
- Jegadeesh, N. & Titman, S. (1993). *Returns to Buying Winners and Selling Losers*. Journal of Finance. — le momentum
- French, K. (1980). *Stock Returns and the Weekend Effect*. Journal of Financial Economics
- Sharpe, W. (1964). *Capital Asset Prices*. Journal of Finance. — décomposition marché / spécifique
- Kaufman, S. et al. (2012). *Leakage in Data Mining*. ACM TKDD. — la taxonomie des fuites
- Baker, M. (2016). *1,500 scientists lift the lid on reproducibility*. Nature 533. — la crise de reproductibilité
- Arlot, S. & Celisse, A. (2010). *A survey of cross-validation procedures*. Statistics Surveys

---

*Prochain cours : notebook 06 — les métriques, les modèles de référence, la validation glissante, les
ablations et la calibration.*
