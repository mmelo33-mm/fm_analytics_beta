import pandas as pd

# =======================
# CONSTANTES
# =======================
RESULTADO_VITORIA = "Vitória"
RESULTADO_EMPATE = "Empate"
RESULTADO_DERROTA = "Derrota"

LOCAL_CASA = "Casa"
LOCAL_FORA = "Fora"


# =======================
# BENCHMARK – GRANDES LIGAS EUROPEIAS
# =======================
BENCHMARK = {
    "xg_usuario": {"min": 0.80, "max": 2.20, "ideal": 1.23},
    "gols_usuario": {"min": 0.80, "max": 2.35, "ideal": 1.40},
    "remates_usuario": {"min": 8.0, "max": 17.50, "ideal": 13.0},
    "remates_a_baliza_usuario": {"min": 3.0, "max": 6.50, "ideal": 4.8},
    "posse_usuario": {"min": 35.0, "max": 58.0, "ideal": 54.0},
    "passes_certos_usuario": {"min": 300, "max": 570, "ideal": 430},
    "aproveitamento": {"min": 20.0, "max": 60.0, "ideal": 55.0}
}


# =======================
# CÁLCULOS
# =======================
def calcular_aproveitamento(df):
    """
    Calcula o aproveitamento percentual de pontos.
    
    Args:
        df: DataFrame com coluna 'resultado'
    
    Returns:
        float: Percentual de aproveitamento (0-100)
    """
    if len(df) == 0:
        return 0.0
    
    pontos = (
        (df["resultado"] == RESULTADO_VITORIA).sum() * 3 +
        (df["resultado"] == RESULTADO_EMPATE).sum() * 1
    )
    pontos_possiveis = len(df) * 3
    
    return (pontos / pontos_possiveis) * 100 if pontos_possiveis > 0 else 0.0


def calcular_percentual_passes(passes_certos, passes_totais):
    """Calcula percentual de acerto de passes."""
    if passes_totais == 0:
        return 0.0
    return (passes_certos / passes_totais) * 100


def calcular_percentual_cruzamentos(cruzamentos_certos, cruzamentos_totais):
    """Calcula percentual de acerto de cruzamentos."""
    if cruzamentos_totais == 0:
        return 0.0
    return (cruzamentos_certos / cruzamentos_totais) * 100


def calcular_percentual_finalizacao(remates_baliza, remates_totais):
    """Calcula percentual de remates no alvo."""
    if remates_totais == 0:
        return 0.0
    return (remates_baliza / remates_totais) * 100


def calcular_eficiencia_gols(gols, xg):
    """Calcula eficiência de finalização (gols / xG)."""
    if xg == 0:
        return 0.0
    return (gols / xg) * 100


# =======================
# COMPARAÇÃO COM BENCHMARK
# =======================
def comparar_com_benchmark(meu_valor, benchmark_info, melhor="maior"):
    """
    Compara valor do usuário com benchmark europeu (intervalos).
    
    Args:
        meu_valor: Valor do usuário
        benchmark_info: Dict com 'min', 'max' e 'ideal'
        melhor: "maior" ou "menor" indica qual direção é melhor
    
    Returns:
        tuple: (status_emoji, status_texto, cor, intervalo_str)
    """
    if pd.isna(meu_valor):
        return "⚪", "Sem dados suficientes", "gray", ""

    min_val = benchmark_info["min"]
    max_val = benchmark_info["max"]
    intervalo_str = f"{min_val:.2f} - {max_val:.2f}"

    if melhor == "maior":
        if meu_valor > max_val:
            return "🟢", "Acima do padrão europeu", "green", intervalo_str
        elif meu_valor >= min_val:
            return "🟡", "Dentro do padrão europeu", "orange", intervalo_str
        else:
            return "🔴", "Abaixo do padrão europeu", "red", intervalo_str
    else:
        if meu_valor < min_val:
            return "🟢", "Acima do padrão defensivo", "green", intervalo_str
        elif meu_valor <= max_val:
            return "🟡", "Dentro do padrão defensivo", "orange", intervalo_str
        else:
            return "🔴", "Abaixo do padrão defensivo", "red", intervalo_str



