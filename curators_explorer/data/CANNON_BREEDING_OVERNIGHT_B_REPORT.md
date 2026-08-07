# Breeding literary canons

Each parent is a converged direction of a gain-hard pruning path, together with its converged reader weights and survivor set. Children are bred by mixing half the jurors of one parent with half of the other (jury_mix) or by seeding from the top-25 books of the summed parent directions (direction_mix), then pushed through the same pruning machinery. A child breeds true if its deepest direction is within 0.85 correlation of a parent (and not within 0.05 of both); it leans at 0.60; otherwise it is a new canon.

Runtime: **1107s**. Semantic context loaded only after every direction was frozen.

## Parent pool

| canon | parent path | canon stage | exact @50 | broad @50 | anti @50 | survivors |
|---|---|---:|---:|---:|---:|---:|
| teacher_p65_s25::s5 | teacher_p65_s25 | 5 | 4 | 8 | 17 | 14,662 |
| teacher_p65_s25::s3 | teacher_p65_s25 | 3 | 3 | 4 | 21 | 43,753 |
| contrastive_careful::s4 | contrastive_careful | 4 | 9 | 16 | 6 | 24,923 |
| contrastive_careful::s5 | contrastive_careful | 5 | 8 | 14 | 18 | 12,073 |
| pairwise_bilateral::s5 | pairwise_bilateral | 5 | 9 | 14 | 10 | 15,284 |
| pairwise_bilateral::s4 | pairwise_bilateral | 4 | 8 | 13 | 4 | 29,760 |

Parent direction correlations:

| | teacher_p65_s25::s5 | teacher_p65_s25::s3 | contrastive_careful::s4 | contrastive_careful::s5 | pairwise_bilateral::s5 | pairwise_bilateral::s4 |
|---|---|---|---|---|---|---|
| teacher_p65_s25::s5 | 1.00 | 0.38 | 0.36 | 0.33 | 0.38 | 0.45 |
| teacher_p65_s25::s3 | 0.38 | 1.00 | 0.02 | -0.07 | 0.05 | 0.12 |
| contrastive_careful::s4 | 0.36 | 0.02 | 1.00 | 0.70 | 0.82 | 0.79 |
| contrastive_careful::s5 | 0.33 | -0.07 | 0.70 | 1.00 | 0.61 | 0.53 |
| pairwise_bilateral::s5 | 0.38 | 0.05 | 0.82 | 0.61 | 1.00 | 0.88 |
| pairwise_bilateral::s4 | 0.45 | 0.12 | 0.79 | 0.53 | 0.88 | 1.00 |

## Does breeding converge?

### jury_mix (321 children)

- Converged (final step corr >= 0.999): **271/321**.
- Breeds true to one parent: **62**.
- Ties (within 0.05 of both; breeds true to the family): **2**.
- Leans to a parent: **106**.
- New canon (below 0.60 to both): **151**.
- Stopped at stage 0 (already an attractor; no pruning happened): **5**.

