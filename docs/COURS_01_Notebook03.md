# Cours 1 — Notebook 03 : construire le panel

**Comment 3,7 millions de messages deviennent 2 740 lignes exploitables**

*Cours détaillé, cellule par cellule. Chaque variable : à quoi elle sert, sa formule, sa valeur ajoutée.
Chaque test : ce qu'il vérifie et pourquoi il est construit ainsi.*

---

## Table des matières

| # | Chapitre |
|---|---|
| 0 | Le vocabulaire de base — à lire en premier |
| 1 | La configuration : pourquoi une seule cellule |
| 2 | Charger les messages — et ce que fait vraiment FinBERT |
| 3 | Le score : `mu = pos − neg` |
| 4 | Les étiquettes Bullish / Bearish |
| 5 | Le fuseau horaire — la décision la plus lourde |
| 6 | Le calendrier de bourse |
| 7 | Affecter chaque message à un jour et une fenêtre |
| 8 | Les trois contrôles d'affectation |
| 9 | Agréger : les sept statistiques |
| 10 | Le format large et le squelette |
| 11 | Les variables de marché : `gap`, `ret_oc`, `ret_cc`, `vol_20d` |
| 12 | La fusion |
| 13 | Les variables d'attention : `nlog`, `nabn`, `disp` |
| 14 | Les dérivées nocturnes : `dmu`, `ma3`, `z20` |
| 15 | Les décalées et les cibles |
| 16 | Les sept contrôles qualité |
| 17 | Récapitulatif — les 10 idées à retenir |

---

# Chapitre 0 — Le vocabulaire de base

Avant de commencer, cinq mots. Si tu les maîtrises, tout le reste devient facile.

## 0.1 — Une observation

Une **observation**, c'est une ligne de ton tableau final. Ici, une observation = **un titre, un jour**.

> AAPL le 2 janvier 2020 → une observation.
> AAPL le 3 janvier 2020 → une autre observation.
> TSLA le 2 janvier 2020 → une troisième.

Tu as 5 titres × 548 jours = **2 740 observations**.

## 0.2 — Une variable (ou « feature »)

Une **variable**, c'est une colonne. C'est une information mesurée pour chaque observation.

> `mu_night_full` = « le sentiment moyen de la nuit » → une variable.
> `gap` = « le saut de prix à l'ouverture » → une autre variable.

Tu as **81 variables**.

## 0.3 — Une cible (ou « target »)

La **cible**, c'est la variable que tu veux **prédire**. Toutes les autres servent à la prédire.

> Cible : `y_gap` = 1 si l'action ouvre en hausse, 0 sinon.

## 0.4 — Un panel

Un **panel** (ou données de panel) est un tableau à **deux dimensions d'identification** : des individus
(ici, les titres) observés à plusieurs dates.

| Type de données | Structure | Exemple |
|---|---|---|
| Coupe transversale | plusieurs individus, **une** date | le prix des 500 actions du S&P le 3 mars 2022 |
| Série temporelle | **un** individu, plusieurs dates | le prix d'AAPL de 2020 à 2022 |
| **Panel** | plusieurs individus × plusieurs dates | **le prix des 5 titres, chaque jour, 2020-2022** |

Le panel est plus riche : il permet de comparer **dans le temps** (AAPL aujourd'hui vs AAPL le mois
dernier) *et* **entre individus** (AAPL vs TSLA le même jour). Mais il impose une discipline : beaucoup de
calculs doivent être faits **titre par titre**, sinon on mélange l'histoire d'AAPL avec celle de TSLA.
C'est le rôle du `groupby("Ticker")` que tu verras partout.

Un panel est **équilibré** si tous les individus ont le même nombre de dates. Le tien l'est :
548 jours pour chacun des 5 titres. C'est important — un panel déséquilibré donne mécaniquement plus de
poids aux titres les mieux couverts.

## 0.5 — Une fuite d'information (« data leakage »)

C'est **l'erreur la plus grave** en finance quantitative, et il faut la comprendre tout de suite.

Il y a fuite quand une variable explicative contient, directement ou indirectement, de l'information qui
n'existait **pas encore** au moment où l'on prétend faire la prédiction.

> **Exemple caricatural.** Je veux prédire s'il pleuvra demain. J'utilise comme variable « le nombre de
> parapluies ouverts demain à midi ». Mon modèle est parfait à 99 %. Il est aussi parfaitement inutile :
> le jour où je dois prédire, je ne connais pas cette variable.

En finance, la fuite est presque toujours **subtile** : une moyenne mobile mal décalée, une normalisation
qui utilise toute la période, un découpage aléatoire au lieu de chronologique. Elle ne provoque aucune
erreur — elle produit juste des résultats trop beaux.

**La règle unique de tout ce projet :**

> Une variable est utilisable pour prédire une cible **si et seulement si** elle est entièrement connue
> **avant** que la cible ne commence à se former.

---

# Chapitre 1 — La configuration

```python
PROJET = r"C:\Users\semy4\OneDrive\Bureau\Fintech_project"
C_JOUR, C_HEURE, C_TICKER = "Jour", "Heure_decimale", "Ticker"
C_POS, C_NEG, C_NEU = "FinBERT_Positive", "FinBERT_Negative", "FinBERT_Neutral"
TICKERS = ["AAPL", "AMZN", "META", "NVDA", "TSLA"]
DEBUT, FIN = "2020-01-02", "2022-03-04"
```

## Pourquoi tout regrouper ici

C'est un principe de génie logiciel appelé **« une seule source de vérité »** (*single source of truth*).

**Le problème qu'il résout.** Imagine que le nom de ta colonne de date soit écrit en dur dans 30 cellules
différentes. Le jour où tu la renommes, il faut modifier 30 endroits. Tu en oublieras un, et le notebook
plantera trois heures plus tard sans que tu comprennes pourquoi.

**En recherche, c'est encore plus important que dans l'industrie**, pour une raison précise : la
**reproductibilité**. Un mémoire doit pouvoir être refait à l'identique. Si les paramètres sont éparpillés,
personne — pas même toi dans six mois — ne saura quelle version a produit quel résultat.

**La valeur ajoutée concrète :** changer de machine = modifier **une ligne**. Changer de période d'étude =
modifier **une ligne**. C'est aussi ce qui te permet de faire une **analyse de sensibilité** : refaire tout
avec `DEBUT = "2021-01-01"` pour voir si les conclusions tiennent.

---

# Chapitre 2 — Charger les messages

## Ce que dit la sortie

```
3,711,333 messages chargés
Colonnes : ['Tweet', 'Ticker', 'Jour', 'Heure_decimale',
            'Texte_Nettoye', 'FinBERT_Positive',
            'FinBERT_Negative', 'FinBERT_Neutral']
```

## 2.1 — Ce que fait FinBERT, expliqué simplement

**BERT** est un modèle de langage : il lit une phrase et la transforme en nombres qui capturent son sens.
**FinBERT** est un BERT ré-entraîné sur des textes financiers.

Pour chaque message, FinBERT renvoie **trois probabilités qui font toujours 1** :

```
p(positif)  +  p(neutre)  +  p(négatif)  =  1
```

Regarde tes propres lignes :

| Message | pos | neg | neu | Lecture |
|---|---|---|---|---|
| « Happy New Year amazing winning AAPL Bull… » | 0,99999 | 0,0000005 | 0,000004 | FinBERT est **certain** que c'est haussier |
| « my dad ended this year by selling half his $aapl… » | 0,00012 | 0,99964 | 0,00024 | **certain** que c'est baissier |
| « Happy New Year :) $AAPL $TSLA $AMZN $SPY » | 0,00007 | 0,00001 | 0,99992 | **aucun contenu financier** |

C'est bien un **modèle probabiliste** : il ne dit pas « ce message est positif », il dit « je suis certain
à 99,999 % que ce message est positif ». Cette nuance est précieuse — elle permet de pondérer un message
franc plus qu'un message ambigu.

## 2.2 — Le chiffre inquiétant : 80,7 % de neutre

```
Masse 'neutre' moyenne de FinBERT : 0.807
Messages classés neutres à plus de 90 % : 75.8%
```

