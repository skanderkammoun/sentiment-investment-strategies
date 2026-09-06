# Cours 2 — Notebook 04 : l'analyse exploratoire

**Comment on découvre où se cache le signal — et comment on prouve qu'on ne s'est pas trompé**

*Cours détaillé, chapitre par chapitre. Chaque test : la notion, la formule, ce qu'il prouve, ce qu'il
ne prouve pas, et le piège associé.*

---

## Table des matières

| # | Chapitre | Notion statistique enseignée |
|---|---|---|
| 0 | À quoi sert une EDA | démarche exploratoire |
| 1 | Cartographier les 81 colonnes | organisation des données |
| 2 | Les identités comptables | validation par redondance |
| 3 | Statistiques descriptives | moyenne, écart-type, comparabilité |
| 4 | La densité du corpus | loi log-normale, quantiles |
| 5 | Prix vs sentiment | **régression fallacieuse** |
| 6 | La corrélation de Pearson | covariance, ρ, ce qu'elle rate |
| 7 | Prédictif vs contemporain | **causalité temporelle** ⭐ |
| 8 | La heatmap | multicolinéarité |
| 9 | Les quintiles | **analyse non paramétrique** ⭐ |
| 10 | Le biais de niveau | **paradoxe de Simpson** |
| 11 | Le test z de proportions | test d'hypothèse, p-value |
| 12 | Le bootstrap par blocs | **indépendance violée** ⭐ |
| 13 | Le Spearman | corrélation de rang, monotonie |
| 14 | Les lags | **falsification** ⭐ |
| 15 | Modèles emboîtés | R², test de Fisher |
| 16 | Les régimes | IC de Fisher, stabilité |
| 17 | Récapitulatif | les 12 idées à retenir |

⭐ = les quatre sections qui font la valeur du mémoire.

---

# Chapitre 0 — À quoi sert une analyse exploratoire

## 0.1 — Le principe

**EDA** = *Exploratory Data Analysis*, analyse exploratoire des données. Le terme vient de John Tukey
(1977), le statisticien qui a aussi inventé la boîte à moustaches et la transformée de Fourier rapide.

Son idée était provocante à l'époque : **avant de tester une hypothèse, il faut regarder les données**.
La statistique classique disait l'inverse — on formule une hypothèse, on collecte, on teste. Tukey a
montré que cette rigidité fait rater l'essentiel.

## 0.2 — Pourquoi cette partie vient AVANT les modèles

Voici l'erreur que fait la majorité des projets de data science :

```
❌ Mauvaise démarche :
   données → modèle → résultat médiocre → autre modèle → encore médiocre
             → « essayons du deep learning » → toujours médiocre → abandon
```

```
✅ Bonne démarche :
   données → EDA → « le signal est ICI, pas LÀ » → modèle sur la bonne cible
```

**C'est exactement l'histoire de ton PFE.** Ta phase 5 initiale a enchaîné les modèles sur `ret_cc` sans
jamais se demander si le signal s'y trouvait. Il n'y était pas. Aucun modèle, aussi sophistiqué soit-il,
ne peut extraire une information qui n'existe pas.

> **L'analogie.** Tu cherches tes clés. La mauvaise méthode : acheter une lampe torche de plus en plus
> puissante et fouiller le salon. La bonne méthode : te demander d'abord dans quelle pièce tu es entré en
> dernier. L'EDA, c'est se poser cette question.

## 0.3 — Ce que la partie 4 doit produire

Elle ne construit **aucun modèle**. Elle produit **quatre décisions** :

| Décision | Fondée sur |
|---|---|
| La cible sera `y_gap`, pas `ret_oc` ni `ret_cc` | ch. 7, 9, 11 |
| Les fenêtres `open30`, `mkt`, `post` sont exclues | ch. 7 |
| Les variables seront normalisées **par titre** | ch. 3, 10 |
| Les modèles **non linéaires** sont justifiés | ch. 9 |

Et elle produit **une preuve** : qu'il n'y a pas de fuite d'information (ch. 14).

---

# Chapitre 1 — Cartographier les 81 colonnes

```
Identité                 ( 2) : Date, Ticker
Prix bruts (OHLCV)       ( 5) : Open, High, Low, Close, Volume
Prix dérivés             ( 7) : prev_close, prev_volume, prev_ret_cc, vol_20d,
                                gap, ret_oc, ret_cc
Cibles binaires          ( 3) : y_gap, y_oc, y_cc
Sentiment — overnight    ( 7) : n, mu, sd, p10, p90, pos, neg
Sentiment — pre          ( 7) : idem
Sentiment — night_full   (10) : idem + nlog, nabn, disp
Sentiment — open30       (10) : idem
Sentiment — mkt          (10) : idem
Sentiment — post         (10) : idem
Dérivées / décalées      (10) : dmu_night, mu_night_ma3, mu_night_z20,
                                mu/nlog/sd_mkt_lag1, mu/nlog/sd_post_lag1, y_gap_net

Total classé : 81 / 81 colonnes
```

## Pourquoi commencer par un inventaire

**Le principe :** on ne peut pas raisonner sur ce qu'on ne connaît pas. Avec 81 colonnes, personne ne les
garde en tête. Il faut une **carte**.

**Le contrôle caché :** la dernière ligne, `81 / 81`. Si le total ne tombait pas juste, cela signifierait
qu'une colonne échappe à la classification — donc qu'une variable existe sans qu'on sache à quelle famille
elle appartient, donc sans qu'on sache si elle est légale.

C'est un **contrôle d'exhaustivité** : simple, et il attrape les oublis.

## La structure qui saute aux yeux

Regarde bien : **six fenêtres × sept statistiques = 42 colonnes** de sentiment, plus 12 colonnes
d'attention. Autrement dit, **54 des 81 colonnes sont la même chose répétée**.

C'est un point important pour comprendre le panel : il n'y a pas 81 idées différentes. Il y a environ
**dix idées** (compter, moyenner, mesurer la dispersion, normaliser…) appliquées à **six moments** de la
journée. Une fois les dix idées comprises, les 81 colonnes se lisent d'un coup.

---

# Chapitre 2 — Les identités comptables

```
gap    = Open / prev_close - 1        : 2.58e-16
ret_oc = Close / Open - 1             : 3.05e-16
(1+gap)(1+ret_oc) = 1 + ret_cc        : 3.33e-16

y_gap == 1[gap > 0]   : True
y_oc  == 1[ret_oc > 0] : True
y_cc  == 1[ret_cc > 0] : True
```

## 2.1 — La notion : la validation par redondance

**L'idée générale.** Quand une quantité peut être calculée de **deux manières indépendantes**, on la
calcule des deux et on compare. Si les deux coïncident, les deux chemins sont probablement corrects.

Cette technique est ancienne et universelle :

| Domaine | Application |
|---|---|
| Comptabilité | la **partie double** — chaque écriture au débit et au crédit, le total doit s'équilibrer |
| Actuariat | la **réconciliation** des provisions par deux méthodes (Chain-Ladder et Bornhuetter-Ferguson) |
| Informatique | les **sommes de contrôle** (checksums) sur les fichiers transférés |
| Ici | `(1+gap)(1+ret_oc) = 1+ret_cc` |

## 2.2 — Pourquoi 10⁻¹⁶ et pas 0

Un ordinateur représente les nombres réels en **virgule flottante double précision** : 64 bits, dont 52
pour la mantisse. Cela donne environ **16 chiffres significatifs**.

```
0,1 + 0,2 = 0,30000000000000004     ← en Python, essaie-le
```

Ce n'est pas un bug : 0,1 n'a pas de représentation binaire exacte, comme 1/3 n'a pas de représentation
décimale exacte.

**L'epsilon machine** vaut environ 2,2 × 10⁻¹⁶. Toute chaîne d'opérations accumule une erreur de cet
ordre. Tes erreurs valent 2,58 × 10⁻¹⁶ et 3,33 × 10⁻¹⁶ — **exactement la précision machine**.

Autrement dit : les formules sont **mathématiquement exactes**, et l'écart observé est uniquement dû à
l'arrondi de l'ordinateur.

**Comment choisir un seuil de tolérance :**

| Seuil | Verdict |
|---|---|
| `< 1e-12` | erreur d'arrondi pure — formule exacte |
| `1e-9` à `1e-6` | suspect — probablement une différence d'arrondi intermédiaire |
| `> 1e-6` | **erreur de formule** |

## 2.3 — L'exemple à savoir refaire au tableau

```
AAPL — 2 janvier 2020
  Clôture de la veille : 73,4125
  Ouverture            : 74,0600   ->  gap    = 74,0600 / 73,4125 − 1 = +0,008820
  Clôture du jour      : 75,0875   ->  ret_oc = 75,0875 / 74,0600 − 1 = +0,013874
  Vérification : (1 + 0,008820) × (1 + 0,013874) − 1 = +0,022816
                  ret_cc affiché                       = +0,022816
```

Si le jury te demande d'expliquer ta décomposition, c'est **ce calcul** que tu écris au tableau. Trois
lignes, aucune ambiguïté.

## 2.4 — La masse « neutre » de FinBERT

```
MASSE 'NEUTRE' DE FinBERT (= 1 - pos - neg)
  moyenne : 0.764   médiane : 0.765
```