| pair | cos A | cos B | class | exact @50 | broad @50 | anti @50 |
|---|---:|---:|---|---:|---:|---:|
| contrastive_careful::s4 x contrastive_careful::s5 | 0.021 | 0.275 | new | 8 | 14 | 11 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.453 | 0.633 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.446 | 0.636 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.459 | 0.637 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.471 | 0.654 | lean:contrastive_careful::s5 | 8 | 14 | 23 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.427 | 0.609 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.440 | 0.621 | lean:contrastive_careful::s5 | 8 | 14 | 23 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.444 | 0.631 | lean:contrastive_careful::s5 | 8 | 14 | 23 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.458 | 0.636 | lean:contrastive_careful::s5 | 8 | 14 | 23 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.441 | 0.633 | lean:contrastive_careful::s5 | 8 | 14 | 25 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.455 | 0.636 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.454 | 0.634 | lean:contrastive_careful::s5 | 7 | 13 | 23 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.477 | 0.659 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.461 | 0.637 | lean:contrastive_careful::s5 | 7 | 13 | 25 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.423 | 0.604 | lean:contrastive_careful::s5 | 8 | 14 | 23 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.427 | 0.600 | lean:contrastive_careful::s5 | 7 | 13 | 25 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.456 | 0.649 | lean:contrastive_careful::s5 | 8 | 14 | 21 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.452 | 0.630 | lean:contrastive_careful::s5 | 8 | 14 | 21 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.463 | 0.642 | lean:contrastive_careful::s5 | 8 | 14 | 21 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.432 | 0.616 | lean:contrastive_careful::s5 | 7 | 13 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.426 | 0.617 | lean:contrastive_careful::s5 | 7 | 13 | 24 |
| contrastive_careful::s4 x love_center | 0.732 | 0.002 | lean:contrastive_careful::s4 | 0 | 0 | 6 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.845 | 0.885 | ties:pairwise_bilateral::s4/contrastive_careful::s4 | 5 | 10 | 11 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.813 | 0.869 | true:pairwise_bilateral::s4 | 5 | 9 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.808 | 0.864 | true:pairwise_bilateral::s4 | 5 | 9 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.806 | 0.865 | true:pairwise_bilateral::s4 | 5 | 8 | 19 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.810 | 0.867 | true:pairwise_bilateral::s4 | 5 | 8 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.808 | 0.864 | true:pairwise_bilateral::s4 | 5 | 8 | 19 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.803 | 0.867 | true:pairwise_bilateral::s4 | 5 | 8 | 19 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.813 | 0.859 | ties:pairwise_bilateral::s4/contrastive_careful::s4 | 5 | 9 | 22 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.807 | 0.864 | true:pairwise_bilateral::s4 | 5 | 8 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.809 | 0.861 | true:pairwise_bilateral::s4 | 5 | 8 | 20 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.804 | 0.867 | true:pairwise_bilateral::s4 | 5 | 9 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.808 | 0.860 | true:pairwise_bilateral::s4 | 5 | 9 | 19 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.810 | 0.864 | true:pairwise_bilateral::s4 | 5 | 8 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.805 | 0.871 | true:pairwise_bilateral::s4 | 5 | 10 | 15 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.807 | 0.866 | true:pairwise_bilateral::s4 | 5 | 9 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.808 | 0.862 | true:pairwise_bilateral::s4 | 5 | 9 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.810 | 0.866 | true:pairwise_bilateral::s4 | 5 | 9 | 19 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.808 | 0.862 | true:pairwise_bilateral::s4 | 5 | 8 | 20 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.806 | 0.863 | true:pairwise_bilateral::s4 | 5 | 8 | 20 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.810 | 0.863 | true:pairwise_bilateral::s4 | 5 | 10 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.805 | 0.867 | true:pairwise_bilateral::s4 | 6 | 11 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.864 | 0.772 | true:contrastive_careful::s4 | 4 | 9 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.828 | 0.736 | lean:contrastive_careful::s4 | 4 | 10 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.824 | 0.729 | lean:contrastive_careful::s4 | 4 | 10 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.819 | 0.731 | lean:contrastive_careful::s4 | 4 | 8 | 12 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.825 | 0.732 | lean:contrastive_careful::s4 | 4 | 11 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.816 | 0.729 | lean:contrastive_careful::s4 | 4 | 7 | 12 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.818 | 0.723 | lean:contrastive_careful::s4 | 4 | 9 | 14 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.826 | 0.729 | lean:contrastive_careful::s4 | 4 | 10 | 15 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.815 | 0.728 | lean:contrastive_careful::s4 | 4 | 8 | 11 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.816 | 0.723 | lean:contrastive_careful::s4 | 4 | 9 | 14 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.821 | 0.732 | lean:contrastive_careful::s4 | 4 | 9 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.825 | 0.732 | lean:contrastive_careful::s4 | 4 | 9 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.815 | 0.725 | lean:contrastive_careful::s4 | 4 | 8 | 13 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.816 | 0.729 | lean:contrastive_careful::s4 | 5 | 10 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.827 | 0.733 | lean:contrastive_careful::s4 | 4 | 11 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.827 | 0.735 | lean:contrastive_careful::s4 | 4 | 9 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.820 | 0.731 | lean:contrastive_careful::s4 | 4 | 8 | 11 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.819 | 0.733 | lean:contrastive_careful::s4 | 4 | 9 | 14 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.820 | 0.731 | lean:contrastive_careful::s4 | 4 | 10 | 14 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.826 | 0.732 | lean:contrastive_careful::s4 | 4 | 9 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.811 | 0.723 | lean:contrastive_careful::s4 | 4 | 7 | 11 |
| contrastive_careful::s5 x love_center | 0.467 | 0.003 | new | 0 | 0 | 6 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.628 | 0.896 | true:pairwise_bilateral::s4 | 7 | 13 | 15 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.632 | 0.859 | true:pairwise_bilateral::s4 | 6 | 11 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.630 | 0.849 | lean:pairwise_bilateral::s4 | 6 | 11 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.552 | 0.888 | true:pairwise_bilateral::s4 | 6 | 10 | 19 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.623 | 0.868 | true:pairwise_bilateral::s4 | 6 | 11 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.626 | 0.852 | true:pairwise_bilateral::s4 | 6 | 11 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.629 | 0.851 | true:pairwise_bilateral::s4 | 6 | 11 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.628 | 0.850 | lean:pairwise_bilateral::s4 | 7 | 12 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.622 | 0.856 | true:pairwise_bilateral::s4 | 5 | 9 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.629 | 0.846 | lean:pairwise_bilateral::s4 | 6 | 12 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.624 | 0.865 | true:pairwise_bilateral::s4 | 5 | 10 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.628 | 0.856 | true:pairwise_bilateral::s4 | 6 | 12 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.568 | 0.898 | true:pairwise_bilateral::s4 | 6 | 12 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.628 | 0.860 | true:pairwise_bilateral::s4 | 6 | 11 | 23 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.620 | 0.862 | true:pairwise_bilateral::s4 | 6 | 12 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.628 | 0.860 | true:pairwise_bilateral::s4 | 6 | 12 | 20 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.636 | 0.850 | lean:pairwise_bilateral::s4 | 6 | 13 | 20 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.622 | 0.862 | true:pairwise_bilateral::s4 | 6 | 11 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.616 | 0.867 | true:pairwise_bilateral::s4 | 6 | 11 | 23 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.620 | 0.860 | true:pairwise_bilateral::s4 | 6 | 12 | 23 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.638 | 0.851 | true:pairwise_bilateral::s4 | 6 | 11 | 23 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | -0.044 | -0.075 | new | 4 | 8 | 12 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.218 | 0.011 | new | 4 | 7 | 31 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.197 | -0.006 | new | 4 | 7 | 27 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.223 | 0.015 | new | 4 | 8 | 27 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.172 | -0.044 | new | 4 | 7 | 33 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.303 | 0.108 | new | 4 | 7 | 28 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.315 | 0.113 | new | 4 | 7 | 25 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.170 | -0.067 | new | 4 | 8 | 31 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.294 | 0.110 | new | 4 | 7 | 24 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.121 | 0.101 | new | 4 | 8 | 13 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.288 | 0.094 | new | 4 | 8 | 24 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.226 | -0.003 | new | 4 | 7 | 33 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.252 | 0.064 | new | 4 | 8 | 28 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.275 | 0.092 | new | 4 | 9 | 25 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.295 | 0.097 | new | 4 | 8 | 26 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.158 | -0.029 | new | 4 | 6 | 28 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.306 | 0.133 | new | 4 | 8 | 25 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.259 | 0.075 | new | 4 | 8 | 28 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.267 | 0.068 | new | 4 | 7 | 28 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.173 | -0.052 | new | 4 | 7 | 32 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.157 | -0.085 | new | 4 | 8 | 32 |
| pairwise_bilateral::s4 x love_center | 0.762 | 0.002 | lean:pairwise_bilateral::s4 | 0 | 0 | 6 |
| pairwise_bilateral::s5 x love_center | 0.653 | 0.003 | lean:pairwise_bilateral::s5 | 0 | 0 | 6 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.811 | 0.955 | true:pairwise_bilateral::s4 | 7 | 12 | 18 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.803 | 0.927 | true:pairwise_bilateral::s4 | 7 | 11 | 19 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.806 | 0.924 | true:pairwise_bilateral::s4 | 7 | 11 | 22 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.805 | 0.925 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.791 | 0.921 | true:pairwise_bilateral::s4 | 7 | 11 | 19 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.795 | 0.923 | true:pairwise_bilateral::s4 | 7 | 12 | 20 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.804 | 0.927 | true:pairwise_bilateral::s4 | 7 | 12 | 23 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.800 | 0.926 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.802 | 0.925 | true:pairwise_bilateral::s4 | 7 | 11 | 23 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.794 | 0.917 | true:pairwise_bilateral::s4 | 7 | 11 | 20 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.809 | 0.929 | true:pairwise_bilateral::s4 | 7 | 11 | 22 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.808 | 0.928 | true:pairwise_bilateral::s4 | 7 | 11 | 24 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.801 | 0.921 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.806 | 0.926 | true:pairwise_bilateral::s4 | 7 | 11 | 22 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.806 | 0.928 | true:pairwise_bilateral::s4 | 7 | 12 | 18 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.798 | 0.921 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.792 | 0.917 | true:pairwise_bilateral::s4 | 7 | 11 | 19 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.792 | 0.915 | true:pairwise_bilateral::s4 | 7 | 11 | 19 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.798 | 0.924 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.798 | 0.926 | true:pairwise_bilateral::s4 | 7 | 11 | 22 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.796 | 0.922 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.569 | -0.274 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.549 | -0.259 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.548 | -0.260 | new | 0 | 1 | 9 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.547 | -0.255 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.551 | -0.253 | new | 0 | 1 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.555 | -0.256 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.553 | -0.250 | new | 0 | 1 | 9 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.552 | -0.260 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.553 | -0.259 | new | 0 | 1 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.555 | -0.251 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.553 | -0.257 | new | 0 | 1 | 10 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.551 | -0.258 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.548 | -0.259 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.552 | -0.254 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.549 | -0.258 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.553 | -0.251 | new | 0 | 1 | 10 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.554 | -0.256 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.552 | -0.252 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.559 | -0.252 | new | 0 | 1 | 9 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.552 | -0.259 | new | 0 | 1 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.549 | -0.255 | new | 0 | 1 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.439 | -0.305 | new | 0 | 1 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.387 | -0.257 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.395 | -0.258 | new | 0 | 0 | 15 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.488 | -0.284 | new | 0 | 2 | 10 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.486 | -0.294 | new | 0 | 2 | 10 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.385 | -0.254 | new | 0 | 0 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.393 | -0.257 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.483 | -0.308 | new | 0 | 2 | 10 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.489 | -0.290 | new | 0 | 2 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.387 | -0.252 | new | 0 | 0 | 15 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.383 | -0.251 | new | 0 | 0 | 15 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.389 | -0.256 | new | 0 | 0 | 16 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.384 | -0.251 | new | 0 | 0 | 15 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.386 | -0.251 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.388 | -0.251 | new | 0 | 0 | 16 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.386 | -0.252 | new | 0 | 0 | 16 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.386 | -0.250 | new | 0 | 0 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.391 | -0.256 | new | 0 | 0 | 16 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.385 | -0.254 | new | 0 | 0 | 16 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.389 | -0.251 | new | 0 | 0 | 17 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.381 | -0.252 | new | 0 | 0 | 13 |
| teacher_p65_s25::s3 x love_center | 0.446 | 0.048 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.625 | -0.067 | lean:teacher_p65_s25::s3 | 2 | 4 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.616 | -0.067 | lean:teacher_p65_s25::s3 | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.615 | -0.067 | lean:teacher_p65_s25::s3 | 1 | 3 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.618 | -0.060 | lean:teacher_p65_s25::s3 | 1 | 3 | 15 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.617 | -0.063 | lean:teacher_p65_s25::s3 | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.617 | -0.060 | lean:teacher_p65_s25::s3 | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.619 | -0.066 | lean:teacher_p65_s25::s3 | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.619 | -0.062 | lean:teacher_p65_s25::s3 | 1 | 3 | 17 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.614 | -0.066 | lean:teacher_p65_s25::s3 | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.613 | -0.066 | lean:teacher_p65_s25::s3 | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.619 | -0.057 | lean:teacher_p65_s25::s3 | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.616 | -0.067 | lean:teacher_p65_s25::s3 | 1 | 3 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.617 | -0.063 | lean:teacher_p65_s25::s3 | 1 | 3 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.616 | -0.065 | lean:teacher_p65_s25::s3 | 1 | 3 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.614 | -0.070 | lean:teacher_p65_s25::s3 | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.617 | -0.061 | lean:teacher_p65_s25::s3 | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.618 | -0.063 | lean:teacher_p65_s25::s3 | 1 | 3 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.615 | -0.062 | lean:teacher_p65_s25::s3 | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.613 | -0.062 | lean:teacher_p65_s25::s3 | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.614 | -0.065 | lean:teacher_p65_s25::s3 | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.617 | -0.067 | lean:teacher_p65_s25::s3 | 1 | 2 | 14 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.518 | -0.349 | new | 1 | 3 | 8 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.475 | -0.338 | new | 1 | 2 | 9 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.480 | -0.331 | new | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.482 | -0.331 | new | 1 | 1 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.479 | -0.330 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.484 | -0.330 | new | 1 | 1 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.485 | -0.331 | new | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.481 | -0.332 | new | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.473 | -0.338 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.479 | -0.333 | new | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.486 | -0.326 | new | 1 | 2 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.487 | -0.328 | new | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.477 | -0.337 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.481 | -0.330 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.486 | -0.327 | new | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.482 | -0.331 | new | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.480 | -0.336 | new | 1 | 2 | 14 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.481 | -0.334 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.482 | -0.330 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.483 | -0.329 | new | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.490 | -0.329 | new | 1 | 2 | 13 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.436 | 0.680 | lean:contrastive_careful::s4 | 5 | 9 | 15 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.415 | 0.651 | lean:contrastive_careful::s4 | 5 | 8 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.414 | 0.659 | lean:contrastive_careful::s4 | 5 | 9 | 21 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.409 | 0.649 | lean:contrastive_careful::s4 | 6 | 11 | 18 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.404 | 0.651 | lean:contrastive_careful::s4 | 6 | 10 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.409 | 0.645 | lean:contrastive_careful::s4 | 6 | 11 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.406 | 0.653 | lean:contrastive_careful::s4 | 5 | 10 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.413 | 0.652 | lean:contrastive_careful::s4 | 6 | 10 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.418 | 0.659 | lean:contrastive_careful::s4 | 5 | 10 | 21 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.406 | 0.645 | lean:contrastive_careful::s4 | 6 | 11 | 18 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.410 | 0.659 | lean:contrastive_careful::s4 | 6 | 10 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.408 | 0.645 | lean:contrastive_careful::s4 | 7 | 12 | 17 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.416 | 0.649 | lean:contrastive_careful::s4 | 6 | 11 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.402 | 0.650 | lean:contrastive_careful::s4 | 6 | 10 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.408 | 0.651 | lean:contrastive_careful::s4 | 5 | 9 | 18 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.405 | 0.654 | lean:contrastive_careful::s4 | 5 | 9 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.407 | 0.649 | lean:contrastive_careful::s4 | 5 | 10 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.397 | 0.654 | lean:contrastive_careful::s4 | 5 | 10 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.410 | 0.653 | lean:contrastive_careful::s4 | 5 | 9 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.413 | 0.652 | lean:contrastive_careful::s4 | 6 | 12 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.409 | 0.650 | lean:contrastive_careful::s4 | 5 | 10 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.380 | 0.113 | new | 5 | 7 | 9 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.344 | 0.192 | new | 6 | 9 | 8 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.332 | 0.184 | new | 4 | 6 | 9 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.339 | 0.179 | new | 5 | 8 | 11 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.343 | 0.030 | new | 4 | 6 | 6 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.325 | 0.179 | new | 5 | 8 | 10 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.365 | 0.259 | new | 6 | 9 | 10 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.337 | 0.184 | new | 6 | 8 | 12 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.335 | 0.192 | new | 6 | 8 | 13 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.347 | 0.058 | new | 5 | 8 | 7 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.324 | 0.183 | new | 4 | 6 | 13 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.346 | 0.128 | new | 6 | 8 | 7 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.343 | 0.122 | new | 7 | 11 | 7 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.343 | 0.106 | new | 6 | 9 | 11 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.334 | 0.204 | new | 6 | 8 | 10 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.339 | 0.198 | new | 6 | 8 | 10 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.310 | 0.128 | new | 3 | 6 | 10 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.345 | 0.192 | new | 6 | 9 | 11 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.327 | 0.045 | new | 3 | 6 | 7 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.328 | 0.191 | new | 4 | 6 | 10 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.338 | 0.187 | new | 4 | 6 | 11 |
| teacher_p65_s25::s5 x love_center | 0.368 | 0.003 | new | 0 | 0 | 6 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.459 | 0.813 | lean:pairwise_bilateral::s4 | 4 | 7 | 23 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.498 | 0.841 | lean:pairwise_bilateral::s4 | 8 | 13 | 20 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.509 | 0.851 | true:pairwise_bilateral::s4 | 9 | 14 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.483 | 0.833 | lean:pairwise_bilateral::s4 | 5 | 10 | 21 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.515 | 0.852 | true:pairwise_bilateral::s4 | 7 | 12 | 18 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.492 | 0.835 | lean:pairwise_bilateral::s4 | 7 | 12 | 17 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.511 | 0.850 | true:pairwise_bilateral::s4 | 7 | 12 | 21 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.497 | 0.840 | lean:pairwise_bilateral::s4 | 7 | 12 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.482 | 0.827 | lean:pairwise_bilateral::s4 | 6 | 11 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.489 | 0.836 | lean:pairwise_bilateral::s4 | 7 | 12 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.507 | 0.847 | lean:pairwise_bilateral::s4 | 8 | 13 | 16 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.500 | 0.839 | lean:pairwise_bilateral::s4 | 7 | 12 | 18 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.501 | 0.844 | lean:pairwise_bilateral::s4 | 6 | 11 | 20 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.501 | 0.839 | lean:pairwise_bilateral::s4 | 7 | 12 | 17 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.497 | 0.839 | lean:pairwise_bilateral::s4 | 8 | 13 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.485 | 0.832 | lean:pairwise_bilateral::s4 | 7 | 12 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.510 | 0.848 | lean:pairwise_bilateral::s4 | 7 | 12 | 16 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.504 | 0.843 | lean:pairwise_bilateral::s4 | 6 | 11 | 20 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.480 | 0.829 | lean:pairwise_bilateral::s4 | 7 | 12 | 20 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.512 | 0.851 | true:pairwise_bilateral::s4 | 7 | 12 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.507 | 0.847 | lean:pairwise_bilateral::s4 | 7 | 12 | 17 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.460 | 0.545 | new | 4 | 8 | 24 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.435 | 0.349 | new | 6 | 10 | 23 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.448 | 0.336 | new | 8 | 11 | 25 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.407 | 0.274 | new | 4 | 7 | 31 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.416 | 0.299 | new | 4 | 7 | 30 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.466 | 0.370 | new | 5 | 10 | 18 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.425 | 0.313 | new | 6 | 9 | 26 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.444 | 0.359 | new | 5 | 8 | 28 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.455 | 0.403 | new | 5 | 7 | 27 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.445 | 0.322 | new | 7 | 11 | 22 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.447 | 0.403 | new | 6 | 9 | 23 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.450 | 0.392 | new | 6 | 11 | 20 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.444 | 0.345 | new | 8 | 13 | 15 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.447 | 0.352 | new | 7 | 13 | 14 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.430 | 0.327 | new | 7 | 12 | 25 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.453 | 0.403 | new | 8 | 11 | 28 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.451 | 0.366 | new | 6 | 8 | 26 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.444 | 0.349 | new | 6 | 10 | 28 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.436 | 0.361 | new | 8 | 14 | 16 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.379 | 0.237 | new | 4 | 7 | 32 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.451 | 0.345 | new | 7 | 11 | 17 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.125 | 0.397 | new | 0 | 2 | 4 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.007 | 0.343 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.008 | 0.343 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.010 | 0.352 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.011 | 0.349 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.012 | 0.346 | new | 0 | 1 | 14 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.007 | 0.346 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.007 | 0.345 | new | 0 | 1 | 15 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.010 | 0.349 | new | 0 | 1 | 11 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.006 | 0.343 | new | 0 | 1 | 14 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.007 | 0.348 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.010 | 0.347 | new | 0 | 1 | 14 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.012 | 0.351 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.009 | 0.343 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.008 | 0.345 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.012 | 0.350 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.011 | 0.346 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.011 | 0.345 | new | 0 | 1 | 14 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.010 | 0.346 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.007 | 0.349 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.013 | 0.349 | new | 0 | 1 | 12 |

