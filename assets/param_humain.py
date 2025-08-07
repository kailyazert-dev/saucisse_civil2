class Noms:
    nom_masculin = {
        "Alexandre", "Bastien", "Charles", "Damien", "Éric",
        "François", "Guillaume", "Hugo", "Ismaël", "Julien",
        "Kévin", "Laurent", "Mathieu", "Nicolas", "Olivier",
        "Paul", "Quentin", "Rémi", "Samuel", "Thomas",
        "Ulysse", "Victor", "William", "Xavier", "Yann",
        "Zacharie", "Antoine", "Bruno", "Cédric", "David",
        "Étienne", "Félix", "Gaspard", "Henri", "Ibrahim",
        "Jean", "Karim", "Léo", "Marc", "Noé",
        "Oscar", "Pierre", "Raphaël", "Sébastien", "Théo",
        "Ugo", "Vincent", "Willy", "Yohan", "Abel"
    }

    nom_feminin = {
        "Alice", "Brigitte", "Claire", "Delphine", "Élodie",
        "Florence", "Gaëlle", "Hélène", "Inès", "Julie",
        "Karine", "Laurence", "Marie", "Nathalie", "Océane",
        "Pauline", "Quitterie", "Rachel", "Sophie", "Thérèse",
        "Ursule", "Valérie", "Wendy", "Yasmina", "Zoé",
        "Amélie", "Barbara", "Camille", "Diane", "Émilie",
        "Fanny", "Geneviève", "Hortense", "Isabelle", "Jeanne",
        "Kenza", "Léa", "Manon", "Nina", "Olympe",
        "Patricia", "Roxane", "Salomé", "Tiffany", "Ulrikke",
        "Véronique", "Wilhelmine", "Yvette", "Agnès", "Chloé"
    }

class Images:
    image_masculin = {
        ":resources:images/animated_characters/male_person/malePerson_idle.png",
        ":resources:images/animated_characters/male_adventurer/maleAdventurer_idle.png",
    }

    image_feminin = {
        ":resources:images/animated_characters/female_person/femalePerson_idle.png",
        ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png",
    }   

