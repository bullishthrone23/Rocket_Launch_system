import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import os


script_dir = Path(__file__).resolve().parent


def resolve_input_path(source_path=None):
	def pick_from_directory(directory):
		preferred_names = ["simulation_results.csv", "simulation_results.txt"]
		for name in preferred_names:
			candidate = directory / name
			if candidate.exists():
				return candidate

		candidates = list(directory.glob("*.csv")) + list(directory.glob("*.txt"))
		if candidates:
			return max(candidates, key=lambda path: path.stat().st_mtime)

		return None

	if source_path is None:
		for candidate in [script_dir / "output", script_dir]:
			resolved = pick_from_directory(candidate)
			if resolved is not None:
				return resolved
		return script_dir / "output" / "simulation_results.csv"

	candidate_path = Path(source_path)
	if candidate_path.is_dir():
		resolved = pick_from_directory(candidate_path)
		return resolved if resolved is not None else candidate_path / "simulation_results.csv"

	if candidate_path.is_absolute():
		return candidate_path

	cwd_candidate = Path.cwd() / candidate_path
	if cwd_candidate.exists():
		return cwd_candidate

	script_candidate = script_dir / candidate_path
	if script_candidate.exists():
		return script_candidate

	return cwd_candidate


input_path = resolve_input_path(sys.argv[1] if len(sys.argv) > 1 else None)

if input_path is None or not input_path.exists():
	print("Error: data file not found.")
	print(f"Checked folder: {script_dir}")
	print("Pass a folder or file path: python Trajectory_Graph.py <folder-or-file>")
	sys.exit(1)

df = pd.read_csv(input_path, comment="#")

if {"Pos_X", "Pos_Y"}.issubset(df.columns):
	pos_x = df["Pos_X"] / 1000.0
	pos_y = df["Pos_Y"] / 1000.0
elif {"Pos_X_m", "Pos_Y_m"}.issubset(df.columns):
	pos_x = df["Pos_X_m"] / 1000.0
	pos_y = df["Pos_Y_m"] / 1000.0
else:
	raise ValueError("Missing trajectory columns: expected Pos_X/Pos_Y or Pos_X_m/Pos_Y_m.")

fig, ax = plt.subplots(figsize=(8, 8))

# Earth and atmosphere
ax.add_patch(plt.Circle((0, 0), 6371, color="blue", alpha=0.3, label="Earth"))
ax.add_patch(plt.Circle((0, 0), 6471, color="cyan", fill=False, linestyle="--", label="Atmosphere (100 km)"))

# Trajectory
ax.plot(pos_x, pos_y, color="orange", linewidth=2, label="Trajectory")
ax.scatter(pos_x.iloc[0], pos_y.iloc[0], color="green", label="Launch")
ax.scatter(pos_x.iloc[-1], pos_y.iloc[-1], color="red", marker="X", label="End")

ax.set_aspect("equal")
ax.grid(True, linestyle=":", alpha=0.6)
ax.set_title("Earth Orbit Simulation")
ax.set_xlabel("X (km)")
ax.set_ylabel("Y (km)")
ax.legend()

plt.tight_layout()

# Optionally save the trajectory image into a provided output directory
if len(sys.argv) > 2:
	out_dir = Path(sys.argv[2])
	try:
		out_dir.mkdir(parents=True, exist_ok=True)
	except Exception:
		pass
	output_path = out_dir / f"{input_path.stem}_trajectory.png"
	plt.savefig(output_path, dpi=300)
	print(f"Trajectory saved to {output_path}")
	try:
		os.startfile(str(output_path))
	except Exception:
		pass

plt.show()