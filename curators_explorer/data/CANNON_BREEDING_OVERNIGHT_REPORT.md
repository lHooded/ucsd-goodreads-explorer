# Breeding literary canons

Each parent is a converged direction of a gain-hard pruning path, together with its converged reader weights and survivor set. Children are bred by mixing half the jurors of one parent with half of the other (jury_mix) or by seeding from the top-25 books of the summed parent directions (direction_mix), then pushed through the same pruning machinery. A child breeds true if its deepest direction is within 0.85 correlation of a parent (and not within 0.05 of both); it leans at 0.60; otherwise it is a new canon.

Runtime: **1338s**. Semantic context loaded only after every direction was frozen.

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

- Converged (final step corr >= 0.999): **275/321**.
- Breeds true to one parent: **62**.
- Ties (within 0.05 of both; breeds true to the family): **2**.
- Leans to a parent: **105**.
- New canon (below 0.60 to both): **152**.
- Stopped at stage 0 (already an attractor; no pruning happened): **5**.

| pair | cos A | cos B | class | exact @50 | broad @50 | anti @50 |
|---|---:|---:|---|---:|---:|---:|
| contrastive_careful::s4 x contrastive_careful::s5 | 0.021 | 0.275 | new | 8 | 14 | 11 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.443 | 0.623 | lean:contrastive_careful::s5 | 8 | 14 | 24 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.488 | 0.655 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.432 | 0.616 | lean:contrastive_careful::s5 | 8 | 14 | 24 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.438 | 0.621 | lean:contrastive_careful::s5 | 8 | 14 | 21 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.453 | 0.635 | lean:contrastive_careful::s5 | 8 | 14 | 24 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.418 | 0.596 | new | 8 | 14 | 24 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.466 | 0.647 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.460 | 0.645 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.435 | 0.611 | lean:contrastive_careful::s5 | 8 | 14 | 21 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.456 | 0.635 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.458 | 0.643 | lean:contrastive_careful::s5 | 8 | 14 | 23 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.469 | 0.648 | lean:contrastive_careful::s5 | 8 | 14 | 20 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.458 | 0.631 | lean:contrastive_careful::s5 | 8 | 14 | 24 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.436 | 0.611 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.448 | 0.628 | lean:contrastive_careful::s5 | 8 | 14 | 21 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.473 | 0.648 | lean:contrastive_careful::s5 | 8 | 14 | 19 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.463 | 0.648 | lean:contrastive_careful::s5 | 8 | 14 | 20 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.460 | 0.642 | lean:contrastive_careful::s5 | 8 | 14 | 24 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.450 | 0.629 | lean:contrastive_careful::s5 | 8 | 14 | 22 |
| contrastive_careful::s4 x contrastive_careful::s5 | 0.454 | 0.639 | lean:contrastive_careful::s5 | 8 | 14 | 24 |
| contrastive_careful::s4 x love_center | 0.732 | 0.002 | lean:contrastive_careful::s4 | 0 | 0 | 6 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.845 | 0.885 | ties:pairwise_bilateral::s4/contrastive_careful::s4 | 5 | 10 | 11 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.807 | 0.859 | true:pairwise_bilateral::s4 | 5 | 8 | 19 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.805 | 0.865 | true:pairwise_bilateral::s4 | 5 | 9 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.810 | 0.868 | true:pairwise_bilateral::s4 | 5 | 10 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.807 | 0.864 | true:pairwise_bilateral::s4 | 5 | 8 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.805 | 0.861 | true:pairwise_bilateral::s4 | 5 | 9 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.809 | 0.867 | true:pairwise_bilateral::s4 | 5 | 10 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.805 | 0.865 | true:pairwise_bilateral::s4 | 5 | 8 | 15 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.807 | 0.864 | true:pairwise_bilateral::s4 | 5 | 8 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.809 | 0.861 | true:pairwise_bilateral::s4 | 5 | 8 | 20 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.812 | 0.863 | true:pairwise_bilateral::s4 | 5 | 8 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.808 | 0.863 | true:pairwise_bilateral::s4 | 4 | 8 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.811 | 0.860 | ties:pairwise_bilateral::s4/contrastive_careful::s4 | 5 | 9 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.805 | 0.862 | true:pairwise_bilateral::s4 | 5 | 9 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.808 | 0.861 | true:pairwise_bilateral::s4 | 5 | 9 | 15 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.809 | 0.866 | true:pairwise_bilateral::s4 | 5 | 8 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.813 | 0.865 | true:pairwise_bilateral::s4 | 5 | 9 | 15 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.807 | 0.860 | true:pairwise_bilateral::s4 | 5 | 8 | 21 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.808 | 0.865 | true:pairwise_bilateral::s4 | 5 | 9 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.810 | 0.862 | true:pairwise_bilateral::s4 | 5 | 10 | 17 |
| contrastive_careful::s4 x pairwise_bilateral::s4 | 0.808 | 0.862 | true:pairwise_bilateral::s4 | 5 | 9 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.864 | 0.772 | true:contrastive_careful::s4 | 4 | 9 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.830 | 0.734 | lean:contrastive_careful::s4 | 4 | 10 | 15 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.814 | 0.729 | lean:contrastive_careful::s4 | 4 | 8 | 9 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.817 | 0.730 | lean:contrastive_careful::s4 | 4 | 9 | 11 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.828 | 0.737 | lean:contrastive_careful::s4 | 4 | 10 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.826 | 0.732 | lean:contrastive_careful::s4 | 4 | 10 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.826 | 0.733 | lean:contrastive_careful::s4 | 5 | 10 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.833 | 0.743 | lean:contrastive_careful::s4 | 4 | 10 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.817 | 0.730 | lean:contrastive_careful::s4 | 4 | 10 | 14 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.827 | 0.732 | lean:contrastive_careful::s4 | 4 | 11 | 14 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.825 | 0.729 | lean:contrastive_careful::s4 | 4 | 9 | 18 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.827 | 0.731 | lean:contrastive_careful::s4 | 4 | 11 | 15 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.818 | 0.728 | lean:contrastive_careful::s4 | 4 | 7 | 10 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.829 | 0.733 | lean:contrastive_careful::s4 | 4 | 9 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.828 | 0.732 | lean:contrastive_careful::s4 | 4 | 11 | 15 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.828 | 0.737 | lean:contrastive_careful::s4 | 4 | 9 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.826 | 0.732 | lean:contrastive_careful::s4 | 4 | 10 | 16 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.812 | 0.723 | lean:contrastive_careful::s4 | 4 | 9 | 12 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.827 | 0.734 | lean:contrastive_careful::s4 | 4 | 10 | 14 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.826 | 0.727 | lean:contrastive_careful::s4 | 4 | 10 | 15 |
| contrastive_careful::s4 x pairwise_bilateral::s5 | 0.823 | 0.731 | lean:contrastive_careful::s4 | 4 | 11 | 16 |
| contrastive_careful::s5 x love_center | 0.467 | 0.003 | new | 0 | 0 | 6 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.628 | 0.896 | true:pairwise_bilateral::s4 | 7 | 13 | 15 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.567 | 0.899 | true:pairwise_bilateral::s4 | 6 | 11 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.627 | 0.854 | true:pairwise_bilateral::s4 | 6 | 10 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.631 | 0.844 | lean:pairwise_bilateral::s4 | 6 | 11 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.629 | 0.849 | lean:pairwise_bilateral::s4 | 6 | 12 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.625 | 0.859 | true:pairwise_bilateral::s4 | 6 | 12 | 20 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.624 | 0.857 | true:pairwise_bilateral::s4 | 6 | 11 | 20 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.622 | 0.848 | lean:pairwise_bilateral::s4 | 6 | 11 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.537 | 0.891 | true:pairwise_bilateral::s4 | 6 | 10 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.567 | 0.892 | true:pairwise_bilateral::s4 | 6 | 11 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.536 | 0.891 | true:pairwise_bilateral::s4 | 6 | 11 | 20 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.619 | 0.871 | true:pairwise_bilateral::s4 | 6 | 11 | 23 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.628 | 0.852 | true:pairwise_bilateral::s4 | 6 | 12 | 19 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.617 | 0.866 | true:pairwise_bilateral::s4 | 6 | 11 | 23 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.623 | 0.867 | true:pairwise_bilateral::s4 | 6 | 11 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.634 | 0.853 | true:pairwise_bilateral::s4 | 6 | 11 | 22 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.629 | 0.854 | true:pairwise_bilateral::s4 | 7 | 13 | 19 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.622 | 0.870 | true:pairwise_bilateral::s4 | 6 | 11 | 20 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.627 | 0.862 | true:pairwise_bilateral::s4 | 6 | 12 | 23 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.567 | 0.894 | true:pairwise_bilateral::s4 | 6 | 11 | 21 |
| contrastive_careful::s5 x pairwise_bilateral::s4 | 0.628 | 0.859 | true:pairwise_bilateral::s4 | 6 | 11 | 24 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | -0.044 | -0.075 | new | 4 | 8 | 12 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.320 | 0.130 | new | 4 | 8 | 24 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.292 | 0.083 | new | 4 | 9 | 30 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.220 | 0.027 | new | 4 | 8 | 24 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.291 | 0.094 | new | 4 | 7 | 28 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.170 | -0.040 | new | 4 | 6 | 33 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.168 | -0.053 | new | 4 | 8 | 31 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.311 | 0.118 | new | 4 | 8 | 28 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.134 | 0.166 | new | 4 | 8 | 15 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.278 | 0.097 | new | 4 | 9 | 29 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.261 | 0.069 | new | 4 | 8 | 24 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.282 | 0.101 | new | 4 | 7 | 27 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.103 | 0.102 | new | 4 | 8 | 13 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.157 | -0.073 | new | 4 | 7 | 32 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.289 | 0.097 | new | 4 | 8 | 29 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.256 | 0.064 | new | 4 | 7 | 28 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.263 | 0.057 | new | 4 | 7 | 30 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.112 | 0.129 | new | 4 | 8 | 11 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.127 | 0.135 | new | 4 | 8 | 10 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.271 | 0.079 | new | 4 | 8 | 28 |
| contrastive_careful::s5 x pairwise_bilateral::s5 | 0.266 | 0.098 | new | 4 | 9 | 30 |
| pairwise_bilateral::s4 x love_center | 0.762 | 0.002 | lean:pairwise_bilateral::s4 | 0 | 0 | 6 |
| pairwise_bilateral::s5 x love_center | 0.653 | 0.003 | lean:pairwise_bilateral::s5 | 0 | 0 | 6 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.811 | 0.955 | true:pairwise_bilateral::s4 | 7 | 12 | 18 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.799 | 0.923 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.791 | 0.920 | true:pairwise_bilateral::s4 | 7 | 12 | 19 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.807 | 0.931 | true:pairwise_bilateral::s4 | 7 | 11 | 23 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.802 | 0.924 | true:pairwise_bilateral::s4 | 7 | 11 | 20 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.803 | 0.925 | true:pairwise_bilateral::s4 | 7 | 11 | 22 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.805 | 0.926 | true:pairwise_bilateral::s4 | 7 | 11 | 19 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.801 | 0.923 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.796 | 0.922 | true:pairwise_bilateral::s4 | 7 | 11 | 18 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.812 | 0.932 | true:pairwise_bilateral::s4 | 7 | 11 | 23 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.799 | 0.923 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.800 | 0.924 | true:pairwise_bilateral::s4 | 7 | 11 | 22 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.792 | 0.920 | true:pairwise_bilateral::s4 | 7 | 11 | 20 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.805 | 0.927 | true:pairwise_bilateral::s4 | 7 | 11 | 22 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.808 | 0.926 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.797 | 0.925 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.802 | 0.921 | true:pairwise_bilateral::s4 | 7 | 11 | 22 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.791 | 0.916 | true:pairwise_bilateral::s4 | 7 | 11 | 20 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.799 | 0.922 | true:pairwise_bilateral::s4 | 7 | 11 | 21 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.803 | 0.926 | true:pairwise_bilateral::s4 | 7 | 12 | 22 |
| pairwise_bilateral::s5 x pairwise_bilateral::s4 | 0.802 | 0.926 | true:pairwise_bilateral::s4 | 7 | 11 | 19 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.569 | -0.274 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.551 | -0.257 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.550 | -0.260 | new | 0 | 1 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.553 | -0.252 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.554 | -0.257 | new | 0 | 1 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.552 | -0.257 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.552 | -0.256 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.556 | -0.260 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.551 | -0.259 | new | 0 | 1 | 8 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.551 | -0.256 | new | 0 | 1 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.557 | -0.255 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.552 | -0.261 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.554 | -0.259 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.552 | -0.262 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.550 | -0.261 | new | 0 | 1 | 9 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.554 | -0.256 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.552 | -0.259 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.551 | -0.259 | new | 0 | 1 | 12 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.553 | -0.256 | new | 0 | 1 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.553 | -0.258 | new | 0 | 1 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s4 | 0.552 | -0.257 | new | 0 | 2 | 11 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.439 | -0.305 | new | 0 | 1 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.387 | -0.251 | new | 0 | 0 | 15 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.387 | -0.253 | new | 0 | 0 | 15 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.388 | -0.255 | new | 0 | 0 | 15 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.393 | -0.255 | new | 0 | 0 | 15 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.384 | -0.251 | new | 0 | 0 | 16 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.391 | -0.252 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.385 | -0.250 | new | 0 | 0 | 15 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.397 | -0.261 | new | 0 | 1 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.381 | -0.246 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.388 | -0.258 | new | 0 | 0 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.389 | -0.259 | new | 0 | 0 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.486 | -0.301 | new | 0 | 2 | 9 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.381 | -0.251 | new | 0 | 0 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.386 | -0.257 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.387 | -0.250 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.386 | -0.254 | new | 0 | 0 | 13 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.386 | -0.254 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.385 | -0.248 | new | 0 | 1 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.389 | -0.255 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x contrastive_careful::s5 | 0.473 | -0.343 | new | 0 | 2 | 9 |
| teacher_p65_s25::s3 x love_center | 0.446 | 0.048 | new | 0 | 0 | 14 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.625 | -0.067 | lean:teacher_p65_s25::s3 | 2 | 4 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.613 | -0.072 | lean:teacher_p65_s25::s3 | 1 | 3 | 14 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.613 | -0.067 | lean:teacher_p65_s25::s3 | 1 | 3 | 15 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.615 | -0.061 | lean:teacher_p65_s25::s3 | 2 | 4 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.616 | -0.063 | lean:teacher_p65_s25::s3 | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.615 | -0.074 | lean:teacher_p65_s25::s3 | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.617 | -0.070 | lean:teacher_p65_s25::s3 | 2 | 4 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.614 | -0.067 | lean:teacher_p65_s25::s3 | 1 | 2 | 14 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.614 | -0.069 | lean:teacher_p65_s25::s3 | 1 | 3 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.615 | -0.068 | lean:teacher_p65_s25::s3 | 2 | 4 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.617 | -0.073 | lean:teacher_p65_s25::s3 | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.616 | -0.063 | lean:teacher_p65_s25::s3 | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.615 | -0.072 | lean:teacher_p65_s25::s3 | 1 | 3 | 15 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.615 | -0.064 | lean:teacher_p65_s25::s3 | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.615 | -0.060 | lean:teacher_p65_s25::s3 | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.618 | -0.067 | lean:teacher_p65_s25::s3 | 1 | 2 | 14 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.613 | -0.067 | lean:teacher_p65_s25::s3 | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.614 | -0.064 | lean:teacher_p65_s25::s3 | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.615 | -0.064 | lean:teacher_p65_s25::s3 | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.614 | -0.070 | lean:teacher_p65_s25::s3 | 1 | 3 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s4 | 0.615 | -0.064 | lean:teacher_p65_s25::s3 | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.518 | -0.349 | new | 1 | 3 | 8 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.485 | -0.327 | new | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.483 | -0.331 | new | 1 | 3 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.488 | -0.331 | new | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.485 | -0.324 | new | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.483 | -0.335 | new | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.483 | -0.333 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.495 | -0.321 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.482 | -0.327 | new | 1 | 1 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.486 | -0.330 | new | 1 | 1 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.484 | -0.326 | new | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.488 | -0.331 | new | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.479 | -0.335 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.485 | -0.327 | new | 1 | 3 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.480 | -0.331 | new | 1 | 2 | 14 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.483 | -0.330 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.491 | -0.324 | new | 1 | 3 | 11 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.486 | -0.331 | new | 1 | 2 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.477 | -0.334 | new | 1 | 1 | 13 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.487 | -0.330 | new | 1 | 2 | 12 |
| teacher_p65_s25::s3 x pairwise_bilateral::s5 | 0.483 | -0.326 | new | 1 | 3 | 12 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.436 | 0.680 | lean:contrastive_careful::s4 | 5 | 9 | 15 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.408 | 0.651 | lean:contrastive_careful::s4 | 5 | 9 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.412 | 0.653 | lean:contrastive_careful::s4 | 5 | 11 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.406 | 0.644 | lean:contrastive_careful::s4 | 6 | 11 | 17 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.410 | 0.649 | lean:contrastive_careful::s4 | 5 | 10 | 18 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.411 | 0.654 | lean:contrastive_careful::s4 | 5 | 9 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.407 | 0.657 | lean:contrastive_careful::s4 | 6 | 10 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.409 | 0.651 | lean:contrastive_careful::s4 | 5 | 9 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.410 | 0.655 | lean:contrastive_careful::s4 | 5 | 9 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.405 | 0.652 | lean:contrastive_careful::s4 | 5 | 9 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.409 | 0.659 | lean:contrastive_careful::s4 | 5 | 9 | 18 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.407 | 0.649 | lean:contrastive_careful::s4 | 5 | 10 | 18 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.411 | 0.653 | lean:contrastive_careful::s4 | 5 | 10 | 17 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.408 | 0.651 | lean:contrastive_careful::s4 | 6 | 10 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.411 | 0.654 | lean:contrastive_careful::s4 | 5 | 9 | 21 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.413 | 0.653 | lean:contrastive_careful::s4 | 6 | 11 | 18 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.410 | 0.654 | lean:contrastive_careful::s4 | 5 | 10 | 20 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.411 | 0.658 | lean:contrastive_careful::s4 | 5 | 10 | 18 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.412 | 0.652 | lean:contrastive_careful::s4 | 5 | 9 | 18 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.408 | 0.645 | lean:contrastive_careful::s4 | 6 | 10 | 19 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.411 | 0.651 | lean:contrastive_careful::s4 | 5 | 9 | 22 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.380 | 0.113 | new | 5 | 7 | 9 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.315 | 0.173 | new | 3 | 5 | 9 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.325 | 0.181 | new | 4 | 6 | 12 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.345 | 0.195 | new | 5 | 8 | 10 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.311 | 0.092 | new | 4 | 6 | 5 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.334 | 0.185 | new | 5 | 7 | 11 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.322 | 0.186 | new | 6 | 9 | 11 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.346 | 0.194 | new | 5 | 8 | 11 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.312 | 0.183 | new | 4 | 7 | 11 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.328 | 0.190 | new | 6 | 9 | 12 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.318 | 0.131 | new | 5 | 7 | 9 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.337 | 0.189 | new | 7 | 10 | 11 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.337 | 0.198 | new | 6 | 8 | 11 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.336 | 0.192 | new | 6 | 9 | 11 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.302 | 0.036 | new | 3 | 5 | 7 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.342 | 0.198 | new | 8 | 11 | 9 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.337 | 0.180 | new | 6 | 8 | 10 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.330 | 0.165 | new | 7 | 9 | 9 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.338 | 0.199 | new | 5 | 8 | 13 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.315 | 0.129 | new | 5 | 8 | 9 |
| teacher_p65_s25::s5 x contrastive_careful::s5 | 0.330 | 0.186 | new | 5 | 8 | 9 |
| teacher_p65_s25::s5 x love_center | 0.368 | 0.003 | new | 0 | 0 | 6 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.459 | 0.813 | lean:pairwise_bilateral::s4 | 4 | 7 | 23 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.491 | 0.835 | lean:pairwise_bilateral::s4 | 7 | 12 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.503 | 0.844 | lean:pairwise_bilateral::s4 | 7 | 12 | 20 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.521 | 0.857 | true:pairwise_bilateral::s4 | 7 | 12 | 20 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.514 | 0.848 | lean:pairwise_bilateral::s4 | 7 | 12 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.518 | 0.854 | true:pairwise_bilateral::s4 | 6 | 11 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.509 | 0.847 | lean:pairwise_bilateral::s4 | 7 | 12 | 17 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.501 | 0.843 | lean:pairwise_bilateral::s4 | 8 | 13 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.511 | 0.848 | lean:pairwise_bilateral::s4 | 6 | 11 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.525 | 0.853 | true:pairwise_bilateral::s4 | 7 | 12 | 18 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.501 | 0.841 | lean:pairwise_bilateral::s4 | 7 | 12 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.500 | 0.841 | lean:pairwise_bilateral::s4 | 6 | 11 | 18 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.494 | 0.839 | lean:pairwise_bilateral::s4 | 7 | 12 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.510 | 0.846 | lean:pairwise_bilateral::s4 | 6 | 11 | 20 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.494 | 0.846 | lean:pairwise_bilateral::s4 | 6 | 11 | 20 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.498 | 0.839 | lean:pairwise_bilateral::s4 | 6 | 11 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.493 | 0.837 | lean:pairwise_bilateral::s4 | 6 | 11 | 20 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.506 | 0.843 | lean:pairwise_bilateral::s4 | 6 | 11 | 17 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.494 | 0.837 | lean:pairwise_bilateral::s4 | 7 | 12 | 18 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.508 | 0.846 | lean:pairwise_bilateral::s4 | 8 | 13 | 18 |
| teacher_p65_s25::s5 x pairwise_bilateral::s4 | 0.492 | 0.839 | lean:pairwise_bilateral::s4 | 7 | 12 | 18 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.460 | 0.545 | new | 4 | 8 | 24 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.504 | 0.442 | new | 5 | 8 | 13 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.451 | 0.347 | new | 6 | 13 | 18 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.380 | 0.224 | new | 4 | 6 | 32 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.448 | 0.333 | new | 6 | 10 | 24 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.455 | 0.331 | new | 6 | 11 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.433 | 0.355 | new | 6 | 11 | 25 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.408 | 0.290 | new | 6 | 10 | 24 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.451 | 0.343 | new | 7 | 11 | 21 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.415 | 0.294 | new | 4 | 7 | 27 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.444 | 0.365 | new | 6 | 9 | 24 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.404 | 0.266 | new | 5 | 7 | 28 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.417 | 0.286 | new | 5 | 8 | 27 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.441 | 0.370 | new | 6 | 9 | 19 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.448 | 0.367 | new | 5 | 8 | 26 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.435 | 0.323 | new | 7 | 12 | 14 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.446 | 0.319 | new | 8 | 14 | 17 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.418 | 0.308 | new | 4 | 6 | 30 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.475 | 0.386 | new | 5 | 8 | 32 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.439 | 0.317 | new | 7 | 10 | 21 |
| teacher_p65_s25::s5 x pairwise_bilateral::s5 | 0.414 | 0.315 | new | 5 | 8 | 30 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.125 | 0.397 | new | 0 | 2 | 4 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.006 | 0.345 | new | 0 | 1 | 15 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.009 | 0.348 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.010 | 0.346 | new | 0 | 1 | 14 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.011 | 0.344 | new | 0 | 1 | 14 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.005 | 0.348 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.012 | 0.345 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.009 | 0.344 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.008 | 0.345 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.008 | 0.348 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.005 | 0.346 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.008 | 0.345 | new | 0 | 1 | 14 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.009 | 0.346 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.009 | 0.348 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.008 | 0.344 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.011 | 0.347 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.013 | 0.346 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.012 | 0.348 | new | 0 | 1 | 12 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.006 | 0.344 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.008 | 0.347 | new | 0 | 1 | 13 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.008 | 0.343 | new | 0 | 1 | 13 |

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

