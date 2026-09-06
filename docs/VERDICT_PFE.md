# Le verdict des sept notebooks

**PFE Finance actuarielle — analyse des sorties des notebooks 03 à 09**

Période : janvier 2020 → mars 2022 · Univers : AAPL, AMZN, META, NVDA, TSLA
Corpus : 3 711 333 messages StockTwits scorés par FinBERT · Panel : 2 740 × 81

| Chiffre | Valeur |
|---|---|
| Messages traités | 3 711 333 (0 perdu) |
| AUC hors échantillon (gap) | **0,671** |
| Écart Q5 − Q1 sur le gap | **+34,8 points** |
| Sharpe du backtest | 6,04 — **non valide, voir §5** |

---

## §0 — Le verdict en trois lignes

### 1. Le résultat scientifique tient

Le sentiment nocturne prédit le **signe du gap d'ouverture** : AUC de **0,671** hors échantillon, positive
sur les 4 plis de validation glissante, sur les 5 titres pris séparément, et sur 4 régimes de marché sur 5.
Les variables de marché seules donnent 0,498 — c'est-à-dire rien. L'apport du texte est donc de
**+0,17 point d'AUC**, ce qui est considérable.

### 2. Le résultat négatif tient aussi

Le même sentiment ne prédit **pas du tout** le rendement de séance : AUC entre 0,487 et 0,522 selon le
modèle, ρ = −0,010, écart entre quintiles extrêmes de −2,2 points (non significatif, z = −0,72). Et
l'analyse de puissance montre que l'étude aurait détecté toute corrélation supérieure à 0,052. Ce n'est
donc pas « on n'a pas trouvé », c'est **« il n'y a rien au-delà de 0,05 »**.

### 3. Mais le backtest ne mesure pas ce qu'il prétend mesurer

Sharpe de **6,04**, rendement annuel de **+94 %**, perte maximale de **−2,8 %** sur un an. Aucune stratégie
réelle sur cinq actions technologiques n'a jamais ressemblé à cela.

Ce n'est pas une erreur de calcul — l'arithmétique est cohérente avec l'AUC. C'est un **problème de
calendrier** : pour capturer un gap il faut acheter à la clôture de la veille, or les tweets qui alimentent
la prédiction n'existent pas encore à ce moment-là. Détail complet au §5.

**La bonne nouvelle** : cette troisième ligne ne détruit rien. Elle transforme la conclusion « on gagne de
l'argent » — que personne ne croirait — en « le signal est réel mais inexploitable », qui est *exactement*
ce que prédit la théorie de l'efficience des marchés. C'est un meilleur mémoire, pas un moins bon.

---

## §1 — Ce qui est solide : la chaîne de données

*Notebook 03 — sept contrôles automatiques, tous passés.*

| Contrôle | Résultat | Ce que ça prouve |
|---|---|---|
| Messages traités | 3 711 333 / 3 711 333 | aucune perte au nettoyage |
| Panel produit | 2 740 × 81 | 5 titres × 548 jours, équilibré |
| (1+gap)(1+ret_oc) = 1+ret_cc | 2,2 × 10⁻¹⁶ | décomposition exacte |
| mu = pos − neg | 1,1 × 10⁻¹⁶ | identité FinBERT vérifiée |
| n_night_full = overnight + pre | 0,0 | fenêtres correctement construites |
| Recoupement avec le script de collecte | < 8 × 10⁻¹⁶ | les deux chaînes concordent |
| Messages de séance en fenêtre nocturne | 0 | aucune contamination |

### Trois faits établis par les données, pas supposés

**Le fuseau horaire.** Le pic d'activité tombe à **10 h**, et 59,3 % des messages sont postés entre 9 h et
16 h (contre 44,0 % entre 13 h et 21 h). Les heures sont donc déjà en **heure de New York** — aucune
conversion nécessaire. Le contrôle indépendant du samedi matin (13,1 % de messages avant 6 h) confirme.
C'est une figure d'annexe : elle coupe court à « comment savez-vous que vos fenêtres sont alignées ? ».

**La fenêtre du lundi absorbe le week-end.** En moyenne **629** messages nocturnes le lundi contre **348**
les autres jours — un rapport de 1,81×. C'est la preuve que `overnight` part bien de la clôture du *jour de
bourse* précédent et non du jour calendaire.

