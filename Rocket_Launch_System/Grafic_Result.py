import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent


def safe_show():
    try:
        plt.show(block=False)
        plt.pause(0.1)
    except Exception:
        pass


def resolve_input_path(source_path=None):
    def pick_from_directory(directory):
        preferred_names = ["simulation_results.csv", "simulation_results.txt", "test.txt"]
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

# Optional args: <input_path> <output_directory>
if len(sys.argv) > 1:
    input_path = resolve_input_path(sys.argv[1])
else:
    input_path = resolve_input_path()

# optional output directory for saved images
out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None

rows = []
try:
    if input_path is None or not input_path.exists():
        raise FileNotFoundError

    if input_path.suffix.lower() == ".csv":
        data = pd.read_csv(input_path, comment="#")

        if {"Time_s", "Altitude_m", "Velocity_kmh", "Acceleration_m_s2", "Fuel_kg"}.issubset(data.columns):
            rows = [
                {
                    "Time": float(row["Time_s"]),
                    "Altitude": float(row["Altitude_m"]),
                    "Velocity": float(row["Velocity_kmh"]),
                    "Acceleration": float(row["Acceleration_m_s2"]),
                    "Fuel": float(row["Fuel_kg"]),
                    "Direction": float(row["Direction_deg"]) if "Direction_deg" in data.columns and pd.notna(row.get("Direction_deg")) else None,
                }
                for _, row in data.iterrows()
            ]
        elif {"Time", "Pos_X", "Pos_Y", "Fuel"}.issubset(data.columns):
            time_values = pd.to_numeric(data["Time"], errors="coerce").to_numpy(dtype=float)
            pos_x = pd.to_numeric(data["Pos_X"], errors="coerce").to_numpy(dtype=float)
            pos_y = pd.to_numeric(data["Pos_Y"], errors="coerce").to_numpy(dtype=float)
            fuel_values = pd.to_numeric(data["Fuel"], errors="coerce").to_numpy(dtype=float)
            phase_values = pd.to_numeric(data["Phase"], errors="coerce").to_numpy(dtype=float) if "Phase" in data.columns else None

            earth_radius_m = 6371000.0
            altitude_m = np.sqrt(pos_x ** 2 + pos_y ** 2) - earth_radius_m

            if len(time_values) > 1:
                vx = np.gradient(pos_x, time_values)
                vy = np.gradient(pos_y, time_values)
                speed_m_s = np.sqrt(vx ** 2 + vy ** 2)
                acceleration_m_s2 = np.gradient(speed_m_s, time_values)
                direction_deg = (np.degrees(np.arctan2(vy, vx)) + 360.0) % 360.0
            else:
                speed_m_s = np.zeros_like(time_values)
                acceleration_m_s2 = np.zeros_like(time_values)
                direction_deg = np.full_like(time_values, np.nan, dtype=float)

            rows = [
                {
                    "Time": float(time_values[i]),
                    "Altitude": float(altitude_m[i]),
                    "Velocity": float(speed_m_s[i] * 3.6),
                    "Acceleration": float(acceleration_m_s2[i]),
                    "Fuel": float(fuel_values[i]),
                    "Direction": float(direction_deg[i]),
                    "Phase": float(phase_values[i]) if phase_values is not None and not np.isnan(phase_values[i]) else None,
                }
                for i in range(len(time_values))
            ]
        else:
            missing_columns = {"Time_s", "Altitude_m", "Velocity_kmh", "Acceleration_m_s2", "Fuel_kg", "Time", "Pos_X", "Pos_Y", "Fuel"} - set(data.columns)
            raise ValueError(f"Missing columns in CSV: {', '.join(sorted(missing_columns))}")
    else:
        # Legacy space-separated format written by older versions of the simulator
        legacy_rows = []
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.lstrip().startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 11:
                    continue

                try:
                    time_s = float(parts[0])
                    altitude_value = float(parts[1])
                    altitude_unit = parts[2]
                    velocity_value = float(parts[3])
                    velocity_unit = parts[4]
                    acceleration_m_s2 = float(parts[5])
                    fuel_kg = float(parts[7])
                    direction_deg = float(parts[9]) if len(parts) >= 10 else None
                except ValueError:
                    continue

                altitude_m = altitude_value * 1000.0 if altitude_unit == "km" else altitude_value
                velocity_kmh = velocity_value * 3.6 if velocity_unit == "m/s" else velocity_value

                legacy_rows.append(
                    {
                        "Time": time_s,
                        "Altitude": altitude_m,
                        "Velocity": velocity_kmh,
                        "Acceleration": acceleration_m_s2,
                        "Fuel": fuel_kg,
                        "Direction": direction_deg,
                    }
                )

        rows = legacy_rows
except FileNotFoundError:
    print("Error: data file not found.")
    print(f"Checked folder: {script_dir}")
    print("Pass a folder or file path: python Grafic_Result.py <folder-or-file>")
    sys.exit(1)

if not rows:
    print("Error: no valid rows were found in the file. Make sure the file was generated by the C program.")
    sys.exit(1)

data = pd.DataFrame(rows)

has_direction = data["Direction"].notna().any()

# Convert altitude to kilometers for better readability in the graph
data['Altitude_km'] = data['Altitude'] / 1000.0

# 2. Configure subplots: altitude, velocity, acceleration, and optional direction
if has_direction:
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 15), sharex=True)
else:
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# 1st chart: altitude over time
ax1.plot(data['Time'], data['Altitude_km'], color='blue', linewidth=2, label='Altitude')
ax1.set_ylabel('Altitude (km)')
ax1.set_title('Launch Telemetry (Simulation)')
ax1.grid(True, linestyle='--')
ax1.legend()

# 2nd chart: velocity over time
ax2.plot(data['Time'], data['Velocity'], color='red', linewidth=2, label='Velocity')
ax2.set_ylabel('Velocity (km/h)')
ax2.grid(True, linestyle='--')
ax2.legend()

# 3rd chart: acceleration over time
ax3.plot(data['Time'], data['Acceleration'], color='green', linewidth=2, label='Acceleration')
ax3.set_xlabel('Time (s)')
ax3.set_ylabel('Acceleration (m/s²)')
ax3.grid(True, linestyle='--')
ax3.legend()

if has_direction:
    ax4.plot(data['Time'], data['Direction'], color='purple', linewidth=2, label='Direction')
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Direction (deg)')
    ax4.grid(True, linestyle='--')
    ax4.legend()
else:
    ax3.set_xlabel('Time (s)')

# Optimize layout
plt.tight_layout()

# 3. Save the graph as a PNG file in the specified output directory (or next to input file if not provided)
if out_dir is not None:
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    output_graph_path = out_dir / f"{input_path.stem}_graph.png"
else:
    output_graph_path = input_path.with_name(f"{input_path.stem}_graph.png")
plt.savefig(output_graph_path, dpi=300)

# 4. Show the graph and print a success message
print(f"Graph generated successfully and saved as '{output_graph_path.name}'!")
try:
    os.startfile(str(output_graph_path))
except Exception:
    pass
safe_show()