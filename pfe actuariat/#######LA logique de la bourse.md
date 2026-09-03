\#######LA logique de la bourse



La bourse c'est predire l'avenir , quand on dit acheter ou vendre , il ne dcrit pas ce qui passe maintenanat , il decrit ce qui



\##le scenario d'achat :



imagine que tu est devant une boutique qui vont des telephones

aujourdhui le telephone coute 100 euro , lalgorithme a lu les twwets de la nuits et dit : Skander les gens adorent ce telephone , il va y avoir une rupture de stock , le prix va monter !

===> donc tu doit acheter aujourdhui à 100 euro , le lendemain comme prévu , le prix monte à 120 euro .Tu revends le telephone .Tu vient de gagner 20 euro du benifice net





======> donc on achette un actif quand on predit que son prix va augmenter , pour le revendre plus cher plus tard . Larticle represente cette action par le chiffre 1



\## le scenario de vente



la plus courant en trading alghjorithmique  est ce qu'on appelle la vente à decouvert (short Selling)

c'est un mecaanisme magique de la finanace qui permet dev gagner de l'argent quand tous s'effondre



exemple : aujourd'hui , le telephone coute 100 euro , ton alogorithme lit les actualité et te dit : skander , ce telephone à defaut de batterie , tout le monde le detste sur TWiter , le prix va s"effronder !



Tonn action : tu vas voir un ami possede ce telephone et tu lui dis : Prete-moi ton telephone , je te le rendrai la semaine prochaine . tu pren ds le telephone et tu le vends immédiatement à un inconnu pour 100 euro .tu as 100 euro dans ta poche



le resultat : le lendemaint le prix de telephone chute à 100 euro . donc tu utilise les 100 euro de tya poche pour racheter le telephone àn 60 euro . il reste 40 euro du benifice . Tu rends le telephone a ton amis .

Regle d'or : on vend quand on predit que le prix va baisser . L'article represente cette action par le symbole -1







Partie 2 : les métriques de l'IA



Imagine  que lalghorithme est une Alarme incendie et le feu represente une "Bonne opportunité boursiere"(une bonne prix)



\-true positive (vrai positive) = l'alarme sonne et il y vraiment un feu . l'algorithme a dit dacheter et laction a vraiment monté ===> c'est parfait



\-true negative(vrai negatif): lalarme ne sonne pas et il nya pas de feu (l'algorithme a dit de ne rien fairev et laction a effectivement baissé ) c'est parfait



\- False positive : lalarme sonne mais il nya pas de faux (lalgorithme a dit dacheter mais laction a chuté ) cest une fausse alerte.

False negative : lalarme ne sonne pas par contre l'action laction a explosé a la hausse Tu as raté une occasion en or ===> c'est une echec silencieux





\############La precision





quant lalarme sonne est ce que je peux lui faire confiance

precision = true positiive / (true positive + false positive )







\#############La Rappel ( recall ou sensibilité )



sur tous les incendies qui se sont declarés dans l'année combien mon alarme a telle reussi à detecter ??





Recall= TruePositive /(TruePositive + FalseNegative)





\#############Le F score



la question : mon alarme est-elle globalement excelente ??



si tu as une alarme qui sonne tout le temps (meme sans feu) , elle aura un Rappel de 100% (elle ne ratera aucun feu) , mais une presion miserable (beaucoup de fausse alertes). Le f Score est la moyenne stricte mathematique qui calcule l'equilibre parfait entre la precision et le Rappel pour sassurer que lalgorithme est vraiment intelligent .





F Score = 2\* ( precision \*recall) / (precision +recall)









\################La courbe ROC et AUC





l'AUC (Area Under Curve - Aire sous la coourbe ) est la note finale de lalgorithme , donnée sur un graphique appelé ROC (Receiver operator Characteristic)



la courbe ROC : trace la capacite de ton model à separer les vrai signaux (taux de vrai positifs ) du bruits (taux de faux positifs )



\-l'AUC est ujne note entre 0 et 1 :



* Si l'AUC est de 1, ton algorithme est un dieu de la finance. Il sépare parfaitement les hausses et les baisse
* Si l'AUC est de 0.5, ton algorithme est aussi intelligent que si tu lançais une pièce de monnaie (pile ou face).
* Si l'AUC est de 0, il se trompe à 100%. Il classe tout ce qui est positif comme négatif, et inversement.