def calcular_score_benchmark(df, aproveitamento_geral):
    """
    Calcula score geral comparando com benchmark por intervalos.
    
    Returns:
        int: Score de -7 a 7
    """
    metricas = {
        "xg_usuario": df["xg_usuario"].mean(),
        "gols_usuario": df["gols_usuario"].mean(),
        "remates_usuario": df["remates_usuario"].mean(),
        "remates_a_baliza_usuario": df["remates_a_baliza_usuario"].mean(),
        "posse_usuario": df["posse_usuario"].mean(),
        "passes_certos_usuario": df["passes_certos_usuario"].mean(),
        "aproveitamento": aproveitamento_geral,
    }

    score = 0

    for chave, meu_valor in metricas.items():
        if pd.isna(meu_valor):
            continue

        benchmark = BENCHMARK[chave]
        min_val = benchmark["min"]
        max_val = benchmark["max"]

        if meu_valor > max_val:
            score += 1          # acima do padrão
        elif meu_valor < min_val:
            score -= 1          # abaixo do padrão
        else:
            score += 0          # dentro do padrão

    return score


def diagnostico_geral(score):
    """
    Retorna diagnóstico baseado no score.
    
    Returns:
        tuple: (tipo, mensagem) - tipo pode ser "success", "warning", "error"
    """
    if score >= 3:
        return "success", "O time apresenta desempenho competitivo em nível europeu."
    elif score >= -2:
        return "warning", "O time está dentro do padrão europeu, mas com margens claras de evolução."
    else:
        return "error", "O time apresenta desempenho abaixo do padrão das principais ligas europeias."


# =======================
# VALIDAÇÕES - CORRIGIDO
# =======================

def validar_dados_partida(dados):
    """
    Valida os dados de uma partida antes de salvar.
    CORRIGIDO: Agora aceita usuario_id como primeiro parâmetro
    
    Args:
        dados: tupla com (usuario_id, time_usuario, time_adv, ..., resultado)
    
    Returns:
        tuple: (bool, str) - (válido, mensagem_erro)
    """
    # Desempacota os dados (agora com usuario_id)
    try:
        (usuario_id, time_usuario, time_adv, local, competicao, temporada, data, rodada,
         posse_usuario, remates_usuario, remates_a_baliza_usuario, xg_usuario, 
         oportunidades_flagrantes_usuario, cantos_usuario,
         passes_totais_usuario, passes_certos_usuario, cruzamentos_totais_usuario,
         cruzamentos_certos_usuario, gols_usuario,
         posse_adv, remates_adv, remates_a_baliza_adv, xg_adv,
         oportunidades_flagrantes_adv, cantos_adv,
         passes_totais_adv, passes_certos_adv, cruzamentos_totais_adv,
         cruzamentos_certos_adv, gols_adv, resultado) = dados
    except ValueError as e:
        return False, f"❌ Erro na estrutura dos dados: {e}"
    
    # Validar campos obrigatórios
    if not time_usuario or not time_adv:
        return False, "❌ Nome dos times é obrigatório."
    
    # Validar passes
    if passes_certos_usuario > passes_totais_usuario:
        return False, "❌ Passes certos não podem ser maiores que passes totais."
    
    if passes_certos_adv > passes_totais_adv:
        return False, "❌ Passes certos do adversário não podem ser maiores que passes totais."
    
    # Validar remates
    if remates_a_baliza_usuario > remates_usuario:
        return False, "❌ Remates a baliza não podem ser maiores que remates totais."
    
    if remates_a_baliza_adv > remates_adv:
        return False, "❌ Remates a baliza do adversário não podem ser maiores que remates totais."
    
    # Validar cruzamentos
    if cruzamentos_certos_usuario > cruzamentos_totais_usuario:
        return False, "❌ Cruzamentos certos não podem ser maiores que cruzamentos totais."
    
    if cruzamentos_certos_adv > cruzamentos_totais_adv:
        return False, "❌ Cruzamentos certos do adversário não podem ser maiores que cruzamentos totais."
    
    # Validar gols vs remates
    if gols_usuario > remates_a_baliza_usuario:
        return False, "❌ Gols não podem ser maiores que remates a baliza."
    
    if gols_adv > remates_a_baliza_adv:
        return False, "❌ Gols do adversário não podem ser maiores que remates a baliza."
    
    # Avisar sobre posse (não bloqueia)
    if abs((posse_usuario + posse_adv) - 100) > 5:
        return True, "⚠️ Aviso: A soma das posses de bola não está próxima de 100%."
    
    return True, ""

# =======================
# PARSER HTML — BEPINEX FM EXPORT
# =======================

