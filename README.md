# MultipliQuest — Jeu de révision des tables de multiplication

> Nom provisoire du projet.

## 1. Présentation

MultipliQuest est un mini-jeu éducatif accessible depuis un navigateur, sur ordinateur, tablette et téléphone. Son objectif est d'aider un enfant à mémoriser et maîtriser progressivement les tables de multiplication de **2 à 12** grâce à des exercices courts et à un système de progression et de récompenses.

Le joueur commence avec les tables de **2, 3 et 4**. Lorsqu'il atteint **95 % de bonnes réponses sur une session complète**, il débloque la table de 5. À partir du niveau 2, le déblocage exige également **95 % de réussite sur les 20 dernières questions de la table la plus récemment débloquée**. Les exercices suivants continuent de proposer les tables déjà acquises tout en intégrant la nouvelle table. Le même principe s'applique jusqu'à la table de 12.

Le jeu doit encourager la régularité, la persévérance et la maîtrise des acquis plutôt que la vitesse.

## 2. Objectifs du MVP

- Réviser les multiplications de 2 à 12, avec des multiplicateurs de 1 à 12.
- Débloquer progressivement les tables, de 5 à 12.
- Maintenir les tables précédentes dans les exercices après chaque déblocage.
- Fournir un retour immédiat sur chaque réponse et afficher la bonne réponse en cas d'erreur.
- Enregistrer la progression pour reprendre une session ultérieurement.
- Récompenser les progrès avec des points d'expérience (XP) et des trophées.
- Proposer une interface ludique, lisible et adaptée à un enfant.

Hors périmètre initial : classement public, multijoueur, messagerie, publicité, achats intégrés et génération d'exercices par IA.

## 3. Fonctionnement pédagogique

### 3.1. Tables et niveaux

| Niveau | Tables proposées | Table nouvellement débloquée |
| --- | --- | --- |
| 1 | 2, 3, 4 | Tables de départ |
| 2 | 2, 3, 4, 5 | 5 |
| 3 | 2 à 6 | 6 |
| 4 | 2 à 7 | 7 |
| 5 | 2 à 8 | 8 |
| 6 | 2 à 9 | 9 |
| 7 | 2 à 10 | 10 |
| 8 | 2 à 11 | 11 |
| 9 | 2 à 12 | 12 |

Le niveau 9 constitue le niveau final : les exercices continuent de mélanger toutes les tables de 2 à 12. La maîtrise de ce niveau peut donner lieu à un trophée final.

### 3.2. Déroulement d'une session

1. Le joueur démarre une session au niveau actuellement débloqué.
2. Le jeu présente une multiplication, par exemple `4 × 7 = ?`.
3. Le joueur saisit sa réponse et la valide.
4. Le jeu indique immédiatement si la réponse est correcte. En cas d'erreur, il affiche la bonne réponse.
5. Les résultats sont enregistrés et le joueur passe à la question suivante.
6. À la fin de la session, le joueur consulte son score, ses XP et sa progression vers le prochain déblocage.

**Paramètres initiaux proposés :** 20 questions par session, sans limite de temps et avec réponse numérique libre. Ces paramètres pourront évoluer après les premiers tests avec le joueur.

### 3.3. Répartition des questions

À chaque niveau, les exercices doivent couvrir **toutes les tables débloquées**, et pas uniquement la dernière. La répartition doit permettre de réviser régulièrement les anciennes tables tout en pratiquant suffisamment la nouvelle.

Pour le MVP, chaque session de 20 questions à partir du niveau 2 contient **10 questions sur la dernière table débloquée** et **10 questions sur les tables précédentes**, réparties aussi équitablement que possible. Au niveau 1, répartir les questions entre les tables 2, 3 et 4. Éviter autant que possible les répétitions immédiates. La pondération de la nouvelle table permet d’atteindre rapidement les 20 tentatives nécessaires à l’évaluation de sa maîtrise.

Une multiplication déjà proposée dans l'ordre inverse, par exemple `3 × 4` et `4 × 3`, peut être présentée comme deux exercices distincts.

## 4. Progression et déblocage

### 4.1. Deux conditions de déblocage

À partir du niveau 2, **les deux conditions suivantes doivent être remplies simultanément** :

1. **Réussite globale :** au moins **19 bonnes réponses sur les 20 questions d'une session complète** au niveau courant (95 %).
2. **Maîtrise de la dernière table débloquée :** au moins **19 bonnes réponses sur les 20 dernières tentatives concernant cette table** (95 %). Ces tentatives peuvent provenir de plusieurs sessions terminées du niveau courant.

Le niveau 1 est une exception : aucune nouvelle table n'a encore été débloquée. Une session complète de 19/20 sur les tables 2, 3 et 4 suffit donc pour accéder au niveau 2 et à la table de 5, sans condition supplémentaire sur la table de 4.

