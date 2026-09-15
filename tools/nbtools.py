"""Utilitaires d'edition de notebooks pour les corrections du PFE."""
import json, io, os, shutil, datetime as dt


def charger(chemin):
    with io.open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)


def sauver(nb, chemin):
    """Ecrit le notebook apres avoir fait une copie .bak horodatee."""
    if os.path.exists(chemin):
        bak = f"{chemin}.{dt.datetime.now():%Y%m%d_%H%M%S}.bak"
        shutil.copy2(chemin, bak)
    with io.open(chemin, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
        f.write("\n")


def src(cell):
    """Source d'une cellule sous forme de chaine unique."""
    s = cell.get("source", [])
    return s if isinstance(s, str) else "".join(s)


def trouver(nb, ancre, type_cellule="code", occurrence=0):
    """Index de la cellule contenant `ancre`. Leve une exception si absente ou ambigue."""
    hits = [i for i, c in enumerate(nb["cells"])
            if c["cell_type"] == type_cellule and ancre in src(c)]
    if not hits:
        raise LookupError(f"ANCRE INTROUVABLE : {ancre!r}")
    if len(hits) <= occurrence:
        raise LookupError(f"ANCRE trouvee {len(hits)}x, occurrence {occurrence} demandee : {ancre!r}")
    return hits[occurrence]


def remplacer_source(nb, idx, nouveau_code):
    """Remplace integralement la source d'une cellule et vide ses sorties."""
    c = nb["cells"][idx]
    c["source"] = nouveau_code.splitlines(keepends=True)
    if c["cell_type"] == "code":
        c["outputs"] = []
        c["execution_count"] = None


def remplacer_bloc(nb, idx, ancien, nouveau):
    """Remplace un fragment de texte a l'interieur d'une cellule. Exige une occurrence unique."""
    c = nb["cells"][idx]
    s = src(c)
    n = s.count(ancien)
    if n != 1:
        raise ValueError(f"Fragment trouve {n} fois (1 attendu) dans la cellule {idx}")
    remplacer_source(nb, idx, s.replace(ancien, nouveau))


def inserer_apres(nb, idx, code, type_cellule="code"):
    """Insere une nouvelle cellule juste apres l'index donne."""
    cellule = {"cell_type": type_cellule, "metadata": {},
               "source": code.splitlines(keepends=True)}
    if type_cellule == "code":
        cellule["outputs"] = []
        cellule["execution_count"] = None
    nb["cells"].insert(idx + 1, cellule)
    return idx + 1


def supprimer(nb, idx):
    del nb["cells"][idx]