### direction_mix (15 children)

- Converged (final step corr >= 0.999): **14/15**.
- Breeds true to one parent: **3**.
- Ties (within 0.05 of both; breeds true to the family): **0**.
- Leans to a parent: **2**.
- New canon (below 0.60 to both): **10**.
- Stopped at stage 0 (already an attractor; no pruning happened): **0**.

| pair | cos A | cos B | class | exact @50 | broad @50 | anti @50 |
|---|---:|---:|---|---:|---:|---:|
| contrastive_careful::s4 x contrastive_careful::s5 | 0.517 | 0.562 | new | 7 | 13 | 19 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.733 | 0.863 | true:pairwise_bilateral::s4 | 1 | 2 | 7 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.417 | 0.380 | new | 5 | 11 | 31 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.453 | 0.878 | true:pairwise_bilateral::s4 | 1 | 2 | 7 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.310 | 0.203 | new | 4 | 10 | 15 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.372 | 0.299 | new | 7 | 13 | 31 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | -0.130 | 0.497 | new | 8 | 14 | 28 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.106 | -0.377 | new | 0 | 0 | 28 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | -0.028 | 0.347 | new | 10 | 15 | 29 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | -0.053 | 0.397 | new | 8 | 13 | 30 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.446 | 0.753 | lean:contrastive_careful::s4 | 4 | 6 | 3 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.445 | 0.462 | new | 4 | 6 | 3 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.466 | 0.905 | true:pairwise_bilateral::s4 | 5 | 9 | 5 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.472 | 0.749 | lean:pairwise_bilateral::s5 | 6 | 10 | 5 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.377 | 0.157 | new | 17 | 23 | 12 |

