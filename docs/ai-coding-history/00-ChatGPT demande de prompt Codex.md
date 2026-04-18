# prompt ChatGPT: projet vtk + C++/SWIG



Mets toi dans la peau d'un expert en développement logiciel C++ / python

J'aimerais étudier le problème suivant à travers un **projet "bac à sable"**:

## contexte

- Souvent, je suis amené à utiliser VTK dans des bibliothèques C++ (imaginons que je suis sous Windows, la bibliothèque s'appelle codecpp.dll). J'utilise CMake pour compiler ce projet. Sous windows, cela me permet d'utiliser le compilateur Visual Studio 2022.
- Actuellement, j'aime travailler avec une version figée de VTK sous windows qui correspond exactement à la version que j'ai sous Ubuntu (9.3.1). Je l'ai donc recompilée moi-même et installée dans C:\local\VTK-9.3.1. 
- Le projet codecpp.dll a besoin d'une interface python pour utiliser mes procédures à travers des scripts et j'utilise SWIG pour créer l'interface (codecpp.py contiendra les shadow classes) via codecpp.i (le fichier d'entrée de SWIG)
-  On imagine donc une bibliothèque dynamique codecpp.dll avec son interface SWIG codecpp.py et _codecpp.pyd
- Cette bibliothèque est donc amenée à être utilisée par des scripts python dans un environnement virtuel (venv). certains de ces scripts pourraient utiliser "pyvista" installé grâce "pip".
- Le problème vient du fait que pyvista va vouloir installer l'interface python de vtk à partir de pip mais ce vtk risque de ne pas être celui que j'ai utilisé (ni la bonne version, ni les mêmes binaires liés à codecpp.dll!)
- Cette double présence de vtk va poser des problèmes lorsque je vais exécuter un script qui utilise simultanément "pyvista" et "codecpp" à travers son interface python, et ce, même si il n'y a aucun échange de données entre pyvista et codecpp! Le premier module va imposer sa version de VTK!

## solution envisagée (proposition à étudier)

Après discussion avec une longue discussion avec une IA, il semblerait que la solution soit de forcer l'installation de mon VTK dans l'environnement virtuel venv où j'utilise le script et où je developpe codecpp et que j'utilise pyvista.

J'aimerais donc mettre en place un projet bac à sable COMPLET qui comprend toutes les étapes de mise en place d'un tel environnement.

Le projet voulu:

* téléchargerait les sources VTK 9.3.1
* les recompilerait avec le visual studio
* les installerait à un endroit où elles sont accessibles pour être d'une part linkée à codecpp et d'autre par accessibles à pip
* un mini-code C++ "natif" utilisant VTK (peu importe ce qu'il fait) serait compilé en dll et interfacé avec SWIG
* un module "python pur" (nommons-le "codepy") regroupant un ensemble de fonctions utilisant pyvista (peu importe ce qu'il fait)
* un environnement virtuel (venv) serait mis en place pour développer simultanément dans codecpp et codepy.
* une série de scripts python seraient bâtis autour de l'utilisation de codecpp et codepy.

## Autres infos:

* J'aimerais utiliser un système moderne (par exemple pyproject.toml)
* j'aimerais à terme distribuer mon application via pip et via pyinstaller/innosetup

## Important

* A terme, j'aimerais que toutes les étapes de gestion du projet (créer un environnement, obtenir les sources VTK du net, le compiler, l'installer, créer l'environnement python, lancer le build du projet, créer l'installeur, etc) soit utilisable à travers un module python utilisant "typer" avec des commandes du style (pmanager get --library vtk --version 9.3.1, etc...) J'aimerais en effet à terme utiliser ce système pour gérer et compiler toutes les dépendances de mes projets C++/python plus lourds qui dépendent de plusieurs bibliothèques qui doivent être recompilées ou installées. Je ne veux pas recréer un système de package manager complet mais j'aimerais bien que le système soit suffisamment flexible pour gérer à terme plusieurs bibliothèques telles que VTK.
* Il s'agit bien d'un projet bac à sable. Ce que font les bibliothèques codecpp et codepy n'a pas d'importance. On se focalise sur le layout du projet, la préparation des bibliothèques, le build system et le runtime
* Je veux quelque chose de moderne, efficace. N'hésite pas à me proposer d'autres technoilogies si tu trouves que ma première idée n'est pas la meilleure

## Ce que je te demande

* Analyse mon problème de manière très poussée. 
* Pose moi autant de question que tu le désires 
* propose moi un fichier AGENTS.md (et d'autres fichiers markdown si nécessaires) 
* propose moi un **prompt le plus détaillé et précis possible pour démarrer une conversation Codex en mode "plan"** pour planifier les étapes de mise en place de ce projet.



---

# questions de ChatGPT:



Voici les questions qui, pour moi, changent vraiment le design :

1. **Veux-tu que le sandbox reste strictement en SWIG**, ou acceptes-tu que je prévoie une variante “future” en `pybind11`/`nanobind` dans les docs ?
   * REPONSE: prévois une variante future, j'utilise SWIG par habitude car tous mes autres projets utilisent SWIG mais je suis ouvert à de nouvelles découvertes par la suite.
2. **Quelle version de Python veux-tu cibler en premier** sous Windows ? 3.11 seulement ? 3.12 ?
   * REPONSE: Mon python principal actuellement installé sur ma machine est 3.10. J'aimerais rester compatible avec cette version; mais je suis bien sur intéressé que ca fonctionne si je change de version.
3. **Veux-tu un dépôt Windows-first**, ou bien un layout qui doit dès le départ préparer Linux/Ubuntu aussi ?
   * REPONSE: Je veux un layout multiplateforme: je développe sous Windows (à la maison) et Ubuntu (au bureau). C'est important que ça marche à terme dans les 2 OS.
4. **Acceptes-tu l’idée d’un wheelhouse local ou d’un index privé** pour ton VTK custom, ou veux-tu absolument un workflow compatible PyPI public ?
   * REPONSE: PyPI public n'est PAS nécessaire. Un wheel local est parfait!
5. **Le sandbox doit-il construire VTK complet**, ou une sélection minimale de modules VTK suffit-elle ?
   * REPONSE: Le plus complet possible car pyvista nécessite un VTK très complet et ça ne fonctionnera pas avec un VTK minimal. Je te fournis les fichiers build_vtk_wheel.sh et install_vtk_wheel.sh auxquels je suis arrivé sous linux ubuntu (ci-joint à ce message)
6. **As-tu besoin d’affichage/rendering**, ou un VTK minimal sans fenêtre te suffit pour prouver le chargement ?
   * REPONSE: oui, un VTK le plus complet possible (voir fichiers)
7. **Veux-tu `uv`**, ou préfères-tu rester sur `venv + pip` pur pour ne pas ajouter un outil ?
   * REPONSE: j'aimerais venv+pip dans un premier temps. Je ne connais pas uv et j'aimerais d'abord utiliser ce que je connais. 
8. **Souhaites-tu GitHub Actions Windows** dès la première version ?
   * REPONSE: Non, pas nécessairement
9. **Veux-tu que `pmanager` soit déjà opérationnel**, ou seulement une ossature CLI dans la v1 ?
   * REPONSE: une ossature suffit
10. **Ton cas réel futur devra-t-il supporter plusieurs libs externes** avec la même logique que VTK, ou VTK est-il vraiment le cas pilote unique au départ ?
    * REPONSE: oui, le but est de gérer à terme des cas avec plusieurs libs externes