## Attraction matrix (jury_mix; entry = true:A : true:B : ties : new over children of the pair)

| A \ B | teacher_p65_s25::s5 | teacher_p65_s25::s3 | contrastive_careful::s4 | contrastive_careful::s5 | pairwise_bilateral::s5 | pairwise_bilateral::s4 |
|---|---|---|---|---|---|---|
| teacher_p65_s25::s5 | - | 0:0:0:21 | 0:0:0:0 | 0:0:0:21 | 0:0:0:21 | 0:3:0:0 |
| teacher_p65_s25::s3 | 0:0:0:21 | - | 0:0:0:21 | 0:0:0:21 | 0:0:0:21 | 0:0:0:0 |
| contrastive_careful::s4 | 0:0:0:0 | 0:0:0:21 | - | 0:0:0:2 | 1:0:0:0 | 0:19:2:0 |
| contrastive_careful::s5 | 0:0:0:21 | 0:0:0:21 | 0:0:0:2 | - | 0:0:0:21 | 0:18:0:0 |
| pairwise_bilateral::s5 | 0:0:0:21 | 0:0:0:21 | 0:1:0:0 | 0:0:0:21 | - | 0:21:0:0 |
| pairwise_bilateral::s4 | 3:0:0:0 | 0:0:0:0 | 19:0:2:0 | 18:0:0:0 | 21:0:0:0 | - |