## Attraction matrix (jury_mix; entry = true:A : true:B : ties : lean:A : lean:B : new over children of the pair)

| A \ B | teacher_p65_s25::s5 | teacher_p65_s25::s3 | contrastive_careful::s4 | contrastive_careful::s5 | pairwise_bilateral::s5 | pairwise_bilateral::s4 |
|---|---|---|---|---|---|---|
| teacher_p65_s25::s5 | - | 0:0:0:0:0:21 | 0:0:0:0:21:0 | 0:0:0:0:0:21 | 0:0:0:0:0:21 | 0:4:0:0:17:0 |
| teacher_p65_s25::s3 | 0:0:0:0:0:21 | - | 0:0:0:0:0:21 | 0:0:0:0:0:21 | 0:0:0:0:0:21 | 0:0:0:21:0:0 |
| contrastive_careful::s4 | 0:0:0:21:0:0 | 0:0:0:0:0:21 | - | 0:0:0:0:20:1 | 1:0:0:20:0:0 | 0:19:2:0:0:0 |
| contrastive_careful::s5 | 0:0:0:0:0:21 | 0:0:0:0:0:21 | 0:0:0:20:0:1 | - | 0:0:0:0:0:21 | 0:17:0:0:4:0 |
| pairwise_bilateral::s5 | 0:0:0:0:0:21 | 0:0:0:0:0:21 | 0:1:0:0:20:0 | 0:0:0:0:0:21 | - | 0:21:0:0:0:0 |
| pairwise_bilateral::s4 | 4:0:0:17:0:0 | 0:0:0:0:21:0 | 19:0:2:0:0:0 | 17:0:0:4:0:0 | 21:0:0:0:0:0 | - |