class IbmI_personnage :
    personnages = {
        'Henry': {
            'nom': 'Henry',
            'charisme': 1,
            'intensite_boof': 1,
            'receptif_boof': 1,
            'rigidite': 1,
            'type': 'Masculin',
            'metier' : 'Développeur',
            'hobbie' : 'Photographie',
            'personnalite' : "Extremement beauf et charismatique",
            'or' : 0,
            'competences' : {
                'physique' : {
                    'force' : 0.1,
                    'vitesse' : 0.1,
                    'endurance' : 0.1,
                    'recuperation' : 0.1
                },
                'intelecte' : {
                    'mathematique' : 0.1,
                    'logique' : 0.1,
                    'musique' : 0.1,
                    'langage' : 0.1,
                    'sociale' : 0.1,
                }
            }
        },
        'Kyle': {
            'nom': 'Kyle',
            'charisme': 0.5,
            'intensite_boof': 0.5,
            'receptif_boof': 0.5,
            'rigidite': 0.7,
            'type': 'Masculin',
            'metier' : 'Développeur',
            'hobbie' : 'Sport',
            'personnalite' : "Primitive, qui aime se battre",
            'or' : 100,
            'competences' : {
                'physique' : {
                    'force' : 0.9,
                    'vitesse' : 0.7,
                    'endurance' : 0.3,
                    'recuperation' : 0.8
                },
                'intelecte' : {
                    'mathematique' : 0.5,
                    'logique' : 0.8,
                    'musique' : 0.4,
                    'langage' : 0.3,
                    'sociale' : 0.4,
                }
            }
        },
        'Mael': {
            'nom': 'Mael',
            'charisme': 0.3,
            'intensite_boof': 0.7,
            'receptif_boof': 0.7,
            'rigidite': 0.6,
            'type': 'Masculin',
            'metier' : 'Développeur',
            'hobbie' : 'Sport, cinéma',
            'personnalite' : "chambreur qui fait beaucoup caca",
            'or' : 100,
            'competences' : {
                'physique' : {
                    'force' : 0.4,
                    'vitesse' : 0.5,
                    'endurance' : 0.8,
                    'recuperation' : 0.2
                },
                'intelecte' : {
                    'mathematique' : 0.2,
                    'logique' : 0.7,
                    'musique' : 0.2,
                    'langage' : 0.5,
                    'sociale' : 0.2,
                }
            }
        },
        'Thomas': {
            'nom': 'Thomas',
            'charisme': 0.5,
            'intensite_boof': 0.4,
            'receptif_boof': 0.4,
            'rigidite': 0.8,
            'type': 'Masculin',
            'metier' : 'Data engineer',
            'hobbie' : 'Miner du bitcoin, la finance',
            'personnalite' : "Tu a une personnalité de geek, et aime les petits minoug",
            'or' : 9000000,
            'competences' : {
                'physique' : {
                    'force' : 0.2,
                    'vitesse' : 0.2,
                    'endurance' : 0.2,
                    'recuperation' : 0.2
                },
                'intelecte' : {
                    'mathematique' : 0.7,
                    'logique' : 0.7,
                    'musique' : 0.3,
                    'langage' : 0.3,
                    'sociale' : 0.2,
                }
            }
        },
        'Louis': {
            'nom': 'Louis',
            'charisme': 0.5,
            'intensite_boof': 0.6,
            'receptif_boof': 0.4,
            'rigidite': 0.6,
            'type': 'Masculin',
            'metier' : 'Data scientist',
            'hobbie' : 'Music',
            'personnalite' : "consensuelle",
            'or' : 9000000,
            'competences' : {
                'physique' : {
                    'force' : 0.2,
                    'vitesse' : 0.3,
                    'endurance' : 0.3,
                    'recuperation' : 0.2
                },
                'intelecte' : {
                    'mathematique' : 1,
                    'logique' : 0.8,
                    'musique' : 1,
                    'langage' : 0.6,
                    'sociale' : 0.75,
                }
            }
        },
        'Ludovic_L': {
            'nom': 'Ludovic_L',
            'charisme': 0.3,
            'intensite_boof': 0.7,
            'receptif_boof': 0.7,
            'rigidite': 0.3,
            'type': 'Masculin',
            'or' : 2000,
            'competences' : {
                'physique' : {
                    'force' : 0.5,
                    'vitesse' : 0.6,
                    'endurance' : 0.7,
                    'recuperation' : 0.7
                },
                'intelecte' : {
                    'mathematique' : 0.2,
                    'logique' : 0.2,
                    'musique' : 0.2,
                    'langage' : 0.2,
                    'sociale' : 0.4,
                }
            }
        },
        'Ilies': {
            'nom': 'Ilies',
            'charisme': 0.6,
            'intensite_boof': 0.8,
            'receptif_boof': 0.9,
            'rigidite': 0.1,
            'type': 'Masculin',
            'or' : 2000,
            'competences' : {
                'physique' : {
                    'force' : 0.2,
                    'vitesse' : 0.2,
                    'endurance' : 0.2,
                    'recuperation' : 0.2
                },
                'intelecte' : {
                    'mathematique' : 0.5,
                    'logique' : 0.5,
                    'musique' : 0.2,
                    'langage' : 0.2,
                    'sociale' : 0.6,
                }
            }
        },
        'Ludovic_S': {
            'nom': 'Ludovic_S',
            'charisme': 0.6,
            'intensite_boof': 0.5,
            'receptif_boof': 0.7,
            'rigidite': 0.8,
            'type': 'Masculin',
            'or' : 2000,
            'competences' : {
                'physique' : {
                    'force' : 0.2,
                    'vitesse' : 0.2,
                    'endurance' : 0.2,
                    'recuperation' : 0.2
                },
                'intelecte' : {
                    'mathematique' : 0.6,
                    'logique' : 0.6,
                    'musique' : 0.3,
                    'langage' : 0.7,
                    'sociale' : 0.5,
                }
            }
        },
        'Abdel': {
            'nom': 'Abdel',
            'charisme': 0.3,
            'intensite_boof': 0.3,
            'receptif_boof': 0.3,
            'rigidite': 1,
            'type': 'Masculin',
            'or' : 2000,
            'competences' : {
                'physique' : {
                    'force' : 0.3,
                    'vitesse' : 0.3,
                    'endurance' : 0.3,
                    'recuperation' : 0.2
                },
                'intelecte' : {
                    'mathematique' : 0.6,
                    'logique' : 0.4,
                    'musique' : 0.3,
                    'langage' : 0.2,
                    'sociale' : 0.4,
                }
            }
        },
        'Hotesse': {
            'nom': 'Hotesse',
            'charisme': 0.5,
            'intensite_boof': 0.4,
            'receptif_boof': 0.4,
            'rigidite': 0.8,
            'type': 'Feminin',
            'metier' : 'Hotesse d''accueil',
            'hobbie' : 'Jouer sur son telephone',
            'personnalite' : "Tu est tres acceuillante",
            'or' : 99999999999999999,
            'competences' : {
                'physique' : {
                    'force' : 1,
                    'vitesse' : 1,
                    'endurance' : 1,
                    'recuperation' : 1
                },
                'intelecte' : {
                    'mathematique' : 1,
                    'logique' : 1,
                    'musique' : 1,
                    'langage' : 1,
                    'sociale' : 1,
                }
            }
        },
    }         