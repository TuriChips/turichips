"""Who answers in which Discord channel."""

AGENTS = {
    "vera":  "architect",
    "theo":  "designer-a",
    "mira":  "designer-b",
    "quinn": "verification-a",
    "rook":  "verification-b",
    "otto":  "infrastructure",
    "petra": "physical-design",
    "juno":  "software-docs",
}

# In #general, an agent answers if you mention its name. If nobody is named, Vera answers.
GENERAL_CHANNEL = "general"
GENERAL_DEFAULT = "vera"


def avatar_url(name: str) -> str:
    return f"https://api.dicebear.com/9.x/bottts-neutral/png?seed=turichips-{name}"