**Le corpus est enfin dense.** Médiane de **1 138** messages par nuit pour TSLA, 571 pour AAPL, 96 pour
NVDA. Seulement **4 nuits sur 2 740** sans aucun message. À comparer à la médiane de 2 messages/jour du
corpus 2023-2026 qui avait fait échouer la première tentative : le bruit d'échantillonnage est divisé par
un facteur ~15.

> **La limite à annoncer soi-même : FinBERT.** Il place en moyenne **80,7 %** de sa masse de probabilité
> sur « neutre », et classe **75,8 % des messages** comme neutres à plus de 90 %. Il ne voit aucun contenu
> financier dans trois messages sur quatre. Ce n'est pas un bug : FinBERT a été entraîné sur de la presse
> financière et ne comprend pas le jargon de forum. Mais cela veut dire que le signal repose en réalité sur
> **le quart des messages** que FinBERT sait lire.

---

## §2 — M1 : le gap, le résultat principal

*Notebooks 04 et 06.*

### L'analyse exploratoire — quintiles intra-ticker

| Quintile de sentiment nocturne | Q1 | Q2 | Q3 | Q4 | Q5 | écart |
|---|---|---|---|---|---|---|
| **% de jours à gap positif** | 39,3 | 53,9 | 63,1 | 63,9 | 74,1 | **+34,8** |
| **% de jours à séance positive** | 52,8 | 48,4 | 48,2 | 52,7 | 50,6 | −2,2 |
| gap moyen (%) | −0,72 | −0,02 | +0,45 | +0,45 | +0,61 | |

Ces deux premières lignes, côte à côte, **sont** le mémoire. Même variable explicative, mêmes jours, deux
cibles : l'une s'étale sur 35 points de pourcentage, l'autre oscille autour de 50 % sans direction.

### Les cinq titres vont dans le même sens

| Titre | Q1 → Q5 (% gap positif) | écart | ρ Spearman | ρ Pearson (IC 95 %) |
|---|---|---|---|---|
| AAPL | 31,8 → 72,7 | +40,9 | +0,900 | 0,349 [0,255 ; 0,414] |
| TSLA | 38,5 → 82,6 | +44,1 | +1,000 | 0,292 [0,187 ; 0,369] |
| NVDA | 44,5 → 77,3 | +32,8 | +1,000 | 0,177 [0,098 ; 0,238] |
| AMZN | 40,0 → 72,7 | +32,7 | +0,900 | 0,243 [0,160 ; 0,332] |
| META | 41,8 → 65,5 | +23,7 | +0,821 | 0,209 [0,146 ; 0,255] |

**5 titres sur 5** significatifs pour le gap (aucun intervalle ne contient zéro), contre **1 sur 5** pour la
séance — et celui-là, AAPL, est *négatif* (−0,082), signe d'une légère réversion après l'ouverture, pas
d'un signal.

### Le test qui écarte la fuite d'information

| Décalage du sentiment | −3 | −2 | −1 | **0** | +1 | +2 | +3 | +5 |
|---|---|---|---|---|---|---|---|---|
| ρ avec le gap du jour J | 0,028 | 0,030 | 0,048 | **0,157** | −0,010 | −0,007 | −0,023 | −0,012 |

Pic net au lag 0, presque rien avant (max 0,048 sur les lags négatifs), rien après. Les trois conditions
d'un signal propre sont réunies : il y a bien un effet, il est **orienté dans le bon sens du temps**, et
l'information est incorporée immédiatement — la signature de l'efficience semi-forte.

### La modélisation (validation glissante, 4 plis)

| Modèle | AUC moy. | écart-type | plis gagnants | lecture |
|---|---|---|---|---|
| Sentiment seul | **0,671** | 0,022 | 4 / 4 | le meilleur |
| Random Forest | 0,670 | 0,018 | 4 / 4 | équivalent |
| Gradient Boosting | 0,667 | 0,018 | 4 / 4 | équivalent |
| Logistique (tout) | 0,664 | 0,027 | 4 / 4 | équivalent |
| **Contrôles de marché seuls** | **0,498** | 0,034 | 2 / 4 | **rien du tout** |

**Deux choses importantes.** D'abord, les modèles complexes n'apportent rien : la régression logistique sur
le sentiment seul fait aussi bien qu'un Random Forest. *Il faut le dire* — un résultat simple et robuste
vaut mieux qu'un résultat complexe et fragile.

Ensuite, la ligne « contrôles seuls » à 0,498 répond définitivement à l'objection *« vous avez juste
redécouvert le momentum »*. Le momentum, la volatilité et le volume ne prédisent **rien**. Tout vient du
texte.

### Les tests de falsification

