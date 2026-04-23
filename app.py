import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import requests
from google import genai
from datetime import datetime, timedelta
from database import inserir_partida, buscar_partidas, deletar_partida, inserir_estatisticas_jogadores, buscar_estatisticas_jogadores, buscar_todas_estatisticas_jogadores
from utils import (
    calcular_aproveitamento, comparar_com_benchmark, calcular_score_benchmark,
    diagnostico_geral, validar_dados_partida, BENCHMARK, RESULTADO_VITORIA,
    RESULTADO_EMPATE, RESULTADO_DERROTA, LOCAL_CASA, LOCAL_FORA,
    calcular_percentual_passes, calcular_percentual_finalizacao,
    parsear_html_fm
)
from licencas import Licenca, PLANOS, get_mensagem_upgrade, comparar_planos
from auth import buscar_usuario
from lang import STRINGS, IDIOMAS, t
from utils import PROMPT_ASSISTENTE

# =======================
# CONFIGURAÇÃO PÁGINA
# =======================
st.set_page_config(
    page_title="FM Analytics 26",
    page_icon="⚽",
    layout="wide"
)

# =======================
# IDIOMA — inicializar antes de tudo
# =======================
if "idioma" not in st.session_state:
    st.session_state.idioma = "pt-br"
    
# =======================
# VERIFICAR LOGIN
# =======================
if 'logado' not in st.session_state or not st.session_state.logado:
    st.warning(t("login_aviso", st.session_state.idioma))
    if st.button(t("btn_ir_login", st.session_state.idioma)):
        st.switch_page("pages/1_Login.py")
    st.stop()

# Buscar dados do usuário
usuario = buscar_usuario(st.session_state.usuario_id)
if not usuario:
    st.error(t("erro_usuario", st.session_state.idioma))
    st.stop()

# Criar licença
data_exp = None
if usuario['data_expiracao']:
    data_exp = datetime.fromisoformat(usuario['data_expiracao'])

licenca = Licenca(usuario['plano'], data_exp)
st.session_state.licenca = licenca

if 'licenca' not in st.session_state:
    st.session_state.licenca = Licenca("FREE")

licenca = st.session_state.licenca
lang = st.session_state.idioma

# =======================
# HEADER
# =======================
col_logo, col_licenca, col_upgrade, col_idioma = st.columns([2, 1, 1, 1])

with col_logo:
    st.title(t("header_titulo", lang))
    st.caption(t("header_caption", lang))

with col_idioma:
    idioma_labels = list(IDIOMAS.keys())
    idioma_valores = list(IDIOMAS.values())
    idx_atual = idioma_valores.index(lang) if lang in idioma_valores else 0
    idioma_label = st.selectbox(
        t("lbl_idioma", lang),
        options=idioma_labels,
        index=idx_atual,
        label_visibility="collapsed",
        key="seletor_idioma"
    )
    novo_idioma = IDIOMAS[idioma_label]
    if novo_idioma != st.session_state.idioma:
        st.session_state.idioma = novo_idioma
        st.rerun()

# =======================
# TABS PRINCIPAIS
# =======================
tab1, tab2, tab3, tab4 = st.tabs([
    t("tab_cadastro", lang),
    t("tab_dashboard", lang),
    t("tab_historico", lang),
    t("tab_ia", lang),
])