**Exemple :** au niveau 2, une session à 19/20 sur les tables 2 à 5 ne suffit pas si le joueur a réussi seulement 17 de ses 20 dernières questions sur la table de 5. Il reste au niveau 2 et continue de s'entraîner. Lorsqu'il atteint 19/20 sur la table de 5, il doit aussi avoir réussi une session complète à 19/20 au niveau 2 pour débloquer la table de 6.

### 4.2. Fenêtre d'évaluation et sessions

- Chaque session comporte **20 questions**, dont **10 sur la dernière table débloquée** et **10 sur les anciennes tables** à partir du niveau 2.
- Pour la maîtrise de la nouvelle table, on utilise une **fenêtre glissante de 20 tentatives** : dès qu'une nouvelle réponse est enregistrée, elle remplace la plus ancienne si la fenêtre en contient déjà 20.
- Tant que le joueur n'a pas répondu à **20 questions de cette table au niveau courant**, la condition de maîtrise n'est pas évaluable et aucun déblocage n'est possible, même avec 100 % sur les premières tentatives.
- La condition globale doit être satisfaite sur **une session complète du niveau courant**. Une session précédente à 95 % reste valable pour ce niveau : il n'est pas nécessaire de réussir les deux conditions lors de la même session.
- Les sessions inachevées ne sont pas prises en compte pour la condition globale ; pour garder une règle simple, leurs tentatives ne sont pas non plus comptabilisées dans la fenêtre de maîtrise.
- Après le déblocage, la fenêtre d'évaluation est réinitialisée pour la **nouvelle** table. Les résultats historiques restent enregistrés.
- Un niveau débloqué l'est définitivement. Les erreurs ultérieures ne retirent ni niveaux, ni XP, ni trophées.
- Au niveau 9, ces deux conditions donnent accès au trophée final au lieu de débloquer une table supplémentaire.

### 4.3. Exemples de progression

| Situation | Résultat |
| --- | --- |
| Niveau 1 : 19/20 sur les tables 2, 3 et 4 | Déblocage de la table de 5. |
| Niveau 2 : 19/20 sur une session, mais seulement 17/20 sur les 20 dernières questions de la table de 5 | Pas de déblocage : poursuivre l'entraînement sur la table de 5. |
| Niveau 2 : 18/20 sur une session et 20/20 sur les 20 dernières questions de la table de 5, sans session globale réussie à ce niveau | Pas de déblocage : il manque la réussite globale. |
| Niveau 2 : une session globale déjà réussie à 19/20 et désormais 19/20 sur la table de 5 | Déblocage de la table de 6. |
| Niveau 9 : réussite globale et maîtrise de la table de 12 | Attribution du trophée final. |

L'écran de progression affiche **deux indicateurs distincts** : « Réussite globale » et « Maîtrise de la nouvelle table », ainsi que le nombre de tentatives restantes avant de pouvoir évaluer cette dernière.

## 5. Gamification

### 5.1. Points d'expérience (XP)

Les XP représentent l'investissement du joueur et sont distincts des critères de déblocage. À titre de règles initiales :

- 10 XP par bonne réponse ;
- 20 XP supplémentaires pour une session réussie à 95 % ou plus (indépendamment du déblocage) ;
- aucun retrait de XP en cas d'erreur.

Les XP n'autorisent pas, à eux seuls, le déblocage d'une table : seule la condition de réussite le permet.

### 5.2. Trophées

Exemples de trophées à implémenter progressivement :

| Trophée | Condition |
| --- | --- |
| Premier pas | Terminer sa première session |
| Sans faute | Réussir une session avec 20/20 |
| Explorateur | Débloquer la table de 5 |
| Persévérant | Terminer 5 sessions |
| Maître des multiplications | Remplir les deux conditions de déblocage au niveau final (tables de 2 à 12) |

Chaque trophée ne peut être attribué qu'une fois par profil. Une animation courte peut accompagner son obtention.

## 6. Écrans du MVP

1. **Accueil :** bouton « Jouer », niveau courant et derniers trophées.
2. **Carte de progression :** tables débloquées, niveau courant et niveaux encore verrouillés.
3. **Exercice :** multiplication, champ de réponse, validation et correction immédiate.
4. **Fin de session :** score, pourcentage de réussite globale, maîtrise de la dernière table, XP gagnés et éventuel déblocage.
5. **Trophées :** récompenses obtenues et conditions des prochains trophées.

L'interface doit fonctionner sur mobile et rester utilisable au clavier.

## 7. Architecture technique envisagée

