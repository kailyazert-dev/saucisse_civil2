# ui/menus/

Menus plein écran du jeu : statistiques, pause et mort.

## Fichiers

| Fichier | Classe | Touche | Rôle |
|---|---|---|---|
| `stats_view.py` | `StatsView(arcade.View)` | P | Écran stats/quêtes/équipement |
| `menu.py` | `Menu` | ESCAPE | Menu pause (overlay) |
| `death_menu.py` | `DeathMenu` | — | Menu mort (overlay) |
| `shop_menu.py` | `ShopMenu` | E / RETURN | Overlay distributeur (mode mercenaire) |

## StatsView

Vue Arcade complète (remplace temporairement la scène).  
3 onglets navigables avec les flèches directionnelles LEFT/RIGHT (pas AZERTY) :
- **Stats** : barres de progression pour les 9 stats en 3 colonnes (Physique / Intellect / Sociale)
- **Quêtes** : quête en cours, objectifs avec statut [x]/[ ]
- **Équipement** : carte arme unique via `player.weapon` — affiche image, dégâts min/max, barre et couleur projectile. Ne supporte pas `weapon_feu`/`weapon_blanc`.

Retour à la scène : P ou ESCAPE.

## Menu

Overlay modal (non-View), dessiné au-dessus de la scène via `menu.draw()`.  
Options : Reprendre, Sauvegarder, Charger une sauvegarde, Retour à la maison, Réinitialiser, Quitter.

Sous-menus : liste des sauvegardes (scroll), saisie de nom (`on_text`), confirmation de suppression (`confirm_delete`).

Navigation : flèches UP/DOWN uniquement — Z/S (AZERTY) **non supportés** dans `Menu` (contrairement à `ShopMenu`).  
Touche DELETE depuis `save_list` ou `load_list` : ouvre le sous-menu `confirm_delete` pour supprimer un slot.

```python
gv.show_menu = True
gv.menu.draw()
gv.menu.handle_key(key)
gv.menu.on_text(char)   # pour la saisie du nom de sauvegarde
gv.menu.reset()         # réinitialise tous les états internes
gv.menu.has_sub()       # → bool : True si un sous-menu est actif
```

## ShopMenu

Overlay distributeur utilisé exclusivement en `MercScene`. Ouvert via la touche E près d'un `Coffre`, fermé par ECHAP.

```python
shop_menu = ShopMenu()
shop_menu.open(items)          # items : list[dict] depuis merc/configs/shop.json
shop_menu.close()
shop_menu.draw(player)
shop_menu.handle_key(key, player)
shop_menu.update(delta_time)   # gère l'expiration du message de feedback
```

Navigation : UP/DOWN ou Z/S (AZERTY). Achat : E ou RETURN.

**Types d'items supportés** (champ `"type"`) : `"soin"`, `"arme"`, `"upgrade_arme"`, `"upgrade_perso"`.

**Armes déjà équipées** : `_is_owned(item, player)` détecte si une arme (`type == "arme"`) est déjà dans le slot correspondant. Le slot est déterminé par le champ `"slot"` de l'item (valeur par défaut `"feu"`) : `player.weapon_feu` si `slot == "feu"`, sinon `player.weapon_blanc`. Si c'est le cas, l'entrée est grisée visuellement avec le label `(Équipé)`, et l'achat est bloqué. Les consommables (`soin`, `upgrade_*`) restent toujours disponibles.

**Effet `upgrade_perso`** : augmente `player.max_health_bonus` du montant `valeur` **et** soigne le joueur du même montant immédiatement. L'attribut `max_health_bonus` peut être absent à l'initialisation (lu avec `getattr(..., 0)`).

## DeathMenu

Overlay affiché quand `player.health <= 0` (après fondu rouge).  
Options : "Recommencer au début" ou "Apparaître à la maison".  
Navigation : flèches UP/DOWN. Confirmation : `arcade.key.ENTER` (et non `arcade.key.RETURN`).

```python
death_menu = DeathMenu()
death_menu.active = True
death_menu.draw()
choice = death_menu.handle_key(key)  # → str | None
```