# =======================
# TAB 1: CADASTRO
# =======================
with tab1:
    st.subheader(t("cadastro_titulo", lang))

    partidas_existentes = buscar_partidas(st.session_state.usuario_id)
    num_partidas = len(partidas_existentes)

    pode_cadastrar, mensagem_erro = licenca.pode_cadastrar_partida(num_partidas)

    if not pode_cadastrar:
        msg = get_mensagem_upgrade("limite_partidas")
        st.error(f"### {msg['titulo']}")
        st.warning(msg['texto'])
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**{msg['oferta']}**")
        with col2:
            if st.button(f"⭐ {msg['cta']}", type="primary", use_container_width=True):
                st.switch_page("pages/upgrade.py")
        st.divider()
        st.subheader(t("limite_dica", lang))
        limite_txt = t("limite_info", lang).format(
            atual=num_partidas,
            max=licenca.configuracao['limite_partidas']
        )
        st.info(limite_txt)
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        time_usuario = st.text_input(t("lbl_seu_time", lang), key="time_usuario")
        local = st.selectbox(t("lbl_local", lang), [LOCAL_CASA, LOCAL_FORA])
        temporada = st.text_input(t("lbl_temporada", lang))
        rodada = st.number_input(t("lbl_rodada", lang), min_value=1, step=1)

    with col2:
        time_adv = st.text_input(t("lbl_adversario", lang))
        competicao = st.text_input(t("lbl_competicao", lang))
        data = st.date_input(t("lbl_data", lang))

    st.divider()

    col_user, col_adv = st.columns(2)

    with col_user:
        st.subheader(t("lbl_seu_time_stats", lang))
        gols_usuario = st.number_input(t("lbl_gols", lang), min_value=0, step=1, key="gols_user")
        posse_usuario = st.number_input(t("lbl_posse", lang), 0, 100, key="posse_user")
        remates_usuario = st.number_input(t("lbl_remates", lang), min_value=0, key="remates_user")
        remates_a_baliza_usuario = st.number_input(t("lbl_remates_baliza", lang), min_value=0, key="baliza_user")
        xg_usuario = st.number_input(t("lbl_xg", lang), min_value=0.0, format="%.2f", key="xg_user")
        oportunidades_flagrantes_usuario = st.number_input(t("lbl_oportunidades", lang), min_value=0, key="opor_user")
        cantos_usuario = st.number_input(t("lbl_cantos", lang), min_value=0, key="cantos_user")
        passes_totais_usuario = st.number_input(t("lbl_passes_totais", lang), min_value=0, key="passes_tot_user")
        passes_certos_usuario = st.number_input(t("lbl_passes_certos", lang), min_value=0, key="passes_cert_user")
        cruzamentos_totais_usuario = st.number_input(t("lbl_cruzamentos_totais", lang), min_value=0, key="cruz_tot_user")
        cruzamentos_certos_usuario = st.number_input(t("lbl_cruzamentos_certos", lang), min_value=0, key="cruz_cert_user")

    with col_adv:
        st.subheader(t("lbl_adv_stats", lang))
        gols_adv = st.number_input(t("lbl_gols", lang), min_value=0, step=1, key="gols_adv")
        posse_adv = st.number_input(t("lbl_posse", lang), 0, 100, key="posse_adv")
        remates_adv = st.number_input(t("lbl_remates", lang), min_value=0, key="remates_adv")
        remates_a_baliza_adv = st.number_input(t("lbl_remates_baliza", lang), min_value=0, key="baliza_adv")
        xg_adv = st.number_input(t("lbl_xg", lang), min_value=0.0, format="%.2f", key="xg_adv")
        oportunidades_flagrantes_adv = st.number_input(t("lbl_oportunidades", lang), min_value=0, key="opor_adv")
        cantos_adv = st.number_input(t("lbl_cantos", lang), min_value=0, key="cantos_adv")
        passes_totais_adv = st.number_input(t("lbl_passes_totais", lang), min_value=0, key="passes_tot_adv")
        passes_certos_adv = st.number_input(t("lbl_passes_certos", lang), min_value=0, key="passes_cert_adv")
        cruzamentos_totais_adv = st.number_input(t("lbl_cruzamentos_totais", lang), min_value=0, key="cruz_tot_adv")
        cruzamentos_certos_adv = st.number_input(t("lbl_cruzamentos_certos", lang), min_value=0, key="cruz_cert_adv")

    if gols_usuario > gols_adv:
        resultado = RESULTADO_VITORIA
        resultado_emoji = "🎉"
    elif gols_usuario < gols_adv:
        resultado = RESULTADO_DERROTA
        resultado_emoji = "😞"
    else:
        resultado = RESULTADO_EMPATE
        resultado_emoji = "🤝"

    info_txt = t("resultado_info", lang).format(
        emoji=resultado_emoji, resultado=resultado,
        gols_u=gols_usuario, gols_a=gols_adv
    )
    st.info(info_txt)

    if st.button(t("btn_salvar", lang), type="primary", use_container_width=True):
        dados = (
            st.session_state.usuario_id,
            time_usuario, time_adv, local, competicao, temporada, str(data), rodada,
            posse_usuario, remates_usuario, remates_a_baliza_usuario, xg_usuario,
            oportunidades_flagrantes_usuario, cantos_usuario, passes_totais_usuario,
            passes_certos_usuario, cruzamentos_totais_usuario, cruzamentos_certos_usuario,
            gols_usuario, posse_adv, remates_adv, remates_a_baliza_adv, xg_adv,
            oportunidades_flagrantes_adv, cantos_adv, passes_totais_adv,
            passes_certos_adv, cruzamentos_totais_adv, cruzamentos_certos_adv,
            gols_adv, resultado
        )

        valido, mensagem = validar_dados_partida(dados)

        if not valido:
            st.error(mensagem)
        else:
            if mensagem:
                st.warning(mensagem)

            if inserir_partida(dados):
                progress_text = t("msg_salvando", lang)
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(0.02)
                my_bar.progress(percent_complete + 1, text=progress_text)
                time.sleep(1)
                my_bar.empty()
                st.success(t("msg_sucesso", lang))


    # =======================
    # IMPORTAÇÃO HTML BEPINEX
    # =======================
    st.divider()
    st.subheader(t("importar_titulo", lang))
    st.caption(t("importar_descricao", lang))

    partidas_para_import = buscar_partidas(st.session_state.usuario_id)

    if not partidas_para_import:
        st.warning(t("importar_sem_partidas", lang))
    else:
        # Monta opções de seleção de partida
        opcoes_partida = {
            row[0]: f"{str(row[6])[:10]} — {row[2]} {row[19+5] if len(row) > 24 else ''}x{row[19+11] if len(row) > 30 else ''} {row[3]}"
            for row in partidas_para_import
        }
        # Forma mais segura: reconstrói o label a partir das colunas conhecidas
        def _label_partida(row):
            # row: (id, usuario_id, time_usuario, time_adv, local, competicao, temporada, data, rodada, ...)
            try:
                time_usuario   = row[2]
                time_adv  = row[3]
                gols_usuario   = row[19]
                gols_adv   = row[30]
                competicao = row[5]
                temporada   = row[6]
                return f"{time_usuario} {gols_usuario}x{gols_adv} {time_adv} - {competicao} {temporada}"
            except Exception:
                return f"Partida #{row[0]}"

        opcoes_partida = {row[0]: _label_partida(row) for row in partidas_para_import}

        partida_selecionada_id = st.selectbox(
            t("importar_selecionar_partida", lang),
            options=list(opcoes_partida.keys()),
            format_func=lambda x: opcoes_partida[x],
            key="importar_partida_select"
        )

        # Avisa se já existem dados importados para essa partida
        if partida_selecionada_id:
            stats_existentes = buscar_estatisticas_jogadores(
                partida_selecionada_id, st.session_state.usuario_id
            )
            if stats_existentes:
                st.warning(t("importar_reimportar_aviso", lang))

        arquivo_html = st.file_uploader(
            t("importar_upload_label", lang),
            type=["html", "htm"],
            key="importar_html_uploader"
        )

        if arquivo_html is not None:
            try:
                conteudo = arquivo_html.read()
                jogadores_importados = parsear_html_fm(conteudo)

                if not jogadores_importados:
                    st.warning(t("importar_sem_jogadores", lang))
                else:
                    st.success(
                        t("importar_preview_titulo", lang).format(n=len(jogadores_importados))
                    )

                    import pandas as pd

                    df_todos = pd.DataFrame(jogadores_importados)

                    # Renomeia colunas para exibição amigável
                    renomear = {
                        "numero": "Núm", "nome": "Nome", "minutos_jogados": "Min",
                        "distancia_km": "Dist.(km)", "perc_passes": "% Passes",
                        "xa": "xA", "assistencias": "Assist.", "xg": "xG", "golos": "Golos",
                        "perc_cruzamentos": "% Cruz.", "passes_progressivos": "Passes Prog.",
                        "oportunidades_flagrantes": "Op. Flagrantes", "passes_decisivos": "Passes Dec.",
                        "perc_remates": "% Remates", "fintas": "Fintas",
                        "faltas_sofridas": "Faltas Sofr.", "remate_na_barra": "Barra",
                        "perc_desarmes": "% Desarmes", "perc_cabeceamentos": "% Cabec.",
                        "faltas_cometidas": "Faltas Com.", "intercepcoes": "Intercep.",
                        "alivios": "Alívios", "desarmes_decisivos": "Desarm. Dec.",
                        "defesas_seguras": "Def. Seguras", "defesas_ponta_dedos": "Def. Ponta",
                        "defesas_desviadas": "Def. Desv.", "remates_sofridos": "Rem. Sofr.",
                        "lancamentos": "Lançamentos", "cantos": "Cantos",
                        "livres_defensivos": "Livres Def.", "livres_ofensivos": "Livres Of.",
                    }
                    df_todos.rename(columns=renomear, inplace=True)

                    cols_principal      = ["Núm", "Nome", "Min", "Dist.(km)", "% Passes", "xA", "Assist.", "xG", "Golos"]
                    cols_passe          = ["Nome", "Min", "% Passes", "% Cruz.", "Passes Prog.", "Op. Flagrantes", "Passes Dec."]
                    cols_ofensivo       = ["Nome", "Min", "% Remates", "Fintas", "Faltas Sofr.", "Barra", "xA", "xG"]
                    cols_defensivo      = ["Nome", "Min", "% Desarmes", "% Cabec.", "Faltas Com.", "Intercep.", "Alívios", "Desarm. Dec."]
                    cols_gr             = ["Nome", "Min", "Def. Seguras", "Def. Ponta", "Def. Desv.", "Rem. Sofr."]
                    cols_bolas_paradas  = ["Nome", "Min", "Lançamentos", "Cantos", "Livres Def.", "Livres Of."]

                    def _safe_cols(df, cols):
                        return df[[c for c in cols if c in df.columns]]

                    tab_p, tab_pa, tab_of, tab_def, tab_gr, tab_bp = st.tabs([
                        t("importar_tab_principal", lang),
                        t("importar_tab_passe", lang),
                        t("importar_tab_ofensivo", lang),
                        t("importar_tab_defensivo", lang),
                        t("importar_tab_gr", lang),
                        t("importar_tab_bolas_paradas", lang),
                    ])

                    with tab_p:
                        st.dataframe(_safe_cols(df_todos, cols_principal), use_container_width=True, hide_index=True)
                    with tab_pa:
                        st.dataframe(_safe_cols(df_todos, cols_passe), use_container_width=True, hide_index=True)
                    with tab_of:
                        st.dataframe(_safe_cols(df_todos, cols_ofensivo), use_container_width=True, hide_index=True)
                    with tab_def:
                        st.dataframe(_safe_cols(df_todos, cols_defensivo), use_container_width=True, hide_index=True)
                    with tab_gr:
                        st.dataframe(_safe_cols(df_todos, cols_gr), use_container_width=True, hide_index=True)
                    with tab_bp:
                        st.dataframe(_safe_cols(df_todos, cols_bolas_paradas), use_container_width=True, hide_index=True)

                    if st.button(t("importar_confirmar", lang), type="primary", use_container_width=True):
                        if inserir_estatisticas_jogadores(
                            partida_selecionada_id,
                            st.session_state.usuario_id,
                            jogadores_importados
                        ):
                            st.success(
                                t("importar_sucesso", lang).format(n=len(jogadores_importados))
                            )
                            st.balloons()
                        else:
                            st.error(t("importar_erro_salvar", lang))

            except Exception as e:
                st.error(t("importar_erro_parse", lang))
                st.exception(e)


