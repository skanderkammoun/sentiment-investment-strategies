# Cours 4 — Notebook 06 : le modèle M1, mesurer honnêtement un pouvoir prédictif

**Le notebook où l'on apprend à ne pas se mentir sur la qualité d'un modèle**

*Cours détaillé, chapitre par chapitre. Chaque métrique : sa définition, sa formule, ce qu'elle vaut
quand on ne sait rien. Chaque modèle : ce qu'il suppose, ce qu'il peut et ne peut pas apprendre.
Chaque test : l'objection du jury auquel il répond.*

---

## Table des matières

| # | Chapitre | Notion enseignée |
|---|---|---|
| 0 | La question posée et le piège de l'accuracy | taux de base |
| 1 | Le chargement : trois blocs, trois régimes | lire un déséquilibre |
| 2 | Les quatre métriques | **AUC, MCC, Brier** ⭐ |
| 3 | Les modèles de référence R1 à R4 | la notion de *baseline* |
| 4 | La régression logistique | log-odds, odds ratio |
| 5 | La régularisation L2 et le choix de C | compromis biais-variance |
| 6 | Les trois spécifications emboîtées | apport net |
| 7 | Lire les coefficients — et le VIF | **colinéarité destructrice** ⭐ |
| 8 | Les arbres : forêt et boosting | non-linéarité |
| 9 | L'importance par permutation | **le grand renversement** ⭐ |
| 10 | La validation glissante | ratio de stabilité |
| 11 | Les ablations et la falsification | contrôle négatif |
| 12 | La calibration | **probabilité juste = prime juste** ⭐ |
| 13 | La robustesse : ticker, LOTO, régime | généralisation transversale |
| 14 | Le bloc de test — ce qui manque | **la cellule non exécutée** ⚠ |
| 15 | Six points à corriger | esprit critique |
| 16 | Récapitulatif et phrases de soutenance | |

---

# Chapitre 0 — La question posée, et le piège de l'accuracy

## 0.1 — La question, en une phrase

> À la clôture de 16h00, en ne connaissant **que** les messages de la nuit qui suit et l'historique de
> marché, peut-on prédire si l'action ouvrira **en hausse** ou **en baisse** le lendemain à 9h30 ?

Trois mots comptent dans cette phrase.

**« que »** — c'est la contrainte anti-fuite du notebook 05. Toute variable qui se forme après 9h30 est
interdite.

**« signe »** — on ne prédit pas *de combien* ça monte, seulement *si* ça monte. C'est une question de
**classification binaire**, beaucoup plus modeste — et beaucoup plus atteignable — qu'une question de
régression.

**« gap »** — et pas la séance. Le notebook 04 a montré que la corrélation sentiment→gap vaut +0,157 alors
que la corrélation sentiment→séance vaut −0,010. Modéliser le gap, c'est modéliser là où il y a quelque
chose à modéliser. Modéliser la séance aurait été honnête mais stérile.

## 0.2 — Le piège dans lequel tombe 80 % de la littérature amateur

Voici l'expérience de pensée la plus importante du notebook.

Imagine un modèle **totalement stupide**. Il ne regarde aucune donnée. Il répond « hausse » tous les jours,
sans exception. Un enfant de six ans peut le coder :

```
prediction = "hausse"     # peu importe l'entrée
```

Sur ton bloc d'entraînement, 59,5 % des jours ont effectivement un gap positif (2020-2021, marché haussier
alimenté par la liquidité post-COVID). Donc ce modèle stupide obtient :

```
Exactitude (accuracy) = 59,5 %
```

Maintenant imagine que tu construis un vrai modèle, avec du NLP, du FinBERT, du gradient boosting, trois
semaines de travail. Il obtient **61 %**.

Tu écris dans ton mémoire : « le modèle atteint 61 % d'exactitude ». Le jury lit. Le jury demande :
« et la référence naïve ? ». Tu réponds 59,5 %. Ton apport réel est de **1,5 point**, pas de 61 points.

> **La règle absolue : une exactitude ne veut rien dire tant qu'on n'a pas donné le taux de base.**

C'est ce qu'on appelle le **taux de base** (*base rate*), ou le **déséquilibre de classes**. Toute mesure
de performance doit être lue **relativement** à ce taux.

## 0.3 — L'exemple qui rend ça inoubliable

Un test médical dépiste une maladie qui touche 1 personne sur 1 000.

Un laboratoire annonce fièrement : **« notre test est exact à 99,9 % »**.

Voici son algorithme complet :

```
resultat = "négatif"     # toujours
```

Sur 1 000 personnes, il se trompe une seule fois (le vrai malade). 999/1000 = 99,9 %. Le test est
parfaitement exact **et parfaitement inutile** : il ne détecte jamais personne.

C'est pour cela que la médecine, l'actuariat et la finance n'utilisent **jamais** l'exactitude seule.
Ils utilisent la sensibilité, la spécificité, l'AUC, le score de Brier. Le notebook 06 fait pareil.

## 0.4 — Ce qui change par rapport à la première tentative du mémoire

Le notebook s'ouvre sur un tableau de comparaison avec une « phase 5 » antérieure. Il vaut la peine d'être
compris, car il résume trois mois de travail.

| | Première tentative (2023-2026) | Ce notebook (2020-2022) |
|---|---|---|
| Cible | rendement de séance | **gap d'ouverture** |
| Densité du corpus | médiane 2 messages/jour | **170 à 1 474 messages/nuit** |
| Normalisation | valeurs brutes | **z-score glissant intra-titre** |
| Validation | découpage aléatoire | **chronologique + glissante** |
| Métrique principale | exactitude | **AUC, MCC, Brier** |
| Résultat | MCC ≈ 0,03, AUC ≈ 0,52 | à mesurer |

Les cinq lignes racontent la même histoire : **la première tentative n'a pas échoué parce que l'idée était
mauvaise, elle a échoué parce que quatre choix méthodologiques étaient mauvais**.

- Mauvaise cible : on cherchait le signal là où il n'est pas.
- Mauvais corpus : 2 messages par jour, c'est du bruit, pas une opinion collective.
- Mauvaise normalisation : le biais de niveau entre titres masquait le signal (Cours 3, ch. 3).
- Mauvaise validation : le découpage aléatoire laisse fuir le futur dans le passé.

**Cette page est un excellent contenu de mémoire.** Elle montre que tu comprends *pourquoi* une méthode
échoue, ce qui est plus difficile — et plus valorisé — que de faire marcher une méthode du premier coup.

---

# Chapitre 1 — Le chargement : trois blocs, trois régimes

## 1.1 — Ce que fait la cellule

```python
df = pd.read_csv(".../DATASET_MODELISATION_2020_2022.csv")
with open(".../config_modelisation.json") as f:
    CFG = json.load(f)

FEATURES  = [c for c in CFG["features"]            if c in df.columns]
FEAT_SENT = [c for c in CFG["features_sentiment"]  if c in df.columns]
FEAT_CTRL = [c for c in CFG["controles"]           if c in df.columns]
FEAT_CONS = [c for c in CFG["features_conservateur"] if c in df.columns]
```

Aucune liste de variables n'est écrite en dur dans ce notebook. Tout vient du fichier JSON produit par le
notebook 05. C'est le principe de la **source unique de vérité** (Cours 3, ch. 13) : si tu ajoutes une
variable, tu la déclares à un seul endroit, et les notebooks 06, 07 et 08 la reprennent automatiquement.

Le `if c in df.columns` est une sécurité : si le CSV et le JSON se désynchronisent, le notebook ne plante
pas, il ignore simplement la colonne absente.

> **Le petit défaut** : ignorer silencieusement une colonne manquante est dangereux. Si demain une faute de
> frappe fait disparaître dix variables, tout tourne comme si de rien n'était, avec un modèle appauvri.
> La bonne pratique est d'ignorer **mais de le dire** :
>
> ```python
> manquantes = [c for c in CFG["features"] if c not in df.columns]
> if manquantes:
>     print(f"ATTENTION — {len(manquantes)} features absentes : {manquantes}")
> ```

## 1.2 — La sortie réelle

```
2 740 lignes | 23 features (14 sentiment + 9 contrôles)
bloc
train    1885
purge      25
valid      520
test       310
```

Traduction :

- **2 740 lignes** = 548 jours de bourse × 5 titres. Ce sont des observations « titre-jour ».
- **23 features** : 14 de sentiment (les `z_` et `rk_`) et 9 de contrôle de marché.
- **25 lignes de purge** = 5 jours × 5 titres. Ce sont les jours jetés à la frontière entre les blocs pour
  éviter que les fenêtres glissantes de 60 jours ne chevauchent la frontière (Cours 3, ch. 8).

Rapport features / observations : 23 features pour 1 885 lignes d'entraînement, soit environ **82
observations par paramètre**. C'est un ratio confortable pour une régression logistique. La règle du pouce
en statistique appliquée est d'au moins 10 à 20 observations par paramètre ; on est très au-dessus.

## 1.3 — Le tableau des taux de base, et ce qu'il révèle

```
train 1885 lignes | valid  520 | test  310
Taux de gaps positifs — train 0.595 | valid 0.606 | test 0.510
```

Ce petit tableau de trois nombres est **la ligne la plus importante du notebook**, et il faut savoir la
commenter en soutenance.

| Bloc | Période | Gaps positifs | Régime de marché |
|---|---|---|---|
| train | jan 2020 → juin 2021 | 59,5 % | krach COVID puis reprise massive |
| valid | juil 2021 → nov 2021 | 60,6 % | plateau, rotation sectorielle |
| test | déc 2021 → mars 2022 | **51,0 %** | resserrement de la Fed, marché sans direction |

**Interprétation.** Sur les deux premiers blocs, presque six ouvertures sur dix sont haussières : c'est un
marché porté. Sur le bloc de test, on tombe à une sur deux : le marché ne monte plus, il oscille.

Trois conséquences pratiques :

**(a) Le modèle est évalué dans un régime qu'il n'a jamais vu.** Ce n'est pas un défaut du découpage — c'est
la réalité de la prévision financière. Un modèle entraîné sur 2020-2021 et déployé en 2022 est exactement
dans cette situation. C'est même une **qualité** : cela rend l'évaluation plus sévère et donc plus crédible.

**(b) L'exactitude sur le test ne se compare pas à l'exactitude sur la validation.** Sur la validation, la
barre naïve est à 60,6 %. Sur le test, elle est à 51,0 %. Un modèle qui ferait 58 % sur le test ferait
mieux (+7 points sur la barre) qu'un modèle faisant 62 % sur la validation (+1,4 point). Ne jamais comparer
deux exactitudes issues de blocs différents.

**(c) L'AUC, elle, est comparable.** C'est un des grands avantages de cette métrique : elle est
**invariante au taux de base**. On y vient au chapitre suivant.

> **La phrase à écrire dans le mémoire** : « La proportion d'ouvertures haussières passe de 59,5 % dans
> l'échantillon d'apprentissage à 51,0 % dans l'échantillon de test, reflétant le changement de régime
> monétaire du premier trimestre 2022. L'évaluation finale porte donc sur un régime distinct de celui de
> l'estimation, ce qui constitue un test de généralisation plus exigeant qu'une validation en régime
> homogène. »

---

# Chapitre 2 — Les quatre métriques

C'est le chapitre théorique le plus dense du cours. Prends le temps. Ces quatre outils te suivront dans
toute ta carrière d'actuaire.

## 2.1 — La matrice de confusion, socle de tout

Toute classification binaire se résume à un tableau 2×2. On note 1 = « gap positif », 0 = « gap négatif ».

```
                      RÉALITÉ
                   1          0
              +---------+---------+
PRÉDICTION  1 |   VP    |   FP    |
              +---------+---------+
            0 |   FN    |   VN    |
              +---------+---------+
```

- **VP** (vrai positif) : on annonce hausse, ça monte. Bien.
- **VN** (vrai négatif) : on annonce baisse, ça baisse. Bien.
- **FP** (faux positif) : on annonce hausse, ça baisse. On achète, on perd.
- **FN** (faux négatif) : on annonce baisse, ça monte. On rate un gain.

L'exactitude est simplement :

```
Accuracy = (VP + VN) / (VP + VN + FP + FN)
```

Elle mélange les deux types d'erreurs dans un seul chiffre, ce qui est précisément son défaut.

## 2.2 — L'AUC : la métrique reine

### La définition intuitive (celle à retenir)

> **L'AUC est la probabilité que, si l'on tire au hasard un jour de hausse et un jour de baisse, le modèle
> attribue un score plus élevé au jour de hausse.**

Cette formulation est exacte et parfaitement compréhensible. Elle dit tout :

- AUC = 0,50 → le modèle classe au hasard, une fois sur deux il se trompe d'ordre. **Aucune information.**
- AUC = 1,00 → tous les jours de hausse ont un score supérieur à tous les jours de baisse. **Parfait.**
- AUC = 0,30 → le modèle classe **à l'envers**. Ce qui est en réalité une information : il suffit
  d'inverser ses prédictions pour obtenir 0,70. C'est exactement le principe du test d'inversion (ch. 11).

### La formule

```
              nombre de paires (i haussier, j baissier) telles que score_i > score_j
AUC  =  ------------------------------------------------------------------------------
                      nombre total de paires (haussier, baissier)
```

### L'exemple à la main

Cinq jours, dont trois montent (notés 1) et deux baissent (notés 0). Le modèle sort les scores suivants :

| Jour | Réalité | Score du modèle |
|---|---|---|
| A | 1 | 0,90 |
| B | 0 | 0,70 |
| C | 1 | 0,60 |
| D | 1 | 0,40 |
| E | 0 | 0,20 |

On forme toutes les paires (jour haussier, jour baissier). Il y en a 3 × 2 = 6 :

```
(A,B) : 0,90 > 0,70  -> correct
(A,E) : 0,90 > 0,20  -> correct
(C,B) : 0,60 < 0,70  -> INCORRECT
(C,E) : 0,60 > 0,20  -> correct
(D,B) : 0,40 < 0,70  -> INCORRECT
(D,E) : 0,40 > 0,20  -> correct

AUC = 4 / 6 = 0,667
```

### Pourquoi elle est la bonne métrique ici

**Première raison : elle ne dépend pas du seuil.** L'exactitude oblige à choisir « au-dessus de 0,5 on dit
hausse ». L'AUC teste **tous les seuils à la fois**. Elle mesure la qualité du **classement**, pas celle
d'une décision arbitraire.

**Deuxième raison : elle ne dépend pas du taux de base.** Que 51 % ou 60 % des jours montent, une AUC de
0,66 signifie toujours la même chose. C'est pour ça qu'on peut comparer la validation et le test avec elle,
alors qu'on ne peut pas le faire avec l'exactitude (§1.3).

**Troisième raison : elle a un sens économique direct.** En trading, on n'a pas besoin de savoir *si* une
action montera. On a besoin de savoir **quelles actions montent le plus par rapport aux autres**, pour
allouer le capital. C'est un problème de classement. L'AUC mesure exactement ça.

### Les ordres de grandeur — à mémoriser

Le notebook donne cette échelle, et elle est juste :

| AUC | Interprétation en finance journalière |
|---|---|
| 0,50 – 0,52 | rien |
| 0,53 – 0,55 | signal faible mais réel, exploitable si les coûts sont bas |
| 0,55 – 0,60 | **bon signal** directionnel |
| > 0,65 | **suspect** — chercher la fuite avant de se réjouir |

