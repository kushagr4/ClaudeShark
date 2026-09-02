SHELL := /bin/bash

.PHONY: setup play arena zip gate test bench suite

setup:
	uv sync

test:
	uv run python -m pytest -q

play:
	uv run python -m harness.play --white . --black baselines/minimax $(if $(FEN),--fen "$(FEN)")

arena:
	uv run python -m harness.arena --opponent baselines/minimax --games 20

# Candidate vs champion, at a per-move budget close to what a full competition
# clock affords. Do not lower the time control to get games faster: see
# PROJECT.md. CS_INCREMENT_MS tells both engines the arena's real increment.
CHAMPION ?= champions/v0_3
GAMES ?= 120
DEPTH ?= 6

suite:
	CS_INCREMENT_MS=200 uv run python -m tools.arena --opponent $(CHAMPION) --games $(GAMES) \
		--base-ms 20000 --increment-ms 200 --ply-cap 200

bench:
	uv run python -m tools.bench --ms 4500

# Deterministic: fixed depth, so node counts are comparable run to run.
# This is the instrument for pruning changes.
compare:
	uv run python -m tools.bench --depth $(DEPTH)

# Which of PVS / null-move / LMR is actually paying for itself.
attribute:
	uv run python -m tools.attribute --depth $(DEPTH) --lmr-safe

# Are the moves any good, not just fast?
quality:
	uv run python -m tools.tactics --ms 1000
	uv run python -m tools.movequality --depth 6 --ref-depth 6 --suite sharp

profile:
	uv run python -m tools.profile_search --ms 3000 --positions 6
	uv run python -m tools.profile_eval

zip:
	uv run python -m harness.package

gate:
	uv run ruff check .
	uv run mypy
	uv run python -m pytest -q
	uv run python -m harness.arena --opponent baselines/random --games 2 --base-ms 5000
