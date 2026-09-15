\###########google scholar

\##############################################################



1\. Fiche d'Identité de l'ArticleTitre : Sentiment Analysis for Effective Stock Market Prediction.  Auteurs : Shri Bharathi et Angelina Geetha.  Université : B.S. Abdur Rahman University, située à Chennai, en Inde.  Année de publication : 2017.  2. La Problématique (Le défi)Les auteurs partent du principe que le marché boursier ne peut pas être deviné uniquement avec des chiffres. Leur objectif principal n'est pas seulement d'obtenir les meilleurs résultats possibles, mais surtout de minimiser les prédictions inexactes qui font perdre de l'argent aux investisseurs.

Leur problématique est donc : Comment prouver que les flux d'actualités (RSS) ont un impact direct sur la bourse, et comment combiner intelligemment l'humeur de ces actualités avec des indicateurs financiers traditionnels pour créer un système de prédiction fiable ?.  3. Les Données (La matière première)L'étude se concentre sur un environnement très spécifique :Données Financières : Ils ont étudié la Bourse d'Amman (Amman Stock Exchange - ASE) en Jordanie. Ils ont ciblé une entreprise spécifique : la banque Arab Bank (ARBK). Ils ont utilisé les prix historiques datant d'avril 2006.  Données Textuelles : Au lieu d'utiliser Twitter, ils ont utilisé des flux RSS (Rich Site Summary). Ce sont des fichiers XML qui permettent de récupérer automatiquement et sans "bruit" (sans spam) les gros titres de l'actualité financière sur des sites spécialisés (comme investing.einnews.com).  4. L'Approche Technique (Les Outils)L'originalité de cet article réside dans son architecture en deux branches parallèles qui se rejoignent à la fin :Branche 1 : L'Analyse du Sentiment (NLP)Ils nettoient le flux RSS, puis utilisent un "POS Tagger" pour repérer les noms et les adverbes.  Ils utilisent une approche basée sur un dictionnaire (WordNet) pour donner un score à chaque mot.  Ils appliquent leur propre algorithme, le SSS (Sentence level Sentiment Score), pour additionner les scores des mots et déduire si la phrase entière est Positive, Négative ou Neutre.  Branche 2 : L'Indicateur Boursier (Moving Average) \* Ils utilisent un outil mathématique très connu en finance : la Moyenne Mobile (Moving Average). L'équation utilisée pour calculer la moyenne mobile sur $n$ périodes est :

$F\_{t}=\\frac{A\_{t-1}+A\_{t-2}+A\_{t-3}+\\cdot\\cdot\\cdot+A\_{t-n}}{n}$   Ils calculent cette moyenne sur 5 jours, 10 jours et 15 jours.  La règle de décision : Si la moyenne à 5 jours est supérieure à celle de 10 jours, et que celle de 10 jours est supérieure à celle de 15 jours, alors l'indicateur financier dit "Positif" (l'action va monter).  La Fusion (Stock Market Prediction) :

La décision finale d'acheter ou de vendre n'est prise que si les deux branches sont d'accord. Si l'actualité RSS est Positive ET que la Moyenne Mobile est Positive, alors le système prédit une hausse certaine. Si l'une des deux branches n'est pas d'accord, le système reste Neutre.  5. Les Résultats (Le Verdict)Les auteurs ont comparé leur système avec des algorithmes classiques (comme les arbres de décision ID3 et C4.5).  Méthode utiliséePrécision (Accuracy)Arbre de décision ID3   46.69%Arbre de décision C4.5   47.49%Moyenne Mobile seule (sans texte)   64.32%Moyenne Mobile + Sentiment RSS (Leur système)   78.75%





\#################################################################

\##Article ecrit par Paraskevas Koukaras , Christina Nousi and Christos Tjortjis en 2022 publié a MDPI telecom







\## problematique : Comment fusionner efficacement des flux de données asynchrones (données financières vs flux de tweets textuels) tout en minimisant le bruit et le biais algorithmique des outils de NLP basiques ?



solution : Framework de classification binaire qui va predire si une action va uagmenter et deminuer



source utilisé : Twitter , Stock Twwets , Yahoo finanace







text blob : une biblio informatique qui lit un texte et lui donne une note de sentiment .

son role principal est de classer chaque tweet dans l'une de ces ces 3 categories : positif , negatif oun neutre





VADER: C'est un outil plus spécialisé concu pour analyser les donées des réseaux sociaux





====> la grande difference avec textBlob , il ne dit que un mesage est negatif ou positif il evalue aussi l'intensité de cette emotion

sooo Vader donne 4 notes : une note  negative , une note positive , u\_ne note neutre et unn score global







=====> les chercheurs ont voulu faire une competition entre ces deux outils .ils ont fait lire les memes données proven,nant de twitter et de StockTwits à Textblob et à VADER pour produisait le quel des outils