## Controls (self-breeding, random-mix, generations)

| child | mode | class | cos to A @deepest | exact @50 | anti @50 |
|---|---:|---:|---:|---:|---:|
| teacher_p65_s25::s5xteacher_p65_s25::s5::jm | self | self:drifted | 0.34943991899490356 | 5 | 15 |
| teacher_p65_s25::s5xrandom::jm | control | control | -0.10195888578891754 | 0 | 23 |
| teacher_p65_s25::s3xteacher_p65_s25::s3::jm | self | self:drifted | 0.4125729203224182 | 0 | 17 |
| teacher_p65_s25::s3xrandom::jm | control | control | 0.05271665006875992 | 0 | 21 |
| contrastive_careful::s4xcontrastive_careful::s4::jm | self | self:stable | 0.8500638008117676 | 9 | 14 |
| contrastive_careful::s4xrandom::jm | control | control | 0.6030118465423584 | 0 | 25 |
| contrastive_careful::s5xcontrastive_careful::s5::jm | self | self:drifted | 0.14006005227565765 | 6 | 18 |
| contrastive_careful::s5xrandom::jm | control | control | 0.4932032823562622 | 0 | 22 |
| pairwise_bilateral::s5xpairwise_bilateral::s5::jm | self | self:drifted | 0.6978515386581421 | 9 | 9 |
| pairwise_bilateral::s5xrandom::jm | control | control | 0.4690917432308197 | 0 | 25 |
| pairwise_bilateral::s4xpairwise_bilateral::s4::jm | self | self:stable | 0.9572464227676392 | 7 | 12 |
| pairwise_bilateral::s4xrandom::jm | control | control | 0.5758657455444336 | 0 | 25 |
| gen0::pairwise_bilateral::s5xpairwise_bilateral::s4 | generation | new | 0.37152814865112305 | 7 | 31 |
| gen1::contrastive_careful::s4xcontrastive_careful::s5 | generation | new | 0.5171910524368286 | 7 | 19 |
| gen2::gen0::pairwise_bilateral::s5xpairwise_bilateral::s4xgen1::contrastive_careful::s4xcontrastive_careful::s5 | generation | new | 0.20971256494522095 | 3 | 27 |
| gen3::teacher_p65_s25::s5xteacher_p65_s25::s3 | generation | new | 0.3771601915359497 | 17 | 12 |
| gen4::gen2::gen0::pairwise_bilateral::s5xpairwise_bilateral::s4xgen1::contrastive_careful::s4xcontrastive_careful::s5xgen3::teacher_p65_s25::s5xteacher_p65_s25::s3 | generation | new | 0.4716247320175171 | 3 | 18 |

