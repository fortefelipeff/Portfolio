import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Union

class TirePressureBackend:
    """
    Backend puro para cálculo de pressões e registro de sessões.
    O método calculate retorna apenas resultados calculados.
    new_session armazena dados brutos + setup.
    export_report garante inclusão e ordenação dos campos calculados agrupados por pneu.
    """

    def __init__(self):
        # armazena cada sessão como um dicionário de inputs brutos + setup
        self._sessions: List[Dict[str, Union[str, float]]] = []

    def calculate(self, data: Dict[str, float]) -> Dict[str, float]:
        """
        data deve conter chaves de pressões e temperaturas:
          - target_FL, target_FR, target_RL, target_RR
          - cold_FL, cold_FR, cold_RL, cold_RR
          - hot_FL, hot_FR, hot_RL, hot_RR
          - air1, track1, air2, track2
        Retorna dict com:
          - new_cold_*, corr_air_*, corr_track_*
        """
        # converte temperaturas para Kelvin
        air1K   = data.get('air1', 0.0) + 273.15
        air2K   = data.get('air2', 0.0) + 273.15
        track1K = data.get('track1', 0.0) + 273.15
        track2K = data.get('track2', 0.0) + 273.15

        results: Dict[str, float] = {}
        for t in ['FL', 'FR', 'RL', 'RR']:
            tgt   = data.get(f"target_{t}", 0.0)
            cold  = data.get(f"cold_{t}",   0.0)
            hot   = data.get(f"hot_{t}",    1.0) or 1.0

            new_cold   = cold * tgt / hot
            corr_air   = new_cold * air2K / air1K if air1K else 0.0
            new_cold_b = new_cold / 14.504
            corr_track = (((new_cold_b + 1) * air2K) /
                          ((air2K * (new_cold_b + 1) / (new_cold_b + 1)) +
                           (track2K - track1K)) - 1) * 14.504 if track1K else 0.0

            results[f"new_cold_{t}"]   = round(new_cold,   2)
            results[f"corr_air_{t}"]   = round(corr_air,   2)
            results[f"corr_track_{t}"] = round(corr_track, 2)

        return results

    def new_session(self,
                    info: Dict[str, str],
                    pressures: Dict[str, float],
                    temps: Dict[str, float],
                    setup: Dict[str, float]) -> None:
        """
        Registra uma nova sessão apenas com os dados brutos e setup,
        sem adicionar campos calculados.
        """
        rec: Dict[str, Union[str, float]] = {}
        rec.update(info)
        rec.update(pressures)
        rec.update(temps)
        rec.update(setup)
        rec['timestamp'] = datetime.now().isoformat()
        self._sessions.append(rec)

    def get_sessions(self) -> List[Dict[str, Union[str, float]]]:
        """Retorna todas as sessões armazenadas (inputs brutos + setup)."""
        return list(self._sessions)

    def export_report(self, path: str) -> None:
        """
        Exporta todas as sessões (inputs + setup + campos calculados) para Excel ou CSV.
        Inclui e ordena colunas calculadas agrupadas por pneu (FL, FR, RL, RR).
        """
        # Prepara registros completos com cálculos
        complete_records: List[Dict[str, Union[str, float]]] = []
        for rec in self._sessions:
            full = dict(rec)
            calc_input = {k: v for k, v in full.items()
                          if k.startswith(('target_', 'cold_', 'hot_', 'air', 'track'))}
            full.update(self.calculate(calc_input))
            complete_records.append(full)

        df = pd.DataFrame(complete_records)

        # Ordena colunas calculadas por pneu: FL, FR, RL, RR
        tire_order = ['FL', 'FR', 'RL', 'RR']
        calc_cols = []
        for t in tire_order:
            calc_cols += [f"new_cold_{t}", f"corr_air_{t}", f"corr_track_{t}"]

        # Mantém colunas originais na ordem, depois adiciona calc_cols em sequência
        original = [c for c in df.columns if c not in calc_cols]
        df = df[original + calc_cols]

        out = Path(path)
        if out.suffix.lower() in ['.xlsx', '.xls']:
            try:
                df.to_excel(out, index=False)
            except ModuleNotFoundError:
                df.to_csv(out.with_suffix('.csv'), index=False)
        else:
            df.to_csv(out, index=False)

if __name__ == "__main__":
    # teste rápido
    backend = TirePressureBackend()
    info = {'session_name': 'Teste', 'start_time': '10:00', 'end_time': '10:30'}
    pressures = {
        'target_FL': 28.5, 'target_FR': 28.5, 'target_RL': 28.5, 'target_RR': 28.5,
        'cold_FL':   25.0, 'cold_FR':   25.5, 'cold_RL':   24.8, 'cold_RR':   25.2,
        'hot_FL':    32.0, 'hot_FR':    31.8, 'hot_RL':    32.1, 'hot_RR':    31.9
    }
    temps = {'air1': 30.0, 'track1': 35.0, 'air2': 32.0, 'track2': 36.5}
    setup = {'de': 1.2, 'dd': 1.3, 'te': 2.1, 'td': 2.0, 'asa': 5.0}

    backend.new_session(info, pressures, temps, setup)
    backend.export_report('report.xlsx')
    print('Relatório gerado com colunas calculadas agrupadas por pneu em report.xlsx')
