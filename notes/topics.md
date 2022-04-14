# Particularly interesting questions
## 04-14-22

### Exploiting and Ignoring Conventions

While adventure games place few formal constraints on what actions are
allowable, or how those actions might affect the game state, most games
adhere to common conventions. Those conventions might be from real life
or literary genres (e.g. keys unlock doors and interesting things are
hidden under beds), or they might be specific to text adventure games
(e.g. movement is along cardinal directions and is generally performed
by typing 'go [direction]). Knowledge of these conventions is important
for a successful play experience, but many of the puzzles at the center
of adventure games rely on defying conventions or expectations. For
instance, going northeast from Location A might reach Location B, but
going southwest from location B might not reach Location A, at least not
all the time!

How does an agent use conventions to simplify its search space, while
keeping the ability to abandon those conventions when percepts indicate
that they might no longer hold?

### Narrowing the Action Space

Theoretically, the action space of text adventure games is the set of
all strings on a game's character encoding set. In practice, these
strings follow a syntax of verb [noun phrase [adverb phrase]], (e.g.
_sleep_, _go north_, _take book_, _look under bed_, _unlock door with
red key_.) Likewise, the vocabulary is generally quite small, as every
accepted word was explicitly coded, either by the individual game's
authors or library authors. A well-designed game is expected to accept
synonyms wherever possible; a player should not struggle to find the
right word to communicate their intentions.

How can our agent appropriately focus its action space?
