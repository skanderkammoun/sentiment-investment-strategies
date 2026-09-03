# 📖 Explication simple : pourquoi mes modèles ne marchent pas, et comment réparer

*Document pédagogique — PFE Kammoun Skander — 2 septembre 2026*

---

# PARTIE 1 — Comment bouge le prix d'une action dans une journée

Pour comprendre le problème, il faut d'abord bien voir **une chose** : dans une journée,
le prix d'une action ne bouge pas d'un seul bloc. Il bouge en **deux morceaux séparés**.

La Bourse américaine est ouverte de **9h30 à 16h00** (heure de New York). Le reste du temps,
elle est **fermée**. Mais les gens, eux, ne dorment pas : ils écrivent des tweets, les
entreprises publient leurs résultats, les journaux sortent des articles… **toute la nuit**.

Donc dans une journée, il y a :

### Morceau n°1 : le GAP (le « saut de la nuit »)
C'est l'écart entre **la clôture d'hier (16h00)** et **l'ouverture d'aujourd'hui (9h30)**.

Pendant ces 17h30, **personne ne peut acheter ni vendre** (marché fermé). Mais l'information
s'accumule. Quand le marché rouvre le matin, le prix **saute d'un coup** pour intégrer tout
ce qui s'est dit pendant la nuit.

```
gap = (Ouverture d'aujourd'hui / Clôture d'hier) − 1
```

### Morceau n°2 : la SÉANCE (le mouvement intra-journalier)
C'est le mouvement **pendant** que le marché est ouvert, de 9h30 à 16h00.

```
séance = (Clôture d'aujourd'hui − Ouverture d'aujourd'hui) / Ouverture d'aujourd'hui
```

C'est **exactement ta variable `StockChange`**.

### Le rendement total de la journée
```
rendement du jour ≈ gap + séance
```

---

## Un exemple réel, tiré de TES données : Apple, lundi 16 mars 2020

| Moment | Prix |
|---|---|
| Vendredi 13 mars, clôture (16h00) | **67,05 $** |
| Lundi 16 mars, ouverture (9h30) | **58,36 $** |
| Lundi 16 mars, clôture (16h00) | **58,42 $** |

