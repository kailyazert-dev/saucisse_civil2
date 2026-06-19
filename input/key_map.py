"""Mapping clavier AZERTY pour le jeu."""
import arcade

MOVE_KEYS = {
    arcade.key.D: ("x",  1, "right"),
    arcade.key.Q: ("x", -1, "left"),
    arcade.key.Z: ("y",  1, "up"),
    arcade.key.S: ("y", -1, "down"),
}
