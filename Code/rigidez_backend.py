# rigidez_backend.py
"""
Backend module para Gerenciador de Distribuição de Rigidez.
Contém todas as funções de cálculo que podem ser importadas e usadas pelo front-end.
"""
from typing import List, Tuple

# Tabelas de (posição, rigidez)
_front = [
    (1.0,  9.3),  (1.5, 10.15), (2.0, 11.0), (2.5, 12.65), (3.0, 14.3),
    (3.5, 17.0), (4.0, 19.7),  (4.5, 23.1),  (5.0, 26.5),  (5.5, 28.2),
    (6.0, 29.9), (6.5, 26.9),  (7.0, 23.9)
]
_rear  = [
    (1.0,  15.4), (1.5, 16.4),  (2.0, 17.4), (2.5, 19.4), (3.0, 21.4),
    (3.5, 24.9),  (4.0, 28.4),  (4.5, 33.45),(5.0, 38.5), (5.5, 42.55),
    (6.0, 46.6),  (6.5, 45.05), (7.0, 43.5)
]

# Dicionários para lookup rápido posição → rigidez
_front_dict = dict(_front)
_rear_dict  = dict(_rear)


def _calcula_rigidez(posicoes: List[float], tabela_dict: dict) -> float:
    """
    Retorna a rigidez de um eixo a partir das posições informadas.

    Args:
        posicoes: lista com duas posições (ex: [2.0, 2.5]).
        tabela_dict: dicionário posição→rigidez.

    Returns:
        valor de rigidez correspondente.

    Raises:
        ValueError: se a média das posições não estiver na tabela.
    """
    media = sum(posicoes) / len(posicoes)
    if media not in tabela_dict:
        raise ValueError(f"Média de posição {media} não encontrada na tabela.")
    return tabela_dict[media]


def get_rigidez(front_setup: List[float], rear_setup: List[float]) -> Tuple[float, float]:
    """
    Calcula a rigidez de cada eixo (dianteiro e traseiro).

    Args:
        front_setup: posições das barras dianteiras (ex: [2.0, 2.5]).
        rear_setup: posições das barras traseiras (ex: [6.0, 6.5]).

    Returns:
        tupla (rigidez_dianteira, rigidez_traseira).
    """
    rig_f = _calcula_rigidez(front_setup, _front_dict)
    rig_r = _calcula_rigidez(rear_setup, _rear_dict)
    return rig_f, rig_r


def get_distribution(front_setup: List[float], rear_setup: List[float]) -> float:
    """
    Calcula o percentual de distribuição da rigidez dianteira sobre o total.

    Args:
        front_setup: posições das barras dianteiras.
        rear_setup: posições das barras traseiras.

    Returns:
        percentual de rigidez dianteira (0-100).
    """
    rig_f, rig_r = get_rigidez(front_setup, rear_setup)
    return rig_f / (rig_f + rig_r) * 100


def find_setups(target_pct: float, tol_pct: float) -> List[Tuple[float, float, float]]:
    """
    Encontra todas as combinações de posições (frente, trás) cuja distribuição
    de rigidez do eixo dianteiro esteja dentro de target ± tol.

    Args:
        target_pct: percentual desejado (0-100).
        tol_pct: tolerância em ponto percentual.

    Returns:
        lista de tuplas (pos_frente, pos_traseira, distribuição_calculada),
        ordenadas pelo menor desvio em relação ao target.
    """
    resultados: List[Tuple[float, float, float]] = []
    for pf, vf in _front:
        for pr, vr in _rear:
            pct = vf / (vf + vr) * 100
            if abs(pct - target_pct) <= tol_pct:
                resultados.append((pf, pr, pct))
    resultados.sort(key=lambda x: abs(x[2] - target_pct))
    return resultados
