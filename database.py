import psycopg2
import streamlit as st

# =======================
# CONEXÃO
# =======================
def conectar():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=5432
    )

# =======================
# INSERÇÃO
# =======================
def inserir_partida(dados):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO partidas (
                usuario_id,
                time_usuario, time_adv, local, competicao, temporada, data, rodada,
                posse_usuario, remates_usuario, remates_a_baliza_usuario, xg_usuario,
                oportunidades_flagrantes_usuario, cantos_usuario, passes_totais_usuario,
                passes_certos_usuario, cruzamentos_totais_usuario, cruzamentos_certos_usuario,
                gols_usuario, posse_adv, remates_adv, remates_a_baliza_adv, xg_adv,
                oportunidades_flagrantes_adv, cantos_adv, passes_totais_adv,
                passes_certos_adv, cruzamentos_totais_adv, cruzamentos_certos_adv,
                gols_adv, resultado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, dados)

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir partida: {e}")
        return False

    finally:
        conn.close()
        
# =======================
# CONSULTA
# =======================
def buscar_partidas(usuario_id=None):
    conn = conectar()
    cursor = conn.cursor()

    try:
        if usuario_id:
            cursor.execute("""
                SELECT * FROM partidas
                WHERE usuario_id = %s
                ORDER BY data DESC
            """, (usuario_id,))
        else:
            cursor.execute("""
                SELECT * FROM partidas
                ORDER BY data DESC
            """)

        return cursor.fetchall()

    except Exception as e:
        print(f"Erro ao buscar partidas: {e}")
        return []

    finally:
        conn.close()

# =======================
# DELETAR
# =======================
def deletar_partida(id_partida, usuario_id=None):
    conn = conectar()
    cursor = conn.cursor()

    try:
        if usuario_id:
            cursor.execute("""
                DELETE FROM partidas
                WHERE id = %s AND usuario_id = %s
            """, (id_partida, usuario_id))
        else:
            cursor.execute("""
                DELETE FROM partidas
                WHERE id = %s
            """, (id_partida,))

        conn.commit()
        return cursor.rowcount > 0

    except Exception as e:
        conn.rollback()
        print(f"Erro ao deletar partida: {e}")
        return False

    finally:
        conn.close()

# =======================
# FILTROS
# =======================
def buscar_partidas_filtradas(usuario_id, temporada=None, competicao=None):
    conn = conectar()
    cursor = conn.cursor()

    query = "SELECT * FROM partidas WHERE usuario_id = %s"
    params = [usuario_id]

    if temporada:
        query += " AND temporada = %s"
        params.append(temporada)

    if competicao:
        query += " AND competicao = %s"
        params.append(competicao)

    query += " ORDER BY data DESC"

    try:
        cursor.execute(query, tuple(params))
        return cursor.fetchall()

    except Exception as e:
        print(f"Erro ao buscar partidas filtradas: {e}")
        return []

    finally:
        conn.close()



# =======================
# ESTATÍSTICAS DE JOGADORES
# =======================

def inserir_estatisticas_jogadores(partida_id: int, usuario_id: int, jogadores: list) -> bool:
    """
    Insere (ou substitui) as estatísticas dos jogadores de uma partida.
    Apaga registros anteriores da mesma partida antes de inserir.

    Args:
        partida_id: ID da partida já cadastrada
        usuario_id: ID do usuário dono da partida
        jogadores:  Lista de dicts retornada por parsear_html_fm()

    Returns:
        bool: True em caso de sucesso
    """
    conn = conectar()
    cursor = conn.cursor()

    try:
        # Remove lançamento anterior (permite reimportar o mesmo HTML)
        cursor.execute(
            "DELETE FROM estatisticas_jogadores WHERE partida_id = %s AND usuario_id = %s",
            (partida_id, usuario_id)
        )

        for j in jogadores:
            cursor.execute("""
                INSERT INTO estatisticas_jogadores (
                    partida_id, usuario_id,
                    numero, nome, minutos_jogados,
                    distancia_km, perc_passes, xa, assistencias, xg, golos,
                    perc_cruzamentos, passes_progressivos, oportunidades_flagrantes, passes_decisivos,
                    perc_remates, fintas, faltas_sofridas, remate_na_barra,
                    perc_desarmes, perc_cabeceamentos, faltas_cometidas, intercepcoes, alivios, desarmes_decisivos,
                    defesas_seguras, defesas_ponta_dedos, defesas_desviadas, remates_sofridos,
                    lancamentos, cantos, livres_defensivos, livres_ofensivos
                ) VALUES (
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                partida_id, usuario_id,
                j.get("numero"), j.get("nome"), j.get("minutos_jogados"),
                j.get("distancia_km", 0), j.get("perc_passes", 0), j.get("xa", 0),
                j.get("assistencias", 0), j.get("xg", 0), j.get("golos", 0),
                j.get("perc_cruzamentos", 0), j.get("passes_progressivos", 0),
                j.get("oportunidades_flagrantes", 0), j.get("passes_decisivos", 0),
                j.get("perc_remates", 0), j.get("fintas", 0),
                j.get("faltas_sofridas", 0), j.get("remate_na_barra", 0),
                j.get("perc_desarmes", 0), j.get("perc_cabeceamentos", 0),
                j.get("faltas_cometidas", 0), j.get("intercepcoes", 0),
                j.get("alivios", 0), j.get("desarmes_decisivos", 0),
                j.get("defesas_seguras", 0), j.get("defesas_ponta_dedos", 0),
                j.get("defesas_desviadas", 0), j.get("remates_sofridos", 0),
                j.get("lancamentos", 0), j.get("cantos", 0),
                j.get("livres_defensivos", 0), j.get("livres_ofensivos", 0),
            ))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir estatísticas de jogadores: {e}")
        return False

    finally:
        conn.close()


def buscar_estatisticas_jogadores(partida_id: int, usuario_id: int) -> list:
    """
    Retorna as estatísticas dos jogadores de uma partida específica.

    Returns:
        list[dict]: Lista de dicts com todos os campos, ordenada por minutos (desc)
                    Retorna lista vazia se não houver registros.
    """
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                numero, nome, minutos_jogados,
                distancia_km, perc_passes, xa, assistencias, xg, golos,
                perc_cruzamentos, passes_progressivos, oportunidades_flagrantes, passes_decisivos,
                perc_remates, fintas, faltas_sofridas, remate_na_barra,
                perc_desarmes, perc_cabeceamentos, faltas_cometidas, intercepcoes, alivios, desarmes_decisivos,
                defesas_seguras, defesas_ponta_dedos, defesas_desviadas, remates_sofridos,
                lancamentos, cantos, livres_defensivos, livres_ofensivos
            FROM estatisticas_jogadores
            WHERE partida_id = %s AND usuario_id = %s
            ORDER BY minutos_jogados DESC NULLS LAST, nome ASC
        """, (partida_id, usuario_id))

        colunas = [desc[0] for desc in cursor.description]
        return [dict(zip(colunas, row)) for row in cursor.fetchall()]

    except Exception as e:
        print(f"Erro ao buscar estatísticas de jogadores: {e}")
        return []

    finally:
        conn.close()

def contar_partidas_usuario(usuario_id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*) FROM partidas
            WHERE usuario_id = %s
        """, (usuario_id,))

        return cursor.fetchone()[0]

    except Exception as e:
        print(f"Erro ao contar partidas: {e}")
        return 0

    finally:
        conn.close()