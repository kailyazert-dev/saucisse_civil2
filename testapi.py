import replicate
import os

# Le token creer sur Replicate

# Prompt 
prompt = (
    "En quelle années la révolution francaise s'est déroulée ?\n"
)

# Appel au modèle Granite sur Replicate 
output = replicate.run(
    "openai/gpt-4o-mini",
    input={
        "prompt": prompt,
        "max_new_tokens": 300,
        "temperature": 0.7
    }
)

# Affichage de la réponse
print("Réponse du model générée :\n")
print("".join(output))