**Trois messages sur quatre** sont classés « neutres à plus de 90 % ». Autrement dit, FinBERT ne voit
aucun contenu financier dans les trois quarts de ton corpus.

**Pourquoi ?** FinBERT a été entraîné sur de la **presse financière** : dépêches Reuters, notes
d'analystes, rapports annuels. Un langage formel, complet, en phrases. Or StockTwits, c'est :

> « $TSLA 🚀🚀🚀 to the moon »
> « $AAPL calls printing »
> « diamond hands 💎🙌 »

FinBERT n'a jamais vu ça pendant son entraînement. Il ne comprend ni les emojis, ni le jargon d'options,
ni les mèmes. Il répond donc « neutre », qui est sa position de repli.

**Ce phénomène a un nom : le décalage de domaine** (*domain shift*). Un modèle entraîné sur une
distribution A appliqué à une distribution B perd de sa performance, même si les deux « parlent de la même
chose ».

**Quelle est la conséquence réelle ?** Ton signal ne repose pas sur 3,7 millions de messages : il repose
sur **le quart** que FinBERT sait lire, soit environ 900 000 messages. Les 2,8 millions restants ajoutent
du zéro à ta moyenne — ils la **diluent** sans l'orienter.

**Et pourtant le signal existe quand même.** C'est en soi un résultat intéressant : même avec un
instrument de mesure imparfait qui ignore 75 % du corpus, on détecte une corrélation de 0,157. Avec un
classifieur adapté au langage des forums, elle serait probablement plus forte. C'est ta **première piste
d'amélioration**, et il faut la présenter comme telle.

## 2.3 — Le déséquilibre entre titres

```
TSLA    1 906 665      (51 % du corpus à lui seul)
AAPL      904 344
AMZN      421 330
META      256 031
NVDA      222 963
```

TSLA représente **plus de la moitié** de tous les messages. C'est un fait sur lequel il faut réfléchir.

**Ce que ça veut dire :** si tu calculais une statistique globale sur tous les messages mélangés, elle
serait à moitié une statistique sur TSLA. Toute conclusion « globale » serait en réalité une conclusion
sur Tesla.

**Pourquoi ce n'est pas grave ici :** parce que le panel agrège **par titre et par jour**. Chaque
observation pèse pareil, qu'elle contienne 96 messages (NVDA) ou 1 138 (TSLA). Le déséquilibre du corpus
brut ne se transmet donc pas au panel.

**Mais il reste une conséquence subtile.** La qualité de mesure n'est pas la même partout : le sentiment
moyen d'une nuit NVDA (96 messages) est bien plus bruité que celui d'une nuit TSLA (1 138 messages). C'est
un cas d'**hétéroscédasticité** — la variance de l'erreur n'est pas constante. Une amélioration possible
serait de pondérer les observations par `√n`.

---

# Chapitre 3 — Le score : `mu = pos − neg`

```python
m["score"] = m["p_pos"] - m["p_neg"]
```

## 3.1 — Pourquoi cette formule et pas une autre

On veut résumer trois probabilités en **un seul nombre** qui dit « à quel point ce message est haussier ».

```
score = p(positif) − p(négatif)          compris entre −1 et +1
```

**Trois propriétés utiles :**

1. **Bornée** entre −1 et +1 — comparable d'un message à l'autre.
2. **Symétrique** — un message parfaitement haussier vaut +1, parfaitement baissier −1.
3. **Le neutre annule** — si `p_neu = 1`, alors `pos ≈ neg ≈ 0` et le score vaut 0.

**Pourquoi pas `p_pos` seul ?** Parce qu'un message à `p_pos = 0,3` peut être soit modérément haussier
(`neg = 0,1`), soit très partagé (`neg = 0,3`). La différence distingue les deux.

**Pourquoi pas `p_pos / (p_pos + p_neg)` ?** Cette formule ignore l'intensité : un message à
(0,50 ; 0,05) et un à (0,05 ; 0,005) donneraient tous deux ≈ 0,91. Or le premier est bien plus informatif.

## 3.2 — Le piège de l'ambiguïté

Un score de 0 recouvre **deux situations très différentes** :

| Cas | pos | neg | neu | score | Interprétation |
|---|---|---|---|---|---|
| A | 0,00 | 0,00 | 1,00 | 0 | message sans contenu financier |
| B | 0,50 | 0,50 | 0,00 | 0 | message **très** chargé mais ambigu |

C'est pour cela qu'on conserve `pos` et `neg` **séparément** dans le panel : le score seul perd cette
information.

## 3.3 — L'identité qui a des conséquences

Puisque `score = p_pos − p_neg` pour **chaque** message, la moyenne suit :

```
        1                                  
mu  =  ─── × Σ ( pos_i − neg_i )  =  moyenne(pos) − moyenne(neg)  =  pos − neg
        n   i
```

Ce n'est pas une approximation, c'est une **identité exacte**. Le notebook la vérifie : erreur maximale
**1,1 × 10⁻¹⁶** — la précision de la machine.

> ### ⚠ La conséquence pour la modélisation : la colinéarité parfaite
>
> Si tu mets `mu`, `pos` et `neg` ensemble dans une régression, tu crées une relation
> **linéairement exacte** entre trois variables explicatives.
>
> **Pourquoi c'est un problème.** Une régression cherche des coefficients β tels que
> `y ≈ β₁·mu + β₂·pos + β₃·neg`. Mais si `mu = pos − neg`, alors une infinité de combinaisons donnent
> exactement le même résultat :
>
> - `(β₁, β₂, β₃) = (1, 0, 0)` → prédiction identique à
> - `(β₁, β₂, β₃) = (0, 1, −1)` → identique à
> - `(β₁, β₂, β₃) = (10, −9, 9)` → identique…
>
> La solution n'est **pas unique**. Numériquement, l'algorithme choisit une des infinités de solutions,
> souvent avec des coefficients énormes et de signes absurdes.
>
> **C'est exactement ce qui s'est passé dans ton notebook 06** : `z_mu_night_full` avec un coefficient de
> **+1,00** et `z_pos_night_full` avec **−0,74**, alors que les deux mesurent l'optimisme et devraient
> avoir le même signe. Les coefficients ne veulent rien dire.
>
> **La mesure de ce problème s'appelle le VIF** (*Variance Inflation Factor*) :
>
> ```
              1
VIF(j)  =  ────────        où R²(j) = R² de la régression de la variable j
            1 − R²(j)             sur toutes les autres variables
```
>
> où `R²ⱼ` est le R² de la régression de la variable *j* sur toutes les autres. Si une variable est
> parfaitement prédite par les autres, `R²ⱼ = 1` et le VIF explose. Règle usuelle : **au-dessus de 5, on
> retire**. Dans ton notebook 06, `ret_cc_lag1` a un VIF de **1 516**.
>
> **Remarque importante :** la colinéarité n'abîme **pas** la qualité de la *prédiction* (l'AUC reste
> bonne), elle abîme l'*interprétation*. Les arbres de décision n'en souffrent pas du tout. C'est donc un
> problème de mémoire — tu veux pouvoir expliquer tes coefficients — pas un problème de performance.

---

# Chapitre 4 — Les étiquettes Bullish / Bearish

```
Aucune colonne d'étiquette Bullish/Bearish dans ce fichier.
```

Le jeu de données Kaggle contient une colonne où **l'auteur du message a lui-même déclaré** son
orientation (bouton « Bullish » ou « Bearish » sur StockTwits). Environ 20-25 % des messages en portent
une. Ton fichier ne l'a pas conservée.

## Pourquoi il faut aller la rechercher

C'est ce qu'on appelle une **vérité terrain externe** (*external ground truth*) : une mesure indépendante
de la même chose, produite par une autre source.

**Usage n° 1 — valider ton instrument de mesure.** Tu as un problème que le raisonnement seul ne peut pas
résoudre : FinBERT met 80 % sur « neutre ». Le jury demandera : *« votre mesure mesure-t-elle réellement
le sentiment ? »*

Avec les étiquettes, tu peux calculer l'AUC de FinBERT pour retrouver l'orientation déclarée. Si elle
dépasse 0,70, tu écris :