| Variante | AUC | attendu | verdict |
|---|---|---|---|
| Toutes les variables | 0,664 | référence | — |
| Sans sentiment | 0,498 | doit chuter | OK |
| Sentiment **inversé** | 0,335 | doit passer sous 0,50 | OK |
| Sentiment **permuté** (placebo) | 0,494 | doit revenir à 0,50 | OK |
| Jeu conservateur (coupé à minuit) | 0,597 | doit rester > 0,50 | OK |
| Leave-one-ticker-out | 0,676 | doit rester > 0,50 | OK |

Le **leave-one-ticker-out** est le plus fort : le modèle entraîné sans jamais voir AAPL obtient 0,727 sur
AAPL. Le signal n'est pas propre à une action, il se transfère à un titre inconnu. C'est l'argument le plus
solide contre l'accusation de surajustement.

> **Une nuance à retenir pour le §5.** Le passage au jeu conservateur (fenêtre coupée à minuit) fait tomber
> l'AUC de 0,664 à **0,597**. Et l'importance par permutation le confirme : la variable de loin la plus
> utile est `z_mu_pre` — les messages postés entre **minuit et 9h30**. Or c'est justement pendant cette
> fenêtre que se déroule la séance de **pré-marché** (4h00 → 9h30).

---

## §3 — M2 : la séance, le résultat négatif bien démontré

*Notebook 07, partie A.*

| Cible | Sentiment seul | Tout | Marché seul |
|---|---|---|---|
| **Séance** (Open → Close) | 0,493 / 0,517 | 0,519 / 0,488 | 0,522 / 0,487 |
| **Gap** (contrôle positif) | **0,671 / 0,664** | **0,664 / 0,672** | 0,498 / 0,505 |

*AUC en validation glissante — logistique / boosting.*

**Le contrôle positif est ce qui rend ce résultat publiable.** Même pipeline, mêmes variables, mêmes plis :
seule la cible change. Le gap sort à 0,67, la séance à 0,50. L'absence de signal sur la séance est donc une
propriété **du marché**, pas une défaillance de la méthode.

### L'analyse de puissance : la phrase qui fait la différence

| Cible | ρ observé | n effectif | ρ détectable à 80 % | conclusion |
|---|---|---|---|---|
| gap | +0,157 | 2 869 | 0,052 | signal détecté |
| ret_oc | −0,010 | 3 123 | 0,050 | sous le seuil |
| ret_cc | +0,093 | 2 988 | 0,051 | signal détecté |

> « Avec 3 123 observations effectives, l'étude dispose d'une puissance de 80 % pour détecter une
> corrélation de 0,050 entre sentiment nocturne et rendement de séance. La corrélation observée est de
> −0,010. Nous pouvons donc **exclure** l'existence d'un effet d'ampleur supérieure à 0,05, et non
> simplement constater notre incapacité à le mesurer. »

Sept variantes ont été testées (jours extrêmes seulement, forte attention, intensité non signée…) : toutes
restent entre 0,49 et 0,56. La conclusion d'absence est robuste — *on n'a pas mal cherché, il n'y a rien*.
Et cela porte un nom : **l'efficience semi-forte** au sens de Fama (1970).

---

## §4 — M3 : le risque, le résultat le plus utile

*Notebook 07, partie B. C'est le pont avec l'actuariat.*