## Increment size: does a larger increment converge more strongly?

| variant | children | mean final step corr | breed-true rate | new-canons | mean exact @50 |
|---|---:|---:|---:|---:|---:|
| hard_mult_0.75 | 6 | 0.99970 | 0.00 | 5 | 3.8 |
| hard_mult_1.0 | 6 | 0.99993 | 0.17 | 4 | 4.2 |
| hard_mult_1.5 | 6 | 0.99996 | 0.17 | 4 | 3.2 |
| hard_mult_2.0 | 6 | 0.99948 | 0.00 | 3 | 0.0 |
| ladder_0.10 | 6 | 0.99957 | 0.00 | 4 | 0.5 |
| ladder_0.20 | 6 | 0.99995 | 0.17 | 4 | 1.5 |
| beta_3.5 | 6 | 0.99966 | 0.00 | 4 | 3.3 |
| beta_5.0 | 6 | 0.99985 | 0.00 | 5 | 5.0 |

## Polyamorous breeding (three parents)

- poly::teacher_p65_s25::s5+contrastive_careful::s4+pairwise_bilateral::s5::r0: class lean:contrastive_careful::s4, cos A/B 0.390/0.710, exact @50 9.
- poly::teacher_p65_s25::s5+contrastive_careful::s4+pairwise_bilateral::s5::r1: class lean:contrastive_careful::s4, cos A/B 0.390/0.710, exact @50 9.
- poly::teacher_p65_s25::s5+contrastive_careful::s4+pairwise_bilateral::s5::r2: class lean:contrastive_careful::s4, cos A/B 0.390/0.710, exact @50 9.