FinBERT place en moyenne **76 %** de sa probabilité sur « neutre » (au niveau des moyennes journalières —
au niveau des messages individuels c'était 80,7 %, cf. Cours 1).

**Ce que cela implique numériquement.** Puisque `mu = pos − neg` et que `pos + neg ≈ 0,24`, la valeur
maximale que `mu` pourrait atteindre est d'environ 0,24. Elle vaut en moyenne 0,11. **Ce n'est pas que la
foule soit tiède** — c'est que l'échelle de mesure est comprimée.

C'est important pour interpréter les coefficients plus tard : un « écart d'une unité de `mu` » n'existe
pas dans tes données. C'est aussi pourquoi on normalise (ch. 3).

---

# Chapitre 3 — Les statistiques descriptives

## 3.1 — Les variables de marché

```
Ticker         AAPL   AMZN   META   NVDA   TSLA
gap     mean  0.066  0.124 -0.025  0.219  0.402      (en %)
        std   1.539  1.417  1.872  1.926  2.978
ret_oc  mean  0.107 -0.017  0.056  0.084  0.129
        std   1.704  1.687  1.827  2.674  3.627
ret_cc  mean  0.173  0.106  0.033  0.304  0.531
        std   2.325  2.142  2.686  3.319  4.683
vol_20d mean  2.052  1.976  2.392  2.996  4.246
```

### Comment lire un tableau moyenne / écart-type

La **moyenne** dit *« vers quoi ça tend »*. L'**écart-type** dit *« de combien ça s'écarte »*.

**Les deux ensemble décrivent la distribution.**

Prends TSLA : gap moyen +0,402 %, écart-type 2,978 %. En supposant une distribution à peu près normale
(hypothèse discutable en finance, mais utile pour l'intuition) :

```
environ 68 % des nuits :  entre −2,58 %  et  +3,38 %      (moyenne ± 1 écart-type)
environ 95 % des nuits :  entre −5,55 %  et  +6,36 %      (moyenne ± 2 écarts-types)
```

**Trois lectures immédiates :**

**1. TSLA gagnait +0,40 % chaque nuit en moyenne.** Sur 548 jours, cela composerait à
(1,004)⁵⁴⁸ ≈ **× 8,9**. C'est la bulle Tesla de 2020-2021, et cela pose un problème pour le backtest :
une stratégie qui achète tous les soirs capterait déjà cette prime sans rien prédire.

**2. La volatilité varie du simple au double** : 1,4 % pour AMZN, 3,0 % pour TSLA. Un gap de +2 % est
banal pour TSLA et exceptionnel pour AMZN.

**3. L'écart-type dépasse largement la moyenne partout.** Pour AAPL : moyenne 0,066 %, écart-type 1,539 %
— un rapport de **23**. Cela signifie que le mouvement d'une nuit donnée est presque entièrement du
**bruit** ; la tendance ne se voit qu'en agrégeant des centaines de jours.

C'est **la difficulté fondamentale de la prévision financière** : le rapport signal/bruit est
catastrophique. C'est pourquoi une corrélation de 0,15 y est considérée comme forte, alors qu'elle serait
ridicule en biologie ou en psychométrie.

## 3.2 — Les variables de sentiment, et le problème de niveau

```
Ticker                  AAPL     AMZN     META     NVDA      TSLA
mu_night_full  mean   0.0945   0.1170   0.1139   0.1627    0.0449
               std    0.0423   0.0489   0.0668   0.0783    0.0323
n_night_full   mean    775.3    349.0    217.3    184.0    1604.7

rapport max/min = 3.6x
```

**NVDA a un sentiment moyen 3,6 fois supérieur à TSLA.**

### Pourquoi ce n'est pas une information sur les titres

Ce n'est pas que la foule aime 3,6 fois plus NVDA. C'est que les **communautés écrivent différemment** :

- les messages TSLA sont plus polémiques, plus chargés en vocabulaire que FinBERT classe en négatif ;
- les messages NVDA sont plus techniques et enthousiastes.

**C'est un biais de mesure lié à l'instrument**, pas une propriété du marché.

### Le calcul qui rend le problème concret

Que vaut un sentiment de **0,12** ?

```
Pour NVDA :  (0,12 − 0,1627) / 0,0783  =  −0,55 écart-type   ->  MÉDIOCRE
Pour TSLA :  (0,12 − 0,0449) / 0,0323  =  +2,33 écarts-types ->  EXCEPTIONNEL
```

**Le même nombre veut dire deux choses opposées.** La valeur brute ne signifie rien hors contexte.

### Ce que ça impose

Toute analyse doit être faite **titre par titre**, ou sur des variables **normalisées par titre**. C'est
la justification :

- des quintiles intra-ticker (ch. 9-10)
- du z-score glissant du notebook 05
- des corrélations calculées séparément par titre (ch. 12)

---

# Chapitre 4 — La densité du corpus

```
        minimum    q25  médiane  moyenne     q75  maximum
AAPL       30.0  388.0    571.0    775.0   858.0   6898.0
AMZN      100.0  198.0    260.0    349.0   360.0   9633.0
META       33.0   76.0    108.0    217.0   171.0  12337.0
NVDA        0.0   60.0     96.0    184.0   199.0   5546.0
TSLA        0.0  701.0   1138.0   1605.0  1902.0  16722.0

Nuits sans aucun message : 4 sur 2 740
Nuits avec moins de 10 messages : 7
```

## 4.1 — Lire des quantiles

Un **quantile** coupe la distribution en parts. Le q25 (premier quartile) est la valeur en dessous de
laquelle se trouvent 25 % des observations.

Pour META : q25 = 76, médiane = 108, q75 = 171. Donc **la moitié des nuits** ont entre 76 et 171 messages.

## 4.2 — Le signe qui ne trompe pas : moyenne ≫ médiane

| Ticker | médiane | moyenne | rapport |
|---|---|---|---|
| META | 108 | 217 | **2,01** |
| NVDA | 96 | 184 | **1,92** |
| AAPL | 571 | 775 | 1,36 |
| TSLA | 1 138 | 1 605 | 1,41 |

**Quand la moyenne dépasse largement la médiane, la distribution est asymétrique à droite** — il y a une
longue queue de valeurs très élevées qui tirent la moyenne vers le haut sans bouger la médiane.

C'est la signature d'une **loi log-normale** : le logarithme de la variable suit une loi normale.

> **Pourquoi la log-normale apparaît si souvent.** Elle émerge dès qu'un phénomène résulte d'effets
> **multiplicatifs** plutôt qu'additifs. Une nuit d'actualité intense n'ajoute pas 200 messages : elle
> **multiplie** l'activité par 5 ou 10. Le théorème central limite appliqué à des produits (donc à des
> sommes de logarithmes) donne une log-normale.
>
> On la retrouve partout : tailles d'entreprises, revenus, durées de sinistres en assurance, tailles de
> villes.

## 4.3 — L'amplitude extrême

META : de **33** à **12 337** messages. Un facteur **374**.

**Ce que cela impliquerait pour un modèle linéaire.** Une régression minimise la somme des **carrés** des
erreurs. Une observation à 12 337 pèse (12 337/108)² ≈ **13 000 fois** plus qu'une observation médiane.
Le modèle serait entièrement dicté par une poignée de jours d'exception.

**D'où le passage au logarithme** (`nlog`), qui transforme les rapports en différences et rend les
observations comparables.

## 4.4 — Les 4 nuits vides

```
Nuits sans aucun message : 4 sur 2 740     (0,15 %)
```

Sur 2 740 observations, **4 seulement** sont muettes. Le corpus est donc quasi complet.

**À comparer avec l'ancien corpus 2023-2026 : médiane de 2 messages par jour.** Là-bas, la majorité des
observations étaient inexploitables. Ici, 99,85 % le sont.

C'est **le fait qui justifie tout le changement de corpus**, et il faut le donner en chiffres, pas en
impressions.

---

# Chapitre 5 — Prix vs sentiment : le piège de la régression fallacieuse

Cette cellule produit une figure. Elle est descriptive — mais elle porte un piège méthodologique
important.

## 5.1 — Le piège

Superposer un **prix** et un **sentiment** donne presque toujours une impression de lien fort, même quand
il n'y en a aucun.

**Pourquoi.** Un prix est une variable **en niveau**, avec une tendance. Un sentiment est une variable
**stationnaire**, qui oscille autour d'une moyenne. Deux séries qui montent ensemble apparaissent
corrélées — sans qu'il y ait de relation causale.

## 5.2 — La régression fallacieuse (Granger & Newbold, 1974)

**L'expérience célèbre.** Granger et Newbold ont simulé des paires de séries **totalement
indépendantes**, chacune étant une marche aléatoire :

```
x(t) = x(t−1) + bruit_1(t)
y(t) = y(t−1) + bruit_2(t)          ← aucun lien entre les deux
```

Puis ils ont régressé `y` sur `x`. Résultat : dans **environ 75 %** des cas, le coefficient était
« significatif » au seuil de 5 %, avec des R² souvent supérieurs à 0,7.

**Alors que les séries n'ont strictement aucun rapport.**

**L'explication.** Les tests statistiques classiques supposent des données **stationnaires** (moyenne et
variance constantes). Une marche aléatoire ne l'est pas : sa variance croît avec le temps. Appliquer un
test conçu pour du stationnaire à du non-stationnaire donne des résultats faux dans le sens du
faux-positif.

