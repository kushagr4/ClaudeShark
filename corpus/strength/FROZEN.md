# Strength-programme start sets (frozen)
source analysis\refresh_2026-09-05\top50_games.jsonl sha256 a975a4154469518c59c22032dbed4a0c7a194f210a79a982dc7764a4414b5e56
previous suite corpus\daily\pool\competition_actual_suite.jsonl (113 positions already played by internal arenas)
seed 20260905; 447 games, 239 distinct starts, 4 of ours excluded, 0 unsuitable, 129 fresh, 107 seen

dev        positions  50  side to move {'b': 43, 'w': 7}  sha256 80b61369d891f3dd895b1af5a6ae9b4489e1c05e7592e4a574691c2bb865cd91
val        positions  40  side to move {'b': 30, 'w': 10}  sha256 30f63a1fdb8acc1d9d0b00cb736e298a42c979ab328436816f8bfcb374948230
holdout_a  positions  50  side to move {'w': 11, 'b': 39}  sha256 a4da229e5975d6e67945ab9a86d678aaf4f9fb0aa1474b94e1ddb53091c8a20f
holdout_b  positions  50  side to move {'b': 36, 'w': 14}  sha256 ac121f5592cbc43502b117b0dd81399941d6c15be301f3010453f9b5a67b771f

positions in more than one set: 0 (must be 0)
dev: baseline + candidate screens. val: pre-promotion confirmation. holdout_a: qualification. holdout_b: confirmation. Never reshuffle.

holdout_c  positions  50  (29 fresh spares + 21 from val; seed 20260906; built 2026-09-06 05:01 as a second confirmation set)  sha256 8394781846871c162ccfdc360f0b875351d5943fde6c91dff4f8d8677d60a49e

# ~2400 stage sets (frozen 2026-09-06 08:50 UK): from corpus/competition_like_v1.jsonl (240 competition-like positions, suite hash 6a8111f22f9ea393), never used as game starts before; 0 unsuitable removed, 0 overlapping the 2300 sets removed; seed 20260906; 50 spare
dev2400        positions  50  sha256 5e0c2bd65a6e50e96c4b84c9e39585e3497c2744044d521c8303c6bc92204cd7
val2400        positions  40  sha256 1912a8f28c59f8aed68cda76b99f44c041e71abc8aac4f58ea154e8d1b23a0f6
holdout2400_a  positions  50  sha256 1f6f5e78e9871a263db919ab7f75e0a896f17817db2f18b138415eeb600a2f9d
holdout2400_b  positions  50  sha256 057371bf6360a6ed288eb6a0dcc67220ee71bbd22e652816f41aa133923c3d56
dev2400: baseline + screens. val2400: confirmation before promotion. holdout2400_a: qualification. holdout2400_b: confirmation. Never reshuffle.