> **Cette dernière ligne est une des plus importantes de tout le mémoire, et le notebook l'écrit
> lui-même : « en finance, un résultat trop beau est presque toujours un bug ».**
>
> Or ce notebook obtient des AUC de **0,66 à 0,67**. Il est donc, par sa propre grille de lecture, dans la
> zone « suspect ». Ce n'est pas une raison de jeter le travail — c'est une raison de faire ce que le
> chapitre 9 et le chapitre 14 vont faire : chercher **où** est la faille. Et il y en a une.

## 2.3 — Le MCC : le coefficient de Matthews

### Le problème qu'il résout

L'exactitude peut être trompée par le déséquilibre. Le MCC, non. C'est simplement le **coefficient de
corrélation de Pearson** entre le vecteur des prédictions (0/1) et le vecteur de la réalité (0/1).

### La formule

```
                     VP × VN  −  FP × FN
MCC  =  --------------------------------------------------------
        racine( (VP+FP)(VP+FN)(VN+FP)(VN+FN) )
```

### Les valeurs

- **MCC = 0** → aucune relation entre prédictions et réalité. C'est ce qu'obtient un modèle qui répond
  toujours la même chose (numérateur nul car FP × FN ou VP × VN s'annule).
- **MCC = 1** → prédiction parfaite.
- **MCC = −1** → prédiction parfaitement inversée.

### L'ordre de grandeur en finance

Un MCC de **0,10 à 0,25** en prédiction boursière journalière est déjà un bon résultat. Ne t'attends jamais
à 0,5. Ici, les modèles obtiennent 0,16 à 0,24 sur la validation, ce qui est cohérent avec les AUC observées.

### Pourquoi le retenir plutôt que le F1

Le F1-score, très populaire en apprentissage automatique, **ignore les vrais négatifs**. En finance, prédire
correctement une baisse a exactement autant de valeur que prédire correctement une hausse (on peut vendre à
découvert, ou simplement rester à l'écart). Le MCC utilise les quatre cases de la matrice. C'est le bon
choix ici, et c'est un argument à citer si le jury demande pourquoi pas de F1.

## 2.4 — Le score de Brier : la métrique de l'actuaire

### La définition

C'est l'**erreur quadratique moyenne sur les probabilités** :

```
              1     n
Brier  =  ---  ×   somme  ( p_i  −  y_i )²
              n    i=1

  p_i = probabilité annoncée par le modèle pour l'observation i
  y_i = réalité (0 ou 1)
```

Plus il est **bas**, mieux c'est.

### L'exemple qui montre ce qu'il pénalise

Trois jours qui **montent tous** (y = 1). Deux modèles :

| | Modèle prudent | Modèle téméraire |
|---|---|---|
| Probabilités annoncées | 0,60 / 0,60 / 0,60 | 0,99 / 0,99 / 0,20 |
| Bonnes réponses (seuil 0,5) | 3/3 | 2/3 |
| **Exactitude** | 100 % | 67 % |
| Brier | 0,16 | 0,213 |

Calcul du prudent : 3 × (1 − 0,60)² / 3 = 0,16.
Calcul du téméraire : [(0,01)² + (0,01)² + (0,80)²] / 3 = 0,213.

Le modèle prudent gagne sur les deux tableaux. Mais surtout : le Brier **punit très fort la sur-confiance**.
Se tromper en annonçant 0,99 coûte (0,8)² = 0,64, alors que se tromper en annonçant 0,55 coûte 0,30. Le
carré est ce qui fait la différence.

### Pourquoi c'est LA métrique d'un mémoire d'actuariat

Voici le lien à faire explicitement dans ta soutenance.

> En assurance, la **prime pure** est égale à la probabilité de sinistre multipliée par le coût du sinistre.
> Si ta probabilité est fausse, ta prime est fausse — même si ton classement des risques est parfait.
>
> En trading, la **taille de position** optimale est une fonction de la probabilité de gain (formule de
> Kelly). Si ta probabilité est fausse, ton dimensionnement est faux, et tu fais faillite même avec un bon
> classement.
>
> **Un bon classement (AUC) ne suffit pas. Il faut des probabilités justes (Brier).** C'est exactement
> l'objet du chapitre 12 sur la calibration.

### Sa valeur de référence

Un modèle sans information qui annonce toujours le taux de base `p` obtient un Brier de `p(1−p)`, ce qu'on
appelle la **variance de Bernoulli**. Ici, avec p = 0,606 sur la validation :

```
Brier de référence = 0,606 × 0,394 = 0,2388
```

Retiens ce nombre : **0,2388**. Tout modèle dont le Brier dépasse 0,2388 sur la validation est **pire que
de ne rien faire**. On va voir que certaines références du notebook sont dans ce cas.

## 2.5 — La fonction `evaluer`, ligne par ligne

```python
def evaluer(y_vrai, proba, seuil=0.5, nom=""):
    y_vrai = np.asarray(y_vrai).astype(int)
    proba  = np.asarray(proba, float)
    pred   = (proba >= seuil).astype(int)
    return {
        "modele": nom,
        "n": len(y_vrai),
        "AUC":      roc_auc_score(y_vrai, proba),      # sur les PROBAS
        "MCC":      matthews_corrcoef(y_vrai, pred),   # sur les DÉCISIONS
        "Brier":    brier_score_loss(y_vrai, proba),   # sur les PROBAS
        "Accuracy": accuracy_score(y_vrai, pred),      # sur les DÉCISIONS
        "base_rate":   y_vrai.mean(),
        "taux_signal": pred.mean(),
    }
```

Détail à ne pas rater : **AUC et Brier prennent les probabilités**, **MCC et Accuracy prennent les décisions
binarisées**. C'est la raison pour laquelle deux modèles peuvent avoir la même AUC et des MCC très
différents : ils classent pareil mais coupent à un endroit différent de l'échelle.

Deux colonnes ajoutées sont malignes :

- **`base_rate`** — le taux de base du bloc évalué. Il est imprimé à côté de l'exactitude, ce qui rend le
  piège du §0.2 **impossible à commettre** : les deux nombres sont côte à côte.
- **`taux_signal`** — la proportion de fois où le modèle dit « hausse ». Un modèle qui dit hausse 99,6 % du
  temps ne prend aucun risque, quelle que soit son exactitude. C'est un indicateur de **dégénérescence**.

Et dans `afficher` :

```python
t["gain_vs_naif"] = t["Accuracy"] - t["base_rate"]
```

C'est le vrai chiffre. **Toujours le regarder avant l'exactitude.**

> **Un point faible à connaître** : le seuil est figé à 0,5. Avec un taux de base de 0,606, ce n'est pas le
> seuil qui maximise le MCC. Les MCC affichés sont donc des **minorants** : le modèle serait meilleur avec
> un seuil réglé (par exemple 0,60) sur la validation. Ce n'est pas une erreur — c'est même prudent — mais
> il faut le dire, sinon on sous-estime ses propres modèles.

---

# Chapitre 3 — Les modèles de référence

## 3.1 — Pourquoi une référence est indispensable

Un chiffre de performance seul ne veut rien dire. **La performance est toujours relative.**

Analogie : dire « j'ai couru le 100 m en 12 secondes » n'a de sens que si l'on sait ce que fait un humain
moyen (14 s), un athlète amateur (11 s) ou Usain Bolt (9,58 s). Sans échelle, 12 secondes ne signifie rien.

En apprentissage automatique, cette échelle s'appelle la **référence** (*baseline*). Le notebook en
construit quatre, de la plus bête à la plus sérieuse.

## 3.2 — Les quatre références

| Référence | Règle | Objection à laquelle elle répond |
|---|---|---|
| **R1 — toujours hausse** | prédire 1 partout | « la classe majoritaire ne suffit-elle pas ? » |
| **R2 — hasard** | probabilité tirée uniformément | contrôle négatif du code |
| **R3 — momentum** | continuation du rendement de la veille | « ce n'est que du momentum » |
| **R4 — sentiment brut** | seuil sur `z_mu_night_full`, sans apprentissage | « l'apprentissage sert-il à quelque chose ? » |

### R3 en détail — pourquoi le momentum

```python
mom = va["ret_cc_lag1"].fillna(0.0).values
proba = 1 / (1 + np.exp(-mom * 50))
```

Le **momentum** est le phénomène documenté par Jegadeesh et Titman (1993) : les titres qui ont monté
récemment ont tendance à continuer de monter à court terme. C'est l'anomalie de marché la mieux établie de
la littérature.

Si ton modèle marchait uniquement parce qu'il redécouvre le momentum, ton apport scientifique serait nul :
tu aurais réinventé une chose connue depuis trente ans, avec du FinBERT en plus. **R3 est là pour écarter
cette accusation.**

La transformation `1/(1+exp(−50x))` convertit un rendement (par exemple +0,02 = +2 %) en une pseudo-
probabilité. Le facteur 50 est un facteur d'échelle : +2 % donne `1/(1+exp(−1)) = 0,73`.

> Remarque technique : **ce facteur 50 n'a aucun effet sur l'AUC**, parce que la fonction logistique est
> strictement croissante et que l'AUC ne dépend que de l'**ordre** des scores. Il n'affecte que le Brier et
> l'exactitude. C'est un bon exercice de compréhension : si tu as saisi pourquoi, tu as compris l'AUC.

### R4 en détail — la vraie barre à franchir

```python
sent  = va["z_mu_night_full"].fillna(0.0).clip(-3, 3).values
proba = 1 / (1 + np.exp(-sent))
```

Ici **aucun apprentissage** : pas de `.fit()`, pas de coefficient estimé, pas de donnée d'entraînement
utilisée. On prend le z-score du sentiment nocturne, on le passe dans une logistique, on appelle ça une
probabilité. Une règle qu'un stagiaire pourrait coder en trente secondes.

C'est **la référence la plus importante des quatre**, et le notebook a raison de le souligner :

> Si un simple seuil sur une variable fait aussi bien qu'un gradient boosting à 250 arbres, alors le modèle
> complexe n'apporte rien — et il faut l'écrire.

Le `.clip(-3, 3)` borne les z-scores extrêmes pour éviter que la logistique ne sature à 0 ou 1 (ce qui
détruirait le Brier). Bonne pratique.

## 3.3 — La sortie réelle, et sa lecture

```
                                modele   n    AUC     MCC  Brier  Accuracy  base_rate  taux_signal  gain_vs_naif
                    R1 toujours hausse 520 0.5000  0.0000 0.3864    0.6058     0.6058       1.0000        0.0000
                             R2 hasard 520 0.4936 -0.0323 0.3366    0.4846     0.6058       0.5019       -0.1212
                       R3 momentum J-1 520 0.5050  0.0088 0.2834    0.5173     0.6058       0.5615       -0.0885
R4 sentiment brut (sans apprentissage) 520 0.5937  0.1194 0.2611    0.5538     0.6058       0.4788       -0.0520
```

Ce tableau est une **leçon de statistique à lui seul**. Décortiquons-le ligne par ligne.

### R1 — la démonstration du piège, en une ligne

```
AUC 0,5000  |  MCC 0,0000  |  Accuracy 0,6058  |  base_rate 0,6058  |  gain 0,0000
```

Le modèle le plus stupide possible obtient **60,58 % d'exactitude**. Et pourtant :

- son **AUC est exactement 0,50** : il ne classe rien du tout, puisque tous les scores sont identiques ;
- son **MCC est exactement 0,00** : aucune corrélation avec la réalité ;
- son **gain vs naïf est exactement 0,00** : par construction, c'est lui la référence naïve.

> **C'est le meilleur paragraphe de ton mémoire pour montrer ta maîtrise méthodologique.** Trois métriques
> disent « zéro information », et une seule — l'exactitude — dit « 61 %, pas mal ». Devine laquelle est
> citée dans les articles de blog sur la prédiction boursière.

Note aussi son **Brier de 0,3864**, très supérieur à la référence de 0,2388 calculée au §2.4. Pourquoi ?
Parce qu'il annonce 0,99 alors que la réalité est à 0,606 : il est **massivement sur-confiant**. Le Brier
le sanctionne durement, l'exactitude ne le voit pas.

### R2 — le contrôle négatif du code

```
AUC 0,4936  |  MCC −0,0323
```

Des probabilités tirées au hasard donnent une AUC de 0,4936 au lieu de 0,5000 exactement. **C'est normal.**
Avec n = 520, l'écart-type de l'AUC sous l'hypothèse nulle vaut environ :

```
sigma  ≈  racine(  (n1 + n0 + 1) / (12 × n1 × n0)  )
       ≈  racine(  521 / (12 × 315 × 205)  )
       ≈  0,0230
```

L'écart observé est de 0,5000 − 0,4936 = 0,0064, soit **0,28 écart-type**. Parfaitement dans le bruit.

**Retiens ce chiffre : ±0,023.** C'est la barre d'erreur d'une AUC sur 520 observations. Cela veut dire
qu'une AUC de 0,53 sur ce bloc **n'est pas significativement différente de 0,50**. Et cela veut dire, à
l'inverse, qu'une AUC de 0,66 est à **7 écarts-types** du hasard — ce qui, si le protocole est propre, est
énorme, et si le protocole ne l'est pas, est un signal d'alarme.

### R3 — la mort du momentum

```
AUC 0,5050  |  MCC 0,0088
```

Le momentum de la veille ne prédit **rien** du gap du lendemain : 0,505 contre 0,50 attendu, soit 0,2
écart-type. Nul.

**Deux lectures possibles**, et il faut donner les deux :

1. **Lecture favorable au mémoire.** Le signal du modèle ne peut pas être du momentum déguisé, puisque le
   momentum seul ne vaut rien. L'objection la plus fréquente d'un jury tombe.
2. **Lecture prudente.** Le momentum classique de Jegadeesh-Titman se mesure sur **3 à 12 mois**, pas sur
   un jour. Ce que R3 teste, c'est l'autocorrélation à un jour, dont la littérature sait depuis longtemps
   qu'elle est quasi nulle sur les grandes capitalisations liquides. R3 ne réfute donc pas *le* momentum,
   il réfute *une* version très courte du momentum. À formuler honnêtement.

### R4 — la barre est haute

```
AUC 0,5937  |  MCC 0,1194  |  Brier 0,2611
```

**Sans le moindre apprentissage**, une seule variable donne une AUC de 0,594, soit **4,1 écarts-types**
au-dessus du hasard. C'est le résultat le plus important du tableau, et il faut le comprendre dans les deux
sens :

- **Le signal existe, et il est simple.** Il n'y a pas besoin de FinBERT + gradient boosting + 23 features
  pour le voir. Une seule colonne suffit. C'est plutôt rassurant : les signaux robustes sont simples ; les
  signaux qui n'apparaissent qu'avec 300 arbres sont souvent du surajustement.
- **La barre à franchir n'est donc pas 0,50, elle est 0,594.** Tout le travail de modélisation des chapitres
  suivants ne se juge que par rapport à ce nombre. Les modèles vont atteindre 0,66 : le gain de
  l'apprentissage est donc d'environ **+0,07 point d'AUC**, pas de +0,16.

Note aussi son `taux_signal` de 0,4788 : ce modèle annonce « hausse » moins d'une fois sur deux, dans un
marché qui monte 60,6 % du temps. Il est donc mal **calibré** (il sous-estime systématiquement) tout en
étant bien **classant**. C'est exactement la dissociation AUC/Brier du §2.4, illustrée sur un cas réel.

---

# Chapitre 4 — La régression logistique

## 4.1 — Pourquoi commencer par le modèle le plus faible

Le notebook donne trois raisons, toutes justes :

**1. Elle est interprétable.** Chaque coefficient a un signe et une amplitude qu'on peut discuter dans le
mémoire, et défendre devant un jury. Un gradient boosting ne donne que des « importances », beaucoup plus
difficiles à raconter.

**2. Elle surajuste peu.** Avec 1 885 lignes et 23 features, un modèle non linéaire a toute latitude pour
apprendre du bruit. Une logistique régularisée, non : elle ne peut ajuster que 24 nombres.

**3. Elle fixe le plancher.** Si les arbres ne battent pas la logistique, c'est que la relation est
essentiellement linéaire — et alors on garde le modèle simple. C'est le principe du **rasoir d'Ockham**
appliqué à la modélisation : à performance égale, le modèle le plus simple gagne, parce qu'il est plus
facile à défendre, plus stable dans le temps, et plus difficile à surajuster.

## 4.2 — La notion : passer d'une droite à une probabilité

### Le problème

Une régression linéaire ordinaire prédit un nombre qui peut valoir −3 ou +7. Une probabilité doit rester
entre 0 et 1. Il faut donc une transformation.

### La solution : les log-odds

On ne modélise pas la probabilité directement, on modélise son **logarithme de la cote** (*log-odds*, aussi
appelé *logit*) :

```
              (      p      )
      ln      ( ----------- )   =   b0  +  b1·x1  +  b2·x2  +  ...  +  bk·xk
              (    1 − p    )
```

**La cote** (*odds*) est `p / (1−p)`. Si p = 0,75, la cote vaut 3 : « trois chances contre une ». C'est le
langage des parieurs et des actuaires.

Le logarithme fait passer la cote, qui vit dans `]0, +infini[`, dans `]−infini, +infini[`. On peut donc y
mettre une combinaison linéaire sans contrainte. C'est tout le truc.

### La transformation inverse

Pour repasser en probabilité :

```
                        1
      p   =   ----------------------
              1  +  exp( − z )
```

où `z = b0 + b1·x1 + ...`. C'est la **fonction sigmoïde**, la courbe en S. Elle vaut 0,5 quand z = 0, elle
tend vers 1 quand z augmente, vers 0 quand z diminue.

Trois valeurs à mémoriser :

```
z = −2  ->  p = 0,119
z =  0  ->  p = 0,500
z = +2  ->  p = 0,881
```

### Comment on estime les coefficients

Par **maximum de vraisemblance**. On cherche les `b` qui maximisent la probabilité d'observer exactement les
données qu'on a observées :

```
Vraisemblance  =  produit sur i  de  [ p_i ^ y_i  ×  (1 − p_i) ^ (1 − y_i) ]
```

En pratique on minimise l'opposé de son logarithme, la **log-vraisemblance négative**, aussi appelée
*log-loss* ou entropie croisée :

```
                 1
   log-loss = − ---  ×  somme [ y_i · ln(p_i)  +  (1 − y_i) · ln(1 − p_i) ]
                 n
```

L'intuition : si la réalité est y = 1 et que le modèle annonce p = 0,01, alors `ln(0,01) = −4,6` et la
pénalité est énorme. Le modèle est violemment poussé à ne pas être confiant et faux. C'est le même esprit
que le Brier, avec un logarithme au lieu d'un carré — donc une punition encore plus sévère de la
sur-confiance.

## 4.3 — L'odds ratio : la traduction en français

C'est **la** notion qui permet d'écrire des phrases dans un mémoire.

```
      odds ratio  =  exp( coefficient )
```

Interprétation : *« quand la variable augmente d'une unité, toutes choses égales par ailleurs, la cote de
l'événement est multipliée par exp(b) »*.

Comme les variables ont été **standardisées** par le `StandardScaler` du pipeline, « une unité » signifie
ici **un écart-type**. C'est ce qui rend les coefficients comparables entre eux.

### Exemple sur ton propre résultat

Le coefficient de `z_mu_night_full` vaut **1,0036**, donc :

```
odds ratio = exp(1,0036) = 2,728
```

**La phrase de mémoire** : *« Lorsque le sentiment nocturne normalisé augmente d'un écart-type, la cote
d'une ouverture haussière est multipliée par 2,73, toutes choses égales par ailleurs. »*

En probabilités concrètes, en partant du taux de base de 0,595 :

```
cote de départ   =  0,595 / 0,405            =  1,469
cote après       =  1,469 × 2,728            =  4,008
probabilité      =  4,008 / (1 + 4,008)      =  0,800
```

On passe de 59,5 % à **80,0 %**. C'est spectaculaire.

> **Et c'est précisément pour ça qu'il faut se méfier.** Un odds ratio de 2,73 sur une seule variable, en
> prédiction boursière journalière, est un chiffre que la littérature académique ne produit à peu près
> jamais. Garde-le en tête : le chapitre 7 va montrer que ce coefficient **ne peut pas être interprété**,
> et le chapitre 9 va montrer que cette variable **n'est même pas celle qui porte le signal**.

## 4.4 — Le pipeline, étage par étage

```python
Pipeline([
    ("imp", SimpleImputer(strategy="median")),
    ("std", StandardScaler()),
    ("clf", LogisticRegression(max_iter=2000, C=C, solver="lbfgs")),
])
```

**Étage 1 — l'imputation par la médiane.** Les valeurs manquantes sont remplacées par la médiane de la
colonne. Pourquoi la médiane et pas la moyenne ? Parce qu'elle est **robuste aux valeurs extrêmes**. Un
z-score de +6 sur un jour de panique tirerait la moyenne vers le haut ; la médiane ne bouge pas.

**Étage 2 — la standardisation.** On centre et on réduit chaque colonne :

```
x_standardisé = ( x − moyenne ) / écart-type
```

Deux raisons impératives :

- **La régularisation L2 pénalise la taille des coefficients.** Si une variable est en pourcentage
  (0 à 100) et une autre en proportion (0 à 1), la première aura un coefficient cent fois plus petit et sera
  cent fois moins pénalisée. La régularisation serait donc appliquée de façon arbitraire.
- **Les coefficients deviennent comparables** entre eux, ce qui est indispensable pour le graphique du
  chapitre 7.

**Le point crucial, et le notebook le fait bien** : ces deux étages sont **dans le pipeline**. Cela signifie
que la médiane et l'écart-type sont calculés **uniquement sur le bloc d'entraînement** à chaque `.fit()`,
puis **appliqués** au bloc d'évaluation. Si on avait standardisé le DataFrame entier avant de découper, la
moyenne du test aurait contaminé le train : c'est la **fuite de prétraitement** (Cours 3, ch. 0, type 3).

> **Une phrase de soutenance qui marque des points** : *« La standardisation est encapsulée dans le pipeline
> scikit-learn, de sorte que ses paramètres sont estimés exclusivement sur l'échantillon d'apprentissage à
> chaque repli de la validation glissante, ce qui exclut toute fuite de prétraitement. »*

---

# Chapitre 5 — La régularisation L2 et le choix de C

## 5.1 — Le problème : le surajustement

Sans contrainte, l'estimation par maximum de vraisemblance cherche les coefficients qui expliquent le mieux
**les données d'entraînement**. Rien ne l'empêche de produire des coefficients gigantesques qui collent au
bruit.

Le cas extrême s'appelle la **séparation parfaite** : s'il existe une combinaison de variables qui sépare
exactement les 1 des 0 dans l'échantillon d'entraînement, la vraisemblance est maximisée en faisant tendre
les coefficients vers l'infini. Le modèle devient infiniment confiant sur des données qu'il n'a jamais vues.

## 5.2 — La solution : la pénalité ridge

On ajoute au critère à minimiser un terme qui punit les gros coefficients :

```
                            1                          k
   Critère  =  C  ×  log-loss   +   (1/2) ×  somme    b_j²
                                            j = 1
```

Le second terme, la somme des carrés des coefficients, s'appelle la **pénalité L2** (ou ridge, ou de
Tikhonov). Il pousse tous les coefficients vers zéro, sans jamais les y amener exactement.

### Le rôle de C

Dans scikit-learn, `C` est l'**inverse de la force de régularisation** :

- **C petit** (0,01) → la pénalité domine → coefficients écrasés → modèle **rigide**, fort biais, faible
  variance.
- **C grand** (3,0) → la vraisemblance domine → coefficients libres → modèle **souple**, faible biais, forte
  variance.

C'est le **compromis biais-variance**, le concept central de tout l'apprentissage statistique.

### L'analogie

Imagine que tu enseignes à un élève. Tu peux :

- lui interdire de retenir plus de trois idées (C petit) : il ne retiendra que les grandes lignes, ratera les
  subtilités, mais ne racontera pas n'importe quoi ;
- le laisser tout mémoriser (C grand) : il connaîtra le cours par cœur, y compris les fautes de frappe du
  polycopié, et sera perdu devant une question reformulée.

La régularisation est la manière de dire : « retiens ce qui se répète, oublie ce qui n'arrive qu'une fois ».

## 5.3 — Pourquoi elle est indispensable **ici** précisément

Le notebook le dit en une phrase : *« la pénalité empêche les coefficients de devenir grands, ce qui est
indispensable quand les features sont corrélées entre elles — ce qui est le cas ici (`z_mu_night_full`,
`z_mu_overnight` et `z_mu_pre` sont liées par construction) »*.

C'est exact, et c'est fondamental. Rappelle-toi la construction des fenêtres (Cours 1) :

```
night_full  =  overnight  ∪  pre
```

La fenêtre « nuit complète » est **l'union** des deux autres. Ces trois variables ne sont donc pas
seulement corrélées : elles sont liées par une relation quasi déterministe. Sans pénalité, la logistique
peut mettre +50 sur l'une et −50 sur l'autre : la somme reste raisonnable, la vraisemblance est légèrement
améliorée, et le modèle est complètement instable.

Le chapitre 7 va montrer que **même avec la pénalité**, le problème n'est pas réglé.

## 5.4 — Le choix de C, et pourquoi c'est fait correctement

```python
meilleur = (None, -np.inf, None)
for C in [0.01, 0.03, 0.1, 0.3, 1.0, 3.0]:
    p   = pipeline_logit(C).fit(tr[feats], tr[CIBLE])     # entraîné sur TRAIN
    auc = roc_auc_score(va[CIBLE], p.predict_proba(va[feats])[:, 1])   # évalué sur VALID
    if auc > meilleur[1]:
        meilleur = (C, auc, p)
```

Deux choses à noter, et les deux sont bien faites :

**(a) La grille est logarithmique** : 0,01 / 0,03 / 0,1 / 0,3 / 1 / 3. On multiplie par environ 3 à chaque
pas. C'est la bonne façon d'explorer un paramètre d'échelle : ce qui compte est l'ordre de grandeur, pas la
valeur exacte. Chercher C = 1,0 puis 1,1 puis 1,2 serait une perte de temps.

**(b) L'entraînement est sur `tr`, l'évaluation sur `va`.** Le bloc de test n'est jamais touché. C'est la
règle des trois échantillons :

```
TRAIN  ->  estimer les coefficients
VALID  ->  choisir les hyperparamètres (C, profondeur, etc.)
TEST   ->  mesurer la performance, UNE SEULE FOIS
```

> **Pourquoi trois et pas deux.** Si l'on choisit C sur le test, on a « optimisé sur le test », et le score
> annoncé est optimiste : c'est devenu un score d'entraînement déguisé. Avec 6 valeurs de C testées, le biais
> est petit ; avec 200 configurations, il devient énorme. Ce phénomène s'appelle le **biais de sélection de
> modèle**, et c'est la deuxième cause de résultats non reproductibles en finance quantitative, juste après
> la fuite de données.

---

# Chapitre 6 — Les trois spécifications emboîtées

## 6.1 — Le principe des modèles emboîtés

Deux modèles sont **emboîtés** (*nested*) quand les variables de l'un sont un sous-ensemble des variables de
l'autre. La différence de performance mesure alors exactement **l'apport des variables ajoutées**.

| Modèle | Variables | Question posée |
|---|---|---|
| **L-ctrl** | 9 contrôles de marché | quelle part vient du marché ? |
| **L-sent** | 14 variables de sentiment | quelle part vient du texte ? |
| **L-tout** | les 23 | le texte apporte-t-il **en plus** du marché ? |

C'est la structure d'argumentation la plus solide qui existe pour répondre à : « comment savez-vous que
c'est bien le sentiment qui prédit, et pas autre chose ? ».

## 6.2 — La sortie réelle

```
                  modele   n    AUC    MCC  Brier  Accuracy  base_rate  taux_signal    C  gain_vs_naif
L-ctrl (contrôles seuls) 520 0.4822 0.0134 0.2400    0.6058     0.6058       0.9962 0.01        0.0000
 L-sent (sentiment seul) 520 0.6642 0.1596 0.2226    0.6192     0.6058       0.7404 1.00        0.0134
       L-tout (les deux) 520 0.6561 0.1726 0.2256    0.6212     0.6058       0.7115 3.00        0.0154

  contrôles de marché seuls .............. 0.4822
  sentiment seul ......................... 0.6642
  les deux ............................... 0.6561
  apport net du sentiment ................ +0.1739
```

## 6.3 — Ce que ces trois lignes disent vraiment

### Les contrôles de marché ne prédisent rien — et même un peu moins que rien

```
AUC = 0,4822
```

C'est **en dessous** de 0,50, de 0,78 écart-type (rappel : sigma ≈ 0,023). Ce n'est pas significativement
différent du hasard, mais ce n'est certainement pas un signal.

**Traduction économique** : les rendements passés, la volatilité, l'amplitude, le volume et le jour de la
semaine ne permettent pas de prédire le signe du gap d'ouverture du lendemain. **C'est exactement ce que
prédit la théorie de l'efficience des marchés en forme faible** (Fama, 1970) : l'information contenue dans
les prix passés est déjà intégrée dans les prix.

> **C'est un résultat, pas un échec.** Ton mémoire vient de vérifier empiriquement, sur 520 observations
> hors échantillon, l'efficience faible du marché sur cinq grandes capitalisations technologiques. Écris-le
> comme tel : cela montre que ton protocole est capable de produire un « rien » quand il n'y a rien — ce qui
> est la condition pour croire ses « quelque chose ».

Regarde aussi les deux autres colonnes :

- `taux_signal = 0,9962` : le modèle dit « hausse » 99,6 % du temps. Il a **dégénéré vers R1**. Il n'a rien
  trouvé, alors il prédit la classe majoritaire. Son exactitude de 0,6058 est donc exactement celle de la
  référence naïve : `gain_vs_naif = 0,0000`, au dix-millième près.
- `C = 0,01` : la validation a choisi la **régularisation la plus forte** de toute la grille. Traduction :
  « le meilleur usage possible de ces variables est de ne pas s'en servir ». La procédure de sélection a
  elle-même reconnu qu'il n'y avait rien à apprendre. C'est élégant.

### Le sentiment seul prédit

```
AUC = 0,6642, soit 7,1 écarts-types au-dessus du hasard
```

Sur la validation, le sentiment nocturne classe correctement deux jours sur trois. C'est très au-dessus de
la référence R4 sans apprentissage (0,5937) : l'apprentissage apporte donc **+0,070 point d'AUC**, ce qui
justifie la modélisation.

### Ajouter les contrôles **dégrade** le modèle

```
L-sent 0,6642    ->    L-tout 0,6561       (−0,0081)
```

C'est contre-intuitif : ajouter de l'information ne devrait pas faire baisser la performance. En théorie,
un modèle qui dispose de plus de variables peut toujours mettre un coefficient nul sur les inutiles.

En pratique, non, pour trois raisons :

1. **Chaque variable inutile ajoute de la variance d'estimation.** Neuf coefficients de plus à estimer sur
   1 885 lignes, c'est neuf sources de bruit.
2. **La régularisation est globale.** La pénalité L2 s'applique à *tous* les coefficients. Pour laisser les
   9 contrôles s'exprimer, la validation a dû choisir C = 3,0 (au lieu de 1,0) : la contrainte s'est
   relâchée sur les variables de sentiment aussi, qui sont donc moins bien régularisées.
3. **La colinéarité se propage.** Les contrôles sont eux-mêmes très corrélés entre eux (chapitre 7), ce qui
   déstabilise toute la matrice à inverser.

> **Ce que ça implique pour ton mémoire.** Le meilleur modèle logistique de ton notebook est **le modèle
> sentiment seul**. Les contrôles n'ont pas leur place dans le modèle final ; leur rôle est d'être un
> **modèle de référence** (L-ctrl) qui prouve que le marché ne prédit rien. Ce sont deux fonctions
> différentes, et le notebook les confond un peu. Voir le chapitre 15, point 3.

## 6.4 — L'« apport net » de +0,1739 : attention à la formulation

Le notebook calcule :

```
apport net = AUC(tout) − AUC(contrôles) = 0,6561 − 0,4822 = +0,1739
```

**Le calcul est juste, mais la formulation est fragile.** Voici pourquoi.

Le point de comparaison retenu, 0,4822, est **en dessous du hasard**. Or un modèle qui obtient 0,48 n'est
pas « moins bon que rien » : il est **équivalent à rien**, le 0,48 étant du bruit d'échantillonnage. Le
plancher naturel n'est donc pas 0,4822 mais **0,50**.

Deux façons plus défendables de présenter la même chose :

```
Version A (par rapport au hasard)
   AUC(sentiment seul) − 0,50            =  0,6642 − 0,50    =  +0,164

Version B (par rapport à la référence sans apprentissage)
   AUC(sentiment seul) − AUC(R4)         =  0,6642 − 0,5937  =  +0,070
```

La version B est la plus honnête et la plus impressionnante intellectuellement, parce qu'elle sépare
proprement deux contributions :

```
+0,094  =  ce qu'apporte la VARIABLE de sentiment  (0,5937 − 0,50)
+0,070  =  ce qu'apporte la MODÉLISATION            (0,6642 − 0,5937)
--------
+0,164  =  total
```

> **La phrase de mémoire** : *« La variable de sentiment brute, sans apprentissage, porte à elle seule 57 %
> du pouvoir prédictif total ; la modélisation multivariée en apporte les 43 % restants. »*
>
> Un jury retient ce genre de décomposition. Elle montre que tu sais d'où vient ton résultat.

---

# Chapitre 7 — Lire les coefficients, et découvrir le VIF

C'est le chapitre le plus important du cours. Il contient le premier des trois grands enseignements du
notebook 06.

## 7.1 — Le tableau des coefficients

```
           feature   famille    coef  odds_ratio
   z_mu_night_full sentiment  1.0036      2.7280
  z_pos_night_full sentiment -0.7439      0.4753     <-- signe NÉGATIF ?!
          z_mu_pre sentiment  0.4604      1.5847
          ampl_ma5    marché  0.2657      1.3043
    z_sd_overnight sentiment  0.2500      1.2840
    z_mu_night_ma3 sentiment -0.1455      0.8646     <-- signe NÉGATIF ?!
         ampl_lag1    marché -0.1161      0.8904
   z_sd_night_full sentiment -0.1116      0.8944
          gap_lag1    marché -0.1021      0.9029
  z_neg_night_full sentiment -0.0958      0.9087
  rk_mu_night_full sentiment -0.0652      0.9369     <-- signe NÉGATIF ?!
    z_mu_overnight sentiment -0.0613      0.9405     <-- signe NÉGATIF ?!
 z_nlog_night_full sentiment  0.0613      1.0632
   ... (les autres sont proches de zéro)
```

## 7.2 — Les signes qui n'ont aucun sens

Regarde bien. Quatre variables ont un signe **économiquement absurde** :

| Variable | Ce qu'elle mesure | Signe attendu | Signe obtenu |
|---|---|---|---|
| `z_pos_night_full` | proportion de messages **positifs** | **+** | **−0,744** |
| `z_mu_night_ma3` | sentiment moyen des 3 dernières nuits | + | −0,146 |
| `rk_mu_night_full` | rang percentile du sentiment nocturne | + | −0,065 |
| `z_mu_overnight` | sentiment de la fenêtre 16h→minuit | + | −0,061 |

Le cas de `z_pos_night_full` est le plus frappant : le modèle affirme que **plus il y a de messages positifs
la nuit, plus l'ouverture a de chances d'être baissière**, avec un odds ratio de 0,475 — la cote est
**divisée par deux**.

C'est évidemment faux. Le notebook 04 a montré le contraire de façon monotone sur les cinq titres.

**Alors que se passe-t-il ?**

## 7.3 — La multicolinéarité, expliquée simplement

### La notion

La **multicolinéarité** est la situation où une variable explicative peut être (presque) reconstruite à
partir des autres. La régression devient alors incapable d'attribuer le crédit correctement.

### L'analogie des deux ouvriers

Deux maçons, Alain et Bernard, travaillent **toujours ensemble**, jamais séparément. Sur 100 chantiers, ils
sont tous les deux présents. Les chantiers avancent bien.

Question : quelle est la contribution d'Alain ? De Bernard ?

**Réponse : impossible à savoir.** Les données ne contiennent aucune information là-dessus, parce qu'on n'a
jamais observé un chantier avec l'un sans l'autre. Le modèle peut écrire :

```
production = 10·Alain + 0·Bernard        (ajustement parfait)
production = 0·Alain  + 10·Bernard       (ajustement parfait)
production = 500·Alain − 490·Bernard     (ajustement parfait aussi !)
```

Les trois solutions expliquent les données **exactement aussi bien**. L'algorithme en choisit une, presque
au hasard, en fonction de détails numériques. Et il peut très bien choisir la troisième, avec un
coefficient négatif énorme sur Bernard.

**C'est exactement ce qui arrive à `z_pos_night_full`.**

### La preuve arithmétique dans ton cas

Rappelle-toi l'identité fondamentale de FinBERT (Cours 1) :

```
mu  =  p_positif  −  p_négatif
```

et, les trois probabilités sommant à 1 :

```
p_positif  +  p_négatif  +  p_neutre  =  1
```

Donc `mu`, `pos` et `neg` ne sont **pas trois informations indépendantes** : connaissant deux d'entre elles,
la troisième est déterminée. En mettant `z_mu_night_full`, `z_pos_night_full` et `z_neg_night_full` dans le
même modèle, on injecte une **quasi-dépendance linéaire exacte**.

Le modèle réagit en mettant +1,00 sur `mu` et −0,74 sur `pos`. La somme des deux effets reste correcte —
c'est pourquoi la **prédiction** est bonne — mais chaque coefficient pris isolément **n'a aucun sens**.

## 7.4 — Le VIF : mettre un chiffre sur le problème

### La définition

Le **facteur d'inflation de la variance** (*Variance Inflation Factor*) mesure, pour chaque variable, à quel
point elle est prévisible par les autres.

```
                    1
   VIF_j  =  ---------------
              1  −  R²_j
```

où `R²_j` est le coefficient de détermination de la régression de la variable j **sur toutes les autres
variables explicatives**.

### La lecture

| VIF | R² correspondant | Interprétation |
|---|---|---|
| 1 | 0 % | variable totalement indépendante des autres — idéal |
| 5 | 80 % | limite d'acceptabilité usuelle |
| 10 | 90 % | problème sérieux |
| 100 | 99 % | coefficient ininterprétable |
| 1000 | 99,9 % | **quasi-dépendance exacte — erreur de spécification** |

### Son sens précis

Le VIF dit littéralement de combien la **variance du coefficient estimé** est multipliée par rapport à une
situation sans colinéarité. Un VIF de 100 signifie que l'écart-type du coefficient est multiplié par 10
(racine de 100). L'intervalle de confiance est dix fois plus large.

## 7.5 — Tes VIF réels — et là, il faut s'asseoir

```
           feature     VIF
       ret_cc_lag1 1516.24     <-- !!!
       ret_oc_lag1  826.92     <-- !!!
          gap_lag1  631.05     <-- !!!
   z_mu_night_full  101.17
  z_pos_night_full   45.63
   z_sd_night_full   24.85
  z_neg_night_full   24.75
    z_mu_overnight   12.62
    z_sd_overnight    8.67
          z_mu_pre    7.96
 z_nabn_night_full    7.09
          z_sd_pre    5.72
 z_nlog_night_full    5.13
    z_mu_night_ma3    5.12
          ampl_ma5    4.52
rk_nabn_night_full    4.08
  rk_mu_night_full    3.97
       z_dmu_night    3.94
         ampl_lag1    3.44
            vol_20    2.96
      vol_dollar_z    2.04
               dow    1.17
          gap_lag2    1.13
```

Le seuil d'alerte usuel est 5. **Treize variables sur 23 le dépassent.** Et trois d'entre elles dépassent
600.

### Les trois monstres : une identité comptable oubliée

`ret_cc_lag1` = 1516, `ret_oc_lag1` = 827, `gap_lag1` = 631. Un VIF de 1516 correspond à un R² de
**99,934 %**. Ce n'est pas de la corrélation, c'est une **relation déterministe**.

Et en effet, elle l'est. Rappelle-toi l'identité multiplicative des rendements (Cours 1) :

```
( 1 + gap )  ×  ( 1 + ret_oc )   =   1 + ret_cc
```

En développant, et parce que les rendements journaliers sont petits (le produit `gap × ret_oc` est de
l'ordre de 0,0001) :

```
ret_cc   ≈   gap  +  ret_oc
```

Les trois variables décalées d'un jour vérifient donc, à 0,01 % près :

```
ret_cc_lag1  ≈  gap_lag1  +  ret_oc_lag1
```

**C'est une identité comptable, pas une corrélation empirique.** Mettre les trois dans le même modèle
revient à écrire une équation où une variable est la somme des deux autres. La matrice à inverser est
quasi singulière.

### Pourquoi c'est LA cause du 0,4822

Souviens-toi : L-ctrl (contrôles seuls) obtient une AUC de **0,4822**, en dessous du hasard, et la validation
a choisi la régularisation maximale (C = 0,01).

On comprend maintenant pourquoi. Trois de ses neuf variables sont liées par une identité exacte. La
régression ne peut rien en tirer de stable, et la seule échappatoire que la validation ait trouvée est
d'écraser tous les coefficients à zéro.

> **Question ouverte, et intéressante pour ton mémoire** : est-ce que le marché ne prédit vraiment rien, ou
> est-ce que la **spécification** des contrôles est mal construite ? Les deux hypothèses expliquent le
> 0,4822. Pour trancher, il suffirait de retirer `ret_cc_lag1` (redondante par construction) et de refaire
> tourner L-ctrl. C'est un travail de dix minutes, et ça vaut la peine : si l'AUC reste à 0,50, ta
> conclusion sur l'efficience faible est solide ; si elle monte à 0,54, il faut la nuancer.
>
> **C'est exactement le genre de correction qui fait la différence entre un bon mémoire et un très bon
> mémoire.** Le code est au chapitre 15.

### Le cas de `z_mu_night_full` : VIF = 101

R² = 99,01 %. Cette variable est reconstructible à 99 % à partir des autres — sans surprise, puisque :

```
night_full = overnight ∪ pre        (union des fenêtres)
mu = pos − neg                      (identité FinBERT)
```

Son coefficient de 1,0036 et son odds ratio de 2,728, si impressionnants au chapitre 4, **sont donc
ininterprétables**. Ne les mets pas dans ton mémoire sans l'avertissement qui va avec.

## 7.6 — Le résumé du chapitre, en une page

**Ce qu'il faut retenir absolument :**

1. La multicolinéarité **ne dégrade pas les prédictions**. Le modèle L-tout prédit bien (AUC 0,656) malgré
   des VIF catastrophiques. La somme des effets reste correcte.
2. Elle **détruit totalement l'interprétation**. Signes inversés, amplitudes absurdes, coefficients qui
   changent complètement si l'on retire une observation.
3. **Il ne faut donc pas interpréter les coefficients de ce modèle.** Ni dans le mémoire, ni en soutenance.
4. Pour interpréter, il existe trois voies propres :
   - **retirer les redondances** (garder `mu`, jeter `pos` et `neg` ; garder `gap` et `ret_oc`, jeter
     `ret_cc`) ;
   - utiliser une méthode **conçue pour la colinéarité** (régression sur composantes principales, PLS,
     Elastic Net) ;
   - utiliser une mesure d'importance **qui ne dépend pas des coefficients** — et c'est exactement ce que
     fait le chapitre 9.

> **La phrase de soutenance** : *« Les facteurs d'inflation de la variance atteignent 1 516 sur les
> rendements retardés, du fait de l'identité comptable liant le gap, le rendement de séance et le rendement
> de clôture à clôture. Les coefficients de la régression logistique ne sont donc pas interprétables
> individuellement ; l'analyse de contribution repose sur l'importance par permutation, qui en est
> exempte. »*
>
> Si tu dis cette phrase, tu montres que tu as compris quelque chose que la majorité des mémoires ignore.

---

# Chapitre 8 — Les arbres : forêt aléatoire et boosting

## 8.1 — Pourquoi la logistique ne peut pas suffire

Rappelle-toi le tableau des quintiles du notebook 04 :

```
Q1: −0,51 %   Q2: +0,27 %   Q3: +0,28 %   Q4: +0,23 %   Q5: +0,52 %
```

Regarde la forme : Q2, Q3 et Q4 sont **plats**. Toute l'information est dans les **extrêmes**.

Or la régression logistique suppose que l'effet est **constant par unité de z-score** : passer de −2 à −1 a
exactement le même effet que passer de 0 à +1. Elle est **structurellement incapable** de représenter « rien
au milieu, beaucoup aux bords ».

Un arbre, lui, découpe l'espace en régions et peut apprendre exactement la règle qu'il faut :

```
si  z_mu_night_full < −1,5   ->   probabilité de gap positif = 0,35
sinon si z_mu_night_full > +1,5  ->  probabilité = 0,72
sinon                            ->  probabilité = 0,60
```

## 8.2 — La forêt aléatoire

### Le principe

On construit 400 arbres, chacun sur :

- un **échantillon bootstrap** des lignes (tirage avec remise) ;
- un **sous-ensemble aléatoire des variables** à chaque nœud (`max_features="sqrt"`, soit environ
  racine(23) ≈ 5 variables candidates).

La prédiction finale est la moyenne des 400.

### Pourquoi ça marche : la réduction de variance

Si l'on moyenne n estimateurs de variance `sigma²` et de corrélation deux à deux `rho` :

```
                                        1 − rho
Var( moyenne )  =  rho · sigma²  +  ------------- · sigma²
                                            n
```

Le second terme s'effondre avec n. **Le premier, non.** C'est pourquoi le double tirage aléatoire (lignes
*et* colonnes) est essentiel : il sert uniquement à **faire baisser rho**, la corrélation entre arbres.
Sans le tirage sur les colonnes, tous les arbres choisiraient la même variable en racine et seraient
quasi identiques : rho ≈ 1, et la moyenne n'apporterait rien.

### La grille testée

```python
max_depth        in (3, 4, 6)
min_samples_leaf in (20, 40, 80)
class_weight     = "balanced_subsample"
```

`min_samples_leaf = 20` signifie qu'une feuille doit contenir au moins 20 observations. Avec 1 885 lignes,
cela borne le nombre de feuilles à environ 94 : impossible de mémoriser des cas individuels. C'est une
régularisation forte et bien choisie.

`class_weight="balanced_subsample"` repondère les classes pour compenser le déséquilibre 60/40. Bon réflexe.

**Résultat retenu : `max_depth=6, min_samples_leaf=20`** — la profondeur maximale de la grille a été
choisie, ce qui suggère qu'une grille plus large (8, 10) aurait peut-être fait mieux. À mentionner comme
limite.

## 8.3 — Le gradient boosting

### Le principe, complètement différent

La forêt construit des arbres **en parallèle** et les moyenne. Le boosting les construit **en séquence**,
chacun corrigeant les erreurs du précédent.

```
F_0  =  prédiction initiale (le taux de base)
pour m = 1, 2, ..., M :
      r_m  =  gradient de la perte au point F_(m−1)      ("ce qui reste à expliquer")
      h_m  =  petit arbre ajusté sur r_m
      F_m  =  F_(m−1)  +  eta · h_m
```

`eta` est le **taux d'apprentissage** (ici 0,02). Chaque arbre ne corrige que 2 % de l'erreur restante. On
avance à tout petits pas, ce qui régularise fortement.

### L'analogie

La forêt aléatoire, c'est **400 experts qui donnent leur avis indépendamment**, et on fait la moyenne. Le
boosting, c'est **250 relecteurs en chaîne** : chacun ne corrige que les fautes que le précédent a laissées.

### Les garde-fous du notebook

```python
max_depth          in (2, 3)        # arbres très courts : 4 à 8 feuilles
learning_rate      in (0.02, 0.05)  # pas minuscules
max_iter           = 250
l2_regularization  = 1.0
early_stopping     = True
validation_fraction= 0.15
```

`early_stopping=True` est important : l'algorithme met de côté 15 % du train, surveille la performance, et
**s'arrête tout seul** quand elle cesse de progresser. C'est une protection automatique contre le
surajustement, qui rend le choix de `max_iter=250` peu critique.

**Résultat retenu : `max_depth=3, learning_rate=0.02, min_samples_leaf=20`** — la configuration la plus
contrainte de la grille. Le modèle a lui-même choisi d'être simple. Bon signe.

## 8.4 — Le classement sur la validation

```
                                modele   n    AUC     MCC  Brier  Accuracy  base_rate  gain_vs_naif
                     Gradient Boosting 520 0.6735  0.1908 0.2223    0.6346     0.6058        0.0288
               L-sent (sentiment seul) 520 0.6642  0.1596 0.2226    0.6192     0.6058        0.0134
                         Random Forest 520 0.6632  0.1990 0.2317    0.6077     0.6058        0.0019
                     L-tout (les deux) 520 0.6561  0.1726 0.2256    0.6212     0.6058        0.0154
R4 sentiment brut (sans apprentissage) 520 0.5937  0.1194 0.2611    0.5538     0.6058       -0.0520
                       R3 momentum J-1 520 0.5050  0.0088 0.2834    0.5173     0.6058       -0.0885
                    R1 toujours hausse 520 0.5000  0.0000 0.3864    0.6058     0.6058        0.0000
                             R2 hasard 520 0.4936 -0.0323 0.3366    0.4846     0.6058       -0.1212
              L-ctrl (contrôles seuls) 520 0.4822  0.0134 0.2400    0.6058     0.6058        0.0000
```

### Les quatre observations qui comptent

**(1) Les quatre modèles appris se tiennent en 0,017 point d'AUC** (0,6561 à 0,6735). Avec une barre
d'erreur de ±0,023, **ils sont statistiquement indiscernables**.

> **Conséquence méthodologique majeure** : dire « le gradient boosting est le meilleur modèle » n'est pas
> soutenable. L'écart de 0,0093 avec la logistique sentiment vaut 0,4 écart-type. La bonne formulation est :
> *« quatre spécifications, de la régression logistique au gradient boosting, produisent des performances
> statistiquement indiscernables, ce qui suggère que la relation est essentiellement capturée par la
> composante linéaire du sentiment. »*

**(2) La non-linéarité n'apporte presque rien.** C'est un résultat en soi. Le tableau des quintiles suggérait
un effet en U, mais le gradient boosting ne gagne que +0,009 sur la logistique. **Conclusion : la relation
est essentiellement monotone**, et la logistique suffit. Rasoir d'Ockham : garde le modèle simple.

**(3) Le Brier départage mieux que l'AUC.** Regarde la forêt aléatoire : AUC 0,6632 (très correcte) mais
Brier 0,2317, nettement moins bon que le boosting (0,2223). C'est un défaut connu : la moyenne de 400 arbres
comprime les probabilités vers le centre et ne descend jamais sous 0,15 ni au-dessus de 0,85. **Elle classe
bien mais annonce mal.** C'est la dissociation du §2.4, illustrée à nouveau.

**(4) Le meilleur `gain_vs_naif` est de +0,0288**, soit 2,9 points d'exactitude au-dessus de la référence
naïve. Voilà le chiffre honnête à annoncer, à côté de l'AUC.

Et vérifie : tous les Brier des modèles appris (0,2223 à 0,2317) sont **sous la référence de Bernoulli
0,2388** calculée au §2.4. Tous apportent donc de l'information probabiliste réelle. R1, R2 et R3 sont
au-dessus : ils sont pires que de ne rien faire.

---

# Chapitre 9 — L'importance par permutation : le grand renversement

C'est le deuxième grand enseignement du notebook, et probablement le résultat le plus important pour la
suite de ton mémoire.

## 9.1 — Pourquoi ne pas utiliser `feature_importances_`

L'importance intégrée aux arbres (*Gini importance*) mesure la réduction totale d'impureté apportée par
chaque variable. Elle a deux défauts sévères, démontrés par Strobl et al. (2007) :

- **Elle favorise les variables continues à forte cardinalité.** Une variable continue offre des centaines
  de points de coupe possibles, une variable binaire un seul. La première a donc mécaniquement plus de
  chances d'être choisie, même sans lien avec la cible.
- **Elle est calculée sur les données d'entraînement.** Une variable utilisée pour mémoriser du bruit
  apparaît comme importante.

## 9.2 — Le principe de la permutation

L'idée est d'une simplicité totale :

> **On mélange aléatoirement une colonne, et on regarde de combien la performance chute.**

En mélangeant la colonne, on **détruit son lien avec la cible** tout en conservant sa distribution. Si le
modèle s'appuyait vraiment dessus, sa performance s'effondre. Sinon, rien ne bouge.

```python
imp = permutation_importance(gb, va[FEATURES], va[CIBLE],
                             n_repeats=30, scoring="roc_auc")
```

Trois points bien faits :

- **calculée sur la validation**, pas sur le train : on mesure l'utilité **hors échantillon** ;
- **`n_repeats=30`** : la permutation est aléatoire, on la répète 30 fois pour obtenir une moyenne et un
  écart-type ;
- **`scoring="roc_auc"`** : cohérent avec la métrique principale.

## 9.3 — Le résultat, et le choc

```
           feature  perte_AUC  ecart_type   famille
          z_mu_pre     0.0867      0.0202 sentiment    <-- ÉCRASE TOUT
  z_neg_night_full     0.0277      0.0095 sentiment
 z_nlog_night_full     0.0165      0.0055 sentiment
          z_sd_pre     0.0162      0.0070 sentiment
            vol_20     0.0115      0.0039    marché
       ret_cc_lag1     0.0044      0.0027    marché
          gap_lag1     0.0034      0.0020    marché
       z_dmu_night     0.0027      0.0037 sentiment
          ampl_ma5     0.0026      0.0018    marché
    z_mu_overnight     0.0024      0.0016 sentiment
   z_mu_night_full     0.0022      0.0051 sentiment    <-- QUASI NUL !
      vol_dollar_z     0.0021      0.0012    marché
               dow     0.0014      0.0024    marché
  z_pos_night_full     0.0007      0.0004 sentiment    <-- QUASI NUL !
   z_sd_night_full    -0.0003      0.0007 sentiment
    z_sd_overnight    -0.0019      0.0022 sentiment

Part de l'importance totale : sentiment 0.1559 | marché 0.0261
```

### Le renversement complet

Compare avec les coefficients du chapitre 7 :

| Variable | Coefficient logistique | Importance par permutation |
|---|---|---|
| `z_mu_night_full` | **1,0036** (le plus gros) | **0,0022** (rang 11, quasi nul) |
| `z_pos_night_full` | **−0,7439** (2ᵉ) | **0,0007** (rang 14, nul) |
| **`z_mu_pre`** | 0,4604 (3ᵉ) | **0,0867** (rang 1, écrase tout) |

**Les deux analyses se contredisent frontalement.** Et c'est l'analyse par permutation qui a raison.

### L'explication

C'est le prolongement direct du chapitre 7. La logistique met un gros coefficient sur `z_mu_night_full`
parce qu'elle a besoin de le compenser avec −0,74 sur `z_pos_night_full` : c'est un **artefact de la
colinéarité**, pas une mesure d'importance.

Le gradient boosting, lui, n'a pas ce problème : les arbres choisissent une variable à chaque nœud, et si
deux variables portent la même information, l'arbre en prend une et ignore l'autre. Quand on permute
`z_mu_night_full`, le modèle ne perd presque rien, **parce qu'il ne s'en servait pas** — il utilisait
`z_mu_pre`, qui contient la même information sous une forme plus fine.

### Deux mises en garde techniques à connaître

**(a) Les importances par permutation sont sous-estimées en présence de variables redondantes.** Si deux
colonnes portent la même information, permuter l'une seule ne fait rien perdre : l'autre compense. Les
valeurs quasi nulles de `z_mu_night_full`, `z_mu_overnight`, `rk_mu_night_full` reflètent donc **la
redondance**, pas nécessairement l'inutilité. La bonne pratique serait de permuter des **groupes** de
variables corrélées ensemble.

**(b) Les importances négatives** (`z_sd_overnight` à −0,0019) signifient que mélanger la colonne
**améliore** le modèle. C'est du bruit d'estimation quand la vraie importance est nulle. C'est utile : cela
donne l'échelle du bruit, ici environ ±0,002. Toute importance en dessous de 0,005 est donc à considérer
comme nulle.

### Le partage sentiment / marché

```
sentiment 0,1559     marché 0,0261        ratio = 6,0
```

**Six fois plus d'importance au texte qu'au marché.** C'est un chiffre puissant pour ton mémoire, et il
confirme la décomposition emboîtée du chapitre 6 par une méthode complètement différente. Quand deux
méthodes indépendantes concordent, la conclusion est solide.

## 9.4 — Et maintenant, la mauvaise nouvelle

Il faut regarder **quelle** variable domine.

```
z_mu_pre   =   sentiment moyen de la fenêtre  minuit  →  9h30
```

Elle porte à elle seule **56 % de l'importance de sentiment** (0,0867 sur 0,1559), et **3,1 fois plus** que
la deuxième.

Or cette fenêtre **recouvre la séance de pré-marché américaine, qui va de 4h00 à 9h30**.

Pendant ce pré-marché, il se négocie réellement des actions. Les prix bougent. Et surtout : **le prix
d'ouverture de 9h30 est littéralement en train de se former**. Ce n'est pas un événement instantané — c'est
l'aboutissement de cinq heures et demie de cotation.

Donc, quand un utilisateur écrit à 8h45 « TSLA is ripping premarket », il ne **prédit** pas l'ouverture :
il **décrit** un prix déjà largement formé, que ton modèle va ensuite « prédire » à 9h30.

**Ce n'est pas une fuite au sens technique** : aucune donnée du futur n'entre dans le calcul, l'horodatage
est respecté, le notebook 05 est irréprochable. C'est une **fuite économique** : l'information est
disponible avant l'événement, mais elle n'est pas *actionnable*, parce qu'au moment où le message est écrit,
le mouvement de prix a déjà eu lieu sur le marché de pré-ouverture.

### Ce que ça explique

Trois choses d'un coup :

1. **Pourquoi l'AUC est à 0,67**, dans la zone que le notebook lui-même déclare « suspecte ».
2. **Pourquoi le « jeu conservateur » (coupé à minuit) tombe à 0,597** (chapitre 11) : on lui retire
   précisément `z_mu_pre`, et l'AUC chute de 0,067. Ce n'est pas un détail — c'est la mesure directe de la
   composante non-actionnable du signal.
3. **Pourquoi le backtest du notebook 08 donne un Sharpe de 6** : il capitalise sur une information que
   personne ne peut négocier au prix supposé.

### Comment le tourner dans le mémoire

Surtout, **n'essaie pas de le cacher**. Au contraire : c'est le meilleur passage possible de ta discussion.

> *« L'analyse d'importance par permutation révèle que 56 % du pouvoir prédictif provient de la seule
> fenêtre minuit–9h30. Cette fenêtre recouvrant la séance de pré-ouverture (4h00–9h30), pendant laquelle le
> prix d'ouverture se forme effectivement, le signal correspondant relève davantage de la description
> contemporaine d'un mouvement en cours que d'une véritable anticipation. La spécification conservatrice,
> restreinte aux messages antérieurs à minuit, conserve une AUC de 0,597 (soit 4,2 écarts-types au-dessus du
> hasard) : c'est cette valeur, et non 0,671, qui mesure la part réellement anticipatrice du sentiment. »*

Ce paragraphe transforme un problème en résultat. Et il te protège complètement de la question qu'un jury
compétent posera de toute façon.

---

# Chapitre 10 — La validation glissante

## 10.1 — Pourquoi un seul découpage ne suffit pas

Le score obtenu sur une unique période de validation dépend de cette période. Si juillet–novembre 2021 a été
calme, le score sera flatteur. Si cette période a été agitée, il sera pessimiste.

**Un seul chiffre ne dit rien de la stabilité.**

## 10.2 — Le principe

```
Pli 1 : [====== entraînement ======]--purge--[test]
Pli 2 : [========= entraînement =========]--purge--[test]
Pli 3 : [============ entraînement ============]--purge--[test]
Pli 4 : [=============== entraînement ===============]--purge--[test]
```

À chaque pli, on entraîne sur **tout le passé disponible** et on teste sur la période suivante. C'est une
**fenêtre extensible** (*expanding window*), par opposition à une fenêtre glissante de taille fixe.

> **C'est la seule validation acceptable en finance**, parce que c'est la seule qui reproduit la situation
> réelle : au 1er mars, on ne dispose que des données antérieures au 1er mars.

Une validation croisée classique à 5 blocs entraînerait sur 2021-2022 pour prédire 2020. Absurde.

## 10.3 — La fonction, et son piège

```python
def plis_walk_forward(dates, n_plis=6, taille_test=60, min_train=250):
    jours = np.sort(pd.unique(dates))
    plis, fin = [], len(jours)
    for _ in range(n_plis):
        d0 = fin - taille_test
        if d0 - PURGE < min_train:
            break
        plis.append((jours[:d0 - PURGE], jours[d0:fin]))
        fin = d0
    return plis[::-1]
```

Trois points à comprendre :

**(a) `jours[:d0 - PURGE]`** — l'entraînement s'arrête `PURGE = 5` jours avant le début du test. C'est
l'**embargo** de López de Prado (2018), qui coupe le chevauchement des fenêtres glissantes de 60 jours.

**(b) La boucle part de la fin** et remonte le temps, puis `[::-1]` remet les plis dans l'ordre
chronologique pour l'affichage.

**(c) On demande 6 plis, on en obtient 4.** Déroulons avec 548 jours au total :

```
fin=548  ->  d0=488,  488−5=483 >= 250  OK   test = jours 488..547
fin=488  ->  d0=428,  423       >= 250  OK   test = jours 428..487
fin=428  ->  d0=368,  363       >= 250  OK   test = jours 368..427
fin=368  ->  d0=308,  303       >= 250  OK   test = jours 308..367
fin=308  ->  d0=248,  243       <  250  STOP
```

Quatre plis. Ce n'est pas un bug (`n_plis` est un maximum), mais la sortie ne le signale pas. **À mentionner
comme limite : quatre mesures, c'est peu pour parler de stabilité.**

## 10.4 — Le résultat

```
DÉTAIL PAR PLI (AUC)
pli   Contrôles seuls  Gradient Boosting  Logistique (tout)  Random Forest  Sentiment seul
1              0.4935             0.6425             0.6427         0.6528          0.6533
2              0.5128             0.6703             0.6490         0.6605          0.6552
3              0.4534             0.6703             0.6618         0.6744          0.6763
4              0.5317             0.6860             0.7035         0.6937          0.7002

SYNTHÈSE
                   plis  AUC_moy  AUC_std  AUC_min  AUC_max  plis_gagnants  MCC_moy  stabilite
Sentiment seul        4   0.6712   0.0219   0.6533   0.7002              4   0.2026      7.817
Random Forest         4   0.6703   0.0180   0.6528   0.6937              4   0.2415      9.461
Gradient Boosting     4   0.6673   0.0181   0.6425   0.6860              4   0.2413      9.243
Logistique (tout)     4   0.6642   0.0274   0.6427   0.7035              4   0.2132      5.993
Contrôles seuls       4   0.4979   0.0335   0.4534   0.5317              2   0.0248     −0.063
```

### Ce qui est excellent

**4 plis sur 4 au-dessus de 0,50** pour tous les modèles de sentiment. Aucun pli négatif. Le signal est
présent sur toute la période 2020–2022, à travers le krach COVID, la reprise, l'euphorie retail et le
resserrement monétaire.

**Les contrôles font 2 plis sur 4** — exactement ce qu'on attend d'un tirage à pile ou face.

### Le ratio de stabilité, et sa surinterprétation

```
stabilite  =  ( AUC_moyenne − 0,50 )  /  écart-type des AUC entre plis
```

Pour « Sentiment seul » : (0,6712 − 0,50) / 0,0219 = **7,82**.

Le notebook dit : « au-dessus de 1, le signal domine la variabilité ». C'est vrai comme indication
descriptive. Mais **il ne faut surtout pas lire ce 7,82 comme une statistique de test**, pour trois raisons :

1. **Les plis ne sont pas indépendants.** Le pli 4 s'entraîne sur 483 jours, le pli 3 sur 423 : ils
   partagent 88 % de leurs données d'entraînement. Les modèles sont donc quasi identiques et leurs erreurs
   corrélées. L'écart-type entre plis **sous-estime massivement** la vraie variabilité.
2. **Quatre points, ça ne fait pas un écart-type fiable.** L'incertitude sur un écart-type estimé à partir
   de n = 4 est de l'ordre de ±40 %.
3. **Le dénominateur mesure la mauvaise chose.** Il mesure la variabilité *entre périodes*, pas
   l'incertitude d'échantillonnage *à l'intérieur* d'une période (qui est de ±0,023 par pli de 60 jours,
   soit ±0,046 pour un intervalle à 95 %).

> **La bonne formulation pour le mémoire** : *« L'AUC hors échantillon est positive sur les quatre replis,
> avec une moyenne de 0,671 et une étendue de 0,653 à 0,700. La faible dispersion entre replis doit être
> interprétée avec prudence, les échantillons d'apprentissage se recouvrant à plus de 85 %. »*

### La tendance croissante — et le problème qu'elle cache

```
pli 1 : 0,653   ->   pli 2 : 0,655   ->   pli 3 : 0,676   ->   pli 4 : 0,700
```

L'AUC monte régulièrement. Deux explications possibles, et il faut les donner toutes les deux :

1. **Explication bénigne** : plus de données d'entraînement à chaque pli (303 → 483 jours), donc une
   meilleure estimation. C'est le comportement attendu d'une courbe d'apprentissage.
2. **Explication inquiétante** : les dernières périodes sont plus faciles à prédire. Or on a vu (§8.3 du
   notebook) que le régime « Resserrement Fed » donne l'AUC la plus élevée (0,7134). Ce serait alors un
   effet de régime, pas d'apprentissage.

**Et il y a une troisième chose, plus grave, dont on parle au chapitre 14.**

---

# Chapitre 11 — Les ablations et les tests de falsification

## 11.1 — La notion d'ablation

Une **ablation** consiste à retirer un ingrédient et à mesurer ce qu'on perd. Le terme vient de la
neurophysiologie : pour savoir à quoi sert une région du cerveau, on l'inactive et on observe ce qui cesse
de fonctionner.

En modélisation, c'est la manière la plus directe de répondre à « d'où vient réellement le résultat ? ».

| Ablation | Objection du jury |
|---|---|
| Sentiment retiré | « le signal vient-il du texte ou du marché ? » |
| Volume retiré | « n'est-ce pas juste l'intensité d'attention ? » |
| Fenêtre `pre` retirée | « vos messages de 9h ne sont-ils pas déjà dans le prix ? » |
| Sentiment inversé | contrôle de cohérence : la performance doit **chuter** |
| Sentiment permuté | contrôle négatif : l'AUC doit revenir à 0,50 |

## 11.2 — Le piège du test d'inversion, et pourquoi ce notebook a raison

C'est un point subtil que le notebook explique **très bien**, et que 95 % des travaux se trompent.

> Si l'on inverse le signe du sentiment **à la fois** dans l'entraînement et dans le test, l'AUC ne bouge
> **pas d'un iota**.

Pourquoi ? Parce que la régression apprend simplement le coefficient opposé :

```
avant :  z = +1,00 × sentiment      ->  classement C
après :  z = −1,00 × (−sentiment)   ->  classement C, identique
```

Le classement est rigoureusement le même, donc l'AUC aussi. **Le test ne mesure rien du tout.**

La bonne façon de faire :

```
1.  entraîner le modèle NORMALEMENT
2.  inverser le sentiment UNIQUEMENT dans le jeu de test
3.  si le modèle utilisait vraiment le sentiment dans le bon sens,
    l'AUC doit passer SOUS 0,50
```

D'où le paramètre `ou` dans la fonction :

```python
def auc_walkforward(feats, transformation=None, ou="test", proto=None):
    ...
    if transformation is not None:
        b = transformation(b)              # toujours le test
        if ou == "deux":
            a = transformation(a)          # le train aussi, pour le placebo
```

Et la distinction est correcte :

- **inversion → `ou="test"`** : on teste si le modèle a appris le bon **sens** ;
- **placebo → `ou="deux"`** : on veut détruire la relation **partout**, pour vérifier que le pipeline
  n'invente pas de signal à partir de rien.

> **C'est un des meilleurs passages du notebook**, et il mérite d'être cité tel quel en soutenance. Il
> montre que tu as compris la différence entre tester une **direction** et tester une **existence**.

## 11.3 — Les résultats

```
                       Variante  n_features applique_a  AUC_moy  AUC_std  delta_vs_complet
           Toutes les variables          23       test   0.6642   0.0237            0.0000
   SANS sentiment (marché seul)           9       test   0.4979   0.0290           -0.1663
                 Sentiment SEUL          14       test   0.6712   0.0190           +0.0070
        SANS volume de messages          20       test   0.6659   0.0225           +0.0017
Jeu CONSERVATEUR (coupé minuit)          13       test   0.5969   0.0165           -0.0673
    Sentiment INVERSÉ (falsif.)          23       test   0.3346   0.0125           -0.3296
    Sentiment PERMUTÉ (placebo)          23       deux   0.4942   0.0423           -0.1700
```

### Ligne par ligne

**Sans sentiment : 0,4979.** Exactement le hasard. Le marché seul ne prédit rien. Confirme le chapitre 6 par
une méthode glissante. ✓

**Sentiment seul : 0,6712, mieux que tout.** Les contrôles nuisent, comme au chapitre 6. ✓

**Sans volume : 0,6659, quasi inchangé.** Retirer `nlog` et `nabn` ne coûte que 0,002. **Le signal est dans
la direction du sentiment, pas dans l'intensité de l'attention.** C'est un résultat intéressant en soi : la
littérature sur l'attention (Da, Engelberg, Gao 2011) montre que le volume de recherches Google prédit les
rendements ; ici, ce n'est pas le canal. À dire.

**Sentiment inversé : 0,3346.** C'est le test le plus élégant du notebook.

```
0,3346  =  1  −  0,6654
```

Le modèle inversé est le miroir presque exact du modèle normal (0,6642). C'est mathématiquement ce qu'on
attend : inverser toutes les variables d'un modèle linéaire inverse exactement le classement, donc
`AUC_inversée = 1 − AUC_normale`. **La cohérence de ce nombre valide l'implémentation.** Et le fait qu'il
soit très en dessous de 0,50 prouve que le modèle utilise bien le sentiment dans le sens économiquement
attendu.

**Sentiment permuté : 0,4942.** Le placebo revient au hasard (0,25 écart-type). **Le pipeline n'invente
rien.** Si ce chiffre avait été à 0,58, il y aurait eu une fuite quelque part dans le code.

Note son écart-type élevé (0,0423, contre 0,019 pour les autres) : sans signal, la performance est instable
d'un pli à l'autre. C'est cohérent — et c'est un signe supplémentaire que le placebo fonctionne.

**Jeu conservateur : 0,5969.** Voilà **le chiffre le plus important de tout le notebook**.

```
0,6642  (toutes fenêtres)   →   0,5969  (coupé à minuit)      perte : −0,067
```

Le jeu conservateur retire tout ce qui est postérieur à minuit — donc `z_mu_pre`, `z_sd_pre`, et tout ce qui
en dérive. C'est-à-dire précisément la variable qui portait 56 % de l'importance (chapitre 9).

Et il reste **0,597**, soit **4,2 écarts-types au-dessus du hasard** avec 60 observations par pli.

> **Voilà comment il faut le lire, et c'est la conclusion du mémoire :**
>
> ```
> 0,597   part ANTICIPATRICE   — messages écrits avant minuit, plusieurs heures
>                                avant l'ouverture, aucun marché ouvert
> 0,067   part CONTEMPORAINE   — messages de la fenêtre minuit–9h30, qui recouvre
>                                le pré-marché où le prix se forme déjà
> ------
> 0,664   total mesuré
> ```
>
> **La part anticipatrice est réelle, significative, et défendable. La part contemporaine ne l'est pas.**

Et rappelle-toi le point du chapitre 15 du Cours 3 : le « jeu conservateur » n'est en réalité **pas
totalement** conservateur, parce que `z_dmu_night` et `z_mu_night_ma3` passent le filtre par leur nom tout en
dérivant de `mu_night_full`. Le vrai chiffre conservateur est donc **un peu inférieur** à 0,597. À corriger
avant de rédiger — c'est le point 1 du chapitre 15.

## 11.4 — Une ablation qui manque

Les cinq ablations sont bien choisies, mais il en manque une, et c'est la plus intéressante compte tenu du
chapitre 9 :

```
Ablation manquante :  RETIRER z_mu_pre SEULE (et rien d'autre)
```

Elle isolerait exactement l'effet de la fenêtre suspecte, sans retirer en même temps `z_sd_pre` et les
variables dérivées. Le code est au chapitre 15.

---

# Chapitre 12 — La calibration : probabilité juste = prime juste

## 12.1 — La distinction fondamentale

Deux qualités **totalement différentes** d'un modèle probabiliste :

| Qualité | Question | Métrique |
|---|---|---|
| **Discrimination** | classe-t-il les jours dans le bon ordre ? | AUC |
| **Calibration** | quand il annonce 70 %, ça monte-t-il 70 % du temps ? | Brier, courbe de fiabilité |

Un modèle peut être **parfaitement discriminant et complètement décalibré**.

### L'exemple

Un météorologue annonce chaque jour une probabilité de pluie. Sur les jours où il annonce 90 %, il pleut
60 % du temps. Sur les jours où il annonce 20 %, il pleut 10 % du temps.

- **Discrimination : parfaite.** Il ordonne correctement les jours pluvieux et les jours secs.
- **Calibration : mauvaise.** Ses chiffres sont systématiquement trop élevés.

Si tu utilises ses annonces pour décider de sortir le parapluie, tout va bien (tu compares 90 % et 20 %). Si
tu les utilises pour **tarifer une assurance annulation d'événement en plein air**, tu fais faillite : tu
factures une prime pour 90 % de risque alors que le risque réel est de 60 %.

## 12.2 — Pourquoi c'est LE chapitre d'un mémoire d'actuariat

Fais le lien explicitement. Il est direct :

```
ASSURANCE                         TRADING
prime pure = p × sinistre         taille de position = f(p)   [Kelly]
si p est faux -> prime fausse     si p est faux -> ruine
```

**La formule de Kelly** donne la fraction optimale du capital à engager :

```
              p × (1 + b)  −  1
      f*  =  --------------------
                      b
```

avec `p` la probabilité de gain et `b` le rapport gain/perte. Elle dépend de `p`, pas du classement. Un
modèle décalibré qui annonce 0,75 au lieu de 0,60 conduit à des positions **beaucoup trop grosses**. Et
Kelly est notoirement impitoyable : miser deux fois la fraction optimale donne une espérance de croissance
**nulle**, quelle que soit la qualité du signal.

**Le notebook 08 (backtest) dimensionne les positions. Il dépend donc directement de ce chapitre.**

## 12.3 — Comment on mesure la calibration

On découpe les prédictions en groupes de probabilité prédite, et dans chaque groupe on compare :

- la probabilité **annoncée** (moyenne du groupe) ;
- la fréquence **observée** (proportion réelle de hausses).

Un modèle parfaitement calibré se place sur la **diagonale**.

Le notebook utilise `strategy="quantile"` : des groupes de **taille égale**, plutôt que des intervalles de
largeur égale. C'est le bon choix — avec des intervalles fixes, les groupes extrêmes contiennent trois
observations et le graphique est illisible.

## 12.4 — La correction par régression isotonique

```python
CalibratedClassifierCV(FrozenEstimator(modele), method="isotonic").fit(X, y)
```

La **régression isotonique** ajuste la fonction **croissante** (monotone non décroissante) qui minimise
l'erreur quadratique entre probabilités prédites et réalité.

Pourquoi imposer la croissance ? Parce qu'on veut **corriger les probabilités sans changer le classement**.
Une transformation croissante préserve l'ordre, donc **l'AUC ne bouge pas d'un pouce**. Seul le Brier
s'améliore.

> C'est très élégant : on répare la calibration sans toucher à la discrimination. Deux problèmes séparés,
> deux traitements séparés.

Alternative : le **scaling de Platt**, qui ajuste une sigmoïde à deux paramètres. Plus rigide, mais plus
stable sur petits échantillons. Avec 520 observations, l'isotonique est acceptable, mais elle a tendance à
surajuster (elle peut créer autant de paliers que d'observations).

**Note technique** : le code gère les deux API de scikit-learn (`cv="prefit"` avant la version 1.6,
`FrozenEstimator` depuis) avec un `try/except ImportError`. Bon réflexe de reproductibilité.

## 12.5 — Le résultat

```
Brier AVANT calibration : 0.2223
Brier APRÈS calibration : 0.2098        (−5,6 %)
```

L'amélioration est réelle. Mais il y a **un défaut méthodologique important** :

> La calibration est **ajustée sur la validation** puis **évaluée sur la validation**. Le 0,2098 est donc un
> score **dans l'échantillon**, et il est optimiste.
>
> La régression isotonique est très flexible — elle peut créer beaucoup de paliers — donc le
> surajustement est réel. Il faudrait soit un troisième bloc dédié à la calibration, soit une validation
> croisée interne.
>
> **À corriger, ou au minimum à signaler dans le mémoire.** Voir le chapitre 15, point 5.

## 12.6 — La table de fiabilité par décile : le plus beau résultat du notebook

```
decile   n  p_predite  freq_observee  gap_moyen_pct
0       52     0.2790         0.3846        -0.7830
1       52     0.4240         0.5192        -0.3733
2       52     0.5048         0.4038        -0.1957
3       52     0.5561         0.6154        +0.0589
4       52     0.5981         0.4808        -0.1955
5       52     0.6287         0.5577        +0.0666
6       52     0.6584         0.5962        +0.3294
7       52     0.6819         0.8269        +0.5343
8       52     0.7109         0.8462        +0.7058
9       52     0.7592         0.8269        +0.8742
```

### Ce qu'il faut regarder — la colonne de droite

```
décile 0  :  gap moyen  −0,78 %
décile 9  :  gap moyen  +0,87 %
--------------------------------
écart     :        1,65 point de pourcentage
```

**C'est le résultat le plus important du notebook**, et voici pourquoi.

L'AUC est un nombre abstrait. Le MCC aussi. Un jury d'actuariat, une direction financière, un recruteur : ils
ne « sentent » pas une AUC de 0,67.

Mais **1,65 point de pourcentage d'écart de rendement d'ouverture entre le premier et le dernier décile de
probabilité prédite** — ça, tout le monde le comprend immédiatement. C'est de l'argent.

Et surtout : cette colonne **n'a jamais servi à l'entraînement**. Le modèle a été entraîné sur `y_gap`, une
variable **binaire** (monte / baisse). Il n'a jamais vu l'amplitude. Le fait que les déciles de probabilité
s'ordonnent selon le **rendement moyen** est une validation **externe** de la qualité du modèle.

### La progression est-elle monotone ?

```
−0,78  →  −0,37  →  −0,20  →  +0,06  →  −0,20  →  +0,07  →  +0,33  →  +0,53  →  +0,71  →  +0,87
                                          ^^^^^
                                    la seule rupture
```

**Neuf transitions, huit croissantes, une décroissante** (décile 3 → décile 4). Avec 52 observations par
décile, une inversion locale est parfaitement attendue : l'erreur-type d'une moyenne de gap sur 52 jours
est d'environ 0,2 point de pourcentage, donc l'écart de 0,25 point entre les déciles 3 et 4 est dans le
bruit.

Une façon rigoureuse de le dire : le **coefficient de corrélation de Spearman** entre le rang du décile et
le gap moyen vaut ici **0,933** (9 concordances sur 10 rangs), largement significatif.

### La calibration, elle, est franchement imparfaite

Compare les colonnes `p_predite` et `freq_observee` :

| Décile | Prédit | Observé | Écart |
|---|---|---|---|
| 0 | 0,279 | 0,385 | **+0,106** (sous-estime) |
| 1 | 0,424 | 0,519 | **+0,095** (sous-estime) |
| 4 | 0,598 | 0,481 | **−0,117** (surestime) |
| 7 | 0,682 | 0,827 | **+0,145** (sous-estime) |
| 8 | 0,711 | 0,846 | **+0,135** (sous-estime) |

Le modèle est **globalement trop timide** : il n'annonce jamais moins de 0,28 ni plus de 0,76, alors que les
fréquences réelles vont de 0,38 à 0,85. C'est le comportement classique d'un modèle régularisé — et c'est
exactement ce que la régression isotonique corrige.

> **La phrase de mémoire** : *« Le rendement d'ouverture moyen croît de manière quasi monotone à travers les
> déciles de probabilité prédite, de −0,78 % dans le premier décile à +0,87 % dans le dernier, soit un écart
> de 1,65 point de pourcentage. Cette relation constitue une validation externe du modèle, l'amplitude du
> rendement n'ayant jamais été utilisée lors de l'apprentissage, effectué sur une cible binaire. »*

---

# Chapitre 13 — La robustesse : ticker, LOTO, régime

## 13.1 — Test 1 : le modèle marche-t-il sur les cinq titres ?

```
Ticker   n    AUC    MCC  base
  AAPL 104 0.6432 0.1026 0.577
  AMZN 104 0.6450 0.1812 0.606
  META 104 0.6118 0.1042 0.548
  NVDA 104 0.7406 0.2310 0.625
  TSLA 104 0.6971 0.3417 0.673
```

**Cinq titres sur cinq au-dessus de 0,61.** Le signal n'est pas porté par une seule action.

C'est une vérification indispensable. Si TSLA avait fait 0,85 et les quatre autres 0,52, la moyenne de 0,67
aurait été une illusion d'agrégation — et TSLA est précisément le titre le plus discuté sur StockTwits, donc
le suspect naturel.

**L'ordre est intéressant** : NVDA (0,741) et TSLA (0,697) en tête, META (0,612) en queue. Deux lectures :

1. NVDA et TSLA sont les titres les plus « retail » de l'échantillon, ceux où la foule des petits porteurs
   pèse le plus. Le sentiment social devrait y être plus informatif. **Cohérent avec la théorie du
   *noise trader* de De Long, Shleifer, Summers et Waldmann (1990).**
2. META a connu, sur la période, des chocs d'information fondamentale (changement de nom, effondrement du
   titre en février 2022) que le sentiment social ne capture pas.

**Attention à la barre d'erreur** : avec n = 104 par titre, l'écart-type d'une AUC est d'environ ±0,055.
L'écart entre NVDA (0,741) et META (0,612) vaut 1,7 écart-type combiné — **il n'est pas significatif**. Ne
dis pas « le signal est plus fort sur NVDA » : dis « les cinq titres sont individuellement au-dessus du
hasard, sans différence statistiquement établie entre eux ».

## 13.2 — Test 2 : le leave-one-ticker-out — le test le plus exigeant

```python
for tk in tickers:
    a = données SANS le titre tk        # entraînement
    b = données DU titre tk             # test
```

On entraîne sur quatre titres et on teste sur **le cinquième, jamais vu**.

```
Ticker_exclu  n_test    AUC
        AAPL     481 0.7274
        AMZN     481 0.6678
        META     481 0.6164
        NVDA     481 0.6522
        TSLA     481 0.7157
AUC moyenne hors échantillon transversal : 0.6759
```

**Cinq sur cinq largement au-dessus de 0,50. Moyenne 0,676, aussi bonne que le walk-forward temporel.**

### Pourquoi ce test est si convaincant

Il exclut une famille entière d'explications alternatives. Le modèle ne peut pas avoir appris :

- « TSLA monte souvent » — le titre est absent de l'entraînement ;
- une particularité du corpus StockTwits propre à un titre ;
- un effet de niveau spécifique (déjà éliminé par le z-score intra-titre, mais ceci le reconfirme).

**Ce qu'il a appris est une relation générale entre sentiment normalisé et gap**, transférable à un actif
inconnu.

> **La phrase de soutenance** : *« Un protocole de validation croisée transversale par exclusion de titre
> (leave-one-ticker-out) produit une AUC moyenne de 0,676 sur des actifs absents de l'échantillon
> d'apprentissage, indiquant que la relation estimée n'est pas spécifique à un titre. »*

### La limite à mentionner honnêtement

Cinq titres, **tous de la technologie américaine à très grande capitalisation**, tous très commentés sur
StockTwits, sur une période de deux ans marquée par un afflux exceptionnel d'investisseurs particuliers.

Ce que le test montre : la relation se transfère **à l'intérieur de cet univers**. Ce qu'il ne montre pas :
qu'elle se transférerait à une valeur bancaire européenne, ou à une petite capitalisation peu commentée.
**Dis-le toi-même avant qu'on te le demande.**

Note aussi que ce test utilise `bloc in ["train", "valid"]` : il n'entame pas le bloc de test. Correct.

## 13.3 — Test 3 : par régime de marché

```
            Regime   n    AUC
   Euphorie retail 345 0.6426       (jan–juin 2021)
Plateau / rotation 640 0.6603       (juil–déc 2021)
  Resserrement Fed 215 0.7134       (jan–mars 2022)
```

**Trois régimes, trois AUC au-dessus de 0,64.** Le signal survit à des contextes de marché très différents.

Deux remarques importantes :

**(a) Deux régimes manquent.** Le krach COVID (jan–mars 2020) et la reprise (avr–déc 2020) n'apparaissent
pas, parce que le walk-forward n'a que quatre plis et que ses fenêtres de test commencent au jour 308,
c'est-à-dire environ en avril 2021. **Le tableau ne couvre pas 2020 du tout.** C'est une limite réelle : on
ne sait pas ce que fait le modèle pendant un krach. À dire.

**(b) Le meilleur régime est le resserrement Fed — qui est le bloc de test.** Et c'est le problème du
chapitre 14.

---

# Chapitre 14 — Le bloc de test : ce qui manque, et ce qui a fuité

C'est le troisième grand enseignement, et le plus délicat.

## 14.1 — Ce que dit le notebook, et il a raison

```
⚠️ À ne faire qu'une seule fois

Le bloc de test (décembre 2021 → mars 2022) n'a jamais été utilisé jusqu'ici. Le chiffre
obtenu ci-dessous est LE chiffre du mémoire.

Si le résultat déçoit, la tentation sera de revenir modifier le modèle puis de relancer
cette cellule. NE LE FAIS PAS.
```

L'avertissement est parfaitement juste, et bien écrit. **Le problème est qu'il est faux sur les faits.**

## 14.2 — Constat 1 : la cellule finale n'a jamais été exécutée

Dans le fichier que tu m'as envoyé, la cellule du §9 porte :

```
execution_count : null
outputs         : []
```

Toutes les autres cellules sont numérotées de 1 à 11. **La dernière n'a jamais tourné.**

### Ce que cela implique concrètement

1. **Il n'y a aucun résultat de test dans ton mémoire.** Tous les chiffres que tu as vus — 0,664, 0,671,
   0,676 — sont des chiffres de **validation** ou de **validation glissante**. Le chiffre hors échantillon
   final n'existe pas.
2. **L'intervalle de confiance par bootstrap n'a jamais été calculé.** C'est pourtant le nombre qui décide
   si tu peux affirmer quelque chose.
3. **Le fichier `PREDICTIONS_M1_TEST.csv` n'a jamais été écrit.** Or c'est l'entrée du notebook 08
   (backtest). Si le notebook 08 a tourné, il a lu **une version antérieure** de ce fichier, produite dans
   une session précédente, avec on ne sait quel modèle. **C'est à vérifier en priorité.**

### Ce qu'il faut faire

Exécuter la cellule. Une fois. Sans rien changer avant. Et écrire le résultat, quel qu'il soit.

## 14.3 — Constat 2 : le walk-forward a déjà consommé le bloc de test

Celui-ci est plus subtil, et plus important.

```python
d_wf  = df.dropna(subset=[CIBLE]).copy()      # <-- TOUT le DataFrame
plis  = plis_walk_forward(d_wf["Date"], n_plis=6, taille_test=60)
```

`d_wf` contient **tous les blocs**, y compris le test. La fonction découpe ensuite les plis **en partant de
la fin du calendrier**.

Refaisons le calcul avec tes chiffres réels :

```
Total :        548 jours de bourse
  train  377 jours  (1 885 lignes / 5)
  purge    5 jours  (   25 / 5)
  valid  104 jours  (  520 / 5)
  test    62 jours  (  310 / 5)
  ------------------
         548 jours   ✓

Le bloc TEST occupe donc les jours d'indice 486 à 547.

Les plis construits :
  pli 4 (le dernier) : test = jours 488 .. 547   ->  100 % DANS le bloc test
  pli 3              : test = jours 428 .. 487   ->  2 jours dans le bloc test
  pli 2              : test = jours 368 .. 427   ->  dans la validation
  pli 1              : test = jours 308 .. 367   ->  dans la validation
```

**Le quatrième pli du walk-forward est, à deux jours près, exactement le bloc de test.**

### Les conséquences

Le bloc de test a été utilisé :

- dans la **synthèse walk-forward** (§5) ;
- dans **toutes les ablations** (§6), donc dans le chiffre du jeu conservateur ;
- dans l'analyse **par régime** (§8.3) — le régime « Resserrement Fed » **est** le bloc de test.

Ce n'est pas une fuite au sens où le futur entrerait dans l'entraînement — chaque pli s'entraîne bien
uniquement sur son passé, avec purge. La méthode est propre **en tant que walk-forward**.

Mais cela **annule la promesse du §9** : le test n'est plus vierge. Le protocole annoncé (« ce bloc n'a
jamais été utilisé ») ne correspond plus à ce que fait le code.

### Et c'est justement le pli qui donne le meilleur score

```
pli 4 :  Logistique 0,7035  |  RF 0,6937  |  GB 0,6860  |  Sentiment seul 0,7002
```

Le pli le plus performant des quatre est celui qui recouvre le bloc de test. Et le régime « Resserrement
Fed » — le même — affiche la meilleure AUC par régime (0,7134). Ce n'est probablement pas grave, mais **tu
ne peux pas le savoir**, parce que tu as déjà regardé.

### Les deux options honnêtes

**Option A — la plus propre.** Restreindre le walk-forward à train + valid :

```python
d_wf = df[df["bloc"].isin(["train", "purge", "valid"])].dropna(subset=[CIBLE]).copy()
```

On perd le pli 4. Il reste 3 plis, ce qui est peu, mais le bloc de test redevient réellement vierge, et
le §9 retrouve tout son sens.

**Option B — la plus simple à assumer.** Garder le code tel quel, et **changer la formulation** du mémoire :

> *« La validation glissante couvre l'ensemble de la période, replis de test compris. L'évaluation finale
> reportée au §9 ne constitue donc pas une évaluation en aveugle stricte, mais une confirmation sur le
> dernier repli avec un modèle réestimé sur l'ensemble train + validation. »*

**Ce qu'il ne faut surtout pas faire**, c'est garder le code de l'option B et le discours de l'option A.
C'est exactement ce qu'un membre de jury attentif détectera en lisant ton annexe de code.

> **Mon conseil : l'option A.** Trois plis honnêtes valent mieux que quatre plis contestables, et le §9
> devient alors le résultat propre qu'il prétend être.

## 14.4 — Ce que fait la cellule du §9 quand elle tournera

```python
trva = d[d["bloc"].isin(["train", "valid"])]        # réentraînement sur TOUT le passé
m = clone(proto).fit(trva[feats], trva[CIBLE])      # hyperparamètres FIGÉS avant
p = m.predict_proba(te[feats])[:, 1]                # une seule prédiction sur le test
```

**Le réentraînement sur train + valid est correct** : une fois les hyperparamètres choisis, il n'y a plus de
raison de se priver des 520 lignes de validation. On passe de 1 885 à 2 405 lignes d'entraînement, soit
+28 %. L'estimation est meilleure.

**Le bootstrap est bien construit** :

```python
for _ in range(2000):
    i = rng.integers(0, len(y), len(y))     # tirage avec remise
    aucs.append(roc_auc_score(y[i], p[i]))
lo, hi = np.percentile(aucs, [2.5, 97.5])
```

C'est un bootstrap **par percentiles**, correct pour une AUC.

> **Une réserve technique à mentionner** : ce bootstrap tire des **lignes individuelles** au hasard. Or les
> 310 lignes du test sont 62 jours × 5 titres, et les cinq titres d'un même jour sont fortement corrélés
> (quand le marché ouvre en hausse, il ouvre en hausse pour tout le monde). Le nombre d'observations
> **effectivement indépendantes** est donc plus proche de 62 que de 310.
>
> Un bootstrap **par blocs de jours** (on tire des journées entières, avec leurs 5 titres) donnerait un
> intervalle **plus large** et plus honnête. C'est la même idée que le block bootstrap de Künsch (1989) vu
> au Cours 2.

### À quoi t'attendre

Avec 62 jours effectifs, l'écart-type d'une AUC est d'environ :

```
sigma  ≈  racine( 63 / (12 × 32 × 30) )  ≈  0,074
```

L'intervalle de confiance à 95 % fera donc environ **±0,145**. Si l'AUC test sort à 0,63, l'intervalle sera
approximativement `[0,49 ; 0,77]` — **et il contiendra 0,50**.

**Prépare-toi à ce résultat, et prépare la bonne phrase :**

> *« Sur le bloc de test (62 jours, 310 observations), l'AUC atteint 0,6x, avec un intervalle de confiance
> bootstrap à 95 % de [0,4y ; 0,7z]. Compte tenu de la corrélation transversale entre titres, le nombre
> d'observations effectivement indépendantes est de l'ordre de 62, ce qui limite la précision de
> l'estimation. Le résultat est donc cohérent avec les 0,671 obtenus en validation glissante sur un
> échantillon quatre fois plus large, mais ne permet pas à lui seul de rejeter l'hypothèse nulle. La
> conclusion du mémoire s'appuie sur l'ensemble du protocole — validation glissante, ablations,
> falsification, généralisation transversale — et non sur ce seul chiffre. »*

**Cette phrase est meilleure que n'importe quel chiffre.** Elle montre que tu comprends la puissance
statistique, ce qui est rare et immédiatement valorisé.

---

# Chapitre 15 — Six points à corriger

Voici la liste, par ordre d'importance, avec le code.

## Point 1 — Exécuter le §9 (critique)

Rien à modifier. Ouvre le notebook, exécute la dernière cellule, **une fois**, et note le résultat.

Vérifie ensuite la date de `PREDICTIONS_M1_TEST.csv` : si elle est antérieure, le notebook 08 a travaillé sur
un fichier périmé, et il faut le relancer.

## Point 2 — Décider du statut du walk-forward (critique)

```python
# Option A — le bloc de test redevient vierge
d_wf = (df[df["bloc"].isin(["train", "purge", "valid"])]
          .dropna(subset=[CIBLE]).copy())
plis = plis_walk_forward(d_wf["Date"], n_plis=6, taille_test=60, min_train=200)
print(f"{len(plis)} plis construits, dernier jour utilisé : "
      f"{pd.Timestamp(plis[-1][1][-1]).date()}")
print(f"Premier jour du bloc test : {te['Date'].min().date()}")
assert pd.Timestamp(plis[-1][1][-1]) < te["Date"].min(), "Le walk-forward touche le test !"
```

L'`assert` final est la bonne pratique : il rend l'erreur **impossible à refaire**.

## Point 3 — Retirer les redondances exactes des contrôles

```python
# ret_cc = gap + ret_oc (identité comptable) -> on en retire une
FEAT_CTRL_PROPRE = [c for c in FEAT_CTRL if c != "ret_cc_lag1"]

m = pipeline_logit(1.0).fit(tr[FEAT_CTRL_PROPRE], tr[CIBLE])
auc = roc_auc_score(va[CIBLE], m.predict_proba(va[FEAT_CTRL_PROPRE])[:, 1])
print(f"L-ctrl SANS ret_cc_lag1 : AUC = {auc:.4f}   (avec : 0.4822)")

# Et pour le sentiment : mu = pos − neg, on garde mu
FEAT_SENT_PROPRE = [c for c in FEAT_SENT
                    if not c.startswith(("z_pos", "z_neg"))]
```

Puis recalculer les VIF. S'ils passent tous sous 10, **les coefficients redeviennent interprétables**, et tu
peux enfin écrire de vraies phrases sur les odds ratios.

## Point 4 — Ajouter l'ablation de `z_mu_pre` seule

```python
FEAT_SANS_PRE = [f for f in FEATURES if f != "z_mu_pre"]
m, s = auc_walkforward(FEAT_SANS_PRE)
print(f"SANS z_mu_pre seule : AUC = {m:.4f} ± {s:.4f}   (complet : 0.6642)")
```

C'est la mesure la plus directe de la composante non-actionnable. À mettre dans le mémoire à côté du jeu
conservateur.

## Point 5 — Évaluer la calibration hors échantillon

```python
from sklearn.model_selection import train_test_split
va_cal, va_eval = train_test_split(va, test_size=0.5, shuffle=False)   # chronologique

gb_cal = calibrer_modele_entraine(gb, va_cal[FEATURES], va_cal[CIBLE])
b_avant = brier_score_loss(va_eval[CIBLE], gb.predict_proba(va_eval[FEATURES])[:, 1])
b_apres = brier_score_loss(va_eval[CIBLE], gb_cal.predict_proba(va_eval[FEATURES])[:, 1])
print(f"Brier hors échantillon — avant {b_avant:.4f} | après {b_apres:.4f}")
```

`shuffle=False` est essentiel : le découpage doit rester chronologique.

## Point 6 — Régler le seuil de décision sur la validation

```python
seuils = np.linspace(0.35, 0.75, 41)
mccs = [matthews_corrcoef(va[CIBLE], (p_va >= s).astype(int)) for s in seuils]
s_opt = seuils[int(np.argmax(mccs))]
print(f"Seuil optimal (MCC) : {s_opt:.3f}  ->  MCC = {max(mccs):.4f}   (à 0,50 : {mccs[15]:.4f})")
```

À faire **sur la validation uniquement**, puis appliquer tel quel au test.

## Bonus — le bootstrap par blocs pour le §9

```python
jours = te["Date"].unique()
rng, aucs = np.random.default_rng(0), []
for _ in range(2000):
    j = rng.choice(jours, size=len(jours), replace=True)     # on tire des JOURS
    idx = np.concatenate([np.where(te["Date"].values == d)[0] for d in j])
    if len(np.unique(y[idx])) > 1:
        aucs.append(roc_auc_score(y[idx], p[idx]))
print(f"IC 95 % par blocs de jours : [{np.percentile(aucs,2.5):.4f} ; "
      f"{np.percentile(aucs,97.5):.4f}]")
```

---

# Chapitre 16 — Récapitulatif

## 16.1 — Les quinze idées à retenir

1. **Une exactitude sans son taux de base ne veut rien dire.** 61 % contre 59,5 %, c'est +1,5 point.
2. **L'AUC est la probabilité de classer un jour de hausse au-dessus d'un jour de baisse.** Elle est
   invariante au seuil et au taux de base.
3. **La barre d'erreur d'une AUC est d'environ ±0,023 sur 520 observations**, ±0,074 sur 62 jours effectifs.
   Toujours la calculer avant de commenter un écart.
4. **Le Brier de référence vaut p(1−p).** Ici 0,2388. Tout score supérieur est pire que de ne rien faire.
5. **Le MCC utilise les quatre cases de la matrice de confusion**, contrairement au F1. C'est le bon choix
   en finance, où prédire une baisse vaut autant que prédire une hausse.
6. **Une référence sans apprentissage (R4) est la vraie barre à franchir.** Ici 0,594 : la modélisation
   n'apporte que +0,070.
7. **Les contrôles de marché seuls donnent 0,498.** L'efficience faible est vérifiée — c'est un résultat.
8. **Ajouter des variables inutiles dégrade le modèle** (0,6642 → 0,6561), par variance d'estimation,
   régularisation globale et colinéarité.
9. **La multicolinéarité ne casse pas la prédiction, elle casse l'interprétation.** VIF jusqu'à 1 516 :
   les coefficients de ce modèle sont ininterprétables.
10. **L'identité `ret_cc ≈ gap + ret_oc` rend trois contrôles quasi dépendants.** C'est une erreur de
    spécification, pas une donnée de la nature.
11. **L'importance par permutation contredit les coefficients** : `z_mu_pre` domine (0,087), pas
    `z_mu_night_full` (0,002). C'est la permutation qui a raison.
12. **56 % du signal vient de la fenêtre minuit–9h30, qui recouvre le pré-marché.** Le jeu conservateur
    (0,597) est le chiffre défendable, pas 0,664.
13. **Le test d'inversion doit porter sur le test seul**, sinon il ne mesure rien. Résultat : 0,335 ≈
    1 − 0,665. Cohérence parfaite.
14. **Le leave-one-ticker-out à 0,676 est l'argument le plus fort** contre l'accusation de surajustement.
15. **Le rendement moyen croît de −0,78 % à +0,87 % à travers les déciles**, alors que le modèle n'a jamais
    vu l'amplitude. C'est le résultat le plus parlant du mémoire.

## 16.2 — Le notebook 06 en une page

```
ENTRÉE : 2 740 lignes, 23 features (14 sentiment + 9 contrôles)
         train 1 885 | purge 25 | valid 520 | test 310
         taux de gaps positifs : 0,595 / 0,606 / 0,510

RÉFÉRENCES (validation, n=520, sigma_AUC ≈ 0,023)
  R1 toujours hausse ........ AUC 0,500   Acc 0,606 = taux de base
  R2 hasard ................. AUC 0,494
  R3 momentum J−1 ........... AUC 0,505   -> le momentum ne prédit rien
  R4 sentiment brut ......... AUC 0,594   -> LA barre à franchir

MODÈLES (validation)
  Gradient Boosting ......... AUC 0,674   MCC 0,191   Brier 0,222
  Logistique sentiment ...... AUC 0,664   MCC 0,160   Brier 0,223
  Random Forest ............. AUC 0,663   MCC 0,199   Brier 0,232
  Logistique tout ........... AUC 0,656   MCC 0,173   Brier 0,226
  Logistique contrôles ...... AUC 0,482   -> le marché ne prédit rien
  -> les 4 modèles appris sont statistiquement indiscernables

DIAGNOSTIC
  VIF max 1 516 (ret_cc_lag1) -> coefficients ininterprétables
  Importance permutation : z_mu_pre 0,087 (56 %) >> tout le reste
  Part sentiment / marché : 0,156 / 0,026  (ratio 6,0)

WALK-FORWARD (4 plis de 60 jours)
  Sentiment seul 0,671 [0,653 ; 0,700]   4/4 plis gagnants
  Contrôles      0,498                   2/4 plis

ABLATIONS
  sans sentiment ............ 0,498   -> le texte est nécessaire
  sans volume ............... 0,666   -> la direction compte, pas l'intensité
  conservateur (< minuit) ... 0,597   -> LA PART ANTICIPATRICE RÉELLE
  inversé (test seul) ....... 0,335 = 1 − 0,665  -> cohérence parfaite
  placebo permuté ........... 0,494   -> aucune fuite dans le pipeline

ROBUSTESSE
  par ticker  : 5/5 entre 0,612 et 0,741
  LOTO        : 5/5, moyenne 0,676 sur titres jamais vus
  par régime  : 3/3 entre 0,643 et 0,713 (2020 non couvert)

CALIBRATION
  Brier 0,2223 -> 0,2098 (isotonique, mais ajustée et évaluée sur le même bloc)
  Déciles : gap moyen de −0,78 % à +0,87 %, Spearman 0,93

⚠ MANQUE : le §9 n'a jamais été exécuté. Aucun résultat de test n'existe.
⚠ PROBLÈME : le pli 4 du walk-forward recouvre le bloc de test à 97 %.
```

## 16.3 — Les six phrases pour la soutenance

1. « L'exactitude n'est jamais reportée seule : elle est systématiquement accompagnée du taux de base de la
   période. Sur la validation, une règle constante prédisant la hausse atteint 60,6 % d'exactitude pour une
   AUC de 0,500 et un MCC nul — ce qui illustre pourquoi la métrique principale retenue est l'AUC. »

2. « Une référence sans apprentissage, consistant à seuiller directement le z-score du sentiment nocturne,
   atteint déjà une AUC de 0,594. La modélisation multivariée porte cette valeur à 0,664 : l'apport propre
   de l'apprentissage est donc de sept centièmes d'AUC, et non de seize. »

3. « Les facteurs d'inflation de la variance atteignent 1 516, du fait de l'identité comptable liant le gap,
   le rendement de séance et le rendement de clôture à clôture. Les coefficients ne sont donc pas
   interprétables individuellement, et l'analyse de contribution repose sur l'importance par permutation,
   qui en est exempte. »

4. « L'importance par permutation attribue 56 % du pouvoir prédictif à la seule fenêtre minuit–9h30, qui
   recouvre la séance de pré-ouverture. La spécification conservatrice, restreinte aux messages antérieurs à
   minuit, conserve une AUC de 0,597 : c'est cette valeur qui mesure la part réellement anticipatrice du
   sentiment. »

5. « Le test d'inversion est appliqué exclusivement à l'échantillon d'évaluation, une inversion symétrique
   laissant l'AUC inchangée par simple retournement des coefficients. L'AUC obtenue, 0,335, est le
   complément à un de l'AUC nominale de 0,665, ce qui confirme que le modèle exploite le sentiment dans le
   sens économiquement attendu. »

6. « Une validation croisée transversale par exclusion de titre produit une AUC moyenne de 0,676 sur des
   actifs absents de l'échantillon d'apprentissage. La relation estimée n'est donc pas spécifique à un
   titre, mais sa généralisation reste circonscrite à un univers de grandes capitalisations technologiques
   américaines fortement commentées. »

---

## Références

- Fawcett, T. (2006). *An introduction to ROC analysis*. Pattern Recognition Letters 27. — l'AUC
- Matthews, B.W. (1975). *Comparison of the predicted and observed secondary structure of T4 phage lysozyme*.
  Biochimica et Biophysica Acta. — le MCC
- Brier, G.W. (1950). *Verification of forecasts expressed in terms of probability*. Monthly Weather Review.
- Hosmer, D. & Lemeshow, S. (2000). *Applied Logistic Regression*. Wiley. — logistique, odds ratios, VIF
- Hoerl, A. & Kennard, R. (1970). *Ridge Regression*. Technometrics. — la pénalité L2
- Breiman, L. (2001). *Random Forests*. Machine Learning 45. — la forêt aléatoire
- Friedman, J. (2001). *Greedy Function Approximation: A Gradient Boosting Machine*. Annals of Statistics.
- Strobl, C. et al. (2007). *Bias in random forest variable importance measures*. BMC Bioinformatics. —
  pourquoi la permutation plutôt que Gini
- Zadrozny, B. & Elkan, C. (2002). *Transforming classifier scores into accurate multiclass probability
  estimates*. KDD. — la régression isotonique
- Niculescu-Mizil, A. & Caruana, R. (2005). *Predicting good probabilities with supervised learning*. ICML.
- Kelly, J.L. (1956). *A New Interpretation of Information Rate*. Bell System Technical Journal.
- Fama, E. (1970). *Efficient Capital Markets*. Journal of Finance. — l'efficience en forme faible
- Jegadeesh, N. & Titman, S. (1993). *Returns to Buying Winners and Selling Losers*. Journal of Finance.
- De Long, J.B. et al. (1990). *Noise Trader Risk in Financial Markets*. Journal of Political Economy.
- Da, Z., Engelberg, J. & Gao, P. (2011). *In Search of Attention*. Journal of Finance. — l'attention
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. — purge, embargo, walk-forward
- Künsch, H. (1989). *The Jackknife and the Bootstrap for General Stationary Observations*. Annals of
  Statistics. — le bootstrap par blocs

---

*Prochain cours : notebook 07 — les modèles M2 et M3, la prévision de l'amplitude et de la volatilité,
la perte QLIKE et le test de couverture de Kupiec pour la VaR.*