> « Sur les N messages portant une étiquette posée par leur auteur, le score FinBERT retrouve
> l'orientation déclarée avec une AUC de 0,XX. L'instrument de mesure est donc **validé sur une source
> externe et indépendante**. »

C'est de la **validation d'instrument**. En actuariat comme en sciences expérimentales, c'est une étape
obligatoire qu'on saute rarement impunément.

**Usage n° 2 — une mesure alternative gratuite.** Tu peux construire, sans aucun modèle :

```
                 nombre de messages « Bullish »
bull_rate  =  ──────────────────────────────────────
              nb « Bullish »  +  nb « Bearish »
```

et refaire toute la partie 4 avec. Si les deux mesures donnent la même conclusion, ton résultat ne dépend
plus du choix de FinBERT. C'est le **test de robustesse le plus rentable** du mémoire : peu de travail,
beaucoup de crédibilité.

---

# Chapitre 5 — Le fuseau horaire

## 5.1 — Le problème

Ton fichier a `Jour` et `Heure_decimale`. Mais `Heure_decimale` est **un nombre sans étiquette** : rien ne
dit si c'est l'heure de New York ou l'heure UTC.

Or la bourse de New York ouvre à **9h30 heure locale**, ce qui donne :

| Période | Fuseau NY | 9h30 NY = |
|---|---|---|
| novembre → mars | EST (UTC−5) | **14h30 UTC** |
| mars → novembre | EDT (UTC−4) | **13h30 UTC** |

**Si on se trompe de 5 heures, tous les messages changent de fenêtre.** Ceux de 14h UTC — juste avant
l'ouverture, donc de l'information **prédictive** — seraient rangés dans `mkt`, une fenêtre
**contemporaine**. Le signal disparaîtrait, ou une fuite apparaîtrait.

Et attention : le décalage **n'est pas constant**. Retrancher 5 h toute l'année fausserait environ
**8 mois sur 12** (la période d'heure d'été). C'est pour cela qu'on utilise toujours
`tz_localize` + `tz_convert` et **jamais** une soustraction manuelle : la bibliothèque connaît les dates
de changement d'heure, pas nous.

## 5.2 — Le diagnostic : trancher par les données

On ne cherche pas la réponse dans la documentation — on la **déduit du comportement observé**.

**L'idée.** Les marchés produisent une empreinte horaire très reconnaissable : l'activité explose à
l'ouverture, reste forte pendant la séance, s'effondre la nuit. Il suffit donc de regarder **à quelle
heure les gens écrivent**.

```
Heure la plus active : 10h
part 9h-16h  : 59.3%      ← si les heures sont en NY
part 13h-21h : 44.0%      ← si les heures sont en UTC

=> VERDICT : les heures sont déjà en HEURE DE NEW YORK.
```

Le pic à **10h** et 59,3 % des messages entre 9h et 16h : c'est sans ambiguïté. Tes heures sont déjà en
heure de marché, aucune conversion n'est nécessaire.

**Pourquoi ce test fonctionne si bien.** Les deux hypothèses prédisent des choses **différentes et
mutuellement exclusives**. Si c'était de l'UTC, le pic tomberait vers 15-16h (= 10-11h NY). Il tombe à
10h. Une hypothèse est éliminée.

C'est la démarche scientifique de base : formuler deux hypothèses concurrentes, trouver une observation
qui les distingue, et laisser les données trancher.

## 5.3 — Le second contrôle, indépendant

```
Messages par jour — vendredi : 5,408   samedi : 935   (rapport 0.17)
Part des messages du samedi postés avant 6h : 13.1%
```

**Pourquoi un deuxième test ?** Parce qu'un seul test peut mentir. Si la communauté StockTwits était très
européenne, le profil horaire serait décalé pour une raison qui n'a rien à voir avec le fuseau
d'enregistrement.

**L'idée du test.** Si les heures étaient en UTC, le tout début du samedi UTC (00h-06h) correspondrait au
**vendredi soir new-yorkais** (19h-01h) — encore actif. On attendrait donc beaucoup de messages avant 6h
le samedi. On en trouve **13,1 %**, une valeur faible : cohérent avec l'hypothèse « heure de New York ».

Les deux tests, construits sur des raisonnements différents, donnent la même réponse. C'est ce qu'on
appelle une **convergence de preuves** — bien plus solide qu'un test unique.

**Au passage**, le rapport vendredi/samedi de 0,17 est lui-même une validation : l'activité s'effondre le
week-end, comme attendu quand on parle de bourse.

> **Pour le mémoire :** cette figure va en annexe. Elle répond par avance à la question
> *« comment savez-vous que vos fenêtres sont bien alignées ? »* — et cette question **sera** posée.

---

# Chapitre 6 — Le calendrier de bourse

```python
CALENDRIER = np.array(sorted(fin["Date"].unique()))
```

## L'idée : déduire le calendrier des prix eux-mêmes

On pourrait installer une bibliothèque de calendriers boursiers. On fait autrement, et c'est **plus
fiable** : si Yahoo Finance renvoie une ligne de prix pour une date, c'est que la bourse était ouverte ce
jour-là.

```
607 jours de bourse dans le calendrier
Week-ends présents (doit être 0) : 0
  2020-01-20 : absent — férié bien exclu      (Martin Luther King Day)
  2020-07-03 : absent — férié bien exclu      (Independence Day observé)
  2020-11-26 : absent — férié bien exclu      (Thanksgiving)
  2020-12-25 : absent — férié bien exclu      (Noël)
  2021-07-05 : absent — férié bien exclu      (Independence Day observé)
```

Ce calendrier gère **automatiquement** : week-ends, fériés fédéraux américains, fermetures
exceptionnelles, et même les décalages de fériés (le 4 juillet 2020 tombait un samedi, le marché a fermé
le vendredi 3).

## Le principe général à retenir

> Quand deux sources de données doivent être alignées, **déduis le calendrier de la source la plus
> contraignante** plutôt que d'en importer un de l'extérieur.

Un calendrier externe peut diverger de tes données (mauvaise place boursière, mise à jour manquée, fuseau
différent) et tu ne le verras jamais. Un calendrier déduit ne peut pas diverger — il *est* les données.

## Une subtilité importante : la marge d'amorçage

```
3,035 lignes de prix | 2019-11-04 -> 2022-03-31
```

Tes prix commencent le **4 novembre 2019**, deux mois avant la période d'étude. Ce n'est pas un hasard —
c'est nécessaire, pour deux raisons :

1. **`prev_close` du 2 janvier 2020** est la clôture du 31 décembre 2019. Sans elle, le premier `gap` de
   chaque titre serait vide.
2. **`vol_20d`** a besoin de 20 jours d'historique. Sans amorçage, tout le premier mois serait vide.

**Une asymétrie à savoir expliquer :** les **prix** remontent avant 2020, les **messages** non. C'est
pourquoi `vol_20d` est renseigné dès la première ligne alors que `mu_night_z20` est vide pendant les 20
premiers jours. Ce n'est pas une incohérence, c'est la conséquence de deux sources qui ne commencent pas
au même moment.

---

# Chapitre 7 — Affecter chaque message

C'est **le cœur du notebook**. Tout le reste n'est que de l'agrégation.

## 7.1 — Les six fenêtres

| Fenêtre | De | À | Durée |
|---|---|---|---|
| `overnight(D)` | **16h00 du jour de bourse précédent** | 00h00 du jour D | ~8 h (ou ~56 h le lundi) |
| `pre(D)` | 00h00 du jour D | 09h30 | 9,5 h |
| `night_full(D)` | = `overnight` ∪ `pre` | — | toute la fermeture |
| `open30(D)` | 09h30 | 10h00 | 0,5 h |
| `mkt(D)` | 10h00 | 16h00 | 6 h |
| `post(D)` | 16h00 du jour D | 00h00 du lendemain | 8 h |

## 7.2 — Pourquoi ce découpage et pas un autre

Ces frontières ne sont pas arbitraires : elles correspondent à des **changements de régime de marché**.