> **L'exemple pédagogique classique.** Sur 1990-2010, la consommation de fromage aux États-Unis et le
> nombre de personnes mortes étranglées dans leurs draps sont corrélées à **0,95**. Les deux augmentent
> avec le temps et la population. Il n'y a évidemment aucun lien.

## 5.3 — La correction appliquée

Le notebook ne trace pas le prix brut : il trace le **gap cumulé** et un sentiment **lissé sur 10 jours**.

**Pourquoi le gap cumulé ?** Parce que c'est exactement la quantité que le sentiment est censé prédire. Si
le lien existe, il doit se voir là — et pas seulement sur le prix total, qui monte de toute façon.

**Une observation importante sur cette figure :** la courbe du gap cumulé monte régulièrement. Cela révèle
une **prime de risque overnight** — détenir le titre pendant la nuit rapporte en moyenne, indépendamment
de tout signal.

C'est un phénomène documenté : sur les grandes actions américaines, une part majoritaire du rendement
historique s'est formée **marché fermé**. Et cela a une conséquence directe pour ton backtest :

> **Une stratégie qui achèterait tous les soirs, sans rien prédire du tout, capterait déjà cette prime.**
> Le modèle doit donc être comparé à cette référence — c'est le « Long systématique du gap » du
> notebook 08 — et pas seulement au buy & hold.

---

# Chapitre 6 — La corrélation de Pearson

## 6.1 — La notion

La corrélation mesure **à quel point deux variables varient ensemble**.

```
                  covariance(X, Y)
rho(X, Y)  =  ──────────────────────────
              écart-type(X) × écart-type(Y)
```

où la covariance est :

```
                     1     n
covariance(X,Y)  =  ─── ×  Σ  ( x_i − moyenne(X) ) × ( y_i − moyenne(Y) )
                     n    i=1
```

## 6.2 — Comprendre la formule sans les maths

Regarde le terme `(x_i − moyenne_X) × (y_i − moyenne_Y)`. Pour chaque observation, il vaut :

| Situation | (x − x̄) | (y − ȳ) | produit |
|---|---|---|---|
| X au-dessus de sa moyenne, Y aussi | + | + | **positif** |
| X en dessous, Y en dessous | − | − | **positif** |
| X au-dessus, Y en dessous | + | − | **négatif** |

Si les deux variables évoluent dans le même sens, la plupart des produits sont positifs et la somme est
grande. Si elles n'ont aucun rapport, les produits positifs et négatifs se compensent et la somme est
proche de zéro.

**La division par les écarts-types** rend le résultat sans unité et borné entre −1 et +1. C'est ce qui
permet de comparer une corrélation « sentiment/gap » à une corrélation « taille/poids ».

## 6.3 — Ce que la corrélation NE mesure pas

**Trois limites majeures, à connaître absolument.**

### Limite 1 — Elle ne mesure que le lien LINÉAIRE

```
X  = −3, −2, −1, 0, 1, 2, 3
Y  =  9,  4,  1, 0, 1, 4, 9        (Y = X², lien parfait et déterministe)

corrélation de Pearson = 0,00
```

Un lien parfait, une corrélation nulle. La corrélation ne voit que les droites.

**C'est pourquoi le notebook fait aussi une analyse par quintiles** (ch. 9) : elle ne suppose aucune forme.

### Limite 2 — Elle ne dit rien de la causalité

Corrélation ≠ causalité. Trois explications possibles pour toute corrélation observée :

| Explication | Exemple ici |
|---|---|
| X cause Y | le sentiment influence le prix d'ouverture |
| Y cause X | le prix (pré-marché) influence ce que les gens écrivent |
| Z cause les deux | une nouvelle publique fait à la fois monter le prix et écrire les gens |

**Le chapitre 7 est entièrement consacré à départager ces cas** — c'est le cœur méthodologique du mémoire.

### Limite 3 — Elle est sensible aux valeurs extrêmes

Un seul point aberrant peut créer ou détruire une corrélation. D'où l'usage complémentaire du Spearman
(ch. 13) et des quintiles (ch. 9).

## 6.4 — Quel ordre de grandeur est « bon » ?

**Cela dépend entièrement du domaine.**

| Domaine | ρ typique d'un effet réel |
|---|---|
| Physique (loi déterministe) | 0,99 |
| Psychométrie | 0,4 – 0,6 |
| Épidémiologie | 0,2 – 0,4 |
| **Finance, prévision journalière** | **0,03 – 0,15** |

**Pourquoi si bas en finance ?** Parce que le marché est **compétitif**. Si une variable prédisait le prix
à 0,5, des milliers de professionnels l'exploiteraient immédiatement, et la corrélation disparaîtrait
— c'est le mécanisme même de l'efficience.

> **Une corrélation de 0,157 en finance journalière est donc un résultat fort.** Et une corrélation de
> 0,60 serait **suspecte** : il faudrait chercher la fuite d'information avant de se réjouir.

---

# Chapitre 7 — Prédictif vs contemporain ⭐

**C'est la section la plus importante du notebook 04 pour la crédibilité du mémoire.**

## 7.1 — Le tableau brut

```
A) FENÊTRES PRÉDICTIVES
 Cible       Fenetre    n     rho   p_value              STATUT
   gap        mu_pre 2734  0.1816  1.0e-21  PRÉDICTIVE (limite)
   gap mu_night_full 2736  0.1572  1.3e-16  PRÉDICTIVE (limite)
   gap  mu_overnight 2735  0.0967  4.1e-07  PRÉDICTIVE
ret_oc        mu_pre 2734  0.0128  5.0e-01  PRÉDICTIVE (limite)
ret_oc mu_night_full 2736 -0.0103  5.9e-01  PRÉDICTIVE (limite)
ret_oc  mu_overnight 2735 -0.0274  1.5e-01  PRÉDICTIVE

B) FENÊTRES CONTEMPORAINES / POSTÉRIEURES — À EXCLURE
ret_oc        mu_mkt 2736  0.2030  7.9e-27  CONTEMPORAINE
ret_oc       mu_post 2733  0.1699  3.7e-19  CONTEMPORAINE
ret_cc        mu_mkt 2736  0.1934  1.8e-24  CONTEMPORAINE
```

## 7.2 — Le piège, et pourquoi presque tout le monde y tombe

Regarde le tableau complet, sans distinction : **la plus forte corrélation de tout le notebook est
`mu_mkt → ret_oc = 0,2030`**. Il serait tentant de l'annoncer comme le meilleur résultat.

**Ce serait une faute grave.**

`mu_mkt` agrège les messages postés **de 10h à 16h**. `ret_oc` est le rendement **de 9h30 à 16h**. Les
deux se déroulent **au même moment**.

Cette corrélation dit donc simplement :

> *« Quand le prix monte pendant la séance, les gens tweetent positivement pendant la séance. »*

C'est une **réaction**, pas une prédiction. Pour l'exploiter, il faudrait connaître à 9h30 les messages
qui seront écrits entre 10h et 16h. Impossible.

`mu_post` est pire encore : les messages sont postés **après** la clôture, donc après que `ret_oc` soit
définitivement figé. **La flèche causale est inversée.**

## 7.3 — La règle formelle

> Une fenêtre de texte est utilisable pour prédire une cible **si et seulement si elle se ferme avant que
> la cible ne commence à se former.**

Les trois cibles démarrent au plus tard à l'ouverture (9h30). Donc :

| Fenêtre | Se ferme à | ≤ 9h30 ? | Statut |
|---|---|---|---|
| `overnight` | 00h00 | oui | **prédictive** |
| `pre` | 09h30 | oui, tout juste | **prédictive (limite)** |
| `night_full` | 09h30 | oui, tout juste | **prédictive (limite)** |
| `open30` | 10h00 | non | contemporaine |
| `mkt` | 16h00 | non | contemporaine |
| `post` | 00h00 (J+1) | non | postérieure |

**Pourquoi coder la règle plutôt que l'appliquer de tête.** Parce qu'une règle codée ne s'oublie pas, se
vérifie, et se documente. Le jour où tu ajoutes une septième fenêtre, la classification se fait
automatiquement.

## 7.4 — Le gradient qui valide la construction

Regarde les trois corrélations prédictives sur le gap :

| Fenêtre | Se ferme | ρ avec le gap |
|---|---|---|
| `mu_overnight` | minuit | **+0,097** |
| `mu_night_full` | 9h30 | **+0,157** |
| `mu_pre` | 9h30 | **+0,182** |

**Plus l'information est fraîche, plus elle est informative.** Les messages de 8h du matin en disent plus
sur l'ouverture que ceux de 21h la veille.

**Pourquoi c'est important.** Ce gradient est **cohérent avec la microstructure des marchés**, et il est
difficile à obtenir par hasard. Si les corrélations étaient toutes identiques, ou dans le désordre, on
soupçonnerait un artefact. Là, elles s'ordonnent exactement comme la théorie le prédit.

C'est ce qu'on appelle un **contrôle de validité de construit** (*construct validity*) : la mesure se
comporte comme le concept qu'elle prétend mesurer.

## 7.5 — Le résultat négatif, dans le même tableau

```
ret_oc mu_night_full 2736 -0.0103  p = 5.9e-01
```

Même variable, mêmes jours, cible différente : **le signal disparaît complètement**. Une p-value de 0,59
signifie qu'un tel résultat arriverait 59 fois sur 100 par pur hasard.

