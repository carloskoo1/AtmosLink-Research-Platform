from __future__ import annotations

RULES={
"characterization_replication":{
 "interpretation":"The exploratory association is not stable across development periods and should not be promoted.",
 "alternatives":[
  "The initial association may be a development-period fluctuation.",
  "The relationship may depend on an unmodeled time-varying regime."
 ],
 "tests":[
  "Require sign and effect-direction stability across prespecified contiguous temporal blocks.",
  "Retain the candidate as screened out unless a newly registered formulation is tested without reusing failed evidence as confirmation."
 ]},
"temporal_cycle_control":{
 "interpretation":"The apparent association is not robust to temporal trend or diurnal-cycle control and should not be promoted.",
 "alternatives":[
  "Shared time-of-day structure may explain both atmospheric and RF variation.",
  "Slow temporal drift may create an association without a direct atmospheric-to-RF relationship."
 ],
 "tests":[
  "Use same-clock or seasonally matched controls.",
  "Test residual association after prespecified temporal-trend adjustment."
 ]},
"temporal_independence":{
 "interpretation":"The candidate lacks stable event-level temporal independence and should not be promoted.",
 "alternatives":[
  "Serial dependence may inflate block-level support.",
  "Repeated observations from the same regime may create pseudoreplication."
 ],
 "tests":[
  "Re-express support using refractory event episodes rather than row counts.",
  "Require directionally consistent results across contiguous temporal folds."
 ]},
"strict_temporal_direction":{
 "interpretation":"The candidate fails temporal precedence and should not be promoted as a precursor.",
 "alternatives":[
  "The atmospheric and RF events may reflect a shared regime.",
  "The atmospheric transition may be coincident with or downstream of RF change."
 ],
 "tests":[
  "Compare prespecified pre-event and post-event RF entry counts around independent atmospheric events.",
  "Require post-event excess to preserve direction across temporal folds."
 ]},
"matched_trajectory_screening":{
 "interpretation":"The matched trajectory association fails the registered robustness controls and should not be promoted.",
 "alternatives":[
  "The association may reflect persistent context rather than a directional precursor.",
  "The result may be sensitive to outcome definition or control support."
 ],
 "tests":[
  "Apply prespecified same-clock matched controls and multiplicity correction.",
  "Use post-event trajectories as a negative-control check for temporal precedence."
 ]},
"strict_pre_post_temporal_direction":{
 "interpretation":"The apparent enrichment does not preserve pre/post temporal ordering and should not be promoted.",
 "alternatives":[
  "A shared environmental regime may create enrichment without directional precedence.",
  "Temporal clustering may produce apparent block-level association."
 ],
 "tests":[
  "Require post-only RF entries to exceed pre-only entries under the registered event window.",
  "Do not access the confirmatory holdout for a candidate that already fails development directionality."
 ]}
}

def render(candidate:dict)->dict:
    gate=candidate["failed_gate"]
    if gate not in RULES:
        raise KeyError(f"Unregistered failed gate: {gate}")
    r=RULES[gate]
    return {
      "candidate_id":candidate["candidate_id"],
      "system":"B0_DETERMINISTIC_TEMPLATE",
      "description":r["interpretation"],
      "alternative_explanations":list(r["alternatives"]),
      "falsification_tests":list(r["tests"]),
      "recommended_action":"SCREEN_OUT",
      "numeric_claims_generated":False,
      "validation_status_claimed":False
    }