| Frontière | Ce qui change |
|---|---|
| **16h00** | la bourse ferme, les prix cessent d'être cotés en continu |
| **00h00** | frontière calendaire (utile pour séparer « soir » et « matin ») |
| **09h30** | la bourse ouvre — le prix saute d'un coup, c'est le **gap** |
| **10h00** | la première demi-heure est atypique : volatilité extrême, spreads larges, exécution des ordres accumulés pendant la nuit |
| **16h00** | la bourse ferme à nouveau |

**Pourquoi isoler `open30` ?** Parce que les 30 premières minutes ne ressemblent à rien d'autre. Les
ordres accumulés pendant 17 h s'exécutent, la volatilité y est 3 à 5 fois supérieure au reste de la
séance. Les mélanger au reste diluerait les deux.

## 7.3 — La règle du lundi

Regarde bien la définition de `overnight` : elle part du **jour de bourse** précédent, pas du jour
calendaire.

- **Mardi** → `overnight(mardi)` = lundi 16h → mardi 00h. C'est exactement `post(lundi)`.
- **Lundi** → `overnight(lundi)` = **vendredi** 16h → lundi 00h. Cela comprend le vendredi soir,
  **tout le samedi et tout le dimanche**.

**Pourquoi c'est la bonne définition.** Ce qui compte n'est pas le calendrier civil, c'est **l'intervalle
pendant lequel le marché est fermé**. Un investisseur qui achète le vendredi à 16h ne peut rien faire
jusqu'au lundi 9h30 : tout ce qui se dit pendant ces 65 heures est pertinent pour le gap du lundi.

## 7.4 — Deux affectations, pas une

Un message peut appartenir à **deux fenêtres à la fois** — et ce n'est pas un bug :