**Ces deux lignes côte à côte — `gap` à +0,157 et `ret_oc` à −0,010 — sont le cœur du mémoire.**

## 7.6 — Le paragraphe à recopier

> « Les corrélations les plus élevées obtenues sans précaution (μ_mkt → ret_oc = 0,203 ;
> μ_post → ret_cc = 0,170) correspondent à des fenêtres de texte contemporaines ou postérieures à la
> formation du rendement. Elles mesurent la réaction du sentiment au prix, et non l'inverse. Elles ne
> constituent pas un signal exploitable et sont exclues de l'espace des variables explicatives. Seules les
> fenêtres se clôturant au plus tard à l'ouverture sont retenues. »

**Pourquoi afficher le bloc B au lieu de le cacher ?** Parce que montrer qu'on a **vu** ces corrélations,
compris pourquoi elles ne valent rien, et décidé de les écarter, vaut infiniment mieux que de faire comme
si elles n'existaient pas. C'est la différence entre un travail rigoureux et un travail naïf.

---

# Chapitre 8 — La heatmap et la multicolinéarité

La matrice de corrélation croise toutes les variables entre elles. Elle sert **deux buts distincts**.

## But 1 — Voir le signal

Les trois dernières colonnes (`gap`, `ret_oc`, `ret_cc`) montrent le lien avec les cibles. La colonne
`gap` est nettement colorée ; la colonne `ret_oc` est blanche.

## But 2 — Détecter la multicolinéarité entre variables explicatives

C'est le bloc en haut à gauche, et c'est là que se joue l'interprétabilité des modèles.

**Le problème.** `night_full` est construite **à partir de** `overnight` et `pre` :

```
mu_night_full = ( n_overnight × mu_overnight  +  n_pre × mu_pre ) / n_night_full
```

Les trois variables sont donc **liées par construction** et fortement corrélées entre elles.

### Ce qui se passe si on les met toutes les trois

Une régression cherche des coefficients β tels que `y ≈ β₁·A + β₂·B + β₃·C`. Si `C` est une combinaison
de `A` et `B`, il existe une **infinité** de solutions équivalentes. L'algorithme en choisit une, souvent
avec des coefficients énormes et de signes absurdes.

**La conséquence pratique :** l'AUC reste bonne (la *prédiction* n'est pas abîmée), mais les coefficients
deviennent **ininterprétables**. Pour un mémoire, c'est rédhibitoire — tu veux pouvoir dire *« un
écart-type de sentiment supplémentaire multiplie la cote par 1,35 »*.

### La mesure : le VIF

```
              1
VIF(j)  =  ────────
            1 − R²(j)
```

où `R²(j)` est le R² de la régression de la variable *j* sur **toutes les autres**.

**Interprétation :** le VIF dit de combien la variance du coefficient est **gonflée** par la colinéarité.
Un VIF de 100 signifie que l'écart-type du coefficient est √100 = 10 fois plus grand qu'il ne devrait
l'être.

| VIF | Verdict |
|---|---|
| 1 | aucune colinéarité |
| < 5 | acceptable |
| 5 – 10 | à surveiller |
| **> 10** | **problématique** |

**Dans ton notebook 06** : `ret_cc_lag1` a un VIF de **1 516**, `z_mu_night_full` de **101**. La cause est
mécanique : `ret_cc = (1+gap)(1+ret_oc)−1` et `mu = pos − neg` sont des identités exactes.

### La règle pour la suite

> Garder **soit** `night_full` (version agrégée), **soit** le couple `overnight` + `pre` (version
> décomposée). **Jamais les trois.**
>
> Et de même : soit `mu`, soit le couple (`pos`, `neg`). Jamais les trois.

---

# Chapitre 9 — Les quintiles ⭐

## 9.1 — La notion

Un **quintile** est un cinquième de la distribution. On trie les observations selon une variable, on les
coupe en cinq paquets de taille égale, et on regarde ce qui se passe dans chacun.

```
Q1 = les 20 % de jours au sentiment le plus NÉGATIF
Q2 = les 20 % suivants
Q3 = les 20 % du milieu
Q4 = les 20 % suivants
Q5 = les 20 % de jours au sentiment le plus POSITIF
```

## 9.2 — Pourquoi c'est supérieur à la corrélation

La corrélation résume la relation en **un seul chiffre**, en supposant qu'elle est **linéaire**.

Les quintiles ne supposent **rien**. C'est une méthode **non paramétrique** : elle ne postule aucune forme
de relation. Si l'effet est concentré aux extrêmes, en escalier, ou en U, les quintiles le montrent ; la
corrélation le rate.

**Autre avantage : la lisibilité.** « ρ = 0,157 » ne parle à personne. « Quand le sentiment est dans les
20 % les plus négatifs, l'action ouvre en hausse 39 % du temps ; quand il est dans les 20 % les plus
positifs, 74 % du temps » — tout le monde comprend.

## 9.3 — Le résultat

```
      n  gap_moy  pct_gap_pos  seance_moy  pct_seance_pos  cc_moy
Q1  549   -0.717         39.3       0.194            52.8  -0.526
Q2  545   -0.016         53.9      -0.018            48.4  -0.033
Q3  548    0.452         63.1      -0.131            48.2   0.318
Q4  545    0.452         63.9       0.182            52.7   0.637
Q5  549    0.612         74.1       0.135            50.6   0.752

Écart Q5-Q1 sur le GAP    : +34.8 points
Écart Q5-Q1 sur la SÉANCE :  -2.2 points
```

**Ces deux colonnes côte à côte sont ta figure principale.**

- `pct_gap_pos` s'étale sur **34,8 points** : 39,3 → 74,1
- `pct_seance_pos` oscille entre 48,2 et 52,8 **sans direction** : c'est du pile ou face

Même variable explicative, mêmes jours, deux cibles. L'une est prévisible, l'autre non.

## 9.4 — Ce que la forme de la relation nous apprend

Regarde `gap_moy` : −0,717 / −0,016 / +0,452 / +0,452 / +0,612.

**Q3 et Q4 sont identiques.** L'essentiel de l'écart vient des **extrêmes**, surtout de Q1.

### Conséquence 1 : les modèles linéaires vont sous-performer

Une régression logistique suppose un effet **constant par unité** de sentiment. Elle est structurellement
incapable de représenter « rien au milieu, beaucoup aux bords ».

**D'où la décision du notebook 06 :** tester aussi des **arbres de décision**, qui découpent l'espace en
zones et peuvent apprendre « si `z < −1,5` alors probabilité = 0,35 ».