## Valley audits (unpaired 24-start census on the canon stage)

| object | literary pole | mixed | mirror pole |
|---|---:|---:|---:|
| teacher_p65_s25::s5 | 20 | 2 | 2 |
| teacher_p65_s25::s3 | 22 | 0 | 2 |
| contrastive_careful::s4 | 21 | 1 | 2 |
| contrastive_careful::s5 | 4 | 18 | 2 |
| pairwise_bilateral::s5 | 24 | 0 | 0 |
| pairwise_bilateral::s4 | 15 | 0 | 9 |
| teacher_p65_s25::s5xteacher_p65_s25::s3::jm | 2 | 11 | 11 |
| teacher_p65_s25::s5xteacher_p65_s25::s3::dm | 19 | 4 | 1 |
| teacher_p65_s25::s5xcontrastive_careful::s5::jm | 4 | 11 | 9 |
| teacher_p65_s25::s5xcontrastive_careful::s5::dm | 12 | 2 | 10 |
| teacher_p65_s25::s5xpairwise_bilateral::s5::jm | 5 | 9 | 10 |
| teacher_p65_s25::s3xcontrastive_careful::s4::jm | 13 | 0 | 11 |

## New-canon heads (deepest stage)

### teacher_p65_s25::s5xteacher_p65_s25::s3::jm

