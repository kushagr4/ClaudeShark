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

# Candidate vs champion, at a per-move budget close to the competition's.
# Do not lower the time control to get games faster: see PROJECT.md.
CHAMPION ?= champions/v0_2
GAMES ?= 120

suite:
	uv run python -m tools.arena --opponent $(CHAMPION) --games $(GAMES) \
		--base-ms 20000 --increment-ms 200 --ply-cap 200

bench:
	uv run python -m tools.bench --ms 4500

# Deterministic head-to-head depth comparison at the real per-move budget.
compare:
	uv run python -m tools.bench --ms 4500 --engine $(CHAMPION)
	uv run python -m tools.bench --ms 4500

zip:
	uv run python -m harness.package

gate:
	uv run ruff check .
	uv run mypy
	uv run python -m pytest -q
	uv run python -m harness.arena --opponent baselines/random --games 2 --base-ms 5000