## Controls (self-breeding, random-mix, generations)

| child | mode | class | cos to A @deepest | exact @50 | anti @50 |
|---|---:|---:|---:|---:|---:|
| teacher_p65_s25::s5xteacher_p65_s25::s5::jm | self | self:drifted | 0.34943991899490356 | 5 | 15 |
| teacher_p65_s25::s5xrandom::jm | control | control | 0.17280349135398865 | 0 | 25 |
| teacher_p65_s25::s3xteacher_p65_s25::s3::jm | self | self:drifted | 0.4125729203224182 | 0 | 17 |
| teacher_p65_s25::s3xrandom::jm | control | control | 0.06039881333708763 | 0 | 25 |
| contrastive_careful::s4xcontrastive_careful::s4::jm | self | self:stable | 0.8500638008117676 | 9 | 14 |
| contrastive_careful::s4xrandom::jm | control | control | 0.5927085876464844 | 0 | 25 |
| contrastive_careful::s5xcontrastive_careful::s5::jm | self | self:drifted | 0.14006005227565765 | 6 | 18 |
| contrastive_careful::s5xrandom::jm | control | control | 0.46828728914260864 | 0 | 26 |
| pairwise_bilateral::s5xpairwise_bilateral::s5::jm | self | self:drifted | 0.6978515386581421 | 9 | 9 |
| pairwise_bilateral::s5xrandom::jm | control | control | 0.5858609676361084 | 0 | 26 |
| pairwise_bilateral::s4xpairwise_bilateral::s4::jm | self | self:stable | 0.9572464227676392 | 7 | 12 |
| pairwise_bilateral::s4xrandom::jm | control | control | 0.5371364951133728 | 0 | 25 |
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
