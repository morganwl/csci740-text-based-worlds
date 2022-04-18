# Knowledge and Inference in Text-Based Worlds

## Changes, Notes, To-Do

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
    