produisait les meilleurs résultats pour la prediction de laction



Fonctionnnement :





ces ddeux outils sont classiques et n'utilisent pas l'IA .

TextBolb et Vader sont des algoruthmes basées sur des lexiques et des regles .

c'est comme un correcteur qui utilise un dictionnnaire géant ou chaque mot posséde une "note" d'emotion.



les créaateurs de ces outils ont assigné des scores à des milliers de  mots  (par exemples benifices vaut +2  , faillite vaut -3 )



l'argorithme lit le message sur Twitter ou StockTwits et le deceoupe  mot par mot, il cherche chaque mot dans le dectionnaire et additionne les points pour donner une note global .





**maintenanat le plus de VADER PAR RAPPORT au TEXTBLOB :**



**Vadder est un peut plus intelligent que TEXTBLOB car il a des regles supplémentaires pour les réseaux sociaux. il repere les majuscules (BENIFICE aurra une note plus superieur que "benifice"), il analyse la ponctuation (les points dexclamation augmentent le score ) et il comprend les inversions (si tu ecris "pas bon" il va inverser la note de "bon "**







**##############que est ce qu'il fait les chercheurs iciii ???**







**ils associent VADER avec SVM donne des meilleurs resultat**



**## les limites de vadder : il se treompe dans les sarcasme  aussi ils ne comprennet pas en finanace**

**par exemple pour un twwet " le chommage s'effondre " VADDER va voir le mot seffondre (négatif ) et va donner une mauvaise note alors quen finanace la baisse du chomage est une tres bonne signe aussi ils interprete des mauvais données comme etand un bonne tweet**





**les chercheurs trouve un score de 76.3 % de F Score**

**===> ce score est le F score**





**pourquoi on utilise le F Score : car il ya un desequilibre , il ya naturellement plus de jours ou laction monte ("Acheter") que de jours ou elle baisse (Vendre) .**



si un alghorithme est stupide et decide de dire "Acheter" tous les jours sans reflechir , il aurra mathématiquement une bonne precision gloobal " accuracy " simplement par ce que le marché à tendance à monté . c'est un etriche statistique .pour empecher l'alghorithme de tricher sur des données desequilibre , les chercheurs exigeant l'utilisation du F-Score



**que est ce quon prend de cette article**



**on va utiliser l'equation pour mesurer la variation du priox de laction  Microsoft :
StockChange= (Close-Open ) / open**



**======> cette formule est fort car il calcule la rentabilité strictement pendant les heures ou la marché est ouvert .Elle bloque les mauvaises surprises et les sauts de prix qui arrivent la nuit quand la bourse est fermé**



* **on va utiliser VADER comme BAseline**

\###################################################2eme article techrxivv



Titre : Prediction of the Stock Market Based on Machine Learning and Sentiment Analysis.

Auteurs : Prajwal Jishtu, Harshil Prajapati, et le Dr. Jinan Fiaidhi.

Université : Lakehead University, située au Canada (Thunder Bay, Ontario).

Date de publication : Décembre 2022





La problématique est donc : Comment extraire intelligemment les sentiments cachés dans les vrais articles de presse économique, et quel est le meilleur algorithme informatique pour croiser ces textes avec les prix historiques afin de deviner la tendance du marché ?.







\##Data



Les auteurs separent  leurs données en deux blocs :Les données financières : Ils ont récupéré l'historique de 5 très grandes entreprises européennes (l'indice FTSE 100) : AstraZeneca, Unilever, HSBC, BP et GSK. Ils ont utilisé le site Yahoo Finance pour récupérer le prix d'ouverture, de clôture, le volume.



Les données textuelles (News) : Au lieu d'utiliser des petits tweets de particuliers, ils ont programmé des robots ("Web Scraping") pour aspirer des vrais articles de presse économique sur le site Investing.com.









4\. Les Outils et l'Approche TechniqueLeur pipeline (le cheminement de l'information) est un modèle que tu pourrais presque copier pour ton PFE :A. Le Nettoyage du Texte (Prétraitement)

Ils ont nettoyé les articles de presse en enlevant les mots inutiles (stop words) et la ponctuation. Ils ont utilisé deux techniques pour simplifier les mots :  Stemming : Couper la fin des mots pour garder la racine (ex: "programmation" devient "programm").  Lemmatisation : Une méthode plus intelligente qui remplace un mot par sa version du dictionnaire (ex: "mieux" devient "bien").  B. La Transformation du Texte en Mathématiques (Vecteurs)