Pendant le week-end, c'est la panique COVID. Dans ton corpus StockTwits, **1 807 tweets** ont
été publiés sur AAPL entre la clôture de vendredi et l'ouverture de lundi, avec un sentiment
très négatif (`mu_night_full = −0,024`, un des plus négatifs de tout l'historique).

Résultat :

- **Le GAP : −12,96 %.** Le prix s'est effondré **avant que quiconque puisse échanger**.
- **La SÉANCE : +0,11 %.** Autrement dit : **rien du tout**.

👉 **Toute l'information de la panique est passée dans le gap. La séance n'a rien fait.**

Autre exemple, dans l'autre sens — Apple, jeudi 9 janvier 2020 (sentiment nocturne parmi les
plus positifs de l'historique) : **gap = +1,34 %**, séance = +0,78 %. Là encore, le gros du
mouvement est dans le saut d'ouverture.

---

# PARTIE 2 — Ce que tu as demandé à ton modèle (et pourquoi c'était perdu d'avance)

Dans ton `README.md`, tu écris :

> *« Pour isoler les réactions intraday nettes et **éliminer le bruit nocturne** (gaps
> d'ouverture), le modèle utilise : StockChange = (Close − Open) / Open »*

Tu as donc **volontairement jeté le morceau n°1 (le gap)** pour ne garder que le morceau n°2
(la séance). L'intention était bonne : tu voulais enlever du bruit.

**Mais le gap n'était pas du bruit. C'était le signal.**

Voilà pourquoi. Regarde **quand** tes textes sont publiés (compté sur tes 3,7 millions de tweets) :

| Quand ? | Nombre de tweets | Part |
|---|---|---|
| Avant l'ouverture (00h00 → 9h30) | 671 910 | 18 % |
| Pendant la séance (9h30 → 16h00) | 2 088 555 | 56 % |
| Après la clôture (16h00 → minuit) | 950 868 | 26 % |

**44 % de tes textes sont publiés quand le marché est fermé.** Ces textes-là expliquent le
**gap**. Et le gap, tu l'as supprimé de ta cible.

### Trois analogies pour bien fixer l'idée

**Analogie 1 — Le match de foot.**
Tous les buts sont marqués dans les 80 premières minutes. Tu essaies de deviner le score
final en ne regardant **que les 10 dernières minutes**. Tu n'y arriveras jamais, non pas
parce que tu es mauvais, mais parce que **tu ne regardes pas le moment où ça s'est joué**.

**Analogie 2 — La pluie.**
La météo du soir annonce un orage cette nuit. Le matin, le sol est **déjà** trempé.
Tu demandes à ton modèle : *« avec la météo d'hier soir, dis-moi si le sol va sécher entre
9h et 16h »*. La météo d'hier soir prédit très bien **que le sol soit mouillé au réveil**
(= le gap). Elle ne dit rien sur ce qui se passe **après** le réveil (= la séance).

**Analogie 3 — L'ascenseur.**
Le sentiment nocturne, c'est le bouton qu'on appuie pendant la nuit. Le gap, c'est
l'ascenseur qui monte d'un coup à 9h30. La séance, c'est ce qui se passe **une fois arrivé
à l'étage**. Tu mesures le bouton, et tu regardes le couloir de l'étage. Les deux n'ont
pas de rapport direct.

---

# PARTIE 3 — La preuve chiffrée, dans TES données

J'ai classé les 2 192 journées de ton corpus (4 tickers × 548 jours) en **5 groupes**, du
sentiment nocturne le plus négatif au plus positif. Puis j'ai regardé ce qui s'est passé
ensuite.

| Groupe (sentiment de la nuit) | GAP moyen | % de jours où le **gap** monte | SÉANCE moyenne | % de jours où la **séance** monte |
|---|---|---|---|---|
| **Q1 — très négatif** | **−0,80 %** | **37,6 %** | +0,20 % | 54,2 % |
| Q2 — négatif | −0,00 % | 53,4 % | +0,00 % | 48,4 % |
| Q3 — neutre | +0,40 % | 63,6 % | −0,06 % | 49,7 % |
| Q4 — positif | +0,49 % | 64,2 % | +0,05 % | 49,5 % |
| **Q5 — très positif** | **+0,63 %** | **72,7 %** | +0,15 % | 51,0 % |

**Lis les deux colonnes en gras :**

- Colonne « gap » : on passe de **37,6 %** à **72,7 %**. C'est un écart de **35 points**.
  👉 **C'est énorme. Le sentiment de la nuit prédit très bien le saut d'ouverture.**

- Colonne « séance » : on passe de **54,2 %** à **51,0 %**. C'est **3 points**, et même dans
  le mauvais sens (le sentiment le plus négatif donne le plus de séances haussières !).
  👉 **C'est du hasard pur. Le sentiment de la nuit ne dit rien sur la séance.**

**Voilà, en une seule ligne, pourquoi tes modèles font MCC = 0,026 et AUC = 0,51 :
tu leur demandes de prédire la colonne de droite alors que toute l'information est
dans la colonne de gauche.**

Ce n'est **pas** un problème de modèle. Ce n'est **pas** un problème de LSTM ou de XGBoost.
Tu aurais mis n'importe quel modèle du monde, il aurait échoué de la même façon.

---

# PARTIE 4 — Le deuxième problème : tu n'avais presque pas de texte

Ton ancien dataset (2023-2026) contient 33 059 titres répartis sur 3 798 couples
(jour, ticker). Ça fait une moyenne de 8 textes par jour… mais la **moyenne ment**.
Voici la réalité :

| Ticker | Médiane de messages par jour |
|---|---|
| MSFT | **1,5** |
| AAPL, AMZN, GOOGL, JPM, META, TSLA | **2** |
| BRK-B | 3 |
| UNH | 5 |

Et surtout : **79 % des journées reposent sur 5 messages ou moins.**

### Analogie — le sondage électoral

Imagine qu'on te demande de prédire le résultat d'une élection :

- **Version « ancien dataset »** : tu interroges **2 personnes**. L'une dit « gauche »,
  l'autre dit « droite ». Ton résultat : 50/50. Le lendemain tu interroges 2 autres
  personnes : 100 % « gauche ». Ton indicateur saute dans tous les sens **sans aucun
  rapport avec la réalité**. Ce n'est pas une mesure, c'est du bruit.

- **Version « nouveau dataset StockTwits »** : tu interroges **900 personnes** (AAPL) ou
  **1 766 personnes** (TSLA) chaque jour. Là, ta mesure est stable et fiable.

En statistique, la précision d'une moyenne s'améliore en **√n** :
- avec n = 2 → précision ≈ 1,4
- avec n = 900 → précision ≈ 30

👉 **Ton nouveau corpus mesure le sentiment environ 20 à 30 fois plus précisément.**

C'est pour ça que ton nouveau dataset est une **excellente décision**. Tu as eu raison de
changer. Il fallait juste aussi changer la cible.

---

# PARTIE 5 — Ta question : « dois-je scraper les prix heure par heure ? »

## Ce que tu as en tête

Tu te dis : *« mon texte est à l'heure près, mes prix sont au jour. Ça ne colle pas.
Donc il faut que je descende mes prix à l'heure aussi. »*

C'est logique comme réflexe, mais **c'est l'inverse qu'il faut faire**.

## Pourquoi c'est l'inverse

### Analogie — la montre et le calendrier

Tu as une **montre** qui donne les secondes (= tes tweets horodatés) et un **calendrier**
qui donne les jours (= tes prix quotidiens).

Tu veux transformer le calendrier en montre. Mais **on ne peut pas inventer de
l'information qui n'existe pas**. En revanche, tu peux très facilement faire l'inverse :
**regarder ta montre et regrouper**.

C'est ce qu'on appelle **agréger par fenêtres** :

```
Tous les tweets entre 16h00 (hier) et 9h30 (aujourd'hui)  →  1 seul chiffre  →  prédit le GAP
Tous les tweets entre 9h30 et 10h00                        →  1 seul chiffre  →  prédit la séance
Tous les tweets entre 16h00 et minuit                      →  1 seul chiffre  →  prédit demain
```

Tu **ne perds rien**. Tu gardes toute la finesse de l'heure, mais tu la **ranges** pour
qu'elle corresponde exactement aux moments où le prix, lui, existe.

Et surtout : **tu passes de 1 cible à 3 cibles**, donc de 1 modèle à 3 modèles. Ton mémoire
devient plus riche, pas plus pauvre.

## Et si tu veux quand même les prix intraday ?

D'abord, sache que **yfinance ne peut pas le faire pour 2020-2022** :

| Intervalle demandé | Historique maximum disponible |
|---|---|
| `1m` (1 minute) | **30 jours** (et 7 jours par requête) |
| `1h` (1 heure) | **730 jours**, soit rien avant ~septembre 2024 |
| `1d` (1 jour) | **illimité** ✅ |

Donc pour 2020-2022 en intraday, il faut passer par un autre fournisseur :

| Fournisseur | Prix | Historique | Remarque |
|---|---|---|---|
| **Alpaca** | **gratuit** | 7+ ans | Le meilleur choix gratuit. Attention : sur le plan gratuit, les prix viennent de la place IEX seule (~2-3 % du volume total), donc les barres 1 minute sont un peu bruitées. Acceptable si tu agrèges en 30 minutes sur des grosses valeurs comme AAPL ou TSLA. |
| **Polygon.io** (Starter) | ~29 $/mois | 5 ans | Qualité professionnelle, prix consolidés. Le mieux si tu peux payer 1 ou 2 mois. |
| **FirstRate Data / Kibot** | achat unique (~50-150 $) | 15+ ans | Fichiers à télécharger une fois, pas d'API. Pratique pour un mémoire. |
| **Databento** | à l'usage | complet | Très propre mais facturé au volume. |

👉 **Mon conseil : ne fais pas ça maintenant.** Fais d'abord les solutions 1 à 4 ci-dessous
avec les données que tu as **déjà** (tu as tout ce qu'il faut, rien à collecter). Si tu as
encore du temps avant la soutenance, ajoute Alpaca en bonus.

---

# PARTIE 6 — Les solutions concrètes

## 🥇 SOLUTION 1 — Changer de cible : prédire le GAP *(la solution principale)*

**Ce que tu prédis :** est-ce que le prix va **ouvrir** plus haut que la clôture d'hier ?

```
cible  :  y_gap = 1 si (Open_aujourd'hui / Close_hier − 1) > 0, sinon 0
features:  sentiment de tous les tweets entre 16h00 hier et 9h30 aujourd'hui
           + volume de tweets, désaccord, et les valeurs des jours précédents
```

**Pourquoi ça va marcher :** c'est démontré plus haut — 37,6 % → 72,7 % de réussite entre
le groupe le plus négatif et le plus positif.

**La stratégie qui va avec :** j'achète à la clôture de 16h00 si le sentiment de la soirée
est très positif, je revends à l'ouverture le lendemain matin à 9h30. C'est une stratégie
réelle et connue, appelée **stratégie overnight**.

**Ce que tu dois surveiller :** attention aux jours de publication de résultats (earnings).
Ces soirs-là, les gens tweetent **parce que** le résultat vient de sortir — donc ce n'est pas
le sentiment qui prédit le prix, c'est l'annonce qui cause les deux. Il faut marquer ces
jours-là avec une variable indicatrice et vérifier que le signal tient **aussi** en dehors.

---

## 🥈 SOLUTION 2 — Garder ta cible actuelle, mais changer les prédicteurs

Tu ne veux pas abandonner `(Close − Open)/Open` ? Très bien, **garde-la**, mais alors il
faut la prédire avec le bon signal.

```
cible   :  y_séance = 1 si (Close − Open)/Open > 0
features:  sentiment de la PREMIÈRE DEMI-HEURE de séance (9h30 → 10h00)
           + sentiment de la nuit (comme contrôle)
```

L'idée : à 10h00 du matin, le gap a déjà eu lieu. Ce que les gens disent **entre 9h30 et
10h00** peut contenir de l'information sur le reste de la journée. Et là, tu prédis
seulement de 10h00 à 16h00, pas 9h30 à 16h00.

⚠️ **Important :** il est très possible que ça ne marche pas non plus, ou faiblement.
**Et ce n'est pas grave.** Au contraire :

> **Montrer que le gap est prévisible mais que la séance ne l'est pas, c'est un vrai
> résultat scientifique.** Ça veut dire que le marché intègre l'information publique
> dès l'ouverture — c'est une **vérification empirique de l'efficience semi-forte des
> marchés**. C'est un très bon chapitre de mémoire, bien meilleur qu'un modèle qui
> prédit tout à 51 %.

---

## 🥉 SOLUTION 3 — La cible « clôture à clôture »

```
cible   :  y_cc = 1 si (Close_aujourd'hui / Close_hier − 1) > 0
features:  sentiment de la nuit + sentiment de la première demi-heure
```

C'est le compromis : cette cible contient **le gap ET la séance**. Corrélation observée dans
tes données : **+0,11 à +0,23** selon le ticker. Moins fort que le gap seul, mais plus facile
à traduire en stratégie (on garde la position toute la journée).

---

## 🏅 SOLUTION 4 — L'angle actuariel : prédire le RISQUE, pas la direction

**C'est la solution que je te recommande le plus fortement pour un PFE d'actuariat**,
et personne ne te l'a proposée.

Prédire **la direction** d'un prix, c'est très difficile (c'est presque un pile ou face).
Prédire **la volatilité**, c'est beaucoup plus facile et beaucoup plus robuste — et c'est
**exactement le métier d'un actuaire** : mesurer le risque, pas parier sur le sens.

```
cible   :  volatilité du jour  =  (High − Low) / Open      (« amplitude »)
           ou : |rendement du jour|
features:  - le DÉSACCORD entre investisseurs  (l'écart-type du sentiment dans la nuit)
           - le VOLUME ANORMAL de messages     (log(nb tweets) − sa moyenne des 20 jours)
           - la polarisation                    (beaucoup de très positifs ET de très négatifs)
```

**L'intuition :** quand tout le monde est d'accord, il ne se passe rien. Quand les gens se
disputent violemment sur StockTwits, **le prix bouge fort** — peu importe dans quel sens.

C'est un résultat très solide dans la littérature, et ça débouche directement sur des
applications actuarielles concrètes :
- calcul de **VaR** conditionnelle au sentiment,
- **dimensionnement des positions** (réduire l'exposition quand le désaccord explose),
- **provisionnement** et mesure de risque de marché.

👉 Mon conseil : fais **Solution 1 + Solution 4**. Ça donne un mémoire complet :
*« le sentiment prédit la direction à l'ouverture, et il prédit le risque toute la journée »*.

---

## 🎁 SOLUTION 5 *(optionnelle, si tu as du temps)* — Les prix intraday

Avec Alpaca (gratuit), tu récupères les prix par tranche de 30 minutes pour 2020-2022, et
tu testes : *« le sentiment de la demi-heure t prédit-il le rendement de la demi-heure t+1 ? »*

C'est exactement la méthode de **Renault (2017, Journal of Banking & Finance)**, la référence
académique du domaine sur StockTwits. Ça ferait un excellent dernier chapitre.

Mais **seulement après** avoir fini les solutions 1 à 4.

---

# PARTIE 7 — Concrètement, quoi faire cette semaine

| Jour | Action | Fichier |
|---|---|---|
| **1** | Lancer la collecte des prix (NVDA manque dans tes données) | `src/data/collection/collecte_finance_2020_2022.py` ✅ écrit |
| **1** | Lancer la construction du panel par fenêtres | `src/data/traitement/build_panel_windows_2020_2022.py` ✅ écrit et **testé** |
| **2** | Refaire l'EDA sur les **3 cibles** (gap / séance / close-close) + graphiques par quintile | nouveau notebook `06_EDA_Windows.ipynb` |
| **3-4** | Modèle 1 (gap) : Logistic → RandomForest → LightGBM, validation walk-forward par dates | `07_Modeling_Gap.ipynb` |
| **5** | Modèle 4 (volatilité / risque) : régression sur le désaccord et le volume anormal | `08_Modeling_Risque.ipynb` |
| Semaine suivante | Backtest de la stratégie overnight avec frais (10 bps aller-retour) | `09_Backtesting.ipynb` |

**Les 2 scripts sont déjà écrits et fonctionnent.** Le panel a été généré et vérifié :
`data/processed/PANEL_SENTIMENT_WINDOWS_2020_2022.csv` (2 192 lignes × 77 colonnes).

---

# PARTIE 8 — Ce qu'il faut retenir en 5 phrases

1. **Le prix bouge en deux morceaux** : le saut de la nuit (gap) et la séance. Tu as jeté le premier.
2. **Ton texte est publié la nuit**, donc il explique le gap — pas la séance.
3. **Preuve dans tes données** : le sentiment nocturne fait passer le taux de gaps positifs de 37 % à 73 %, mais laisse la séance à 50 % (= hasard).
4. **Ton ancien corpus avait 2 messages par jour**, c'était impossible de mesurer quoi que ce soit. Le nouveau en a des centaines : très bonne décision.
5. **Tu n'as pas besoin de prix intraday.** Tu as besoin de changer de cible, et d'ajouter une cible « risque » qui est l'angle actuariel de ton PFE.
