# Ch 9. Inference in First-Order Logic
## Russell and Norvig

### 9.1 Propositional vs First-Order Inference

One approach to first-order is to convert everything to propositional
logic and then use PC algorithms for inference.

Rule of Universal Instantiation says we can infer any sentence where
ground term is substituted for universally quantified variable.

for all v, alpha becomes Substitute({v/g}, alpha)

Rule of existential instantiation replaces existentially quantified
variable with new constant symbol.

there exists v, alpha becomes Substitute({v/k}, alpha)

(In other words, we create a new object and infer alpha about it. This
is a Skolem constant.)

#### 9.1.1 Reduction to propositional inference

Applying Universal and Existential instantiation, and replacing
Predicates with binary variables, we get sentences in PC. (One for every
object for every universal sentence.) Unfortunately, if any sentences
include functions, the set of all possible ground terms becomes
infinite. (Recursively applied function.)

Fortunately, we can use iterative deepening to limit the depth of
recursive functions and create a finite propositional subset.

This approach is complete, but semi-decidable. (We can find any
entailment exists, but we can never know for sure that a sentence is not
entailed.)