def _parse_minutos(valor: str):
    """
    Normaliza o campo 'Min' do HTML exportado pelo BepInEx.
    Exemplos: '90' → 90, '57 (Sai)' → 57, '45 (Entra)' → 45, '' → None
    """
    if not valor or not valor.strip():
        return None
    try:
        return int(valor.strip().split()[0])
    except (ValueError, IndexError):
        return None


def _parse_percentual(valor: str):
    """
    Remove símbolo % e converte para int.
    Exemplos: '0%' → 0, '93' → 93, '0,00' → 0
    Campos como Passes Decisivos vêm como '5%' → tratamos como unidade 5.
    """
    if not valor or not valor.strip():
        return 0
    limpo = valor.strip().replace('%', '').replace(',', '.').strip()
    try:
        return int(float(limpo))
    except ValueError:
        return 0


def _parse_decimal(valor: str):
    """Converte valor decimal com vírgula ou ponto para float."""
    if not valor or not valor.strip():
        return 0.0
    try:
        return float(valor.strip().replace(',', '.'))
    except ValueError:
        return 0.0


def _parse_distancia(valor: str):
    """
    Extrai valor numérico de strings como '7,1 km' → 7.1
    """
    if not valor or not valor.strip():
        return 0.0
    try:
        return float(valor.strip().replace(' km', '').replace(',', '.'))
    except ValueError:
        return 0.0


