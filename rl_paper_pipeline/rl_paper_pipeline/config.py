import os

VAULT_PATH = os.path.expanduser(r"C:/Users/janop/OneDrive/Documents/Obsidian Vault/03 Research/Reinforcement Learning")  # change to your vault

OPENALEX_BASE = "https://api.openalex.org/works"

# Reinforcement learning concept ID in OpenAlex
# (Machine learning → Reinforcement learning)
RL_CONCEPT_ID = "https://openalex.org/C2778793908"

MAX_RESULTS = 20

#LLM_MODEL = "gpt-4o-mini"
LLM_MODEL = "mistral"  # alternative model

DEFAULT_QUERY = None  # user-defined natural language query