# Knowledge and Inference in Text-Based Worlds

## Changes, Notes, To-Do

### Saturday, May 7

- I've decided to try using an SQL database for storing my Knowledge
  Base. This let's me leverage the databases relational engine for
  efficiently querying predicates and aliases. For now, I think I will
  implement a very simple RE parser for my logic statements, but I might
  regret that and jump to Tatsu.
- Basic schema is:
  - Variables, i.e. all objects known or thought to exist in the world
  - Properties, instantiations of Predicates on given variables
    - One Properties table for each arity of Predicate (I add these
      dynamically as new Predicates are encountered)
  - Functions, i.e. a statement taking one or more arguments which
    evaluates to a single variable.
      - For this logic, functions may only be reasoned upon if they
        evaluate to an explicitly defined variable.
  - Predicates, abstract Predicates
  - Rules, rules for the outcomes of actions when certain preconditions
    are met.
- So far, I've got it working with Asking and Telling of
  Predicates/Properties. Still need to set up Rules and Functions.

### Friday, May 6

- Starting on RoverTwo, trying to choose best knowledge representation
  - Linear logic approach uses Tatsu and provides fully featured logic
    representation, but would require a couple of days just to learn the
    (separate) logic language

### Thursday, May 5

- RoverOne, a crude knowledge-based agent is able to solve all
  procedural mazes with significantly fewer moves than the NaiveAgent
  - I expected solution times to be the same for all runs, but there
    seem to be variations between runs. Maybe this is because the
    exploration module iterates over sets in the knowledge base, which
    might not behave deterministically?
  - RoverOne also visits significantly more spaces in a single
    runthrough than NaiveAgent
- RoverOne's knowledge base lacks the ability to distinguish between
  distinct rooms with the same name, which leads to inconsistent
  behavior. These are frequent in Zork I.
- TextWorld uses fairly idiosyncratic formatting for scene descriptions,
  which I have crudely handled.
- RoverOne recognizes an unsuccessful move action as one that results in
  the first non-blank line ending in a period. This seems to work in
  most cases, but is certainly exploiting a convention with no
  understanding.
- Now that I have a functional agent, I'd like to create a RoverTwo that
  uses a more standard logic representation

#### RoverOne in brief

1. Scan room description for words in a fixed list of directions, adding
   those words as 'exit' predicates to the knowledge base
2. Uses iterative deepening search to see if a path exists to the
   current goal (not relevant, because it does not currently have a
   means to determine a goal)
3. If a path exists, follow it, otherwise, pursue exploration goals
   a. If a stored exploration goal exists, pursue it
   b. If not, search the knowledge base for an 'exit' predicate without
   a matching 'go' function, and add that to exploration goals
   c. If no exploration goals are found, add all possible directions
   from the current location to the exploration goals (strike out
   randomly)
4. If traveling a direction from the current location leads to a new
   location, create a go(location, direction) = destination function in
   the KB
5. If traveling in a direction does not lead to a new location, add a
   circular go function to the KB (go(location, direction) = location)


### Monday, March 18

- for now, I will call my agent "ohotnik" (Russian for hunter)
- basic outline of approach
  - [x] write simple benchmark script that runs the agents on a set of
    games, collating and reporting results
  - generate a few TextWorld games for basic exploration, simple object
    interaction (take, open), complex object interaction (unlocking
    doors with keys)
  - write baseline Rover-1 agent (use static list of "go <direction>"
    actions to explore and route-find
  - begin working on knowledge-based agent
    - write initial parser
      - identify locations
      - parse descriptions into objects, properties and verbs
      - attempt to recognize action success, semantic action rejection
        (action not possible or relevant in current state), syntactic
        action rejection (action not understood by game parser)
      - suggest verbs for exploration by comparing word embeddings with
        a static verb list
    - write initial knowledge-base 
    