exact/broad/anti @50 0/2/4.

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.910)
2. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.885)
3. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.866)
4. *Maus II: A Survivor's Tale: And Here My Troubles Began (Maus, #2)* — Art Spiegelman (0.856)
5. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.856)
6. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.855)
7. *If This Is a Man / The Truce* — Primo Levi (0.851)
8. *March: Book Two (March, #2)* — John             Lewis (0.837)
9. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.832)
10. *Between the World and Me* — Ta-Nehisi Coates (0.829)

### teacher_p65_s25::s5xteacher_p65_s25::s3::dm

exact/broad/anti @50 17/23/12.

1. *Crime and Punishment* — Fyodor Dostoyevsky (0.971)
2. *One Hundred Years of Solitude* — Gabriel Garcia Marquez (0.969)
3. *Anna Karenina* — Leo Tolstoy (0.957)
4. *Lolita* — Vladimir Nabokov (0.948)
5. *War and Peace* — Leo Tolstoy (0.947)
6. *The Master and Margarita* — Mikhail Bulgakov (0.945)
7. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.935)
8. *The Stranger* — Albert Camus (0.933)
9. *Stoner* — John  Williams (0.926)
10. *The Metamorphosis* — Franz Kafka (0.911)

### teacher_p65_s25::s5xcontrastive_careful::s5::jm

exact/broad/anti @50 5/7/9.

1. *Crime and Punishment* — Fyodor Dostoyevsky (0.847)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.842)
3. *Collected Fictions* — Jorge Luis Borges (0.811)
4. *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie (0.808)
5. *Labyrinths:  Selected Stories and Other Writings* — Jorge Luis Borges (0.785)
6. *Fullmetal Alchemist, Vol. 3 (Fullmetal Alchemist, #3)* — Hiromu Arakawa (0.784)
7. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.780)
8. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.768)
9. *The Poisonwood Bible* — Barbara Kingsolver (0.765)
10. *Ficciones* — Jorge Luis Borges (0.748)

### teacher_p65_s25::s5xcontrastive_careful::s5::dm

exact/broad/anti @50 4/6/3.

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.891)
2. *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie (0.881)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.870)
4. *Calvin and Hobbes* — Bill Watterson (0.865)
5. *Ficciones* — Jorge Luis Borges (0.862)
6. *Labyrinths:  Selected Stories and Other Writings* — Jorge Luis Borges (0.857)
7. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.843)
8. *1984* — George Orwell (0.835)
9. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.834)
10. *The Hate U Give* — Angie Thomas (0.830)

### teacher_p65_s25::s5xpairwise_bilateral::s5::jm

exact/broad/anti @50 4/8/24.

1. *East of Eden* — John Steinbeck (0.909)
2. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.890)
3. *The Things They Carried* — Tim O'Brien (0.886)
4. *The Importance of Being Earnest* — Oscar Wilde (0.877)
5. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.854)
6. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.834)
7. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.827)
8. *Hamlet* — William Shakespeare (0.821)
9. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.820)
10. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.815)

### teacher_p65_s25::s3xcontrastive_careful::s4::jm

exact/broad/anti @50 0/1/11.

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.878)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.848)
3. *The Complete Calvin and Hobbes* — Bill Watterson (0.846)
4. *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie (0.834)
5. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.818)
6. *Beard Science (Winston Brothers, #3)* — Penny Reid (0.815)
7. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.812)
8. *Calvin and Hobbes* — Bill Watterson (0.810)
9. *The Hate U Give* — Angie Thomas (0.806)
10. *More Than Forever (More Than, #4)* — Jay McLean (0.794)
