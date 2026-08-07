{
 "seed": 20260819,
 "checks": [
  {
   "check": "parent_replay_size",
   "ok": true,
   "detail": "80000"
  },
  {
   "check": "random_tree_deterministic",
   "ok": true
  },
  {
   "check": "random_40k_union_equals_parent",
   "ok": true
  },
  {
   "check": "random_40k_disjoint",
   "ok": true
  },
  {
   "check": "random_20k_0_0_subset_of_40k",
   "ok": true
  },
  {
   "check": "random_20k_0_1_subset_of_40k",
   "ok": true
  },
  {
   "check": "random_20k_1_0_subset_of_40k",
   "ok": true
  },
  {
   "check": "random_20k_1_1_subset_of_40k",
   "ok": true
  },
  {
   "check": "random_20k_union_equals_parent",
   "ok": true
  },
  {
   "check": "random_20k_pairwise_disjoint",
   "ok": true
  },
  {
   "check": "random_20k_sizes",
   "ok": true
  },
  {
   "check": "rating_stats_alignment_hashes",
   "ok": true,
   "detail": "user+book payload hashes and mean lengths verified"
  },
  {
   "check": "spectral_tree_deterministic",
   "ok": true
  },
  {
   "check": "spectral_tree_sizes",
   "ok": true
  },
  {
   "check": "spectral_40k_union",
   "ok": true
  },
  {
   "check": "spectral_40k_disjoint",
   "ok": true
  },
  {
   "check": "spectral_20k_union",
   "ok": true
  },
  {
   "check": "median_split_ties_stable",
   "ok": true
  },
  {
   "check": "residual_csr_format",
   "ok": true
  },
  {
   "check": "residual_row_l2",
   "ok": true
  },
  {
   "check": "residual_empty_rows_ok",
   "ok": true
  },
  {
   "check": "residual_shape",
   "ok": true
  },
  {
   "check": "edge_ui_matches_parent_row",
   "ok": true
  },
  {
   "check": "edge_raw_id_roundtrip",
   "ok": true,
   "detail": "sampled 5 raw ids: [8, 8, 8, 8, 8]"
  },
  {
   "check": "spectral_edges_deterministic",
   "ok": true
  },
  {
   "check": "spectral_edge_coverage_valid",
   "ok": true,
   "detail": "parents=2400 with_edges=2400 empty_rows=0 empty_row_fraction=0.0000 nnz_nonempty_min=10 median=169.0 max=1546"
  },
  {
   "check": "spectral_members_are_payload_indices",
   "ok": true
  },
  {
   "check": "leading_direction_shape",
   "ok": true
  },
  {
   "check": "leading_direction_unit",
   "ok": true
  },
  {
   "check": "reversal_endpoint_shape",
   "ok": true
  },
  {
   "check": "reversal_direction_shape",
   "ok": true
  },
  {
   "check": "reversal_stage0_shape",
   "ok": true
  },
  {
   "check": "reversal_stages_positive",
   "ok": true
  },
  {
   "check": "reversal_deterministic",
   "ok": true
  },
  {
   "check": "reversal_no_semantics",
   "ok": true
  },
  {
   "check": "chunk_roundtrip",
   "ok": true
  },
  {
   "check": "chunk_spec_hash_rejected",
   "ok": true
  },
  {
   "check": "chunk_scope_change_rejected",
   "ok": true
  },
  {
   "check": "corrupt_chunk_detected",
   "ok": true
  },
  {
   "check": "cleanup_removed_chunks",
   "ok": true
  },
  {
   "check": "synthetic_two_mode_clustering",
   "ok": true
  },
  {
   "check": "recurrence_across_replicates",
   "ok": true
  },
  {
   "check": "single_replicate_not_recurrent",
   "ok": true
  },
  {
   "check": "convex_hull_beats_best_single",
   "ok": true
  },
  {
   "check": "cross_arm_maps_to_intended_modes",
   "ok": true
  },
  {
   "check": "cross_arm_original_index_not_filtered",
   "ok": true,
   "detail": "nearest_mode_index=1 id=recurrent_mode_0.50_p000_1 key=recur_cent_0.50_p000_1 distinct=1"
  },
  {
   "check": "fast_clustering_matches_census",
   "ok": true
  },
  {
   "check": "recurrence_null_nondegenerate_multiple_parents",
   "ok": true,
   "detail": "sd=0.1590 mean=0.7833"
  },
  {
   "check": "recurrence_slice_equals_direct",
   "ok": true,
   "detail": "sliced 12x12 similarity clustering matches direct vectors at all 3 taus"
  },
  {
   "check": "effective_dim_gram_matches_svd",
   "ok": true,
   "detail": "svd=27.166312 gram=27.166312"
  },
  {
   "check": "prereport_nulls_match_geometry",
   "ok": true,
   "detail": "14 null rows populated and matching geometry JSON"
  },
  {
   "check": "prereport_cross_arm_per_tau",
   "ok": true,
   "detail": "cross-arm rows are per-tau (not cumulative) and match geometry"
  },
  {
   "check": "unblind_not_run",
   "ok": true,
   "detail": "phase_unblind is implemented but never invoked during label-blind smoke"
  },
  {
   "check": "spectral_diagnostics_survive_consolidation",
   "ok": true,
   "detail": "parents=['0'] coverage=2400"
  },
  {
   "check": "census_json_sealed_in_geometry_and_manifest",
   "ok": true,
   "detail": "census json sha256 in geometry seal + manifest artifacts; geometry marked partial (smoke scope)"
  },
  {
   "check": "restricted_scope_rejected_without_allow_partial",
   "ok": true,
   "detail": "consolidate refused restricted scope"
  },
  {
   "check": "r20k_similarity_computed_once",
   "ok": true,
   "detail": "site counter=1 (expect 1), 8 r20k rows, stored sim matches direct product: True"
  },
  {
   "check": "semantic_firewall_artifacts",
   "ok": true,
   "detail": ""
  },
  {
   "check": "semantic_flag_false",
   "ok": true
  },
  {
   "check": "smoke_check_names_unique",
   "ok": true,
   "detail": "60 checks, 0 duplicate(s)"
  }
 ],
 "passed": true,
 "git_head": "bfd8ee315e2cec0134143cfa8b5420fb72d646c8",
 "runtime_seconds": 123.88392639160156
}