- **Frontend :** React, TypeScript et Vite.
- **Backend :** Python, Django et Django REST Framework.
- **Base de données :** SQLite en développement ; PostgreSQL en production si l'hébergeur retenu le justifie.
- **Gestion Python :** `uv`.
- **Qualité :** Ruff, mypy, pytest et tests d'API.
- **Tests de parcours :** Playwright pour les principaux scénarios utilisateur.
- **Versionnement et CI :** GitHub et GitHub Actions.

L'architecture doit rester simple : la logique métier de génération des questions, de calcul des résultats, de progression et d'attribution des trophées appartient au backend, idéalement dans des services testables. Le frontend gère la présentation et les interactions.

## 8. Modèle de données prévisionnel

- **PlayerProfile :** pseudonyme, niveau courant, total de XP.
- **GameSession :** joueur, niveau joué, date de début et de fin, statut, score et nombre de questions.
- **QuestionAttempt :** session, table, multiplicateur, réponse fournie, résultat et ordre de présentation. Les tentatives des sessions terminées servent au calcul des 20 dernières réponses de la nouvelle table.
- **Trophy :** identifiant, nom, description et règle d'attribution.
- **PlayerTrophy :** joueur, trophée et date d'obtention, avec unicité sur le couple joueur/trophée.

Les tables débloquées peuvent être déduites du niveau courant ; il n'est pas nécessaire de stocker une liste redondante pour le MVP.

## 9. Sécurité et confidentialité

Le jeu est destiné à un enfant et doit limiter les données personnelles au strict nécessaire.

- Prévoir un compte parent et un profil enfant sans adresse e-mail propre à l'enfant.
- Ne pas proposer de profil public, de classement public ni de communication entre joueurs.
- Vérifier les droits d'accès côté serveur sur chaque profil et chaque session.
- Valider les réponses et calculer les scores, XP, déblocages et trophées côté serveur.
- Protéger les sessions et formulaires (cookies sécurisés, HTTPS, CSRF et validation des entrées).
- Limiter les tentatives de connexion et conserver les secrets hors du dépôt.
- Configurer les sauvegardes et ne pas enregistrer de données personnelles inutiles dans les journaux.

## 10. Utilisation de Codex

Le projet disposera d'un fichier `AGENTS.md` contenant les conventions communes et les commandes de vérification. Les tâches seront confiées à Codex par incréments limités, avec une description du comportement attendu et des tests associés.

Ordre de développement suggéré :

1. Initialiser le dépôt, le backend, le frontend et les outils de qualité.
2. Implémenter et tester la génération des multiplications pour les tables autorisées.
3. Développer une session de 20 questions et la validation des réponses.
4. Implémenter la double condition des 95 % (session globale et fenêtre glissante sur la dernière table), puis le déblocage progressif jusqu’à 12.
5. Enregistrer les sessions et permettre la reprise de la progression.
6. Ajouter les XP, les trophées et les écrans de progression.
7. Mettre en place l'authentification parent, les permissions et les protections de base.
8. Ajouter la CI, les tests de parcours et préparer le déploiement.

Chaque fonctionnalité métier doit disposer de tests automatisés, notamment pour les seuils de réussite (18/20, 19/20, 20/20), les fenêtres glissantes, les sessions inachevées, les deux conditions indépendantes, les transitions de niveau et l’impossibilité de dépasser la table de 12.

## 11. Critères d'acceptation de la première version

- Un nouveau joueur commence avec les tables de 2, 3 et 4.
- Une session contient 20 questions sur les tables accessibles.
- Au niveau 1, 18/20 ne débloque rien ; 19/20 ou 20/20 débloque la table de 5.
- À partir du niveau 2, 19/20 sur une session **et** 19/20 sur les 20 dernières tentatives de la nouvelle table sont nécessaires pour débloquer la suivante.
- Un score global de 95 % ne suffit pas si la dernière table n’est pas maîtrisée ; inversement, maîtriser la dernière table ne suffit pas sans session globale réussie.
- À partir du niveau 2, 10 questions par session concernent la dernière table débloquée et 10 questions concernent les tables précédentes.
- La maîtrise est calculée sur une fenêtre glissante de 20 tentatives issues de sessions terminées au niveau courant.
- Chaque nouveau niveau conserve les tables précédentes dans les exercices.
- Le joueur retrouve son niveau, ses XP et ses trophées après reconnexion.
- Un même trophée n'est pas attribué deux fois.
- Le score et la progression ne peuvent pas être modifiés directement par le navigateur.
- Le jeu est utilisable sur téléphone et ordinateur.

## 12. Évolutions possibles

Après validation du MVP : révisions ciblées sur les multiplications fréquemment ratées, tableau de bord détaillé par table, difficulté adaptative, avatars et personnalisation visuelle, défis quotidiens facultatifs et tableau de bord parent.