| Modèle (cible : log de l'amplitude intraday) | R² in-sample | R² hors échantillon | QLIKE |
|---|---|---|---|
| Naïf — amplitude de la veille | — | 0,242 | 0,708 |
| Effets fixes ticker seuls | 0,240 | — | — |
| **Volatilité passée** (référence) | 0,444 | 0,495 | 0,438 |
| **+ attention sociale** | **0,485** | **0,527** | **0,392** |

L'apport net du texte est de **+0,032 point de R² hors échantillon** au-delà d'un modèle de volatilité déjà
très bon, avec un test de Fisher écrasant (F = 38,4 ; p = 5 × 10⁻³⁸). Le QLIKE — la fonction de perte de
référence pour la volatilité, qui pénalise la *sous-estimation* du risque — s'améliore de 0,438 à 0,392.

### La Value-at-Risk conditionnelle : le résultat d'actuariat

| Modèle de VaR 95 % | Dépassements | Taux observé | Cible | Kupiec (p) | Verdict |
|---|---|---|---|---|---|
| Inconditionnelle (quantile historique) | 55 / 896 | 6,14 % | 5 % | 0,131 | risque sous-estimé |
| **Conditionnelle (pilotée par l'attention)** | 45 / 896 | **5,02 %** | 5 % | **0,976** | couverture exacte |

La VaR conditionnelle atteint une couverture **quasi parfaite** (5,02 % contre 5 % visés, p de
Kupiec = 0,976) là où la VaR historique classique sous-estime le risque (6,14 % de dépassements). Et elle le
fait avec une VaR moyenne équivalente (−3,83 % contre −3,81 %) : **même capital immobilisé, meilleure
protection**.

> **C'est ce résultat qu'il faut mettre en avant devant un jury d'actuariat.** Prédire la *direction* est
> difficile et non rentable. Prédire le *risque* fonctionne, s'améliore mesurablement grâce au texte, et se
> traduit directement en un outil réglementaire validé par un test de couverture standard (Bâle,
> Solvabilité II).

---

## §5 — Le backtest : pourquoi le Sharpe de 6 n'est pas réel

*Notebook 08. La section la plus importante de ce document.*

| Stratégie (coût 10 bp) | Rendement annuel | Sharpe | Drawdown max |
|---|---|---|---|
| **Modèle — proportionnel** | +94,1 % | 6,04 | −2,8 % |
| Long systématique du gap | −13,4 % | −0,76 | −17,3 % |
| Buy & hold (5 actions) | +21,7 % | 0,75 | −26,1 % |
| Positions aléatoires | −9,8 % | −0,74 | −14,5 % |

Un Sharpe de 6 avec une perte maximale de 2,8 % sur un an — pendant une période qui contient le
resserrement de la Fed et une correction de 20 % sur le Nasdaq. **Cela n'existe pas.** Les meilleurs fonds
quantitatifs du monde tournent autour de 2.

### Ce n'est pas une erreur de calcul

Avec un gap moyen de 1,20 % en valeur absolue, ce rendement suppose un taux de réussite directionnelle de
**65,6 %** — ce qui est parfaitement cohérent avec une AUC de 0,663 et un taux de base de 55 %. Le calcul du
P&L est juste. **C'est l'hypothèse de négociabilité qui est fausse.**

### Le problème, en une image

```
   16h00 (J−1)                                          09h30 (J)
        │                                                    │
        │◄──── les messages de la nuit arrivent ici ────────►│
        │◄──────────── le gap se forme ici ─────────────────►│
        │                                                    │
        ●                                                    ●
  Il faut acheter ICI                            …mais on ne sait qu'ICI
  (dernier prix négociable)                  (quand tous les messages sont là)

        └───────── 17 h 30 d'information venue du futur ─────┘
```

Le gap est le mouvement entre la clôture de la veille et l'ouverture. Pour l'encaisser, il faut détenir le
titre **pendant toute la nuit** — donc acheter à 16h00 le jour J−1. À cet instant, aucun des messages de la
fenêtre nocturne n'a encore été écrit.

Le problème est même plus profond que le simple calendrier. La fenêtre `pre` (minuit → 9h30) est la variable
la plus importante du modèle, et elle recouvre la **séance de pré-marché** (4h00 → 9h30), pendant laquelle le
prix d'ouverture est littéralement en train d'être fabriqué. Un tweet de 8h45 qui dit « AAPL +3 % en
pré-marché » ne prédit rien : il *décrit* le gap.

### La preuve est déjà dans le notebook

| Test de robustesse (notebook 08) | Rendement | Sharpe | Drawdown |
|---|---|---|---|
| Référence | +94,1 % | 6,04 | −2,8 % |
| **Signal retardé d'un jour** | **−7,7 %** | **−0,53** | −15,9 % |
| Signal inversé | −144,5 % | −9,27 | −75,0 % |
| Sans le meilleur mois | +78,0 % | 6,29 | −2,8 % |

La ligne « signal retardé d'un jour » avait été écrite comme un simple test de détection de fuite. En
réalité, **c'est la seule version économiquement valide de la stratégie** : elle utilise le sentiment de la
nuit précédente pour se positionner à la clôture, ce qui est faisable. Et elle donne un Sharpe de **−0,53**.

> **La conclusion économique du mémoire.** Le signal existe et il est fort. Mais il devient observable
> **exactement au moment où il cesse d'être négociable**. La version implémentable perd de l'argent.
>
> Ce n'est pas un échec : c'est la définition même de l'efficience de marché au sens de **Jensen (1978)** —
> un marché est efficient s'il n'existe aucune stratégie dégageant un profit *net des coûts et des
> contraintes de mise en œuvre*. Une anomalie statistique peut donc coexister avec l'efficience.

**Ce qu'il ne faut surtout pas faire :** présenter le Sharpe de 6,04 en soutenance. Le premier membre du
jury qui connaît les marchés demandera comment la position est prise, et la démonstration s'effondrera en
direct. Présenter le résultat statistique (AUC 0,671), puis expliquer soi-même pourquoi il n'est pas
exploitable.

---

## §6 — Trois corrections avant de rédiger

### 1. Colinéarité catastrophique dans la régression logistique

Les VIF affichés par le notebook 06 sont ingérables : `ret_cc_lag1` à **1 516**, `ret_oc_lag1` à 827,
`gap_lag1` à 631, et `z_mu_night_full` à **101**. Au-delà de 5, un coefficient n'est déjà plus
interprétable.

La cause est mécanique : `ret_cc = (1+gap)(1+ret_oc)−1` et `mu = pos − neg` sont des **identités exactes**.
Mettre les trois membres dans la même régression rend la matrice quasi singulière.

**Correctif :** retirer `ret_cc_lag1` (garder `gap_lag1` et `ret_oc_lag1`), et retirer `z_pos_night_full` /
`z_neg_night_full` quand `z_mu_night_full` est présent. L'AUC ne bougera quasiment pas — les arbres n'en
souffrent pas — mais les coefficients redeviendront lisibles. Sans cela, le coefficient de +1,00 sur
`z_mu_night_full` et de −0,74 sur `z_pos_night_full` (de signe opposé alors que les deux mesurent
l'optimisme) sont ininterprétables.

### 2. Le bloc de test final n'a jamais été évalué

Le notebook 09 signale `[MANQUE] Résultats TEST M1 (06)`. La dernière section du notebook 06 n'a pas tourné.
**Tous les chiffres d'AUC disponibles sont donc des chiffres de validation**, pas de test verrouillé.

Ce n'est pas grave — la validation glissante est déjà hors échantillon et c'est elle qui compte le plus.
Mais il faut soit exécuter cette cellule **une seule fois** et reporter le chiffre, soit écrire clairement
dans le mémoire que l'évaluation repose sur la validation glissante à 4 plis. **Ne pas laisser croire**
qu'un test verrouillé a été fait.

### 3. Le régime « Reprise / liquidité » n'est pas significatif

Sur les cinq régimes, quatre donnent une corrélation significative, mais **avril → décembre 2020** donne
ρ = 0,058 avec un intervalle [−0,005 ; +0,120] qui touche zéro. Le notebook le marque « fragile ».

Il faut le reporter, pas le masquer. Interprétation plausible : pendant le rebond en V post-COVID, tout
montait quoi qu'il arrive, et le sentiment individuel se noyait dans un mouvement de marché généralisé.
C'est un point de discussion intéressant, pas une faiblesse.

---

## §7 — La conclusion du PFE, rédigée

> Ce travail examine si le sentiment exprimé sur les réseaux sociaux financiers contient une information
> exploitable sur les prix. Il s'appuie sur 3,7 millions de messages StockTwits couvrant cinq titres
> technologiques de janvier 2020 à mars 2022, scorés par FinBERT et agrégés en fenêtres alignées sur les
> horaires de la bourse de New York.
>
> La contribution méthodologique centrale est la **décomposition du rendement quotidien** en deux
> composantes : le *gap* d'ouverture, qui se forme marché fermé, et le rendement de *séance*. Cette
> séparation révèle une asymétrie nette. Le sentiment nocturne prédit le signe du gap — ρ = 0,157, écart de
> 34,8 points de pourcentage entre quintiles extrêmes, AUC de 0,671 en validation glissante, effet
> significatif sur les cinq titres pris séparément et sur quatre régimes de marché sur cinq. Il ne prédit en
> revanche **pas** le rendement de séance : ρ = −0,010, AUC de 0,50, et l'analyse de puissance permet
> d'exclure tout effet d'ampleur supérieure à 0,05.
>
> Cette asymétrie n'est pas un demi-échec : elle constitue une **vérification empirique de l'hypothèse
> d'efficience semi-forte** (Fama, 1970). L'information publique véhiculée par les messages nocturnes est
> intégralement incorporée au prix dès l'ouverture, et il n'en subsiste rien pour la séance. La structure
> temporelle du signal le confirme : la corrélation est maximale au décalage zéro et disparaît dès le
> lendemain.
>
> L'analyse économique conduit toutefois à nuancer fortement l'exploitabilité de ce signal. La capture du
> gap suppose une position prise à la clôture de la veille, soit jusqu'à dix-sept heures avant que
> l'information textuelle ne soit disponible ; la fenêtre de pré-marché, qui porte l'essentiel du pouvoir
> prédictif, est de surcroît **contemporaine** de la formation du prix d'ouverture. La version
> implémentable de la stratégie — décalée d'une journée pour respecter cette contrainte — dégage un ratio
> de Sharpe de −0,53. Le signal est donc statistiquement réel et économiquement inaccessible, ce qui est
> précisément la définition de l'efficience au sens de **Jensen (1978)**.
>
> Le résultat le plus directement valorisable relève de la **gestion du risque** plutôt que de la prévision
> directionnelle. L'attention sociale anormale améliore la prévision de l'amplitude intraday au-delà d'un
> modèle de volatilité historique (R² hors échantillon de 0,527 contre 0,495 ; QLIKE de 0,392 contre 0,438),
> et se traduit par une Value-at-Risk conditionnelle dont la couverture empirique est statistiquement exacte
> (5,02 % de dépassements pour une cible de 5 % ; test de Kupiec, p = 0,976), là où la VaR historique
> inconditionnelle sous-estime le risque (6,14 %). À capital immobilisé équivalent, la protection est
> meilleure.
>
> Ces conclusions doivent être lues à la lumière de trois limites. L'univers se réduit à cinq titres
> technologiques très liquides, sélectionnés *ex post* pour leur volume de discussion, ce qui introduit un
> biais de sélection. La période, marquée par la crise sanitaire, un afflux de liquidité sans précédent et
> un essor du trading des particuliers, n'est pas représentative d'un régime ordinaire. Enfin, FinBERT,
> entraîné sur de la presse financière, classe 76 % des messages comme neutres : le signal repose donc sur
> la fraction du corpus que le modèle sait interpréter, et un classifieur adapté au registre des forums
> constituerait la première voie d'amélioration.

---

## §8 — Ce qu'il reste à faire

| Priorité | Action | Pourquoi |
|---|---|---|
| 1 | Refaire le backtest avec un **décalage d'un jour** et en faire le résultat principal | c'est la seule version défendable ; le Sharpe de 6 ne doit pas apparaître dans le mémoire autrement que comme un contre-exemple pédagogique |
| 2 | Retirer `ret_cc_lag1`, `z_pos`, `z_neg` et relancer la logistique | rendre les coefficients interprétables (VIF actuels : 1 516 et 101) |
| 3 | Récupérer les étiquettes **Bullish / Bearish** des fichiers Kaggle | valider FinBERT sur une vérité terrain externe — répond directement à la limite des 76 % de neutres |
| 4 | Ajouter une variante `overnight` seul (coupée à minuit) comme spécification principale | AUC 0,597, plus faible mais exempte de toute objection de pré-marché |
| 5 | Exécuter la cellule de test final du notebook 06, **une seule fois** | ou assumer explicitement que l'évaluation repose sur la validation glissante |

### Le message à retenir

Ce travail est **bon**, et il l'est pour une raison qui n'a rien à voir avec le niveau de l'AUC. Un échec
initial a été diagnostiqué au lieu d'être contourné, et le diagnostic était juste (mauvaise cible, corpus
trop mince). Une asymétrie entre deux composantes du rendement a été démontrée, avec une interprétation
théorique solide. Et une batterie de tests — falsification par inversion, placebo par permutation,
leave-one-ticker-out, lags négatifs, analyse de puissance — a été mise en place, ce que très peu de mémoires
sur ce sujet font.

La seule chose qui manquait était de reconnaître que le résultat le plus spectaculaire était le moins
crédible. Maintenant que c'est fait, l'ensemble tient debout.

---

## Références citées

- Fama, E. F. (1970). *Efficient Capital Markets: A Review of Theory and Empirical Work*. Journal of Finance.
- Jensen, M. C. (1978). *Some Anomalous Evidence Regarding Market Efficiency*. Journal of Financial Economics.
- Kupiec, P. (1995). *Techniques for Verifying the Accuracy of Risk Measurement Models*. Journal of Derivatives.
- Antweiler, W. & Frank, M. (2004). *Is All That Talk Just Noise?*. Journal of Finance.
- Tetlock, P. (2007). *Giving Content to Investor Sentiment*. Journal of Finance.
- Da, Z., Engelberg, J. & Gao, P. (2011). *In Search of Attention*. Journal of Finance.
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.