L'ordinateur ne lit pas les lettres. Les auteurs ont utilisé trois méthodes pour transformer les mots en chiffres : le Bag of Words (compter combien de fois un mot apparaît), le Word2Vec (comprendre le sens du mot), et le TF-IDF (donner plus de poids aux mots rares et importants).  5. Les Modèles Prédictifs (Le "Cerveau")Les auteurs ont organisé une compétition entre 3 algorithmes de prédiction pour voir lequel était le meilleur:  ARIMA et SARIMA : Ce sont de vieux modèles mathématiques très connus en statistiques. Ils regardent uniquement la ligne du passé pour dessiner la ligne du futur.  LSTM (Long Short-Term Memory) : C'est la star de l'Intelligence Artificielle pour les séries temporelles (comme la bourse). C'est un réseau de neurones qui possède une "mémoire" : il est capable de se souvenir des événements importants qui se sont passés il y a longtemps, et d'oublier les choses inutiles.  6. Le Verdict et les RésultatsLa conclusion de l'article est sans appel :Les modèles statistiques classiques (ARIMA et SARIMA) font un travail correct si on veut deviner le prix pour demain (court terme), mais ils sont incapables de comprendre la bourse sur la durée.  Le modèle LSTM écrase la concurrence. Il réussit à prédire le marché avec une précision de 78.81% et produit l'erreur mathématique la plus faible (RMSE).



\###################Article
Titre : AI-Based Sentiment Analysis for Stock Market Prediction: A Systematic Literature Review.

&#x20;Auteurs : Fanyi Zhao et Tianxing Tang.



Universités : Stevens Institute of Technology (New Jersey, USA) et Middlebury Institute of International Studies (Californie, USA).  Date de publication : Mai 2026. C'est un document extrêmement récent et à la pointe de la technologie actuelle.





2\. La Problématique (Le constat d'échec de la recherche actuelle)Les auteurs partent d'un constat simple : la recherche sur l'intelligence artificielle appliquée à la bourse a explosé ces dix dernières années, passant des simples comptages de mots aux grands modèles de langage.

Cependant, il manque un cadre commun pour comparer toutes ces méthodes. La vraie problématique de l'article est donc : Parmi toutes les techniques d'IA existantes, quelles sont les sources de données et les algorithmes qui fonctionnent réellement pour prédire le marché, et quels sont les défis qui bloquent encore les chercheurs ?.  3. Les Données (Où cherchent-ils l'information ?)Les auteurs ont épluché 87 études publiées entre 2011 et 2024. Ils ont classé les sources de texte utilisées par les chercheurs :  Les actualités financières (utilisées dans 67.8% des études).  Les réseaux sociaux comme Twitter (utilisés dans 58.6% des études).  Les rapports officiels et réglementaires (utilisés dans 18.4% des études).  Les rapports d'analystes et les retranscriptions d'appels sur les résultats financiers.  4. Les Outils et Modèles (L'évolution technologique)L'article décrit parfaitement les 4 générations d'outils informatiques, de la plus ancienne à la plus moderne :Les Lexiques (Lexicon-Based) : L'utilisation de dictionnaires comme VADER ou Loughran-McDonald (LM), qui est spécialement calibré pour le vocabulaire financier.  Le Machine Learning Classique : L'utilisation de modèles comme Support Vector Machines (SVM), Naive Bayes (NB) et Random Forests (RF).  Le Deep Learning : L'arrivée des réseaux de neurones complexes comme les LSTM (Long Short-Term Memory) et CNN (Convolutional Neural Networks).  Les Modèles de Langage (Transformers et LLMs) : L'utilisation de modèles massifs comme FinBERT, RoBERTa, et même GPT-3.5/GPT-4.  5. Les Résultats et Mathématiques (Ce qui fonctionne)L'article est formel : les modèles basés sur l'architecture "Transformer" (comme FinBERT) dominent totalement le marché, atteignant jusqu'à 65.28% de précision directionnelle sur les références standards.  Les auteurs rappellent l'importance d'utiliser des mathématiques rigoureuses pour l'évaluation, notamment la formule du Matthews Correlation Coefficient (MCC) pour gérer les bases de données déséquilibrées:

&#x20; $$MCC=\\frac{TP \\times TN - FP \\times FN}{\\sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}}$$Ils modélisent également la corrélation mathématique classique entre le sentiment et le prix de l'action de cette manière:

$r=\\frac{Cov(S\_t,R\_{t+1})}{Std(S\_t) \\times Std(R\_{t+1})}$  Un résultat crucial pour toi : combiner plusieurs sources (par exemple Twitter ET les actualités financières) avec les prix historiques améliore les performances de prédiction de 3.2 à 7.8 points de pourcentage par rapport à une seule source.  6. Les Défis (Où tu dois faire attention)Le Bruit : Le sarcasme et les robots spammeurs sur les réseaux sociaux faussent énormément les résultats.  La Décomposition Temporelle (Temporal Decay) : L'utilité d'une actualité chute très vite. Le signal "meurt" généralement après 5 jours pour Twitter et 8 jours pour la presse.  Le Biais Américain : 73.6% des études se concentrent sur le marché boursier américain (S\&P 500, DJIA), ce qui pose un problème de généralisation pour les autres pays.