*(Sur tes données, les arbres n'ont finalement pas fait mieux — 0,670 contre 0,671. C'est un résultat en
soi : la relation, bien que non linéaire, est suffisamment simple pour qu'un modèle linéaire la capte.)*

### Conséquence 2 : une stratégie ne doit pas trader tous les jours

Si Q2, Q3 et Q4 n'apportent rien, y prendre position ne fait que payer des frais. **D'où la « zone
neutre » du backtest** : on ne trade que Q1 et Q5.

### Conséquence 3 : l'asymétrie négative

```
Q1 : gap moyen −0,717 %       écart à la moyenne générale : très grand
Q5 : gap moyen +0,612 %       écart : plus modeste
```

Comme la moyenne inconditionnelle des gaps est **positive** (marché haussier), le **pessimisme nocturne
est relativement plus informatif que l'optimisme**.

C'est cohérent avec la littérature sur l'asymétrie des mauvaises nouvelles (**Hong & Stein, 1999**) : les
investisseurs pessimistes sont souvent empêchés d'agir (la vente à découvert est coûteuse et risquée),
donc leur information met plus de temps à s'incorporer — et se libère d'un coup à l'ouverture.

**C'est un excellent paragraphe de discussion.**

## 9.5 — Le test par titre : la vraie robustesse

```
AAPL  : Q1= 31.8%  Q2= 51.4%  Q3= 66.4%  Q4= 61.5%  Q5= 72.7%   écart = +40.9
AMZN  : Q1= 40.0%  Q2= 59.6%  Q3= 67.3%  Q4= 63.3%  Q5= 72.7%   écart = +32.7
META  : Q1= 41.8%  Q2= 58.7%  Q3= 50.9%  Q4= 58.7%  Q5= 65.5%   écart = +23.7
NVDA  : Q1= 44.5%  Q2= 50.5%  Q3= 66.1%  Q4= 68.8%  Q5= 77.3%   écart = +32.8
TSLA  : Q1= 38.5%  Q2= 49.5%  Q3= 65.1%  Q4= 67.0%  Q5= 82.6%   écart = +44.1
```

**Les cinq titres vont dans le même sens, sans exception.**

**Pourquoi c'est beaucoup plus convaincant que le chiffre global.** Un résultat agrégé peut toujours
provenir d'un artefact de mélange (voir ch. 10). Cinq réplications indépendantes, non.

C'est le principe de la **réplication** — le fondement de la méthode expérimentale. Un résultat qui ne se
réplique pas n'est pas un résultat.

*(META brise légèrement la monotonie en Q3 avec 50,9 %. C'est normal : avec 110 observations par
quintile, l'incertitude sur chaque pourcentage est d'environ ±9 points. Un petit décrochage est attendu.)*

---

# Chapitre 10 — Le biais de niveau et le paradoxe de Simpson

## 10.1 — Le problème

Le notebook calcule les quintiles de **deux façons** :

| Version | Comment | Écart Q5−Q1 |
|---|---|---|
| **Intra-ticker** | quintiles calculés **séparément** pour chaque titre | **+34,8 pts** |
| Poolé | quintiles calculés sur les 2 740 jours mélangés | +28,2 pts |

**Pourquoi la version poolée est plus faible ?** Ce tableau le montre :

```
Composition des quintiles POOLÉS (% de chaque ticker) :
Ticker  AAPL  AMZN  META  NVDA  TSLA
Q1      14.2   8.9  17.9   6.0  52.9     <- plus de la MOITIÉ de Q1 est du TSLA
Q2      24.7  15.9  15.0   8.2  36.2
Q3      30.9  22.9  22.5  14.1   9.7
Q4      25.0  33.6  19.9  20.8   0.5
Q5       5.3  18.8  24.9  50.8   0.2     <- plus de la MOITIÉ de Q5 est du NVDA
```

Si les quintiles étaient neutres, chaque case vaudrait 20 %. **L'écart à 20 % mesure exactement le biais
de niveau.**

Rappelle-toi le chapitre 3 : NVDA a un sentiment moyen de 0,163 et TSLA de 0,045. Quand on trie tous les
jours ensemble, le quintile « très positif » se remplit mécaniquement de jours NVDA, et le « très
négatif » de jours TSLA.

## 10.2 — Ce qu'on mesure vraiment en poolé

La version poolée mélange **deux effets** :

| Effet | Nature | Valeur scientifique |
|---|---|---|
| **Temporel** : « quand le sentiment de NVDA est haut *pour NVDA*, NVDA gappe up » | vrai signal | ✅ |
| **Transversal** : « NVDA a un sentiment élevé, et NVDA a beaucoup monté » | artefact | ❌ |

**La version intra-ticker isole le premier effet.** Chaque titre est comparé à sa propre histoire.

## 10.3 — Le paradoxe de Simpson

Ce phénomène a un nom et une longue histoire.

> **Le paradoxe de Simpson** (1951) : une tendance observée dans plusieurs groupes peut **s'inverser**
> quand on agrège les groupes.

**L'exemple historique — Berkeley, 1973.** L'université est accusée de discriminer les femmes :

```
Admission globale :   hommes 44 %   femmes 35 %      <- écart de 9 points
```

Mais en regardant **département par département**, les femmes étaient admises à taux égal ou supérieur
dans presque tous.

**L'explication.** Les femmes candidataient massivement dans les départements les plus sélectifs (lettres,
taux d'admission ~10 %), les hommes dans les moins sélectifs (ingénierie, ~50 %). L'agrégation créait une
discrimination apparente qui n'existait dans aucun département.

**Le mécanisme est exactement le même que le tien** : une variable cachée (le département / le ticker)
est liée à la fois à la variable explicative et à la cible.

## 10.4 — La leçon générale

> **Quand des groupes hétérogènes sont mélangés, toujours vérifier le résultat groupe par groupe.**

Dans ton cas, l'agrégation ne renverse pas la conclusion — elle l'**atténue** (28,2 au lieu de 34,8). Mais
elle aurait pu la renverser, et la seule façon de le savoir est de regarder.

**C'est aussi pour cela que le notebook affiche le tableau de composition.** Il transforme une intuition
(« il pourrait y avoir un biais ») en un fait chiffré (« Q1 est à 52,9 % du TSLA »).

---

# Chapitre 11 — Le test z de différence de proportions

## 11.1 — Pourquoi un test

Les quintiles montrent un écart de 34,8 points. **Mais est-ce que cet écart pourrait venir du hasard ?**

Avec 549 observations par groupe, même deux groupes identiques donneraient un écart non nul. Le test
répond à : *« quelle est la probabilité d'observer un écart aussi grand si, en réalité, il n'y avait
aucune différence ? »*

## 11.2 — La construction

```
                 p5  −  p1
z  =  ────────────────────────────────
       ┌──────────────────────────┐
      \│ p̄ × (1 − p̄) × (1/n1 + 1/n5)
```

où `p̄` est la proportion combinée des deux groupes.

**Comment lire cette formule :**

- Le **numérateur** est ce qu'on observe : l'écart entre les deux proportions.
- Le **dénominateur** est ce à quoi on pourrait s'attendre **par hasard** — l'erreur type de l'écart.
- Le rapport `z` est donc : **« combien d'erreurs types représente l'écart observé ? »**

Un `z` de 2 signifie « l'écart vaut 2 fois ce que le hasard produirait typiquement » — c'est le seuil
usuel de significativité à 5 %.

## 11.3 — Les résultats

```
cible  pct_Q1  pct_Q5  n_par_groupe  ecart_pts      z   p_value
y_gap    39.3    74.1           549      34.79  11.63  0.00e+00
 y_oc    52.8    50.6           549      -2.19  -0.72  4.69e-01
 y_cc    44.1    61.9           549      17.85   5.93  3.11e-09
```

| Cible | Lecture |
|---|---|
| `y_gap` | z = **11,63** — l'écart vaut 11,6 fois ce que le hasard produirait. Incontestable. |
| `y_oc` | z = **−0,72** — dans la marge du hasard. **Aucun signal.** |
| `y_cc` | z = **5,93** — significatif mais plus faible |

## 11.4 — La vérification de cohérence interne

Le résultat sur `y_cc` est une **preuve de cohérence** qu'il faut savoir expliquer.

Puisque `ret_cc = gap composé avec ret_oc`, et que le signal est dans le gap mais pas dans la séance,
l'effet sur `ret_cc` doit être **positif mais plus faible** que sur le gap.

```
gap    : +34,8 points
ret_cc : +17,8 points      <- environ la moitié
ret_oc :  −2,2 points
```

**C'est exactement ce qu'on observe.** Si `ret_cc` avait montré un effet plus fort que `gap`, il y aurait
eu une incohérence à expliquer.

## 11.5 — Ce qu'est vraiment une p-value

**La p-value est le concept le plus mal compris de toute la statistique.** Voici la définition exacte :

> La p-value est la probabilité d'observer un résultat **au moins aussi extrême** que celui obtenu,
> **si l'hypothèse nulle était vraie**.

L'hypothèse nulle ici : *« il n'y a aucune différence entre Q1 et Q5 »*.

### Ce que la p-value n'est PAS

| Affirmation | Vrai ? |
|---|---|
| « p = 0,05 → il y a 5 % de chances que l'hypothèse nulle soit vraie » | ❌ **FAUX** |
| « p = 0,05 → il y a 95 % de chances que mon résultat soit vrai » | ❌ **FAUX** |
| « p < 0,05 → l'effet est important » | ❌ **FAUX** (ça ne dit rien de la taille) |
| « p = 0,05 → si l'hypothèse nulle était vraie, un tel résultat arriverait 5 fois sur 100 » | ✅ **VRAI** |

La p-value raisonne **en supposant l'hypothèse nulle vraie**. Elle ne peut donc pas dire quelle est la
probabilité que cette hypothèse soit vraie — ce serait circulaire.

### Le piège : significatif ≠ important

Avec un très grand échantillon, **n'importe quel effet minuscule devient significatif**. Une corrélation
de 0,001 sur un million d'observations aurait une p-value écrasante — et aucune valeur pratique.

**C'est pourquoi le notebook rapporte toujours trois choses ensemble :**

1. la **taille de l'effet** (34,8 points)
2. la **significativité** (z = 11,63)
3. l'**incertitude** (intervalle de confiance — chapitre suivant)

> **En 2016, l'American Statistical Association a publié une déclaration officielle** mettant en garde
> contre l'usage mécanique du seuil p < 0,05. C'est dire à quel point le sujet est sensible. Dans un
> mémoire, rapporter un intervalle de confiance vaut toujours mieux qu'une p-value seule.

---

# Chapitre 12 — Le bootstrap par blocs ⭐

## 12.1 — Le problème que personne ne voit

Tous les tests classiques — Pearson, z-test, Student — supposent que les observations sont
**indépendantes**.

**Tes observations ne le sont pas du tout.** Deux raisons :

### Dépendance temporelle (autocorrélation)

Le sentiment d'aujourd'hui ressemble à celui d'hier. Si TSLA fait l'objet d'une polémique lundi, elle
durera probablement jusqu'à mercredi. Les jours consécutifs ne sont pas des tirages indépendants.

### Dépendance transversale

Les 5 titres sont tous du Nasdaq, tous technologiques. Quand le marché baisse, ils baissent ensemble. Le
2 mars 2022, tu n'as pas 5 observations indépendantes — tu en as **une** répétée 5 fois avec des
variations.

## 12.2 — Pourquoi c'est grave

Le nombre **effectif** d'observations est bien inférieur à 2 740. Or l'erreur type décroît en `1/√n`.

Si le n effectif réel est 600 au lieu de 2 740, l'erreur type est sous-estimée d'un facteur
√(2740/600) ≈ **2,1**. Les intervalles de confiance sont deux fois trop étroits, et les p-values
beaucoup trop petites.

> **C'est l'erreur la plus courante dans les mémoires sur le sentiment**, et c'est une question classique
> de jury : *« vos observations sont-elles indépendantes ? »*

## 12.3 — Le bootstrap, l'idée générale

Le **bootstrap** (Efron, 1979) répond à : *« si je refaisais l'expérience, quelle variabilité
obtiendrais-je ? »*

**L'astuce.** On ne peut pas refaire l'expérience. Mais on peut **rééchantillonner** les données dont on
dispose : tirer au hasard, avec remise, un échantillon de même taille, et recalculer la statistique. En
répétant 1 000 fois, on obtient une **distribution** de la statistique — et donc son intervalle de
confiance.

> **Le nom vient de l'expression anglaise** *« to pull oneself up by one's bootstraps »* — se soulever en
> tirant sur ses propres lacets. L'idée est là : on estime l'incertitude en n'utilisant que les données
> elles-mêmes, sans hypothèse théorique.

## 12.4 — Pourquoi « par blocs »

Le bootstrap classique tire des **observations isolées** au hasard. Cela **détruit** la structure
temporelle : on pourrait tirer le lundi, puis le vendredi de trois mois plus tard, puis le mardi
d'avant…

Le **bootstrap par blocs** (Künsch, 1989) tire des **segments contigus** — ici, des blocs de 20 jours
consécutifs.

```
Bootstrap classique :   [lun] [ven+3mois] [mar-2ans] [jeu] ...    ← structure détruite
Bootstrap par blocs :   [20 jours consécutifs] [20 jours] [20 jours] ...  ← structure préservée
```

**En préservant les blocs, on préserve l'autocorrélation à l'intérieur des blocs.** L'intervalle de
confiance obtenu est donc **honnête** : plus large, et plus juste.

**Comment choisir la taille du bloc ?** Assez grand pour capturer la dépendance (ici, ~1 mois de bourse),
assez petit pour avoir beaucoup de blocs différents. 20 jours est un compromis standard.

## 12.5 — Les résultats

```
Cible Ticker   n     rho              IC95       conclusion
   gap   AAPL 548  0.3491 [+0.255 ; +0.414]     SIGNIFICATIF
   gap   AMZN 548  0.2432 [+0.160 ; +0.332]     SIGNIFICATIF
   gap   META 548  0.2086 [+0.146 ; +0.255]     SIGNIFICATIF
   gap   NVDA 547  0.1773 [+0.098 ; +0.238]     SIGNIFICATIF
   gap   TSLA 545  0.2917 [+0.187 ; +0.369]     SIGNIFICATIF

ret_oc   AAPL 548 -0.0820 [-0.149 ; -0.006]     SIGNIFICATIF
ret_oc   AMZN 548 -0.0116 [-0.099 ; +0.072] non significatif
ret_oc   META 548  0.0420 [-0.030 ; +0.123] non significatif
ret_oc   NVDA 547 -0.0168 [-0.078 ; +0.046] non significatif
ret_oc   TSLA 545  0.0161 [-0.044 ; +0.084] non significatif

Nombre de titres significatifs sur 5 :
  gap       5
  ret_cc    5
  ret_oc    1
```

### Comment lire un intervalle de confiance

`[+0,255 ; +0,414]` pour AAPL se lit : *« les données sont compatibles avec une vraie corrélation comprise
entre 0,255 et 0,414 »*.

**La règle de décision est visuelle :** si l'intervalle **ne contient pas zéro**, l'effet est
significatif.

**Pourquoi c'est mieux qu'une p-value :** l'intervalle donne aussi l'**amplitude plausible** de l'effet.
Une p-value dit seulement « ce n'est probablement pas zéro ». Un intervalle dit « c'est probablement entre
0,26 et 0,41 » — ce qui est bien plus utile.

### Le résultat sur AAPL / ret_oc : à savoir expliquer

AAPL est le seul titre où la séance est « significative » — et le coefficient est **négatif** (−0,082),
avec un intervalle qui frôle zéro : `[−0,149 ; −0,006]`.

**Deux interprétations à présenter honnêtement :**

1. **Une légère réversion.** Après une ouverture poussée par un sentiment très positif, le prix rend une
   petite partie du mouvement pendant la séance. C'est cohérent avec une **surréaction à l'ouverture**,
   phénomène documenté.

2. **Un faux positif.** Avec 5 titres × 3 cibles = 15 tests, la probabilité d'obtenir au moins un
   « significatif » par hasard au seuil de 5 % est de 1 − 0,95¹⁵ ≈ **54 %**. Il est donc probable qu'au
   moins un test ressorte par pur hasard.

**La bonne formulation en soutenance :** *« un seul titre sur cinq montre un effet sur la séance, de signe
négatif et à la limite de la significativité ; compte tenu du nombre de tests effectués, nous le traitons
comme une hypothèse à retester plutôt que comme un résultat. »*

C'est le problème des **comparaisons multiples**, et le reconnaître est une marque de rigueur.

---

# Chapitre 13 — Le Spearman : tester la monotonie

## 13.1 — Pearson vs Spearman

| | Pearson | Spearman |
|---|---|---|
| Travaille sur | les **valeurs** | les **rangs** |
| Détecte | les relations **linéaires** | les relations **monotones** |
| Sensible aux extrêmes | **oui** | non |

**Le Spearman, c'est simplement le Pearson calculé sur les rangs.**

```
Valeurs :  2,  5,  9,  100        ->  rangs : 1, 2, 3, 4
```

La valeur 100, aberrante, devient simplement « le 4ᵉ ». C'est ce qui rend le Spearman **robuste**.

**Ce qu'est une relation monotone :** qui va toujours dans le même sens, sans forcément être une droite.

```
X :  1    2    3    4    5
Y :  1    4    9   16   25        (Y = X²)

Pearson  = 0,98   (presque linéaire sur cet intervalle)
Spearman = 1,00   (PARFAITEMENT monotone)
```

## 13.2 — L'usage ici

```
AAPL  : rho = +0.900   |  Q1 = 31.8 %  ->  Q5 = 72.7 %
AMZN  : rho = +0.900
META  : rho = +0.821
NVDA  : rho = +1.000
TSLA  : rho = +1.000

Moyenne des rho : +0.924
Titres à rho > 0 : 5 / 5
```

On teste : *« le % de gaps positifs croît-il régulièrement de Q1 à Q5 ? »*

Un ρ de +1,000 (NVDA, TSLA) signifie une **monotonie parfaite** : chaque quintile est strictement
au-dessus du précédent. Pour META (+0,821), le décrochage de Q3 casse légèrement l'ordre.

## 13.3 — Le piège absolu : ne PAS reporter la p-value

```
NE PAS reporter la p-value de ce test dans le mémoire (n = 5 points).
```

**Pourquoi.** Ce test porte sur **5 points** — les 5 moyennes de quintiles. Avec n = 5 :

- il n'existe que 5! = **120** permutations possibles ;
- la plus petite p-value **atteignable** par un test exact est donc **1/120 ≈ 0,0083**.

Toute p-value inférieure est **mathématiquement impossible**. Elle proviendrait d'une approximation
(scipy utilise une loi de Student) dont la statistique **diverge** quand ρ = 1 :

```
             ┌─────────┐
             │  n − 2  │
t  =  rho ×  │ ─────── │       ->  quand rho = 1, le dénominateur est 0
            \│  1−rho² │           et t part à l'infini
```

**Plus fondamentalement**, ce test jette 2 740 observations pour n'en garder que 5 déjà moyennées. Il perd
99,8 % de l'information.

> **Le rôle du Spearman ici est purement descriptif** : montrer que la relation est **monotone**. La
> significativité vient du z-test (ch. 11) et du bootstrap (ch. 12), qui utilisent toutes les
> observations.
>
> **Savoir quand un test est approprié — et le dire — est aussi important que savoir le calculer.**

---

# Chapitre 14 — Les lags : la preuve d'absence de fuite ⭐

**C'est le test le plus important du notebook pour la crédibilité du travail.**

## 14.1 — L'idée

On décale le sentiment de −3 à +5 jours et on recalcule la corrélation avec le gap du jour J.

```
lag = +1  ->  on utilise le sentiment d'HIER pour expliquer le gap d'aujourd'hui
lag =  0  ->  le sentiment de la nuit qui précède l'ouverture       <- la relation étudiée
lag = −1  ->  on utilise le sentiment de DEMAIN pour expliquer le gap d'aujourd'hui  (!)
```

## 14.2 — Les trois conditions d'un signal propre

| Condition | Ce qu'on doit observer | Ce que ça prouve |
|---|---|---|
| **1** | lag 0 : corrélation forte | il y a bien un signal |
| **2** | lags **négatifs** ≈ 0 | **pas de fuite** — les fenêtres sont bien alignées |
| **3** | lags **positifs** ≈ 0 | l'information est incorporée immédiatement |

### Pourquoi la condition 2 est la plus importante

**Le sentiment de demain ne peut pas causer le gap d'aujourd'hui.** C'est logiquement impossible.

Donc si on trouvait une forte corrélation à lag −1, cela signifierait une **erreur d'alignement** :
décalage de fuseau, messages rattachés au mauvais jour de bourse, décalage d'un jour dans le code. Une
fuite d'information qui invaliderait tout le mémoire.

**C'est un test de falsification** au sens de Popper : on cherche activement à **réfuter** son propre
résultat. Si le test passe, la confiance augmente énormément.

### Pourquoi la condition 3 compte aussi

Si le signal persistait 24h, il existerait un arbitrage évident que personne n'aurait exploité — beaucoup
plus suspect qu'informatif. Sa disparition rapide est la **signature de l'efficience**.

## 14.3 — Les résultats

```
Cible     gap  ret_cc  ret_oc
lag
-3     0.0279  0.0320  0.0188
-2     0.0296  0.0384  0.0256
-1     0.0479  0.1375  0.1396
 0     0.1572  0.0933 -0.0103
 1    -0.0098 -0.0241 -0.0230
 2    -0.0073 -0.0079 -0.0049
 3    -0.0227 -0.0137  0.0013
 5    -0.0124 -0.0009  0.0085

VERDICT
  rho(lag 0) sur le gap                = +0.1572
  |rho| maximal sur les lags NÉGATIFS  = 0.0479
  rapport                              = 0.30
  [OK] Aucune fuite détectée.
```

### Sur la colonne `gap` : les trois conditions sont réunies

- lag 0 : **+0,157** — fort
- lags négatifs : maximum **0,048** — trois fois plus petit
- lags positifs : entre −0,023 et −0,007 — nul

## 14.4 — La ligne à savoir expliquer : lag −1 sur `ret_oc` = 0,1396

Regarde la colonne `ret_oc` : à lag −1, la corrélation vaut **+0,1396** — plus forte que tout ce qu'on
observe à lag 0 !

**Est-ce une fuite ?** Non. C'est **la preuve la plus élégante du chapitre 7.**

**Ce que dit ce chiffre :** le sentiment de la nuit **qui suit** le jour J est corrélé au rendement de
séance du jour J. Autrement dit :

> *« Ce que les gens écrivent le soir dépend de ce que le prix a fait pendant la journée. »*

C'est **le sentiment qui réagit au prix**, pas l'inverse. Exactement le mécanisme qui rendait
`mu_mkt → ret_oc = 0,203` inexploitable.

**Cette ligne confirme donc, de façon indépendante, la décision d'exclure les fenêtres contemporaines.**
Elle mérite d'être commentée dans le mémoire — c'est le genre de détail qui montre qu'on a vraiment
compris ses données.

## 14.5 — La précision de vocabulaire à maîtriser

> **« Lag 0 » n'est pas « contemporain » au sens d'une fuite.**
>
> `mu_night_full` du jour J se ferme à 9h30, et `gap` du jour J se forme à 9h30. La relation va donc de
> « juste avant » vers « juste après ».
>
> **Il faut le dire explicitement dans le mémoire**, sinon un lecteur pressé croira à un problème.

*(Nuance signalée dans le verdict général : la fenêtre `pre` recouvre la séance de pré-marché, ce qui rend
la relation plus « simultanée » qu'il n'y paraît. Statistiquement le test est valide ; économiquement,
c'est ce qui empêche de trader le signal.)*

---

# Chapitre 15 — Modèles emboîtés et incrément de R²

## 15.1 — Le changement de question

Jusqu'ici on cherchait à prédire une **direction**. Ici on change : peut-on prédire l'**amplitude** ?

| | Direction | Amplitude |
|---|---|---|
| On prédit | le **signe** du rendement | la **taille** du mouvement |
| Arbitrable ? | oui, donc arbitré | difficilement (il faut des options) |
| Persistance | quasi nulle | **forte** |
| R² typique | 0,001 – 0,01 | **0,3 – 0,6** |

**Pourquoi la volatilité se prédit et pas la direction.** Si la direction était prévisible, tout le monde
achèterait et le prix s'ajusterait instantanément. La volatilité, elle, ne peut pas être « arbitrée
away » : elle est une propriété du processus, pas une opportunité de profit direct.

## 15.2 — La bonne question, et la mauvaise

❌ *« L'attention corrèle-t-elle avec la volatilité ? »* → oui, trivialement. Les jours agités font parler.
Cette corrélation ne prouve rien.

✅ *« L'attention apporte-t-elle de l'information **au-delà de la volatilité de la veille** ? »*

## 15.3 — La technique : les modèles emboîtés

Deux modèles sont **emboîtés** si l'un est un cas particulier de l'autre — si le petit s'obtient en
mettant certains coefficients du grand à zéro.

```
[M0] amplitude ~ effets fixes ticker
[M1] amplitude ~ effets fixes + volatilité passée
[M2] amplitude ~ effets fixes + volatilité passée + attention        <- M1 emboîté dans M2
[M3] amplitude ~ ... + désaccord
```

On regarde **combien de R² chaque ajout apporte**.

### Ce qu'est le R²

```
                     variance expliquée par le modèle
R²  =  ────────────────────────────────────────────────
                     variance totale de la cible
```

C'est la **part de la variabilité expliquée**. R² = 0,49 signifie « le modèle explique 49 % de la
variabilité de l'amplitude ».

### Le piège du R² et la correction

**Ajouter n'importe quelle variable augmente toujours le R²**, même une variable purement aléatoire. Avec
autant de variables que d'observations, on atteint R² = 1 sans rien avoir appris.

D'où le **R² ajusté**, qui pénalise le nombre de variables :

```
R²ajusté = 1 − (1 − R²) × (n − 1) / (n − k − 1)      k = nombre de variables
```

Si une variable n'apporte rien, le R² ajusté **baisse**.

## 15.4 — Les résultats

```
[M0] effets fixes ticker seuls              R2 = 0.2271   R2ajusté = 0.2260
[M1] + volatilité passée   <-- RÉFÉRENCE    R2 = 0.4876   R2ajusté = 0.4865
[M2] + attention anormale nocturne          R2 = 0.5109   R2ajusté = 0.5096
[M3] + désaccord (sd du sentiment)          R2 = 0.5112   R2ajusté = 0.5097

  Apport de la volatilité passée   (M1 − M0) : +0.2605
  Apport de l'attention anormale   (M2 − M1) : +0.0233
  Apport du désaccord              (M3 − M2) : +0.0003

Test de Fisher emboîté M1 vs M2 : F = 127.67, p = 5.93e-29
```

### Comment lire ces chiffres

**M0 → M1 : +0,26.** La volatilité passée explique 26 points de R² supplémentaires. C'est le
**regroupement de volatilité** de Mandelbrot : un jour agité suit un jour agité. Effet massif et attendu.

**M1 → M2 : +0,023.** L'attention nocturne ajoute 2,3 points. **Petit en valeur absolue, mais :**

1. la référence est déjà excellente (48,8 %) — ajouter à un bon modèle est difficile ;
2. le test de Fisher donne **F = 127,67, p = 6 × 10⁻²⁹** — l'apport est systématique, pas fortuit ;
3. le R² ajusté **monte aussi** (0,4865 → 0,5096) — ce n'est pas de la sur-paramétrisation.

**M2 → M3 : +0,0003.** Le désaccord n'apporte **rien**. Et c'est un résultat en soi.

## 15.5 — Le test de Fisher emboîté

**La question :** l'amélioration du R² est-elle plus grande que ce que le hasard produirait en ajoutant
une variable quelconque ?

```
        ( R²grand − R²petit ) / (nombre de variables ajoutées)
F  =  ───────────────────────────────────────────────────────────
              ( 1 − R²grand ) / ( n − k − 1 )
```

**Numérateur** : ce qu'on gagne, par variable ajoutée.
**Dénominateur** : ce qui reste inexpliqué, par degré de liberté.

Si F est grand, le gain dépasse largement le bruit. Ici **F = 127,67** : le gain est 128 fois supérieur au
bruit typique.

## 15.6 — Les coefficients, et le résultat qui surprend

```
                  Coef.  Std.Err.       t   P>|t|
log_ampl_lag1    0.2306    0.0227  10.1617  0.0000
log_ampl_ma5     0.4858    0.0297  16.3691  0.0000
nabn_night_full  0.1351    0.0120  11.2529  0.0000
sd_night_full    0.2217    0.1749   1.2675  0.2051     <- NON significatif
```

**`nabn_night_full` : coefficient +0,135, t = 11,25.** Une unité d'attention anormale supplémentaire
augmente le log de l'amplitude de 0,135 — soit environ **+14 % d'amplitude**. Massivement significatif.

**`sd_night_full` : p = 0,205 — non significatif.**

**C'est un résultat qu'il faut reporter, pas cacher :**

> Ce qui compte n'est pas que les gens soient **en désaccord**, c'est qu'ils soient **nombreux à parler**.

Le volume d'attention prédit la volatilité ; la dispersion des opinions n'apporte rien de plus une fois le
volume pris en compte. C'est une contribution empirique intéressante — la littérature sur le désaccord
(Miller 1977) suggérait l'inverse.

**Une variable testée et rejetée est une information.** Un mémoire qui ne rapporte que les variables qui
marchent est un mémoire suspect.

---

# Chapitre 16 — Les régimes de marché

## 16.1 — Pourquoi découper la période

2020-2022 n'est pas une période homogène. Elle contient un krach, un rebond historique, une bulle
spéculative et un retournement monétaire.

**Un signal qui n'existerait que pendant un seul épisode ne serait pas un signal, mais un accident.**

## 16.2 — Le découpage

| Régime | Période | Ce qui s'y passe |
|---|---|---|
| Krach COVID | 02/01 → 23/03/2020 | chute de 34 % du S&P en 33 jours |
| Reprise / liquidité | 24/03 → 31/12/2020 | QE massif, rebond en V |
| Euphorie retail | 01/01 → 30/06/2021 | GameStop, meme stocks, pic Robinhood |
| Plateau / rotation | 01/07 → 31/12/2021 | fin du rallye, rotation sectorielle |
| Resserrement Fed | 01/01 → 04/03/2022 | pivot monétaire, correction du Nasdaq |

> **Une précaution à écrire dans le mémoire :** ces régimes sont définis **ex post**, avec des dates
> connues aujourd'hui. C'est acceptable pour une analyse **descriptive**, mais il faut préciser qu'ils ne
> sont **pas** utilisés comme variable explicative dans les modèles — sinon ce serait une fuite.

## 16.3 — Les résultats

```
             Regime   n  rho_gap          IC95_gap  rho_seance  fiable
        Krach COVID 280    0.192 [+0.077 ; +0.302]      -0.026     OUI
Reprise / liquidité 985    0.058 [-0.005 ; +0.120]      -0.037 fragile
    Euphorie retail 620    0.157 [+0.080 ; +0.233]       0.024     OUI
 Plateau / rotation 640    0.215 [+0.140 ; +0.288]       0.023     OUI
   Resserrement Fed 211    0.281 [+0.152 ; +0.401]      -0.071     OUI
```

**Quatre régimes sur cinq sont significatifs.** Et la colonne `rho_seance` reste collée à zéro partout —
la même conclusion, répétée cinq fois.

### Le régime « fragile » : à reporter honnêtement

Avril → décembre 2020 : ρ = 0,058, intervalle `[−0,005 ; +0,120]` qui **touche zéro**.

**Interprétation plausible.** Pendant le rebond en V post-COVID, tout montait quoi qu'il arrive. Le marché
était dominé par un facteur commun massif (l'injection de liquidité), et le sentiment individuel se noyait
dedans.

**Ne pas masquer ce résultat.** Le reporter et l'interpréter est un point de discussion intéressant, pas
une faiblesse. Un mémoire où tout est significatif partout est un mémoire dont on se méfie.

### La tendance intéressante

```
Krach COVID          0.192
Reprise              0.058
Euphorie retail      0.157
Plateau              0.215
Resserrement Fed     0.281      <- le plus fort
```

Le signal est **le plus fort dans le régime le plus récent et le plus tendu**. C'est rassurant pour la
validité externe : le signal ne s'affaiblit pas avec le temps, et il ne dépend pas de l'épisode meme
stocks.

## 16.4 — L'intervalle de confiance de Fisher

Une corrélation est bornée entre −1 et +1 : sa distribution n'est **pas symétrique**, surtout près des
bornes. On ne peut donc pas construire l'intervalle directement.

**La transformation z de Fisher** règle le problème :

```
z  =  arctanh(rho)  =  ½ × ln( (1+rho) / (1−rho) )
```

Cette transformation « étire » l'intervalle [−1, +1] vers tout l'axe réel, et rend `z` approximativement
**normal**, avec un écart-type simple :

```
écart-type de z  =  1 / racine(n − 3)
```

On construit alors l'intervalle sur `z`, puis on revient en arrière avec `tanh`.

```
IC sur z      :  z ± 1,96 / racine(n−3)
IC sur rho    :  tanh( borne inférieure )  ,  tanh( borne supérieure )
```

**C'est pourquoi les intervalles ne sont pas symétriques autour de ρ.** Regarde le krach COVID :
ρ = 0,192, intervalle `[0,077 ; 0,302]` — 0,115 en dessous, 0,110 au-dessus. Léger, mais réel.

### La colonne « fiable » : pourquoi elle existe

```python
"OUI" if (len(s) >= 60 and lo * hi > 0) else "fragile"
```

Deux conditions :

1. **au moins 60 observations** — en dessous, l'intervalle est si large qu'il ne veut rien dire ;
2. **l'intervalle ne contient pas zéro** — `lo × hi > 0` teste que les deux bornes ont le même signe.

**Le rôle de cette colonne est d'empêcher la sur-interprétation.** Sans elle, on pourrait être tenté de
commenter le 0,058 du régime « Reprise » comme s'il s'agissait d'un résultat.

---

# Chapitre 17 — Récapitulatif

## 17.1 — Les 12 idées à retenir

| # | Idée | Chapitre |
|---|---|---|
| **1** | **L'EDA vient avant les modèles.** Aucun modèle ne peut extraire une information qui n'existe pas. | 0 |
| **2** | **Vérifier avant d'analyser.** Une identité comptable vraie à 10⁻¹⁶ valide toute la chaîne de calcul. | 2 |
| **3** | **En finance, l'écart-type dépasse la moyenne de 20 fois.** Le rapport signal/bruit est catastrophique — d'où ρ = 0,15 comme « bon » résultat. | 3 |
| **4** | **Moyenne ≫ médiane = loi log-normale.** Passer au log avant tout modèle linéaire. | 4 |
| **5** | **La régression fallacieuse** : deux séries tendancielles paraissent corrélées sans lien aucun. | 5 |
| **6** | **La corrélation ne voit que les droites**, ne dit rien de la causalité, et craint les extrêmes. | 6 |
| **7** | **Une fenêtre n'est prédictive que si elle ferme avant que la cible ne se forme.** ⭐ | 7 |
| **8** | **Les variables liées par construction créent une colinéarité** qui rend les coefficients absurdes (VIF). | 8 |
| **9** | **Les quintiles ne supposent aucune forme** et rendent le résultat lisible par tous. ⭐ | 9 |
| **10** | **Paradoxe de Simpson** : toujours vérifier groupe par groupe avant d'agréger. | 10 |
| **11** | **Une p-value ne dit pas la probabilité que l'hypothèse soit vraie.** Préférer l'intervalle de confiance. | 11 |
| **12** | **Les observations financières ne sont pas indépendantes** → bootstrap par blocs. ⭐ | 12 |

Et le plus important :

| **13** | **Chercher activement à réfuter son propre résultat** (lags négatifs, falsification). C'est ce qui distingue un travail scientifique d'un exercice technique. ⭐ | 14 |

## 17.2 — Les résultats du notebook 04, en une page

```
mu_night_full  ->  gap d'ouverture   :  rho = +0.1572     ✅ signal
mu_night_full  ->  séance            :  rho = −0.0103     ❌ rien
mu_night_full  ->  close-close       :  rho = +0.0933     ✅ intermédiaire (cohérent)

Écart Q5 − Q1 sur le GAP     : +34.8 points   (z = 11.63)
Écart Q5 − Q1 sur la SÉANCE  :  −2.2 points   (z = −0.72, p = 0.47)

Monotonie             : 5 titres sur 5, Spearman moyen +0.924
Bootstrap par blocs   : 5 titres sur 5 significatifs pour le gap, 1 sur 5 pour la séance
Lags négatifs         : max 0.048 contre 0.157 au lag 0  ->  pas de fuite
Régimes               : 4 sur 5 significatifs
Attention -> risque   : +0.023 de R² au-delà de la volatilité passée (F = 128)
```

## 17.3 — Les cinq phrases pour la soutenance

1. « L'analyse exploratoire précède la modélisation : elle sert à **choisir la cible**, pas à prédire.
   C'est elle qui a révélé que le signal était dans le gap et non dans la séance. »

2. « Nous distinguons explicitement les fenêtres **prédictives** des fenêtres **contemporaines**. Les
   corrélations les plus fortes du tableau brut sont contemporaines : elles mesurent la réaction du
   sentiment au prix, et sont exclues. »

3. « L'analyse par quintiles est **non paramétrique** : elle ne suppose aucune forme de relation. Elle
   montre un écart de 34,8 points sur le gap et de −2,2 points sur la séance, avec les mêmes données. »

4. « Les observations n'étant ni indépendantes dans le temps ni entre titres, l'incertitude est estimée
   par **bootstrap par blocs**, qui préserve l'autocorrélation. Cinq titres sur cinq sont significatifs
   pour le gap, un sur cinq pour la séance. »

5. « Le test des **décalages négatifs** vérifie que le sentiment futur ne prédit pas le passé. Le rapport
   est de 0,30 : aucune fuite d'information. »

---

## Références

- Tukey, J. (1977). *Exploratory Data Analysis*. Addison-Wesley. — la démarche EDA
- Granger, C. & Newbold, P. (1974). *Spurious Regressions in Econometrics*. Journal of Econometrics
- Simpson, E. (1951). *The Interpretation of Interaction in Contingency Tables*. JRSS-B
- Bickel, P. et al. (1975). *Sex Bias in Graduate Admissions: Data from Berkeley*. Science
- Efron, B. (1979). *Bootstrap Methods: Another Look at the Jackknife*. Annals of Statistics
- Künsch, H. (1989). *The Jackknife and the Bootstrap for General Stationary Observations*. Annals of Statistics
- Fisher, R. A. (1915). *Frequency distribution of the values of the correlation coefficient*. Biometrika
- Miller, E. (1977). *Risk, Uncertainty, and Divergence of Opinion*. Journal of Finance
- Hong, H. & Stein, J. (1999). *A Unified Theory of Underreaction, Momentum Trading and Overreaction*. Journal of Finance
- Wasserstein, R. & Lazar, N. (2016). *The ASA Statement on p-Values*. The American Statistician

---

*Prochain cours : notebook 05 — la construction des variables, le découpage temporel et les quatre tests
anti-fuite.*