# =======================
# TAB 2: DASHBOARD
# =======================
with tab2:
    st.subheader(t("dashboard_titulo", lang))
 
    partidas = buscar_partidas(st.session_state.usuario_id)
 
    if not partidas:
        st.info(t("nenhuma_partida", lang))
        st.stop()
 
    COLUNAS_PARTIDAS = [
        "id", "usuario_id", "time_usuario", "time_adv", "local", "competicao", "temporada", "data", "rodada",
        "posse_usuario", "remates_usuario", "remates_a_baliza_usuario", "xg_usuario",
        "oportunidades_flagrantes_usuario", "cantos_usuario", "passes_totais_usuario",
        "passes_certos_usuario", "cruzamentos_totais_usuario", "cruzamentos_certos_usuario",
        "gols_usuario", "posse_adv", "remates_adv", "remates_a_baliza_adv", "xg_adv",
        "oportunidades_flagrantes_adv", "cantos_adv", "passes_totais_adv",
        "passes_certos_adv", "cruzamentos_totais_adv", "cruzamentos_certos_adv",
        "gols_adv", "resultado",
    ]
 
    df = pd.DataFrame(partidas, columns=COLUNAS_PARTIDAS[:len(partidas[0])])
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values("data").reset_index(drop=True)
 
    # ── Filtros ──────────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns(2)
    todas = t("filtro_todas", lang)
    with col_f1:
        temporadas = [todas] + sorted(df["temporada"].unique().tolist())
        temp_selecionada = st.selectbox(t("lbl_filtro_temporada", lang), temporadas, key="dash_temp")
    with col_f2:
        competicoes = [todas] + sorted(df["competicao"].unique().tolist())
        comp_selecionada = st.selectbox(t("lbl_filtro_competicao", lang), competicoes, key="dash_comp")
 
    df_filtrado = df.copy()
    if temp_selecionada != todas:
        df_filtrado = df_filtrado[df_filtrado["temporada"] == temp_selecionada]
    if comp_selecionada != todas:
        df_filtrado = df_filtrado[df_filtrado["competicao"] == comp_selecionada]
 
    st.session_state.df_para_ia = df_filtrado
 
    if len(df_filtrado) == 0:
        st.warning(t("nenhum_filtro", lang))
        st.stop()
 
    # ── Dados de jogadores (todas as partidas do usuário) ─────────────────
    todos_jogadores = buscar_todas_estatisticas_jogadores(st.session_state.usuario_id)
    df_jog = pd.DataFrame(todos_jogadores) if todos_jogadores else pd.DataFrame()
 
    # Filtra jogadores apenas das partidas do df_filtrado
    ids_filtrados = set(df_filtrado["id"].tolist())
    if not df_jog.empty:
        df_jog = df_jog[df_jog["partida_id"].isin(ids_filtrados)]
 
    tem_jogadores = not df_jog.empty
 
    # ── Derivadas gerais ──────────────────────────────────────────────────
    aproveitamento_geral = calcular_aproveitamento(df_filtrado)
    resumo = df_filtrado["resultado"].value_counts()
    n = len(df_filtrado)
    gols_pro   = df_filtrado["gols_usuario"].sum()
    gols_contra = df_filtrado["gols_adv"].sum()
    saldo_gols  = gols_pro - gols_contra
    perc_passes_geral = calcular_percentual_passes(
        df_filtrado["passes_certos_usuario"].sum(),
        df_filtrado["passes_totais_usuario"].sum()
    )
    perc_fin_geral = calcular_percentual_finalizacao(
        df_filtrado["remates_a_baliza_usuario"].sum(),
        df_filtrado["remates_usuario"].sum()
    )
 
    # ════════════════════════════════════════════════════════════════════
    # SEÇÃO 1 — VISÃO GERAL DO CLUBE
    # ════════════════════════════════════════════════════════════════════
    st.markdown("## 🏟️ Visão Geral do Clube")
 
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Partidas", n)
    c2.metric("✅ Vitórias", resumo.get(RESULTADO_VITORIA, 0))
    c3.metric("🤝 Empates",  resumo.get(RESULTADO_EMPATE, 0))
    c4.metric("❌ Derrotas", resumo.get(RESULTADO_DERROTA, 0))
    c5.metric("🏆 Aproveit.", f"{aproveitamento_geral:.1f}%")
    c6.metric("⚖️ Saldo Gols", f"{saldo_gols:+d}")
 
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("⚽ Gols Pró", gols_pro)
    c2.metric("🥅 Gols Sofridos", gols_contra)
    c3.metric("📐 xG médio", f"{df_filtrado['xg_usuario'].mean():.2f}")
    c4.metric("🎯 xG contra", f"{df_filtrado['xg_adv'].mean():.2f}")
    c5.metric("📊 Posse média", f"{df_filtrado['posse_usuario'].mean():.1f}%")
    c6.metric("🔁 % Passes", f"{perc_passes_geral:.1f}%")
 
    col_pie, col_trend = st.columns([1, 2])
 
    with col_pie:
        fig_pie = px.pie(
            values=resumo.values, names=resumo.index,
            title="Distribuição de Resultados",
            color=resumo.index,
            color_discrete_map={
                RESULTADO_VITORIA: "#22c55e",
                RESULTADO_EMPATE:  "#eab308",
                RESULTADO_DERROTA: "#ef4444"
            },
            hole=0.45
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(showlegend=False, margin=dict(t=40, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)
 
    with col_trend:
        # Forma recente — últimos 10 com barras coloridas
        ultimos = df_filtrado.tail(10).copy()
        cores_forma = ultimos["resultado"].map({
            RESULTADO_VITORIA: "#22c55e",
            RESULTADO_EMPATE:  "#eab308",
            RESULTADO_DERROTA: "#ef4444"
        })
        ultimos["label"] = (
            ultimos["data"].dt.strftime("%d/%m") + " " +
            ultimos["time_adv"].str[:8]
        )
        fig_forma = go.Figure(go.Bar(
            x=ultimos["label"],
            y=[1] * len(ultimos),
            marker_color=cores_forma.tolist(),
            text=ultimos.apply(lambda r: f"{r['gols_usuario']}x{r['gols_adv']}", axis=1),
            textposition="inside",
            hovertext=ultimos.apply(
                lambda r: f"{r['time_usuario']} {r['gols_usuario']}x{r['gols_adv']} {r['time_adv']}", axis=1
            ),
            hoverinfo="text",
        ))
        fig_forma.update_layout(
            title="Forma Recente (últimos 10 jogos)",
            yaxis=dict(visible=False),
            xaxis=dict(tickangle=-30),
            height=260,
            margin=dict(t=40, b=60, l=10, r=10),
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_forma, use_container_width=True)
 
    # ════════════════════════════════════════════════════════════════════
    # SEÇÃO 2 — ATAQUE vs DEFESA
    # ════════════════════════════════════════════════════════════════════
    st.divider()
    st.markdown("## ⚔️ Ataque & 🛡️ Defesa")
 
    col_atq, col_def = st.columns(2)
 
    with col_atq:
        st.markdown("### ⚔️ Poder Ofensivo")
        a1, a2 = st.columns(2)
        a1.metric("Gols/jogo",    f"{df_filtrado['gols_usuario'].mean():.2f}")
        a2.metric("xG/jogo",      f"{df_filtrado['xg_usuario'].mean():.2f}")
        a1.metric("Remates/jogo", f"{df_filtrado['remates_usuario'].mean():.1f}")
        a2.metric("A baliza/jogo",f"{df_filtrado['remates_a_baliza_usuario'].mean():.1f}")
        a1.metric("% Finaliz.",   f"{perc_fin_geral:.1f}%")
        a2.metric("Op. Flagrantes/j",f"{df_filtrado['oportunidades_flagrantes_usuario'].mean():.2f}")
 
        # Over/Under-performance vs xG
        xg_total = df_filtrado["xg_usuario"].sum()
        gols_total = float(gols_pro)
        diff_xg = gols_total - xg_total
        st.markdown(
            f"**Over/Under vs xG:** {'🟢 +' if diff_xg >= 0 else '🔴 '}{diff_xg:.2f} gols "
            f"({'acima' if diff_xg >= 0 else 'abaixo'} do esperado)"
        )
 
    with col_def:
        st.markdown("### 🛡️ Solidez Defensiva")
        d1, d2 = st.columns(2)
        jogos_sem_sofrer = (df_filtrado["gols_adv"] == 0).sum()
        perc_clean = jogos_sem_sofrer / n * 100 if n > 0 else 0
        xg_contra_total = df_filtrado["xg_adv"].sum()
        gols_sofridos = float(gols_contra)
        diff_xg_def = gols_sofridos - xg_contra_total
 
        d1.metric("Gols sofridos/j",  f"{df_filtrado['gols_adv'].mean():.2f}")
        d2.metric("xG sofrido/j",     f"{df_filtrado['xg_adv'].mean():.2f}")
        d1.metric("Clean sheets",     f"{jogos_sem_sofrer} ({perc_clean:.0f}%)")
        d2.metric("Remates sofr./j",  f"{df_filtrado['remates_adv'].mean():.1f}")
        d1.metric("Posse adversária", f"{df_filtrado['posse_adv'].mean():.1f}%")
        d2.metric("Op. Flagr. sofr.", f"{df_filtrado['oportunidades_flagrantes_adv'].mean():.2f}")
 
        st.markdown(
            f"**Def. vs xG sofrido:** {'🟢 ' if diff_xg_def <= 0 else '🔴 +'}{diff_xg_def:.2f} "
            f"({'abaixo' if diff_xg_def <= 0 else 'acima'} do esperado)"
        )
 
    # Gráfico xG pró vs contra por jogo
    fig_xg = go.Figure()
    fig_xg.add_trace(go.Scatter(
        x=df_filtrado["data"], y=df_filtrado["xg_usuario"],
        name="xG Pró", mode="lines+markers",
        line=dict(color="#22c55e", width=2),
        fill="tozeroy", fillcolor="rgba(34,197,94,0.12)"
    ))
    fig_xg.add_trace(go.Scatter(
        x=df_filtrado["data"], y=df_filtrado["xg_adv"],
        name="xG Contra", mode="lines+markers",
        line=dict(color="#ef4444", width=2),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.12)"
    ))
    fig_xg.update_layout(
        title="xG Pró vs xG Contra por Jogo",
        xaxis_title="Data", yaxis_title="xG",
        legend=dict(orientation="h"),
        height=300, margin=dict(t=40, b=40, l=40, r=10)
    )
    st.plotly_chart(fig_xg, use_container_width=True)
 
    # ════════════════════════════════════════════════════════════════════
    # SEÇÃO 3 — CONSTRUÇÃO DE JOGO
    # ════════════════════════════════════════════════════════════════════
    st.divider()
    st.markdown("## 🔄 Construção de Jogo")
 
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Posse média",        f"{df_filtrado['posse_usuario'].mean():.1f}%")
    c2.metric("% Passes",           f"{perc_passes_geral:.1f}%")
    c3.metric("Cantos/jogo",        f"{df_filtrado['cantos_usuario'].mean():.1f}")
    c4.metric("Cruzamentos/jogo",   f"{df_filtrado['cruzamentos_totais_usuario'].mean():.1f}")
 
    perc_cruz = calcular_percentual_passes(
        df_filtrado["cruzamentos_certos_usuario"].sum(),
        df_filtrado["cruzamentos_totais_usuario"].sum()
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("% Cruzamentos",  f"{perc_cruz:.1f}%")
    c2.metric("Passes totais/j",f"{df_filtrado['passes_totais_usuario'].mean():.0f}")
    c3.metric("Passes certos/j",f"{df_filtrado['passes_certos_usuario'].mean():.0f}")
    c4.metric("Cantos adversário/j", f"{df_filtrado['cantos_adv'].mean():.1f}")
 
    # Posse x aproveitamento (scatter)
    df_scatter = df_filtrado.copy()
    df_scatter["cor"] = df_scatter["resultado"].map({
        RESULTADO_VITORIA: "#22c55e",
        RESULTADO_EMPATE:  "#eab308",
        RESULTADO_DERROTA: "#ef4444"
    })
    fig_posse = px.scatter(
        df_scatter, x="posse_usuario", y="gols_usuario",
        color="resultado",
        color_discrete_map={
            RESULTADO_VITORIA: "#22c55e",
            RESULTADO_EMPATE:  "#eab308",
            RESULTADO_DERROTA: "#ef4444"
        },
        trendline="ols",
        title="Posse de Bola vs Gols Marcados",
        labels={"posse_usuario": "Posse (%)", "gols_usuario": "Gols"},
        hover_data={"time_adv": True, "data": True}
    )
    fig_posse.update_layout(height=320, margin=dict(t=40, b=40))
    st.plotly_chart(fig_posse, use_container_width=True)
 
    # ════════════════════════════════════════════════════════════════════
    # SEÇÃO 4 — CASA vs FORA
    # ════════════════════════════════════════════════════════════════════
    st.divider()
    st.markdown("## 🏠 Casa vs ✈️ Fora")
 
    df_casa = df_filtrado[df_filtrado["local"] == LOCAL_CASA]
    df_fora = df_filtrado[df_filtrado["local"] == LOCAL_FORA]
    aprov_casa = calcular_aproveitamento(df_casa)
    aprov_fora = calcular_aproveitamento(df_fora)
 
    metricas_cv = [
        ("Aproveitamento (%)",  f"{aprov_casa:.1f}",  f"{aprov_fora:.1f}"),
        ("Vitórias",            str((df_casa["resultado"]==RESULTADO_VITORIA).sum()), str((df_fora["resultado"]==RESULTADO_VITORIA).sum())),
        ("Empates",             str((df_casa["resultado"]==RESULTADO_EMPATE).sum()),  str((df_fora["resultado"]==RESULTADO_EMPATE).sum())),
        ("Derrotas",            str((df_casa["resultado"]==RESULTADO_DERROTA).sum()), str((df_fora["resultado"]==RESULTADO_DERROTA).sum())),
        ("Gols pró/jogo",       f"{df_casa['gols_usuario'].mean():.2f}" if len(df_casa)>0 else "—", f"{df_fora['gols_usuario'].mean():.2f}" if len(df_fora)>0 else "—"),
        ("Gols sofr./jogo",     f"{df_casa['gols_adv'].mean():.2f}" if len(df_casa)>0 else "—",     f"{df_fora['gols_adv'].mean():.2f}" if len(df_fora)>0 else "—"),
        ("xG médio",            f"{df_casa['xg_usuario'].mean():.2f}" if len(df_casa)>0 else "—",   f"{df_fora['xg_usuario'].mean():.2f}" if len(df_fora)>0 else "—"),
        ("Posse média (%)",     f"{df_casa['posse_usuario'].mean():.1f}" if len(df_casa)>0 else "—", f"{df_fora['posse_usuario'].mean():.1f}" if len(df_fora)>0 else "—"),
    ]
    df_cv = pd.DataFrame(metricas_cv, columns=["Métrica", "🏠 Casa", "✈️ Fora"])
    st.dataframe(df_cv, use_container_width=True, hide_index=True)
 
    # ════════════════════════════════════════════════════════════════════
    # SEÇÃO 5 — TENDÊNCIA E EVOLUÇÃO
    # ════════════════════════════════════════════════════════════════════
    st.divider()
    st.markdown("## 📈 Tendência e Evolução")
 
    # Média móvel de 5 jogos para gols, xG e posse
    df_trend = df_filtrado.copy().reset_index(drop=True)
    df_trend["gols_mm5"]  = df_trend["gols_usuario"].rolling(5, min_periods=1).mean()
    df_trend["xg_mm5"]    = df_trend["xg_usuario"].rolling(5, min_periods=1).mean()
    df_trend["posse_mm5"] = df_trend["posse_usuario"].rolling(5, min_periods=1).mean()
    df_trend["aprov_mm5"] = df_trend["resultado"].map(
        {RESULTADO_VITORIA: 100, RESULTADO_EMPATE: 33, RESULTADO_DERROTA: 0}
    ).rolling(5, min_periods=1).mean()
 
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=df_trend["data"], y=df_trend["gols_mm5"],
        name="Gols (MM5)", line=dict(color="#22c55e", width=2)
    ))
    fig_trend.add_trace(go.Scatter(
        x=df_trend["data"], y=df_trend["xg_mm5"],
        name="xG (MM5)", line=dict(color="#3b82f6", width=2, dash="dot")
    ))
    fig_trend.update_layout(
        title="Média Móvel (5 jogos) — Gols vs xG",
        xaxis_title="Data", yaxis_title="",
        legend=dict(orientation="h"),
        height=280, margin=dict(t=40, b=40)
    )
    st.plotly_chart(fig_trend, use_container_width=True)
 
    # Aproveitamento acumulado
    df_trend["aprov_acum"] = [
        calcular_aproveitamento(df_trend.iloc[:i+1]) for i in range(len(df_trend))
    ]
    fig_aprov = go.Figure(go.Scatter(
        x=df_trend["data"], y=df_trend["aprov_acum"],
        name="Aproveitamento acumulado",
        fill="tozeroy", fillcolor="rgba(34,197,94,0.15)",
        line=dict(color="#22c55e", width=2)
    ))
    fig_aprov.add_hline(y=60, line_dash="dash", line_color="#eab308",
                        annotation_text="Meta 60%", annotation_position="bottom right")
    fig_aprov.update_layout(
        title="Aproveitamento Acumulado ao Longo da Temporada",
        xaxis_title="Data", yaxis_title="Aproveitamento (%)",
        yaxis=dict(range=[0, 105]),
        height=260, margin=dict(t=40, b=40)
    )
    st.plotly_chart(fig_aprov, use_container_width=True)
 
    # ════════════════════════════════════════════════════════════════════
    # SEÇÃO 6 — ANÁLISE DE JOGADORES (só aparece se tiver dados)
    # ════════════════════════════════════════════════════════════════════
    if tem_jogadores:
        st.divider()
        st.markdown("## 👥 Análise Individual de Jogadores")
        st.caption(f"Baseado em {df_jog['partida_id'].nunique()} partida(s) com dados de jogadores importados.")
 
        # Agrega por jogador (soma de contribuições, média de percentuais)
        df_agg = df_jog.groupby("nome").agg(
            partidas        =("partida_id", "nunique"),
            minutos_total   =("minutos_jogados", "sum"),
            golos           =("golos", "sum"),
            assistencias    =("assistencias", "sum"),
            xg_total        =("xg", "sum"),
            xa_total        =("xa", "sum"),
            intercepcoes    =("intercepcoes", "sum"),
            faltas_cometidas=("faltas_cometidas", "sum"),
            faltas_sofridas =("faltas_sofridas", "sum"),
            passes_prog     =("passes_progressivos", "sum"),
            passes_dec      =("passes_decisivos", "sum"),
            fintas          =("fintas", "sum"),
            dist_total      =("distancia_km", "sum"),
            perc_passes_med =("perc_passes", "mean"),
        ).reset_index()
 
        min_safe = df_agg["minutos_total"].replace(0, pd.NA)
        df_agg["golos_90"]  = (df_agg["golos"]  / min_safe * 90).round(2)
        df_agg["xg_90"]     = (df_agg["xg_total"]/ min_safe * 90).round(2)
        df_agg["contrib_90"]= ((df_agg["golos"] + df_agg["assistencias"]) / min_safe * 90).round(2)
        df_agg["dist_90"]   = (df_agg["dist_total"] / min_safe * 90).round(2)
        df_agg = df_agg.sort_values("minutos_total", ascending=False)
 
        tab_art, tab_rank, tab_vol, tab_criacao = st.tabs([
            "🥇 Artilheiros & Assistentes",
            "📊 Ranking Completo",
            "🏃 Volume & Físico",
            "🎯 Criação de Jogo"
        ])
 
        with tab_art:
            col_g, col_a = st.columns(2)
            with col_g:
                st.markdown("**⚽ Top Goleadores**")
                top_gols = df_agg[df_agg["golos"] > 0].nlargest(8, "golos")[
                    ["nome", "partidas", "minutos_total", "golos", "xg_total", "golos_90"]
                ].rename(columns={
                    "nome": "Jogador", "partidas": "Jogos", "minutos_total": "Min",
                    "golos": "Gols", "xg_total": "xG Total", "golos_90": "Gols/90"
                })
                st.dataframe(top_gols, hide_index=True, use_container_width=True)
 
                if len(df_agg[df_agg["golos"] > 0]) > 0:
                    fig_gols = px.bar(
                        df_agg[df_agg["golos"] > 0].nlargest(8, "golos"),
                        x="nome", y=["golos", "xg_total"],
                        barmode="group",
                        color_discrete_map={"golos": "#22c55e", "xg_total": "#3b82f6"},
                        labels={"nome": "", "value": "", "variable": ""},
                        title="Gols vs xG por Jogador"
                    )
                    fig_gols.update_layout(height=280, margin=dict(t=40, b=60), showlegend=True)
                    st.plotly_chart(fig_gols, use_container_width=True)
 
            with col_a:
                st.markdown("**🎯 Top Assistentes**")
                top_assist = df_agg[df_agg["assistencias"] > 0].nlargest(8, "assistencias")[
                    ["nome", "partidas", "minutos_total", "assistencias", "xa_total"]
                ].rename(columns={
                    "nome": "Jogador", "partidas": "Jogos", "minutos_total": "Min",
                    "assistencias": "Assists", "xa_total": "xA Total"
                })
                st.dataframe(top_assist, hide_index=True, use_container_width=True)
 
                # Contribuições totais (G+A)
                st.markdown("**🤝 G+A (Gols + Assistências)**")
                df_ga = df_agg.copy()
                df_ga["G+A"] = df_ga["golos"] + df_ga["assistencias"]
                top_ga = df_ga[df_ga["G+A"] > 0].nlargest(8, "G+A")[["nome", "golos", "assistencias", "G+A", "contrib_90"]]
                top_ga.columns = ["Jogador", "Gols", "Assists", "G+A", "G+A/90"]
                st.dataframe(top_ga, hide_index=True, use_container_width=True)
 
        with tab_rank:
            st.markdown("**Ranking geral — ordenável por qualquer coluna**")
            df_rank = df_agg[[
                "nome", "partidas", "minutos_total", "golos", "assistencias",
                "xg_total", "xa_total", "golos_90", "contrib_90", "perc_passes_med"
            ]].copy()
            df_rank.columns = [
                "Jogador", "Jogos", "Minutos", "Gols", "Assists",
                "xG", "xA", "Gols/90", "G+A/90", "% Passes"
            ]
            df_rank["xG"] = df_rank["xG"].round(2)
            df_rank["xA"] = df_rank["xA"].round(2)
            df_rank["% Passes"] = df_rank["% Passes"].round(1)
            st.dataframe(df_rank, hide_index=True, use_container_width=True, height=400)
 
        with tab_vol:
            st.markdown("**Volume físico e disciplina**")
            df_vol = df_agg[[
                "nome", "minutos_total", "dist_total", "dist_90",
                "intercepcoes", "faltas_cometidas", "faltas_sofridas", "fintas"
            ]].copy()
            df_vol.columns = [
                "Jogador", "Minutos", "Dist. Total (km)", "Dist./90",
                "Intercepções", "Faltas Com.", "Faltas Sofr.", "Fintas"
            ]
            df_vol["Dist. Total (km)"] = df_vol["Dist. Total (km)"].round(1)
            st.dataframe(df_vol, hide_index=True, use_container_width=True, height=400)
 
            # Top distância percorrida
            fig_dist = px.bar(
                df_agg.nlargest(10, "dist_total"),
                x="nome", y="dist_total",
                color="dist_90",
                color_continuous_scale="Viridis",
                labels={"nome": "", "dist_total": "Dist. Total (km)", "dist_90": "Dist./90"},
                title="Top 10 — Distância Total Percorrida"
            )
            fig_dist.update_layout(height=300, margin=dict(t=40, b=60))
            st.plotly_chart(fig_dist, use_container_width=True)
 
        with tab_criacao:
            st.markdown("**Passes decisivos, progressivos e criação de oportunidades**")
            df_cri = df_agg[[
                "nome", "minutos_total", "passes_prog", "passes_dec",
                "xa_total", "assistencias", "fintas"
            ]].copy()
            df_cri.columns = [
                "Jogador", "Minutos", "Passes Prog.", "Passes Dec.",
                "xA", "Assists", "Fintas"
            ]
            df_cri = df_cri.sort_values("Passes Prog.", ascending=False)
            st.dataframe(df_cri, hide_index=True, use_container_width=True, height=360)
 
            col_pp, col_pd = st.columns(2)
            with col_pp:
                top_pp = df_agg[df_agg["passes_prog"] > 0].nlargest(8, "passes_prog")
                if not top_pp.empty:
                    fig_pp = px.bar(top_pp, x="nome", y="passes_prog",
                                    title="Top Passes Progressivos",
                                    labels={"nome": "", "passes_prog": ""},
                                    color_discrete_sequence=["#3b82f6"])
                    fig_pp.update_layout(height=260, margin=dict(t=40, b=60))
                    st.plotly_chart(fig_pp, use_container_width=True)
            with col_pd:
                top_pd = df_agg[df_agg["passes_dec"] > 0].nlargest(8, "passes_dec")
                if not top_pd.empty:
                    fig_pd = px.bar(top_pd, x="nome", y="passes_dec",
                                    title="Top Passes Decisivos",
                                    labels={"nome": "", "passes_dec": ""},
                                    color_discrete_sequence=["#a855f7"])
                    fig_pd.update_layout(height=260, margin=dict(t=40, b=60))
                    st.plotly_chart(fig_pd, use_container_width=True)
 
    # ════════════════════════════════════════════════════════════════════
    # SEÇÃO 7 — PADRÃO EUROPEU
    # ════════════════════════════════════════════════════════════════════
    st.divider()
    st.markdown("## 🌍 Comparativo — Padrão Europeu")
 
    metricas_bench = {
        "xg_usuario":              (t("xg_por_jogo", lang),       df_filtrado["xg_usuario"].mean(), "maior"),
        "gols_usuario":            (t("gols_por_jogo", lang),      df_filtrado["gols_usuario"].mean(), "maior"),
        "remates_usuario":         (t("remates_por_jogo", lang),   df_filtrado["remates_usuario"].mean(), "maior"),
        "remates_a_baliza_usuario":(t("remates_alvo_label", lang), df_filtrado["remates_a_baliza_usuario"].mean(), "maior"),
        "posse_usuario":           (t("posse_media_label", lang),  df_filtrado["posse_usuario"].mean(), "maior"),
        "passes_certos_usuario":   (t("passes_certos_label", lang),df_filtrado["passes_certos_usuario"].mean(), "maior"),
        "aproveitamento":          (t("aproveitamento_label", lang),aproveitamento_geral, "maior"),
    }
 
    linhas_bench = []
    for chave, (label, meu_valor, regra) in metricas_bench.items():
        bm = BENCHMARK[chave]
        emoji, status, cor, intervalo = comparar_com_benchmark(meu_valor, bm, regra)
        linhas_bench.append({
            "Métrica": label,
            "Seu valor": round(meu_valor, 2),
            "Ref. europeia": intervalo,
            "Status": f"{emoji} {status}"
        })
    st.dataframe(pd.DataFrame(linhas_bench), use_container_width=True, hide_index=True)
 
    score = calcular_score_benchmark(df_filtrado, aproveitamento_geral)
    tipo_msg, msg = diagnostico_geral(score)
    if tipo_msg == "success":
        st.success(f"🎯 {msg}")
    elif tipo_msg == "warning":
        st.warning(f"⚠️ {msg}")
    else:
        st.error(f"📉 {msg}")