- un message du **jeudi 18h** est dans `post(jeudi)` **et** dans `overnight(vendredi)` ;
- un message du **samedi 11h** est dans `overnight(lundi)` seulement (le samedi n'étant pas un jour de
  bourse, il n'a pas de fenêtre `post`).

Ce sont **deux points de vue** sur le même message : « ce qui s'est dit après la clôture de jeudi » et
« ce qui s'est dit avant l'ouverture de vendredi ». Les deux sont légitimes, et ils vivent dans des
colonnes différentes.

## 7.5 — L'algorithme, expliqué

```python
i_gauche = np.searchsorted(CALENDRIER, d, side="left")   # 1er jour de bourse >= date
i_droite = np.searchsorted(CALENDRIER, d, side="right")  # 1er jour de bourse >  date
i_nuit = np.where(apres_cloture, i_droite, i_gauche)
```

`searchsorted` répond à : *« à quelle position insérer cette date dans la liste triée des jours de
bourse ? »* C'est une **recherche dichotomique**, en O(log n) — indispensable ici, car une boucle Python
sur 3,7 millions de messages prendrait des heures alors que ceci prend quelques secondes.

La logique :

- message posté **après 16h** → il se rattache forcément au jour de bourse **suivant** (`side="right"`) ;
- message posté **avant 16h** → il se rattache au premier jour de bourse **≥ sa date** (`side="left"`),
  donc à lui-même si c'est un jour ouvré, sinon au prochain (samedi → lundi).

## 7.6 — Les résultats

```
Affectation A — intra-journalière :        Affectation B — nocturne :
  mkt       1 793 119                        overnight    1 096 322
  post        825 168                        pre            619 328
  pre         619 328                        (aucune)     1 995 683
  (aucune)    271 154
  open30      202 564
```

**Lecture.** 1,79 M de messages pendant la séance (48 %), 1,10 M pendant la nuit (30 %), 271 154 un jour
non ouvré (7 %). Les 271 154 messages de week-end n'ont **pas** de fenêtre intra-journalière — normal, il
n'y a pas de séance ce jour-là — mais ils comptent bien dans la fenêtre nocturne du lundi.

---

# Chapitre 8 — Les trois contrôles d'affectation

C'est un principe méthodologique fondamental : **ne jamais faire confiance à un calcul complexe sans le
vérifier par un chemin indépendant.**

## Contrôle 1 — Le lundi absorbe-t-il le week-end ?

```
messages overnight, en moyenne — lundi :  629
                                 autres :  348
rapport : 1.81x
```

**Ce qu'il teste.** Si `overnight` partait du jour **calendaire** précédent au lieu du jour de **bourse**,
le lundi aurait autant de messages que les autres jours. Le rapport de 1,81× prouve que la règle est bien
appliquée.

**Pourquoi 1,81 et pas 3 ?** Parce que l'activité s'effondre le week-end : le samedi ne pèse que 0,17× un
vendredi. Le lundi couvre 3 jours civils, mais deux d'entre eux sont très calmes. Le chiffre attendu est
donc autour de 1 + 0,17 + 0,17 ≈ 1,3 à 2. **1,81 est exactement dans la fourchette.**

Ce genre de vérification — prédire l'ordre de grandeur *avant* de regarder — est la meilleure façon de
détecter une erreur.

## Contrôle 2 — Aucune contamination

```
messages en infraction : 0   -> doit valoir 0
```

**Ce qu'il teste.** Qu'aucun message posté **pendant la séance** (9h30-16h) ne soit classé dans une
fenêtre nocturne. Une seule infraction créerait une fuite : de l'information de la séance servirait à
prédire l'ouverture du même jour.

C'est un test **binaire** : 0 ou échec. Pas de zone grise.

## Contrôle 3 — L'additivité

```
overnight 1 096 322 + pre 619 328 = 1 715 650   |   night_full 1 715 650
cohérent : True
```

**Ce qu'il teste.** Que `night_full` soit exactement l'union de `overnight` et `pre`, sans doublon ni
oubli.

**Pourquoi c'est important.** Ces trois variables seront utilisées ensemble dans les analyses. Si
l'additivité était fausse, tous les raisonnements du type « le signal vient plutôt de `pre` que de
`overnight` » seraient faux.

---

# Chapitre 9 — Agréger : les sept statistiques

Pour chaque triplet (**titre**, **jour**, **fenêtre**), on résume tous les messages en sept nombres.

## 9.1 — Les sept, une par une

### `n` — le nombre de messages

```
n  =  nombre de messages tombant dans la fenêtre
```

**Ce qu'elle mesure :** le **volume d'attention**. Combien de personnes parlent de ce titre.

**Sa valeur ajoutée :** l'attention et le sentiment sont **deux choses différentes**. Une action peut être
massivement discutée sans que l'opinion soit tranchée. Le volume prédit l'**amplitude** des mouvements ;
le sentiment prédit leur **direction**.

### `mu` — le sentiment moyen

```
        1     n
mu  =  ─── ×  Σ  score_i           (la moyenne arithmétique des scores)
        n    i=1
```

**Ce qu'elle mesure :** la **direction** de l'opinion.

**La propriété statistique clé.** `mu` est une **moyenne d'échantillon**. Son erreur type est :

```
              écart-type des scores individuels        σ
erreur type = ──────────────────────────────────  =  ─────
                      racine de n                     √n
```

**C'est la formule la plus importante de tout ton mémoire.** Elle explique pourquoi la première tentative
a échoué :

| Corpus | n par jour | Erreur type | Lecture |
|---|---|---|---|
| Ancien (Reddit 2023-2026) | **2** | σ/√2 ≈ **0,71 σ** | `mu` est du bruit pur |
| Nouveau (StockTwits) | **~500** | σ/√500 ≈ **0,045 σ** | `mu` est une vraie mesure |

Le bruit est divisé par **√250 ≈ 16**. Avec deux messages, `mu` sautait de −1 à +1 au gré de deux tweets
tirés au hasard, sans lien avec l'opinion réelle du marché.

> **L'analogie.** Tu veux connaître la taille moyenne des Tunisiens. Tu mesures 2 personnes → ta moyenne
> peut valoir 1,55 m ou 1,90 m selon qui tu croises. Tu en mesures 500 → ta moyenne sera très proche de
> la vraie valeur. Ce n'est pas que les 500 personnes soient « meilleures » : c'est que **la moyenne de
> beaucoup d'observations est stable**.

### `sd` — l'écart-type

```
           ┌────────────────────────────────┐
           │    1      n                     │
sd  =  \   │  ─────  ×  Σ  (score_i − mu)²   │
        \  │   n−1     i=1                   │
         \√└────────────────────────────────┘
```

**Ce qu'elle mesure :** le **désaccord**. Est-ce que tout le monde dit la même chose, ou est-ce que la
communauté est divisée ?

**Sa valeur ajoutée théorique.** En finance, le désaccord entre investisseurs est une variable étudiée
depuis longtemps (Miller 1977, Diether et al. 2002). L'idée : quand les opinions divergent fortement, le
volume d'échange augmente et la volatilité aussi. Un `sd` élevé avec `mu ≈ 0` ne veut pas dire « rien ne
se passe » — cela veut dire « ça se bagarre ».

**Pourquoi `n−1` et pas `n` ?** C'est la **correction de Bessel**. Diviser par `n` sous-estime
systématiquement la variance, parce qu'on utilise `mu` — lui-même estimé sur les mêmes données — comme
centre. On « perd un degré de liberté ». Diviser par `n−1` rend l'estimateur **non biaisé**.

### `pos` et `neg` — les intensités

```
pos = moyenne des p(positif) des n messages
neg = moyenne des p(négatif) des n messages
```

**Leur valeur ajoutée :** distinguer le neutre du partagé (voir §3.2). Et permettre l'asymétrie : la
littérature montre que les mauvaises nouvelles se propagent différemment des bonnes (Hong & Stein 1999).
Séparer `pos` et `neg` permet de tester si un coefficient diffère de l'autre.

### `p10` et `p90` — les déciles

**Ce qu'ils mesurent :** la forme des **queues** de la distribution.

- `p10` = la valeur en dessous de laquelle se trouvent les 10 % de messages les plus négatifs
- `p90` = la valeur au-dessus de laquelle se trouvent les 10 % les plus positifs

**Pourquoi des déciles plutôt que le min et le max ?** Parce que le minimum et le maximum sont **fragiles**
— un seul message extrême les fait bouger. Les déciles sont des **statistiques robustes** : il faut
déplacer 10 % de l'échantillon pour les changer.

> **L'analogie.** Le salaire moyen d'un village change complètement si un milliardaire s'y installe. Le
> salaire médian, ou le 9ᵉ décile, ne bougent presque pas. Voilà ce qu'est la robustesse.

## 9.2 — Pourquoi `night_full` est recalculé sur les messages

C'est un point **mathématique** important, et il fait une bonne question d'oral.

### Ce qui est additif

La moyenne d'une union **se déduit** des moyennes des sous-groupes, pondérées par les effectifs :

```
                  n1 × mu1  +  n2 × mu2
mu(union)  =  ───────────────────────────      (moyenne pondérée par les effectifs)
                      n1  +  n2
```

Vérifié sur tes données : erreur maximale **1,67 × 10⁻¹⁶**.

### Ce qui n'est PAS additif

**L'écart-type.** La variance d'une union comporte **deux termes** — c'est la **loi de la variance
totale** (ou décomposition de Huygens) :

```
                    n1×σ1² + n2×σ2²        n1×(mu1−mu)² + n2×(mu2−mu)²
variance(union) = ─────────────────  +  ─────────────────────────────
                      n1 + n2                      n1 + n2
                  └──────┬──────┘        └───────────┬───────────┘
                   variance INTRA              variance INTER
              (dispersion DANS chaque      (écart ENTRE les moyennes
                   sous-fenêtre)              des deux sous-fenêtres)
```

- La **variance intra** = « à quel point ça varie *à l'intérieur* de chaque groupe »
- La **variance inter** = « à quel point les groupes sont *différents entre eux* »

> **L'analogie.** Deux classes passent un examen. Classe A : moyenne 8, tous entre 7 et 9. Classe B :
> moyenne 16, tous entre 15 et 17. Dans chaque classe, la dispersion est **faible**. Mais si tu mélanges
> les deux classes, la dispersion devient **énorme** — parce que les deux moyennes sont très éloignées.
> Cette dispersion supplémentaire, c'est la variance inter.

**Ton panel d'origine faisait l'erreur** : il stockait la moyenne pondérée des écarts-types, ce qui ne
retient que la variance intra. Sur AAPL au 2 janvier 2020 : valeur stockée **0,4082**, vraie valeur
**0,4098**. L'écart est faible ici parce que les deux fenêtres ont des moyennes proches — mais il grandit
précisément les nuits où le sentiment bascule entre le soir et le matin, c'est-à-dire les nuits
intéressantes.

**Les percentiles.** Là, c'est pire : **il n'existe aucune formule**. On ne peut pas obtenir le 9ᵉ décile
d'une union à partir des 9ᵉˢ déciles des sous-groupes — il faut les scores individuels.

C'est pour cela que `disp_night_full` était **entièrement vide** dans ton ancien panel : le script tentait
un calcul impossible, et pandas renvoyait `NaN` sans lever d'erreur.

**La solution du notebook 03 :** calculer les statistiques de `night_full` directement sur l'union des
messages. Les trois problèmes disparaissent par construction.

---

# Chapitre 10 — Le format large et le squelette

```
Squelette : 2,740 lignes (5 actions × 548 jours)
Après fusion : 2,740 lignes x 44 colonnes
```

## Pourquoi partir d'un squelette

On construit d'abord le **produit cartésien** de tous les titres × tous les jours de bourse, puis on y
attache les données. On ne part **pas** des messages.

**Le problème que ça évite.** Si on partait des messages, un jour où personne n'a parlé de NVDA
**disparaîtrait** silencieusement du panel. Résultat : NVDA aurait 547 jours et les autres 548. Le panel
serait déséquilibré, et le jour manquant serait invisible.

```
Jours sans aucun message nocturne, par ticker :
  NVDA    1
  TSLA    3
```

Grâce au squelette, ces 4 jours **existent** avec `n = 0`. On les voit, on peut décider quoi en faire.
S'ils avaient disparu, on ne saurait même pas qu'ils ont existé.

## La distinction absence / zéro

Une subtilité qui compte :

| Cas | Valeur correcte | Pourquoi |
|---|---|---|
| Aucun message cette nuit | `n = 0` | c'est une information : personne n'a parlé |
| Écart-type d'un seul message | `NaN` | on ne peut pas calculer une dispersion sur 1 point |
| Décile de zéro message | `NaN` | rien à ordonner |

**On ne fabrique pas une valeur qu'on ne peut pas calculer.** Mettre 0 à la place d'un `NaN` reviendrait
à affirmer « la dispersion était nulle », ce qui est faux — on ne sait pas.

---

# Chapitre 11 — Les variables de marché

## 11.1 — La décomposition, l'idée centrale du mémoire

Une journée boursière a **deux moitiés qui n'obéissent pas aux mêmes règles** :

```
   16h00 (J−1)                    9h30 (J)                     16h00 (J)
        │                             │                             │
        │◄──── marché FERMÉ ─────────►│◄──── marché OUVERT ────────►│
        │        « le gap »           │        « la séance »        │
   prev_close                      Open                         Close
```

| Cible | Formule | Ce qui s'y passe |
|---|---|---|
| `gap` | `Open / prev_close − 1` | l'information accumulée s'incorpore d'un coup à l'ouverture |
| `ret_oc` | `Close / Open − 1` | des milliers d'intervenants arbitrent en continu |
| `ret_cc` | `Close / prev_close − 1` | le total |

**L'identité qui les relie :**

```
( 1 + gap ) × ( 1 + ret_oc )  =  1 + ret_cc
```

Vérifiée sur tes données : erreur maximale **2,22 × 10⁻¹⁶**.

**Pourquoi une multiplication et pas une addition ?** Parce que les rendements se **composent**. Si une
action passe de 100 à 110 (+10 %) puis de 110 à 121 (+10 %), le total n'est pas +20 % mais +21 % :
1,10 × 1,10 = 1,21. Sur des petits rendements l'approximation additive est bonne, mais l'identité exacte
est multiplicative.

**Pourquoi cette décomposition change tout.** Le sentiment nocturne prédit le gap (ρ = +0,157) et ne
prédit pas la séance (ρ = −0,010). Si tu ne modélises que `ret_cc`, tu **mélanges** un morceau prévisible
et un morceau qui est du bruit pur. Le signal se dilue.

**C'est exactement ce qui a fait échouer ta phase 5 initiale.**

## 11.2 — `prev_close` : le pivot

Ce n'est pas un rendement, c'est une **référence**. Sans elle, aucun gap n'est calculable.

C'est aussi la **seule colonne de prix légalement utilisable** comme variable explicative :
`Open`, `High`, `Low`, `Close` du jour J contiennent la réponse qu'on cherche.

## 11.3 — `vol_20d` : la volatilité réalisée

```
vol_20d(t) = écart-type des rendements ret_cc des 20 jours PRÉCÉDENTS

             c'est-à-dire  ret_cc(t−1), ret_cc(t−2), ..., ret_cc(t−20)
             et surtout PAS ret_cc(t)
```

**Ce qu'elle mesure :** le **régime de risque**. Un titre agité ces dernières semaines a de fortes chances
de le rester.

**La propriété qui la rend utile : le regroupement de volatilité** (*volatility clustering*). Observé par
Mandelbrot en 1963, il n'a jamais disparu :

> « Les grands changements tendent à être suivis de grands changements — de l'un ou l'autre signe — et les
> petits changements par de petits changements. »

C'est le fondement de toute la famille des modèles **ARCH/GARCH** (Engle 1982, prix Nobel 2003). Et c'est
pourquoi la volatilité **se prédit** (R² de 0,3 à 0,6) alors que la direction ne se prédit presque pas
(R² de 0,001 à 0,01).

> **Le `.shift(1)` est obligatoire.** La fenêtre doit couvrir les 20 jours **précédents**, pas les 20
> jours **incluant aujourd'hui**. Sinon on utilise l'information du jour pour prédire le jour : c'est la
> fuite la plus fréquente et la plus discrète en finance quantitative.
>
> En pandas : `s.shift(1).rolling(20).std()` et **jamais** `s.rolling(20).std()`.

## 11.4 — Le recoupement avec ton script de collecte

```
prev_close   : écart max = 0.00e+00   -> identique
gap          : écart max = 5.33e-16   -> identique
ret_oc       : écart max = 7.77e-16   -> identique
ret_cc       : écart max = 5.43e-16   -> identique
```

**L'idée du test.** Ton fichier contient déjà ces colonnes, calculées par ton script de collecte. Le
notebook les recalcule et **compare**.

**Ce que ça prouve.** Deux implémentations indépendantes, écrites à des moments différents, donnent le
même résultat à la précision machine près. C'est de la **validation croisée d'implémentation** — la même
logique que la double saisie en comptabilité.

Un écart non nul signalerait un `groupby` oublié ou un tri différent — le genre d'erreur silencieuse qui
empoisonne un projet entier.

---

# Chapitre 12 — La fusion

```python
pan = fin[COLS_FIN].merge(panel, on=["Ticker", "Date"], how="left")
```

## Pourquoi une jointure « à gauche » en partant du marché

Une jointure **à gauche** (`how="left"`) garde **toutes** les lignes de la table de gauche (les prix) et
attache les correspondances de droite (le sentiment) quand elles existent.

**Pourquoi partir du marché et pas du texte ?**

| On part de… | Conséquence |
|---|---|
| **Marché** ✅ | on garde tous les jours de bourse ; un jour sans message a `n = 0` |
| Texte ❌ | on garderait les week-ends (pas de prix → cible impossible) et on perdrait les jours de bourse muets |

La **cible** n'existe que les jours de bourse. Il est donc logique que la table des cibles définisse le
périmètre.

```
Panel fusionné : 2,740 lignes x 56 colonnes
Panel équilibré : True
```

---

# Chapitre 13 — Les variables d'attention

Trois transformations du comptage de messages. Elles servent au modèle de **risque**, pas au modèle de
direction.

## 13.1 — `nlog` : passer au logarithme

```
nlog = logarithme népérien de (1 + n)        noté  ln(1 + n)
```

**Le problème.** La distribution de `n` est **très asymétrique** :

| Ticker | médiane | moyenne | maximum |
|---|---|---|---|
| AAPL | 571 | 775 | **6 898** |
| TSLA | 1 138 | 1 605 | **16 722** |
| META | 108 | 217 | **12 337** |

Regarde META : médiane 108, maximum 12 337 — un facteur **114**. La moyenne (217) est le double de la
médiane : signature classique d'une distribution **log-normale**.

**Pourquoi c'est un problème pour un modèle.** Une régression linéaire minimise la somme des **carrés**
des erreurs. Une observation à 12 337 pèse (12 337/108)² ≈ **13 000 fois** plus qu'une observation
médiane. Le modèle serait entièrement déterminé par une poignée de jours extrêmes.

**Ce que fait le logarithme.** Il transforme les rapports en différences :

| n | ln(1+n) | interprétation |
|---|---|---|
| 100 | 4,6 | |
| 1 000 | 6,9 | +2,3 |
| 10 000 | 9,2 | +2,3 |

Chaque **multiplication par 10** ajoute la même quantité. La distribution devient à peu près symétrique et
le modèle traite les observations équitablement.

**Pourquoi `1 + n` et pas `n` ?** Parce que `ln(0)` vaut −∞. Le `+1` gère les 4 nuits sans message.

## 13.2 — `nabn` : l'attention anormale

```
nabn(t) = nlog(t) − moyenne( nlog(t−1), nlog(t−2), ..., nlog(t−20) )
          └──────┘   └──────────────────────────────────────────────┘
          aujourd'hui              la « normale » des 20 jours passés
```

**C'est la variable la plus intéressante du panel** pour un mémoire d'actuariat.

**L'idée.** `nlog` mesure « combien on parle ». `nabn` mesure **« combien on parle *par rapport à
d'habitude* »**.

> **L'analogie.** Un restaurant a 200 clients ce soir. Est-ce beaucoup ? Impossible à dire dans l'absolu.
> Si sa moyenne est de 50, c'est un événement exceptionnel. Si sa moyenne est de 400, c'est une soirée
> catastrophique. **Le niveau seul n'informe pas ; l'écart à la normale, si.**

**Pourquoi cette variable prédit le risque.** Un pic d'attention signale l'arrivée d'une information
nouvelle et importante : résultats trimestriels, annonce réglementaire, tweet d'Elon Musk. Et une
information importante produit un mouvement de prix important — quelle qu'en soit la direction.

C'est documenté : **Da, Engelberg & Gao (2011)** sur Google Trends, **Antweiler & Frank (2004)** sur les
forums boursiers.

**Sur tes données** (notebook 07) : ajouter `nabn` à un modèle de volatilité fait passer le R² hors
échantillon de **0,495 à 0,527**. Le test de Fisher donne F = 38,4 avec p = 5 × 10⁻³⁸. Petit en valeur
absolue, mais massivement significatif — parce que la référence est déjà très bonne.

> ### Le bug corrigé, et pourquoi il compte
>
> Dans ton ancien panel, la référence divisait par 20 **même quand moins de 20 jours étaient
> disponibles**. Le premier jour, la moyenne des « 20 jours précédents » valait donc 0/20 = 0, et
> `nabn = nlog = 5,76` au lieu de ~0.
>
> ```
> Ancien panel : nabn moyen fortement POSITIF, nabn ≈ 5,8 au jour 1
> Nouveau      : nabn moyen = -0.0059   (attendu : ~0)  ✓
> ```
>
> Le correctif est `min_periods=10` : on divise par le nombre **réel** d'observations, et on laisse `NaN`
> tant qu'il n'y en a pas assez. **Un vide honnête vaut mieux qu'un chiffre faux** — un `NaN` est visible
> et se traite ; une valeur fausse se propage silencieusement.

## 13.3 — `disp` : la dispersion robuste

```
disp = p90 − p10           (l'intervalle interdécile : la largeur des 80 % centraux)
```

**Ce qu'elle mesure :** la largeur du **cœur** de la distribution des opinions — l'intervalle interdécile.

**Pourquoi pas l'écart-type ?** Les deux mesurent la dispersion, mais différemment :

| Mesure | Sensibilité aux extrêmes | Interprétation |
|---|---|---|
| écart-type | **forte** (les écarts sont au carré) | dispersion moyenne |
| p90 − p10 | **faible** | largeur du cœur, 80 % central |

Sur des scores FinBERT très polarisés (beaucoup de valeurs à −1, 0 et +1), l'écart-type peut être trompé
par quelques messages extrêmes. La `disp` décrit mieux « à quel point la communauté typique est divisée ».

**Avoir les deux est un avantage :** si `sd` est élevé mais `disp` faible, cela signifie que la dispersion
vient de quelques messages extrêmes, pas d'un désaccord général. Un modèle peut exploiter cette
différence.

---

# Chapitre 14 — Les dérivées nocturnes

Trois façons de répondre à la question **« ce sentiment est-il élevé ? »**.

## 14.1 — `dmu_night` : la variation

```
dmu_night(t) = mu(t) − mu(t−1)          (la variation d'un jour à l'autre)
```

**Ce qu'elle capte :** le **changement d'humeur** plutôt que le niveau.

**Pourquoi c'est différent du niveau.** En finance, ce qui bouge les prix, ce n'est pas l'information
elle-même — c'est la **surprise**, l'écart entre l'information et ce qui était attendu. Une communauté
durablement optimiste n'apprend rien de nouveau au marché ; une communauté qui passe brutalement de
négative à neutre, si.

C'est le même principe que les « surprises de résultats » : ce n'est pas le bénéfice publié qui fait
bouger l'action, c'est l'écart au consensus.

## 14.2 — `mu_night_ma3` : le lissage

```
              mu(t) + mu(t−1) + mu(t−2)
MA3(t)  =  ──────────────────────────────
                         3
```

**Ce qu'elle fait :** réduire le bruit. Une seule nuit peut être atypique ; trois nuits consécutives, plus
rarement.

**Le compromis à comprendre.** Toute moyenne mobile arbitre entre :

- **fenêtre courte** → réactive, mais bruitée
- **fenêtre longue** → stable, mais en retard

Trois jours est un compromis : assez pour lisser un accident, assez court pour rester réactif.

> **Un point à savoir défendre.** Cette moyenne **inclut** le jour J. Ce n'est **pas** une fuite ici,
> parce que `mu_night_full(J)` est connu à 9h30, avant que le gap ne soit observé. Mais la même
> construction appliquée à une variable de **prix** serait une faute grave. Il faut savoir expliquer
> pourquoi c'est légitime dans un cas et pas dans l'autre.

## 14.3 — `mu_night_z20` : la normalisation — la plus importante

```
              mu(t)  −  moyenne des 20 valeurs PRÉCÉDENTES
z(t)  =  ──────────────────────────────────────────────────────
            écart-type des 20 valeurs PRÉCÉDENTES
```

### Le problème qu'elle résout

```
Moyenne de mu_night_full par ticker :
  NVDA    0.1627
  AMZN    0.1170
  META    0.1139
  AAPL    0.0945
  TSLA    0.0449      <- 3,6 fois moins que NVDA
```

**Est-ce que la foule aime 3,6 fois plus NVDA que TSLA ?** Non. Cela veut dire que les deux communautés
**écrivent différemment**. Les messages TSLA sont plus polémiques, plus chargés en vocabulaire que FinBERT
classe en négatif ; ceux de NVDA sont plus techniques et enthousiastes.

**La conséquence.** Un sentiment de 0,12 est :

- **médiocre** pour NVDA (sous sa moyenne de 0,16)
- **exceptionnel** pour TSLA (0,12 − 0,045) / 0,032 ≈ **+2,3 écarts-types**

La valeur brute ne veut **rien dire** hors contexte.

### Ce qui se passe si on ne normalise pas

Le modèle apprend surtout **l'identité du titre** : « quand `mu` est élevé, c'est probablement NVDA, et
NVDA a beaucoup monté en 2020-2021 ». Il ne mesure pas un signal — il mémorise que NVDA a monté. Cela ne
se généralisera à aucun autre titre, ni à aucune autre période.

### Ce que fait le z-score

Après normalisation :

```
Moyenne de mu_night_z20 par ticker :
  AAPL   -0.0130
  AMZN   -0.0299
  META   -0.0485
  NVDA   -0.0367
  TSLA   -0.0212
```

Tous à ~0. **Les écarts de niveau ont disparu.** Désormais `z = +2` signifie partout la même chose :
*« sentiment anormalement positif pour ce titre, comparé à son propre mois écoulé »*.

C'est **cela**, le vrai signal — et c'est comparable d'un titre à l'autre.

### Pourquoi une fenêtre glissante et non une moyenne globale

Une moyenne calculée sur toute la période 2020-2022 utiliserait des données de 2022 pour normaliser des
jours de 2020 : **une fuite d'information venue du futur**.

La fenêtre glissante n'utilise que le passé, et elle a un second avantage : elle **s'adapte aux
changements de régime**. Le niveau de bavardage sur TSLA en mars 2020 (panique COVID) n'a rien à voir avec
celui de janvier 2022.

### Le détail qui fait tout : le `.shift(1)`

Sans lui, la fenêtre de 20 jours **inclurait le jour J**. On normaliserait `x_t` par une moyenne qui
contient déjà `x_t`. L'effet est faible mais systématique, et il gonfle artificiellement toutes les
performances.

> **C'est l'erreur n° 1 en finance quantitative appliquée.** Retiens la règle : *toute fenêtre glissante
> utilisée comme variable explicative doit être décalée d'au moins un pas.*

### Pourquoi 106 valeurs manquantes

Il faut 20 jours d'historique pour calculer moyenne et écart-type. Les ~21 premiers jours de chaque titre
sont donc `NaN`. C'est normal — et c'est le prix de l'honnêteté.

---

# Chapitre 15 — Les décalées et les cibles

## 15.1 — Les six colonnes `_lag1` : récupérer l'information interdite

Les fenêtres `mkt` et `post` sont **interdites** pour le jour J : elles se ferment après l'ouverture, donc
elles réagissent au prix au lieu de l'annoncer.

Mais celles du **jour J−1** sont parfaitement connues à 16h00 la veille — donc parfaitement légales.

**Deux usages :**

1. **Décrire le climat de la veille.** Une séance où la communauté a été très active et négative annonce
   peut-être une nuit agitée.
2. **Servir de contrôle.** Si le sentiment nocturne garde son pouvoir prédictif **une fois le sentiment
   de la veille pris en compte**, c'est bien l'information *nouvelle* de la nuit qui compte, et non un
   prolongement de la journée passée.

Ce second usage est un raisonnement de **variable de contrôle**, central en économétrie : pour affirmer
que X cause Y, il faut montrer que l'effet subsiste après avoir neutralisé les explications alternatives.

## 15.2 — Les cibles binaires

```
y_gap = 1  si gap > 0
y_gap = 0  sinon
```

```
y_gap       : 0.589
y_oc        : 0.505
y_cc        : 0.534
```

### Le piège du taux de base

**58,9 % des jours ont un gap positif.** Ce n'est pas 50 %.

**Conséquence immédiate :** un modèle qui répondrait « hausse » **tous les jours**, sans regarder aucune
donnée, obtiendrait **58,9 % d'exactitude**.

Si ton modèle affiche 60 %, il n'a presque rien appris — pourtant le chiffre paraît respectable. C'est le
piège dans lequel tombe la majorité des travaux sur la prédiction boursière.

**C'est pourquoi le mémoire reporte l'AUC et le MCC**, pas l'exactitude :

| Métrique | Ce qu'elle mesure | Valeur si aucune information |
|---|---|---|
| **AUC** | probabilité qu'un jour de hausse tiré au hasard reçoive un score supérieur à un jour de baisse | **0,50** toujours |
| **MCC** | corrélation entre prédictions et réalité, robuste au déséquilibre | **0,00** |
| Exactitude | % de bonnes réponses | **58,9 %** ici (trompeur) |

L'AUC vaut 0,50 en l'absence d'information **quel que soit le taux de base**. C'est ce qui la rend
comparable entre problèmes.

### Pourquoi le taux de base est de 58,9 %

Deux raisons :

1. **Le marché monte plus souvent qu'il ne baisse** — c'est la prime de risque actions.
2. **La prime overnight** : sur cette période, une part importante du rendement s'est formée pendant la
   nuit. TSLA gagnait en moyenne **+0,40 % chaque nuit**.

Ce second point est important pour le backtest : **une stratégie qui achèterait tous les soirs sans rien
prédire capterait déjà cette prime**. Le modèle doit donc être comparé à cette référence, et pas seulement
au buy & hold.

## 15.3 — `y_gap_net` : la zone morte

```
y_gap_net = 1          si gap > +15 bp   (+0,15 %)
y_gap_net = 0          si gap < −15 bp   (−0,15 %)
y_gap_net = indéfini   sinon              -> le jour est NEUTRALISÉ
```

**Le problème.** Un « point de base » (bp) vaut 0,01 %. Un gap de +0,013 % donne `y_gap = 1` — « hausse » —
alors que ce mouvement est **plusieurs fois plus petit que les frais de transaction**.

Le modèle est donc noté sur des jours qu'il serait impossible de trader.

**La solution.** On neutralise les jours où `|gap| < 15 bp` :

```
Jours neutralisés : 382 (13.9 %)
y_gap_net : 0.599 (n = 2 358)
```

**Ce que ça change.** Le modèle n'est plus évalué que sur les mouvements **économiquement significatifs**.
C'est le passage d'une évaluation **statistique** à une évaluation **décisionnelle** — un réflexe
d'actuaire : ce qui compte n'est pas d'avoir raison, c'est d'avoir raison **là où ça change quelque
chose**.

---

# Chapitre 16 — Les sept contrôles qualité

```
[OK] Panel équilibré  — 548 jours par ticker
[OK] Aucun doublon (Ticker, Date)
[OK] (1+gap)(1+ret_oc) = 1+ret_cc  — erreur max 2.22e-16
[OK] mu = pos - neg sur toutes les fenêtres  — erreur max 1.11e-16
[OK] n_night_full = n_overnight + n_pre  — erreur max 0.00e+00
[OK] nabn centré sur zéro  — moyenne -0.0059
[OK] disp_night_full calculable  — 99.9% de lignes renseignées
TOUS LES CONTRÔLES PASSENT.
```

## Pourquoi bloquer l'export si un test échoue

```python
if echecs:
    print("Export ANNULÉ : corrige les contrôles en échec d'abord.")
```

**Mieux vaut pas de fichier qu'un fichier faux.** Un fichier faux se propage : tu construis dessus, tu
tires des conclusions, tu rédiges — et tu découvres l'erreur trois semaines plus tard. Un fichier absent
t'arrête immédiatement.

C'est le principe ***fail fast*** : mieux vaut échouer tôt et bruyamment que tard et silencieusement.

## Ce que teste chaque contrôle

| # | Contrôle | Ce qu'il attraperait |
|---|---|---|
| 1 | Panel équilibré | un trou dans les prix, un ticker mal filtré |
| 2 | Pas de doublon | une jointure qui a dupliqué des lignes |
| 3 | Identité de décomposition | une erreur de formule sur les rendements |
| 4 | `mu = pos − neg` | une agrégation incohérente |
| 5 | Additivité des comptages | une mauvaise affectation aux fenêtres |
| 6 | `nabn` centré | le bug de dénominateur |
| 7 | `disp` calculable | des percentiles manquants |

## La notion de test à seuil vs test binaire

Deux types de contrôles cohabitent :

- **Binaires** (1, 2, 5) : ça passe ou ça ne passe pas. Aucune tolérance.
- **À seuil** (3, 4, 6, 7) : on accepte une erreur en dessous d'une limite.

Pour les tests à seuil, la limite (`< 1e-9`) n'est pas arbitraire. Les nombres à virgule flottante en
double précision ont environ **16 chiffres significatifs** ; une suite d'opérations accumule donc une
erreur de l'ordre de 10⁻¹⁵. Un seuil de 10⁻⁹ laisse six ordres de grandeur de marge : assez pour tolérer
l'arrondi machine, assez strict pour attraper une vraie erreur de formule.

**Tes erreurs sont de l'ordre de 2 × 10⁻¹⁶** — la précision machine exactement. Les formules sont
mathématiquement exactes.

---

# Chapitre 17 — Récapitulatif : les 10 idées à retenir

| # | Idée | Où elle sert |
|---|---|---|
| **1** | **L'erreur type d'une moyenne décroît en `1/√n`.** C'est pourquoi 500 messages/nuit valent infiniment mieux que 2. | ch. 9 — justifie tout le changement de corpus |
| **2** | **Une variable n'est utilisable que si elle est connue avant que la cible ne se forme.** | partout — c'est la règle du projet |
| **3** | **Toute fenêtre glissante doit être décalée d'un pas** (`.shift(1)`). | ch. 11, 14 — l'erreur n° 1 en finance quantitative |
| **4** | **Le rendement quotidien se décompose en gap × séance**, et les deux n'obéissent pas aux mêmes règles. | ch. 11 — l'idée centrale du mémoire |
| **5** | **Les moyennes s'additionnent, la dispersion et les percentiles non** (loi de la variance totale). | ch. 9 — corrige deux bugs du panel |
| **6** | **`mu = pos − neg` est une identité exacte** → colinéarité parfaite si on met les trois ensemble. | ch. 3 — explique les VIF absurdes du nb 06 |
| **7** | **Le niveau brut n'informe pas ; l'écart à la normale, si.** D'où le z-score et `nabn`. | ch. 13, 14 |
| **8** | **Une distribution asymétrique se transforme en log** avant tout modèle linéaire. | ch. 13 |
| **9** | **Le taux de base rend l'exactitude trompeuse** → utiliser l'AUC et le MCC. | ch. 15 |
| **10** | **Ne jamais faire confiance à un calcul complexe sans le vérifier par un chemin indépendant.** | ch. 8, 11, 16 |

## Les cinq phrases à savoir dire en soutenance

1. « Le panel est construit en rattachant chaque message à un jour de bourse et à une phase de la journée,
   après vérification que les horodatages sont en heure de New York — vérification faite **sur les
   données**, par le profil horaire d'activité. »

2. « Le calendrier de bourse est déduit des cotations elles-mêmes, ce qui gère automatiquement week-ends,
   fériés et fermetures exceptionnelles. »

3. « La fenêtre nocturne part de la clôture du **jour de bourse** précédent, si bien que celle du lundi
   couvre l'ensemble du week-end — ce que confirme un volume 1,81 fois supérieur aux autres jours. »

4. « Les statistiques de dispersion sont calculées directement sur les messages, et non recombinées à
   partir des sous-fenêtres, parce que ni les écarts-types ni les percentiles ne sont additifs. »

5. « Sept contrôles automatiques bloquent l'export en cas d'échec ; les identités comptables sont
   vérifiées à la précision machine (2 × 10⁻¹⁶). »

---

## Références

- Mandelbrot, B. (1963). *The Variation of Certain Speculative Prices*. Journal of Business. — regroupement de volatilité
- Miller, E. (1977). *Risk, Uncertainty, and Divergence of Opinion*. Journal of Finance. — le désaccord
- Engle, R. (1982). *Autoregressive Conditional Heteroscedasticity*. Econometrica. — modèles ARCH
- Hong, H. & Stein, J. (1999). *A Unified Theory of Underreaction…*. Journal of Finance. — asymétrie des nouvelles
- Antweiler, W. & Frank, M. (2004). *Is All That Talk Just Noise?*. Journal of Finance. — forums boursiers
- Da, Z., Engelberg, J. & Gao, P. (2011). *In Search of Attention*. Journal of Finance. — chocs d'attention
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. — fuites et validation

---

*Prochain cours : notebook 04 — l'analyse exploratoire, les corrélations, les quintiles et les tests
statistiques.*
