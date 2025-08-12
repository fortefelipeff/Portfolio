[Download .zip/.exe]([https://github.com/<usuario>/<repo>/releases/download/<TAG>/<NOME_DO_ARQUIVO>](https://github.com/fortefelipeff/Session-Management-Tool-in-.py-/releases/tag/v0.1))


# Session-Management-Tool-in-.py-

A system for managing tire pressures and anti-roll bar (ARB) stiffness distribution, designed for automotive and motorsport applications.

## Objective
The system allows engineers to log track sessions, compute tire pressure corrections based on environmental conditions, export reports, and analyze the car’s stiffness distribution to support setup decisions.

## Features
- Session logging with tire pressures (target, cold, hot) and ambient/track temperatures
- Automatic tire pressure correction calculations
- Report export to Excel or CSV
- Per-session notes and observations
- Calculation and search of front/rear ARB stiffness combinations
- Stiffness distribution heatmap visualization
- Modern, responsive GUI (PySide6)

## Requirements
- Python 3.8+
- See dependencies in requirements.txt

## Installation
1. Clone the repository or download the files.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the application:
   ```sh
   python Code/tire_pressure_app.py
   ```

## Project Structure
- `Code/tire_pressure_app.py`: Main GUI (PySide6)
- `Code/backend.py`: Logic for tire-pressure corrections and session export
- `Code/rigidez_backend.py`: Logic for stiffness distribution calculations and search
- `assets/images/`: UI images
- `requirements.txt`: Project dependencies

## Basic Usage
1. Fill in session data and tire pressures in the DATA ENTRY tab.
2. Click CALCULATE CORRECTIONS to get suggested adjustments.
3. Save sessions and export reports as needed.
4. In the RIGIDEZ BACKEND tab, compute and explore stiffness combinations and view the heatmap.

## Licence
See the LICENSE file for copyright and usage information.
