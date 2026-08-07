#!/usr/bin/env python3
"""
doctor.py (raíz) — lanzador
===========================

El diagnóstico de verdad vive en chinesereads-carousel/doctor.py y necesita
ejecutarse desde ahí: busca assets/, posts/ y el entorno virtual junto a sí
mismo. Ejecutado desde la raíz reportaría que falta todo.

Este fichero redirige al de verdad, con el Python del venv si existe:

    python3 doctor.py
"""

import os
import subprocess
import sys
from pathlib import Path

SUB = Path(__file__).resolve().parent / "chinesereads-carousel"
REAL = SUB / "doctor.py"

if not REAL.exists():
    sys.exit(f"No encuentro {REAL}")

# El venv del subproyecto da un informe fiel; si no está, el Python actual
# sirve igual y el propio doctor avisará de que falta el entorno virtual.
venv_py = SUB / ".venv" / "bin" / "python"
if os.name == "nt":
    venv_py = SUB / ".venv" / "Scripts" / "python.exe"
python = str(venv_py) if venv_py.exists() else sys.executable

sys.exit(subprocess.call([python, str(REAL), *sys.argv[1:]], cwd=SUB))