# =======================
# TAB 3: HISTÓRICO
# =======================
with tab3:
    st.subheader(t("historico_titulo", lang))

    if not partidas:
        st.info(t("nenhuma_partida_hist", lang))
        st.stop()

    df_display = df.copy()
    df_display["data"] = df_display["data"].dt.strftime("%d/%m/%Y")

    st.dataframe(
        df_display[[
            "data", "time_usuario", "gols_usuario", "gols_adv", "time_adv",
            "resultado", "local", "competicao", "temporada", "xg_usuario", "xg_adv"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.divider()
    st.subheader(t("gerenciar_titulo", lang))

    partida_deletar = st.selectbox(
        t("selecionar_deletar", lang),
        options=df["id"].tolist(),
        format_func=lambda x: f"{df[df['id']==x]['data'].iloc[0].strftime('%d/%m/%Y')} - {df[df['id']==x]['time_usuario'].iloc[0]} {df[df['id']==x]['gols_usuario'].iloc[0]}x{df[df['id']==x]['gols_adv'].iloc[0]} {df[df['id']==x]['time_adv'].iloc[0]}"
    )

    if st.button(t("btn_deletar", lang), type="secondary"):
        if deletar_partida(partida_deletar):
            st.success(t("deletar_sucesso", lang))
            st.rerun()
        else:
            st.error(t("deletar_erro", lang))


# =======================
# TAB 4: ASSISTENTE IA
# =======================
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

with tab4:
    st.subheader(t("tab_ia", lang))
    
    # Recuperamos o DF filtrado que foi salvo na Tab 2
    if 'df_para_ia' in st.session_state and not st.session_state.df_para_ia.empty:
        df_ia = st.session_state.df_para_ia
        
        st.write(f"📋 {t('total_partidas', lang)}: {len(df_ia)}")
        
        # Botão de Ação
        if st.button(t("ia_analisar", lang), type="primary", use_container_width=True):
            
            # 1. Seleção de colunas críticas para não poluir o contexto
            colunas_vaitais = [
                'time_adv', 'local', 'resultado', 'gols_usuario', 'gols_adv',
                'xg_usuario', 'xg_adv', 'posse_usuario', 'remates_usuario',
                'remates_a_baliza_usuario', 'oportunidades_flagrantes_usuario',
                'passes_certos_usuario', 'passes_totais_usuario'
            ]
            
            # Adicionamos notas_treinador se você já tiver criado a coluna no banco
            if 'notas_treinador' in df_ia.columns:
                colunas_vaitais.append('notas_treinador')
            
            dados_contexto = df_ia[colunas_vaitais].to_csv(index=False)
            
            # 2. Chamada da IA
            with st.spinner("🧠 " + t("ia_processando", lang)):
                try:
                    # Injetamos o idioma dinamicamente
                    lang_instruction = f"\n\nIMPORTANT: Respond strictly in {st.session_state.idioma}."
                    
                    # ✅ Novo
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=PROMPT_ASSISTENTE + lang_instruction + "\n\n" + dados_contexto
                    )

                    
                    st.divider()
                    st.markdown(f"### {t['ia_veredito']}")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.warning("⚠️ " + t("msg_sem_dados_ia", lang))


# =======================
# FOOTER
# =======================
st.divider()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.caption(t("footer_email", lang))
with col2:
    st.caption(t("footer_seguro", lang))
with col3:
    st.link_button(t("footer_canal", lang), "https://www.youtube.com/@OnzeVirtual-FC")
with col4:
    st.caption(t("footer_versao", lang))