def parsear_html_fm(conteudo_html: bytes) -> list[dict]:
    """
    Faz o parse do HTML exportado pelo mod BepInEx do Football Manager.
    Lê as 6 tabelas (Estatísticas Principais, Passe, Ofensivo,
    Defensivo, Guarda-Redes, Bolas Paradas) e retorna uma lista
    de dicts com todos os campos por jogador, com o nome como chave
    de junção entre tabelas.

    Args:
        conteudo_html: Bytes do arquivo HTML carregado via st.file_uploader

    Returns:
        list[dict]: Um dict por jogador com todos os campos parseados.
                    Retorna lista vazia em caso de erro.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("beautifulsoup4 não instalado. Adicione 'beautifulsoup4' ao requirements.txt.")

    soup = BeautifulSoup(conteudo_html, "html.parser")

    # Mapeia cada h3 para a tabela imediatamente seguinte
    secoes = {}
    for h3 in soup.find_all("h3"):
        tabela = h3.find_next_sibling("table")
        if tabela:
            secoes[h3.get_text(strip=True)] = tabela

    # Chave de merge: nome do jogador (coluna 'Nome' presente em todas as tabelas)
    jogadores: dict[str, dict] = {}

    def _linhas(tabela):
        """Retorna linhas de dados (pula o header <tr><th>)."""
        return tabela.find_all("tr")[1:]

    def _celulas(tr):
        return [td.get_text(strip=True) for td in tr.find_all("td")]

    # ------------------------------------------------------------------
    # 1. Estatísticas Principais
    #    Colunas: Núm | Min | Nome | Dist. | %Pass./Tent. | xA | Assist. | xG | Golos
    # ------------------------------------------------------------------
    tabela = secoes.get("Estatísticas Principais")
    if tabela:
        for tr in _linhas(tabela):
            c = _celulas(tr)
            if len(c) < 9:
                continue
            nome = c[2].strip()
            jogadores[nome] = {
                "numero":               c[0] if c[0] != "-" else None,
                "nome":                 nome,
                "minutos_jogados":      _parse_minutos(c[1]),
                "distancia_km":         _parse_distancia(c[3]),
                "perc_passes":          _parse_percentual(c[4]),
                "xa":                   _parse_decimal(c[5]),
                "assistencias":         int(c[6]) if c[6].isdigit() else 0,
                "xg":                   _parse_decimal(c[7]),
                "golos":                int(c[8]) if c[8].isdigit() else 0,
            }

    # ------------------------------------------------------------------
    # 2. Passe
    #    Colunas: Núm | Min | Nome | %Pass./Tent. | %Cruz./Tent.
    #             | Passes Progressivos | Oportunidades Flagrantes | Passes Decisivos
    # ------------------------------------------------------------------
    tabela = secoes.get("Passe")
    if tabela:
        for tr in _linhas(tabela):
            c = _celulas(tr)
            if len(c) < 8:
                continue
            nome = c[2].strip()
            extra = {
                "perc_cruzamentos":         _parse_percentual(c[4]),
                "passes_progressivos":      _parse_percentual(c[5]),
                "oportunidades_flagrantes": int(c[6]) if c[6].isdigit() else 0,
                "passes_decisivos":         _parse_percentual(c[7]),  # vem como "X%" → unidade
            }
            if nome in jogadores:
                jogadores[nome].update(extra)
            else:
                jogadores[nome] = {"nome": nome, **extra}

    # ------------------------------------------------------------------
    # 3. Ofensivo
    #    Colunas: Núm | Min | Nome | %Remates | Dist. | Fintas
    #             | Faltas Contra | Remate-Barra | xA | xG
    # ------------------------------------------------------------------
    tabela = secoes.get("Ofensivo")
    if tabela:
        for tr in _linhas(tabela):
            c = _celulas(tr)
            if len(c) < 10:
                continue
            nome = c[2].strip()
            extra = {
                "perc_remates":     _parse_percentual(c[3]),
                "fintas":           int(c[5]) if c[5].isdigit() else 0,
                "faltas_sofridas":  int(c[6]) if c[6].isdigit() else 0,
                "remate_na_barra":  int(c[7]) if c[7].isdigit() else 0,
            }
            if nome in jogadores:
                jogadores[nome].update(extra)
            else:
                jogadores[nome] = {"nome": nome, **extra}

    # ------------------------------------------------------------------
    # 4. Defensivo
    #    Colunas: Núm | Min | Nome | %Desarmes | %Cabeceamentos
    #             | Faltas Cometidas | Intercepções | Alívios | Desarmes Decisivos
    # ------------------------------------------------------------------
    tabela = secoes.get("Defensivo")
    if tabela:
        for tr in _linhas(tabela):
            c = _celulas(tr)
            if len(c) < 9:
                continue
            nome = c[2].strip()
            extra = {
                "perc_desarmes":        _parse_percentual(c[3]),
                "perc_cabeceamentos":   _parse_percentual(c[4]),
                "faltas_cometidas":     int(c[5]) if c[5].isdigit() else 0,
                "intercepcoes":         int(c[6]) if c[6].isdigit() else 0,
                "alivios":              int(c[7]) if c[7].isdigit() else 0,
                "desarmes_decisivos":   _parse_percentual(c[8]),  # vem como "X%" → unidade
            }
            if nome in jogadores:
                jogadores[nome].update(extra)
            else:
                jogadores[nome] = {"nome": nome, **extra}

    # ------------------------------------------------------------------
    # 5. Guarda-Redes
    #    Colunas: Núm | Min | Nome | Defesas Seguras | Defesas Ponta Dedos
    #             | Defesas Desviadas | Remates Sofridos
    # ------------------------------------------------------------------
    tabela = secoes.get("Guarda-Redes")
    if tabela:
        for tr in _linhas(tabela):
            c = _celulas(tr)
            if len(c) < 7:
                continue
            nome = c[2].strip()
            extra = {
                "defesas_seguras":      int(c[3]) if c[3].isdigit() else 0,
                "defesas_ponta_dedos":  int(c[4]) if c[4].isdigit() else 0,
                "defesas_desviadas":    int(c[5]) if c[5].isdigit() else 0,
                "remates_sofridos":     int(c[6]) if c[6].isdigit() else 0,
            }
            if nome in jogadores:
                jogadores[nome].update(extra)
            else:
                jogadores[nome] = {"nome": nome, **extra}

    # ------------------------------------------------------------------
    # 6. Bolas Paradas
    #    Colunas: Núm | Min | Nome | Lançamentos | Cantos
    #             | Livres Defensivos | Livres Ofensivos
    # ------------------------------------------------------------------
    tabela = secoes.get("Bolas Paradas")
    if tabela:
        for tr in _linhas(tabela):
            c = _celulas(tr)
            if len(c) < 7:
                continue
            nome = c[2].strip()
            extra = {
                "lancamentos":        int(c[3]) if c[3].isdigit() else 0,
                "cantos":             int(c[4]) if c[4].isdigit() else 0,
                "livres_defensivos":  int(c[5]) if c[5].isdigit() else 0,
                "livres_ofensivos":   int(c[6]) if c[6].isdigit() else 0,
            }
            if nome in jogadores:
                jogadores[nome].update(extra)
            else:
                jogadores[nome] = {"nome": nome, **extra}

    # Filtra jogadores sem minutos jogados (convocados que não entraram)
    resultado = [j for j in jogadores.values() if j.get("minutos_jogados") is not None]
    return resultado
