import streamlit as st
import pandas as pd
import io

# Adicionar imports para ReportLab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Funções auxiliares para processar os placares
def extrair_scores(placar_str, nosso_time_primeiro=True):
    """Extrai os scores de uma string 'X-Y'."""
    try:
        parts = str(placar_str).split('-')
        if len(parts) == 2:
            score1 = int(parts[0].strip())
            score2 = int(parts[1].strip())
            return (score1, score2) if nosso_time_primeiro else (score2, score1)
        return None, None # Retornar None para indicar falha na extração
    except:
        return None, None

def processar_dados(df):
    """Processa o DataFrame para cálculos."""
    df = df.rename(columns={
        'Data do jogo': 'data_jogo',
        'Hora do jogo': 'hora_jogo',
        'Time adversario': 'time_adversario',
        'Mapa jogado': 'mapa',
        'Placar final do jogo': 'placar_final_str',
        'Placar lado CT': 'placar_ct_str',
        'Placar lado TR': 'placar_tr_str',
        'Pistol CT': 'pistol_ct_resultado',
        'Pistol TR': 'pistol_tr_resultado',
        'Composicao': 'composicao_nossa',
        'Composicao adversaria': 'composicao_adversaria'
    })

    scores_finais = df['placar_final_str'].apply(lambda x: pd.Series(extrair_scores(x)))
    df['placar_final_nosso'] = scores_finais[0]
    df['placar_final_adv'] = scores_finais[1]

    scores_ct = df['placar_ct_str'].apply(lambda x: pd.Series(extrair_scores(x)))
    df['placar_ct_nosso_como_ct'] = scores_ct[0]
    df['placar_ct_adv_como_tr'] = scores_ct[1]

    scores_tr = df['placar_tr_str'].apply(lambda x: pd.Series(extrair_scores(x)))
    df['placar_tr_nosso_como_tr'] = scores_tr[0]
    df['placar_tr_adv_como_ct'] = scores_tr[1]

    df['pistol_ct_resultado'] = df['pistol_ct_resultado'].astype(str).str.lower().str.strip()
    df['pistol_tr_resultado'] = df['pistol_tr_resultado'].astype(str).str.lower().str.strip()

    def limpar_composicao(comp_str):
        if pd.isna(comp_str) or str(comp_str).strip() == '':
            return tuple()
        agentes = sorted([agente.strip() for agente in str(comp_str).split(',') if agente.strip()])
        return tuple(agentes) if agentes else tuple()

    df['composicao_nossa_clean'] = df['composicao_nossa'].apply(limpar_composicao)
    df['composicao_adversaria_clean'] = df['composicao_adversaria'].apply(limpar_composicao)

    df['nosso_time_venceu_partida'] = df['placar_final_nosso'].notna() & df['placar_final_adv'].notna() & (df['placar_final_nosso'] > df['placar_final_adv'])
    df['nosso_time_venceu_lado_ct'] = df['placar_ct_nosso_como_ct'].notna() & df['placar_ct_adv_como_tr'].notna() & (df['placar_ct_nosso_como_ct'] > df['placar_ct_adv_como_tr'])
    df['nosso_time_venceu_lado_tr'] = df['placar_tr_nosso_como_tr'].notna() & df['placar_tr_adv_como_ct'].notna() & (df['placar_tr_nosso_como_tr'] > df['placar_tr_adv_como_ct'])

    return df

def get_color_category(rate):
    if pd.isna(rate): return 'Neutra (50%)'
    if rate > 50: return 'Positiva (>50%)'
    elif rate < 50: return 'Negativa (<50%)'
    else: return 'Neutra (50%)'

def calcular_metricas(df_filtrado, nome_do_mapa_ou_geral="geral"):
    if df_filtrado.empty:
        return {
            "nome_mapa_ou_contexto": nome_do_mapa_ou_geral,
            "win_rate_geral_partidas_nosso_time": 0, "total_partidas_jogadas_nosso_time": 0,
            "win_rate_ct_rounds": 0, "total_ct_rounds_jogados": 0,
            "win_rate_tr_rounds": 0, "total_tr_rounds_jogados": 0,
            "win_rate_pistol_ct": 0, "total_pistols_ct_disputados": 0,
            "win_rate_pistol_tr": 0, "total_pistols_tr_disputados": 0,
            "composicao_stats": pd.DataFrame(), "h2h_stats": pd.DataFrame(),
            "melhor_nossa_composicao_info": {"composicao": "N/A", "win_rate_partidas": 0, "partidas_jogadas": 0, "raw_composicao": tuple()} # Ajustado
        }

    total_partidas_jogadas = len(df_filtrado)

    vitorias_partida_nosso_time = df_filtrado['nosso_time_venceu_partida'].sum()
    win_rate_geral_partidas_nosso_time = (vitorias_partida_nosso_time / total_partidas_jogadas) * 100 if total_partidas_jogadas > 0 else 0

    vitorias_lado_ct_nosso_time = df_filtrado['nosso_time_venceu_lado_ct'].sum()
    win_rate_lado_ct = (vitorias_lado_ct_nosso_time / total_partidas_jogadas) * 100 if total_partidas_jogadas > 0 else 0

    vitorias_lado_tr_nosso_time = df_filtrado['nosso_time_venceu_lado_tr'].sum()
    win_rate_lado_tr = (vitorias_lado_tr_nosso_time / total_partidas_jogadas) * 100 if total_partidas_jogadas > 0 else 0

    vitorias_pistol_ct_nosso_time = (df_filtrado['pistol_ct_resultado'] == 'win').sum()
    win_rate_pistol_ct_nosso_time = (vitorias_pistol_ct_nosso_time / total_partidas_jogadas) * 100 if total_partidas_jogadas > 0 else 0

    vitorias_pistol_tr_nosso_time = (df_filtrado['pistol_tr_resultado'] == 'win').sum()
    win_rate_pistol_tr_nosso_time = (vitorias_pistol_tr_nosso_time / total_partidas_jogadas) * 100 if total_partidas_jogadas > 0 else 0

    # --- Estatísticas de Composição por Partida ---
    comp_data_partida = []
    for _, row in df_filtrado.iterrows():
        nossa_comp_val = str(row['composicao_nossa_clean'])
        adv_comp_val = str(row['composicao_adversaria_clean'])
        nosso_time_venceu = row['nosso_time_venceu_partida']

        if nossa_comp_val != '()':
            comp_data_partida.append({
                'composicao': nossa_comp_val,
                'tipo': 'Nossa',
                'partida_ganha': 1 if nosso_time_venceu else 0,
                'partida_jogada': 1
            })
        if adv_comp_val != '()':
            comp_data_partida.append({
                'composicao': adv_comp_val,
                'tipo': 'Adversária',
                'partida_ganha': 1 if not nosso_time_venceu else 0, # Vitória da comp adversária
                'partida_jogada': 1
            })

    composicao_stats_df = pd.DataFrame()
    # Removido 'lado' de melhor_nossa_composicao_info, pois agora é por partida
    melhor_nossa_composicao_info = {"composicao": "N/A", "win_rate_partidas": 0, "partidas_jogadas": 0, "raw_composicao": tuple()}


    if comp_data_partida:
        comp_df_partida = pd.DataFrame(comp_data_partida)
        if not comp_df_partida.empty:
            # Agrupar por composição e tipo, sem 'lado'
            composicao_stats_df = comp_df_partida.groupby(['composicao', 'tipo']).agg(
                total_partidas_ganhas=('partida_ganha', 'sum'),
                total_partidas_jogadas=('partida_jogada', 'sum')
            ).reset_index()
            composicao_stats_df['win_rate_partidas'] = (composicao_stats_df['total_partidas_ganhas'] / composicao_stats_df['total_partidas_jogadas'] * 100).fillna(0)
            # 'cor_win_rate' agora se baseia em 'win_rate_partidas'
            composicao_stats_df['cor_win_rate'] = composicao_stats_df['win_rate_partidas'].apply(get_color_category)

            nossas_comps_stats_df = composicao_stats_df[composicao_stats_df['tipo'] == 'Nossa'].copy()
            if not nossas_comps_stats_df.empty:
                # Ordenar por win_rate_partidas e depois por total_partidas_jogadas
                nossas_comps_stats_df = nossas_comps_stats_df.sort_values(
                    by=['win_rate_partidas', 'total_partidas_jogadas'],
                    ascending=[False, False]
                )
                top_comp_row = nossas_comps_stats_df.iloc[0]
                try:
                    comp_tuple = eval(top_comp_row['composicao'])
                    cleaned_comp_str = ", ".join(comp_tuple) if isinstance(comp_tuple, tuple) else top_comp_row['composicao']
                except:
                    cleaned_comp_str = top_comp_row['composicao']

                melhor_nossa_composicao_info = {
                    "composicao": cleaned_comp_str,
                    "win_rate_partidas": top_comp_row['win_rate_partidas'], # Nova chave
                    "partidas_jogadas": top_comp_row['total_partidas_jogadas'], # Nova chave
                    "raw_composicao": top_comp_row['composicao']
                    # "lado" foi removido
                }
    # Fim da Estatística de Composição por Partida

    h2h_data = []
    for _, row in df_filtrado.iterrows():
        nossa_comp_h2h = str(row['composicao_nossa_clean'])
        adv_comp_h2h = str(row['composicao_adversaria_clean'])
        if nossa_comp_h2h == '()' or adv_comp_h2h == '()': continue
        h2h_data.append({'nossa_composicao': nossa_comp_h2h, 'composicao_adversaria': adv_comp_h2h,
                            'vitoria_nossa_comp': int(row['nosso_time_venceu_partida']), 'partidas_disputadas': 1})

    h2h_stats_df = pd.DataFrame()
    if h2h_data:
        h2h_df = pd.DataFrame(h2h_data)
        if not h2h_df.empty:
            h2h_stats_df = h2h_df.groupby(['nossa_composicao', 'composicao_adversaria']).agg(
                total_vitorias_nossa_comp=('vitoria_nossa_comp', 'sum'),
                total_partidas_disputadas=('partidas_disputadas', 'sum')
            ).reset_index()
            h2h_stats_df['win_rate_vs_adv_comp'] = (h2h_stats_df['total_vitorias_nossa_comp'] / h2h_stats_df['total_partidas_disputadas'] * 100).fillna(0)
            try:
                h2h_stats_df['nossa_composicao'] = h2h_stats_df['nossa_composicao'].apply(lambda x: ", ".join(eval(x)) if isinstance(eval(x), tuple) else x)
                h2h_stats_df['composicao_adversaria'] = h2h_stats_df['composicao_adversaria'].apply(lambda x: ", ".join(eval(x)) if isinstance(eval(x), tuple) else x)
            except:
                pass
            h2h_stats_df = h2h_stats_df.sort_values(by=['win_rate_vs_adv_comp'], ascending=False)

    return {
        "nome_mapa_ou_contexto": nome_do_mapa_ou_geral,
        "win_rate_geral_partidas_nosso_time": win_rate_geral_partidas_nosso_time,
        "total_partidas_jogadas_nosso_time": total_partidas_jogadas,
        "win_rate_ct_rounds": win_rate_lado_ct,
        "total_ct_rounds_jogados": total_partidas_jogadas,
        "win_rate_tr_rounds": win_rate_lado_tr,
        "total_tr_rounds_jogados": total_partidas_jogadas,
        "win_rate_pistol_ct": win_rate_pistol_ct_nosso_time,
        "total_pistols_ct_disputados": total_partidas_jogadas,
        "win_rate_pistol_tr": win_rate_pistol_tr_nosso_time,
        "total_pistols_tr_disputados": total_partidas_jogadas,
        "composicao_stats": composicao_stats_df, # Agora baseado em partidas
        "h2h_stats": h2h_stats_df,
        "melhor_nossa_composicao_info": melhor_nossa_composicao_info # Agora baseado em partidas
    }


def get_color_for_percentage_text(value):
    if pd.isna(value): return "grey"
    if value > 50: return "green"
    elif value < 50: return "red"
    else: return "orange"

def exibir_metricas_card(label, value, total_label="", total_value="", is_percentage=True):
    color = get_color_for_percentage_text(value) if is_percentage else "black"
    if pd.isna(value):
        formatted_value = "N/A"
    elif is_percentage:
        formatted_value = f"{value:.2f}%"
    else:
        try:
            formatted_value = f"{int(value)}" if pd.api.types.is_number(value) else str(value)
        except ValueError:
            formatted_value = str(value)

    details_text = f"{total_value} {total_label}" if total_label and total_value is not None else ""
    if "rounds CT jogados" in total_label or "rounds TR jogados" in total_label:
        details_text = details_text.replace("rounds", "partidas (lados)").replace("jogados", "jogadas")
    if "pistols CT disputados" in total_label or "pistols TR disputados" in total_label:
        details_text = details_text.replace("pistols", "partidas com pistol").replace("disputados", "disputadas")
    if "Win Rate CT (Rounds)" in label:
        label = label.replace("(Rounds)", "(Lados Vencidos)")
    if "Win Rate TR (Rounds)" in label:
        label = label.replace("(Rounds)", "(Lados Vencidos)")
    details_html = f'<span style="font-size: 0.8em; color: #777;">{details_text}</span>' if details_text else ""
    st.markdown(f"""
    <div style="border: 1px solid #e0e0e0; border-radius: 5px; padding: 10px; margin-bottom:10px; text-align: center;">
        <span style="font-size: 0.9em; color: #555;">{label}</span><br>
        <span style="font-size: 1.75em; color: {color}; font-weight: bold;">{formatted_value}</span><br>
        {details_html}
    </div>""", unsafe_allow_html=True)

def style_win_rate_h2h(val):
    if pd.isna(val): return 'color: grey'
    color = 'red' if val < 50 else ('orange' if val == 50 else 'green')
    return f'color: {color}; font-weight: bold;'

# --- Funções para Geração de PDF ---
def get_reportlab_color(value):
    if pd.isna(value): return colors.grey
    if value > 50: return colors.Color(0, 0.6, 0)
    elif value < 50: return colors.red
    else: return colors.orange

def add_metric_to_story(story, styles, label, value, total_label="", total_value="", is_percentage=True, indent=0):
    color = get_reportlab_color(value) if is_percentage else colors.black
    if pd.isna(value):
        formatted_value = "N/A"
    elif is_percentage:
        formatted_value = f"{value:.2f}%"
    else:
        try:
            formatted_value = f"{int(value)}" if pd.api.types.is_number(value) else str(value)
        except ValueError:
            formatted_value = str(value)

    label_style = ParagraphStyle('MetricLabel', parent=styles['Normal'], fontName='Helvetica-Bold', spaceBefore=6, leftIndent=indent)
    value_style = ParagraphStyle('MetricValue', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14,textColor=color, spaceBefore=2, leftIndent=indent)
    details_style = ParagraphStyle('MetricDetails', parent=styles['Normal'], fontSize=8, textColor=colors.dimgrey, spaceBefore=1, leftIndent=indent)

    details_text_pdf = f"{total_value} {total_label}" if total_label and total_value is not None else ""
    if "rounds CT jogados" in total_label or "rounds TR jogados" in total_label:
        details_text_pdf = details_text_pdf.replace("rounds", "partidas (lados)").replace("jogados", "jogadas")
    if "pistols CT disputados" in total_label or "pistols TR disputados" in total_label:
        details_text_pdf = details_text_pdf.replace("pistols", "partidas com pistol").replace("disputados", "disputadas")
    label_pdf = label
    if "Win Rate CT (Rounds)" in label:
        label_pdf = label.replace("(Rounds)", "(Lados Vencidos)")
    if "Win Rate TR (Rounds)" in label:
        label_pdf = label.replace("(Rounds)", "(Lados Vencidos)")

    story.append(Paragraph(label_pdf, label_style))
    story.append(Paragraph(formatted_value, value_style))
    if details_text_pdf:
        story.append(Paragraph(details_text_pdf, details_style))
    story.append(Spacer(1, 0.1*inch))

def create_h2h_table_reportlab(h2h_stats_df):
    if h2h_stats_df is None or h2h_stats_df.empty:
        return Paragraph("Não há dados de confrontos diretos (H2H) para exibir.", getSampleStyleSheet()['Normal'])
    df_display = h2h_stats_df.copy()
    df_display['win_rate_vs_adv_comp_display'] = df_display['win_rate_vs_adv_comp'].apply(lambda x: f"{x:.2f}%" if not pd.isna(x) else "N/A")
    data = [["Nossa Composição", "Composição Adversária", "Vitórias da Nossa Comp.", "Partidas Disputadas", "Win Rate vs Adv."]]
    for _, row in df_display.iterrows():
        data.append([
            Paragraph(str(row['nossa_composicao']), getSampleStyleSheet()['Normal']),
            Paragraph(str(row['composicao_adversaria']), getSampleStyleSheet()['Normal']),
            str(row['total_vitorias_nossa_comp']),
            str(row['total_partidas_disputadas']),
            Paragraph(str(row['win_rate_vs_adv_comp_display']), ParagraphStyle('WR', textColor=get_reportlab_color(row['win_rate_vs_adv_comp'])))
        ])
    col_widths = [2*inch, 2*inch, 0.8*inch, 0.8*inch, 1*inch]
    table = Table(data, colWidths=col_widths)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),('TOPPADDING', (0,0), (-1,0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 3),('RIGHTPADDING', (0,0), (-1,-1), 3),
    ])
    table.setStyle(style)
    return table

def gerar_relatorio_pdf(metricas_globais, df_map_ranking, metricas_detalhadas_por_mapa, mapas_unicos_ordenados):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(8.5*inch, 11*inch), leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['h1'], fontName='Helvetica-Bold', fontSize=18, alignment=TA_CENTER, spaceAfter=0.2*inch)
    h2_style = ParagraphStyle('Heading2', parent=styles['h2'], fontName='Helvetica-Bold', fontSize=14, spaceBefore=0.2*inch, spaceAfter=0.1*inch)
    h3_style = ParagraphStyle('Heading3', parent=styles['h3'], fontName='Helvetica-Bold', fontSize=11, spaceBefore=0.15*inch, spaceAfter=0.05*inch)
    normal_style = ParagraphStyle('BodyText', parent=styles['Normal'], fontSize=9) # Renomeado para evitar modificar o default

    story.append(Paragraph("Relatório Analítico de Partidas 📊", title_style))
    story.append(Paragraph("🌎 Visão Geral Global", h2_style))
    total_partidas_globais = metricas_globais.get('total_partidas_jogadas_nosso_time', 0)
    add_metric_to_story(story, styles, "Win Rate Lado CT", metricas_globais['win_rate_ct_rounds'], "partidas analisadas", total_partidas_globais)
    add_metric_to_story(story, styles, "Win Rate Pistol CT", metricas_globais['win_rate_pistol_ct'], "partidas analisadas", total_partidas_globais)
    add_metric_to_story(story, styles, "Win Rate Lado TR", metricas_globais['win_rate_tr_rounds'], "partidas analisadas", total_partidas_globais)
    add_metric_to_story(story, styles, "Win Rate Pistol TR", metricas_globais['win_rate_pistol_tr'], "partidas analisadas", total_partidas_globais)

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("🏆 Ranking de Mapas", h2_style))
    if not df_map_ranking.empty:
        ranking_data = [["Rank", "Mapa", "Win Rate (Partidas)", "Total Partidas", "Melhor Composição Nossa"]] # Label ajustado
        df_map_ranking_pdf = df_map_ranking.reset_index(drop=True)
        for i, row in df_map_ranking_pdf.iterrows():
            wr_partidas_text = f"{row['win_rate_geral_partidas_nosso_time']:.2f}%"
            comp_info_mapa = metricas_detalhadas_por_mapa.get(row['mapa'], {}).get('melhor_nossa_composicao_info', {})

            comp_str = comp_info_mapa.get('composicao', 'N/A')
            wr_comp_partidas = comp_info_mapa.get('win_rate_partidas', 0) # Usar win_rate_partidas
            partidas_jog_comp = comp_info_mapa.get('partidas_jogadas', 0) # Usar partidas_jogadas
            comp_details_str = f"{comp_str} (WR Partidas: {wr_comp_partidas:.2f}%, {partidas_jog_comp} partidas)"

            ranking_data.append([
                str(i + 1),
                Paragraph(str(row['mapa']), normal_style),
                Paragraph(wr_partidas_text, ParagraphStyle('WR_Rank', parent=normal_style, textColor=get_reportlab_color(row['win_rate_geral_partidas_nosso_time']))),
                str(row['total_partidas']),
                Paragraph(comp_details_str, normal_style)
            ])
        map_ranking_table = Table(ranking_data, colWidths=[0.5*inch, 1.2*inch, 1.2*inch, 0.8*inch, 3.3*inch])
        map_ranking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 7),
        ]))
        story.append(map_ranking_table)
    else:
        story.append(Paragraph("Não há dados suficientes para gerar o ranking de mapas.", normal_style))
    story.append(PageBreak())

    for mapa_nome in mapas_unicos_ordenados:
        metricas_mapa = metricas_detalhadas_por_mapa.get(mapa_nome)
        if not metricas_mapa: continue
        story.append(Paragraph(f"🗺️ Análise do Mapa: {mapa_nome}", h2_style))
        total_partidas_mapa = metricas_mapa.get('total_partidas_jogadas_nosso_time', 0)
        add_metric_to_story(story, styles, f"Win Rate Geral no {mapa_nome}", metricas_mapa['win_rate_geral_partidas_nosso_time'], "partidas jogadas", total_partidas_mapa)
        story.append(Spacer(1, 0.1*inch))
        add_metric_to_story(story, styles, "Win Rate Lado CT", metricas_mapa['win_rate_ct_rounds'], "partidas analisadas", total_partidas_mapa, indent=0.2*inch)
        add_metric_to_story(story, styles, "Win Rate Pistol CT", metricas_mapa['win_rate_pistol_ct'], "partidas analisadas", total_partidas_mapa, indent=0.2*inch)
        add_metric_to_story(story, styles, "Win Rate Lado TR", metricas_mapa['win_rate_tr_rounds'], "partidas analisadas", total_partidas_mapa, indent=0.2*inch)
        add_metric_to_story(story, styles, "Win Rate Pistol TR", metricas_mapa['win_rate_pistol_tr'], "partidas analisadas", total_partidas_mapa, indent=0.2*inch)

        story.append(Spacer(1, 0.2*inch))
        # Atualizar label para refletir que a melhor comp é por partida
        story.append(Paragraph(f"✨ Melhor Composição no mapa {mapa_nome} (baseado em Win Rate de Partidas)", h3_style))
        melhor_comp_info = metricas_mapa['melhor_nossa_composicao_info']
        if melhor_comp_info['composicao'] != "N/A":
            comp_text = f"Composição: {melhor_comp_info['composicao']}" # Lado não é mais relevante aqui
            # Usar win_rate_partidas e partidas_jogadas
            wr_text = f"Win Rate (Partidas): {melhor_comp_info.get('win_rate_partidas', 0):.2f}% ({melhor_comp_info.get('partidas_jogadas', 0)} partidas jogadas)"
            story.append(Paragraph(comp_text, normal_style))
            story.append(Paragraph(wr_text, ParagraphStyle('CompWR', parent=normal_style, textColor=get_reportlab_color(melhor_comp_info.get('win_rate_partidas', 0)))))
        else:
            story.append(Paragraph("Não há dados suficientes de nossas composições neste mapa.", normal_style))

        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"⚔️ Confrontos: Nossa Composição vs. Composição Adversária em {mapa_nome} (Resultado da Partida)", h3_style))
        h2h_stats_df_mapa = metricas_mapa.get('h2h_stats')
        story.append(create_h2h_table_reportlab(h2h_stats_df_mapa))
        if mapa_nome != mapas_unicos_ordenados[-1]: story.append(PageBreak())
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- Interface Streamlit ---
st.set_page_config(layout="wide")
st.title("Dashboard Analítico de partidas📊")
uploaded_file = st.file_uploader("Carregue seu arquivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df_original = pd.read_csv(uploaded_file)
        if df_original.empty:
            st.error("O arquivo CSV está vazio."); st.stop()
        st.success("Arquivo CSV carregado com sucesso!")
        df_processado = processar_dados(df_original.copy())
        mapas_unicos = sorted(df_processado['mapa'].dropna().astype(str).unique())
        if not mapas_unicos:
            st.warning("Nenhum mapa encontrado nos dados processados. Verifique a coluna 'Mapa jogado'."); st.stop()

        metricas_globais = calcular_metricas(df_processado, "Global")
        metricas_detalhadas_por_mapa = {}
        map_performance_data = []
        for mapa_nome in mapas_unicos:
            df_mapa_loop = df_processado[df_processado['mapa'] == mapa_nome]
            metricas_mapa_loop = calcular_metricas(df_mapa_loop, mapa_nome)
            metricas_detalhadas_por_mapa[mapa_nome] = metricas_mapa_loop
            map_performance_data.append({
                'mapa': mapa_nome,
                'win_rate_geral_partidas_nosso_time': metricas_mapa_loop['win_rate_geral_partidas_nosso_time'],
                'total_partidas': metricas_mapa_loop['total_partidas_jogadas_nosso_time'],
            })
        df_map_ranking = pd.DataFrame(map_performance_data)
        if not df_map_ranking.empty:
            df_map_ranking = df_map_ranking.sort_values(by='win_rate_geral_partidas_nosso_time', ascending=False)

        if not df_processado.empty:
            col_pdf_placeholder, col_pdf_btn = st.columns([0.75, 0.25])
            with col_pdf_btn:
                pdf_bytes = gerar_relatorio_pdf(metricas_globais, df_map_ranking, metricas_detalhadas_por_mapa, mapas_unicos)
                st.download_button(label="📄 Exportar Relatório para PDF", data=pdf_bytes, file_name="relatorio_analitico_partidas.pdf", mime="application/pdf", use_container_width=True)
        st.markdown("---")

        tab_geral_nome = "🌎 Geral"
        tabs_nomes = [tab_geral_nome] + [f"🗺️ {mapa}" for mapa in mapas_unicos]
        tabs = st.tabs(tabs_nomes)

        with tabs[0]: # Aba Geral
            st.header("Visão Geral Global")
            total_partidas_globais_display = metricas_globais.get('total_partidas_jogadas_nosso_time', 'N/A')
            col1, col2 = st.columns(2)
            with col1:
                exibir_metricas_card("Win Rate CT (Rounds)", metricas_globais['win_rate_ct_rounds'], "partidas analisadas", total_partidas_globais_display)
                exibir_metricas_card("Win Rate Pistol CT", metricas_globais['win_rate_pistol_ct'], "partidas analisadas", total_partidas_globais_display)
            with col2:
                exibir_metricas_card("Win Rate TR (Rounds)", metricas_globais['win_rate_tr_rounds'], "partidas analisadas", total_partidas_globais_display)
                exibir_metricas_card("Win Rate Pistol TR", metricas_globais['win_rate_pistol_tr'], "partidas analisadas", total_partidas_globais_display)
            st.markdown("---")
            st.header("🏆 Ranking de Mapas")
            if not df_map_ranking.empty:
                df_map_ranking_display = df_map_ranking.reset_index(drop=True)
                for i, row in df_map_ranking_display.iterrows():
                    rank_color_html = get_color_for_percentage_text(row['win_rate_geral_partidas_nosso_time'])
                    melhor_comp_mapa_info = metricas_detalhadas_por_mapa.get(row['mapa'], {}).get('melhor_nossa_composicao_info', {})

                    # Usar as novas chaves para win_rate_partidas e partidas_jogadas
                    melhor_comp_str = melhor_comp_mapa_info.get('composicao', 'N/A') # Lado não é mais principal aqui
                    wr_melhor_comp = melhor_comp_mapa_info.get('win_rate_partidas', 0)
                    partidas_jog_melhor_comp = melhor_comp_mapa_info.get('partidas_jogadas',0)

                    st.markdown(f"""
                    <div style="border-left: 5px solid {rank_color_html}; padding: 10px; margin-bottom: 10px; background-color: #f9f9f9; border-radius:5px; color: black;">
                        <h4 style="color:black; margin-top:0px; margin-bottom:5px;">{i+1}º - {row['mapa']}</h4>
                        <span style="color:black;">Win Rate Geral (Partidas): </span><strong style="color:{rank_color_html};">{row['win_rate_geral_partidas_nosso_time']:.2f}%</strong> <span style="color:black;">({row['total_partidas']} partidas)</span><br>
                        <span style="color:black;">Melhor Composição Nossa: </span><strong style="color:black;">{melhor_comp_str}</strong>
                        (WR Partidas: <span style="color:{get_color_for_percentage_text(wr_melhor_comp)};">{wr_melhor_comp:.2f}%</span>, {partidas_jog_melhor_comp} partidas)
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("Não há dados suficientes para gerar o ranking de mapas.")

        for i, mapa_nome_tab in enumerate(mapas_unicos): # Abas por Mapa
            with tabs[i+1]:
                metricas_mapa_tab = metricas_detalhadas_por_mapa.get(mapa_nome_tab)
                if not metricas_mapa_tab:
                    st.warning(f"Métricas não encontradas para o mapa {mapa_nome_tab}"); continue
                st.header(f"Análise do Mapa: {mapa_nome_tab}")
                total_partidas_mapa_display = metricas_mapa_tab.get('total_partidas_jogadas_nosso_time', 'N/A')
                exibir_metricas_card(f"Win Rate Geral no {mapa_nome_tab}", metricas_mapa_tab['win_rate_geral_partidas_nosso_time'], "partidas jogadas", total_partidas_mapa_display)
                st.markdown("---")
                col_map1, col_map2 = st.columns(2)
                with col_map1:
                    exibir_metricas_card("Win Rate CT (Rounds)", metricas_mapa_tab['win_rate_ct_rounds'], "partidas analisadas", total_partidas_mapa_display)
                    exibir_metricas_card("Win Rate Pistol CT", metricas_mapa_tab['win_rate_pistol_ct'], "partidas analisadas", total_partidas_mapa_display)
                with col_map2:
                    exibir_metricas_card("Win Rate TR (Rounds)", metricas_mapa_tab['win_rate_tr_rounds'], "partidas analisadas", total_partidas_mapa_display)
                    exibir_metricas_card("Win Rate Pistol TR", metricas_mapa_tab['win_rate_pistol_tr'], "partidas analisadas", total_partidas_mapa_display)
                st.markdown("---")
                # Atualizar label para refletir que a melhor comp é por partida
                st.subheader(f"✨ Melhor Composição no mapa {mapa_nome_tab} (baseado em Win Rate de Partidas)")
                melhor_comp_info = metricas_mapa_tab['melhor_nossa_composicao_info']
                if melhor_comp_info['composicao'] != "N/A":
                    cor_melhor_comp_html = get_color_for_percentage_text(melhor_comp_info.get('win_rate_partidas',0))
                    # Lado não é mais incluído no display da composição principal aqui, pois a métrica é geral da partida
                    st.markdown(f"""
                    Composição: **{melhor_comp_info['composicao']}**<br>
                    Win Rate (Partidas): <strong style="color:{cor_melhor_comp_html};">{melhor_comp_info.get('win_rate_partidas', 0):.2f}%</strong> ({melhor_comp_info.get('partidas_jogadas', 0)} partidas jogadas)
                    """, unsafe_allow_html=True)
                else:
                    st.write("Não há dados suficientes de nossas composições neste mapa.")
                st.markdown("---")
                st.subheader("⚔️ Confrontos: Nossa Composição vs. Composição Adversária (Resultado da Partida)")
                h2h_stats_df_mapa = metricas_mapa_tab.get('h2h_stats')
                if h2h_stats_df_mapa is not None and not h2h_stats_df_mapa.empty:
                    styled_h2h_df_mapa = h2h_stats_df_mapa.style.apply(lambda row: [''] * (len(row) -1) + [style_win_rate_h2h(row['win_rate_vs_adv_comp'])], axis=1, subset=['win_rate_vs_adv_comp']).format({'win_rate_vs_adv_comp': "{:.2f}%", 'total_vitorias_nossa_comp': "{:}", 'total_partidas_disputadas': "{:}"}).set_table_styles([{'selector': 'th', 'props': [('text-align', 'left')]}]) .set_properties(**{'width': '150px', 'text-align': 'left'})
                    st.write(f"Win Rate da Nossa Composição contra Composições Adversárias Específicas em {mapa_nome_tab}:")
                    st.dataframe(styled_h2h_df_mapa, use_container_width=True)
                else:
                    st.write(f"Não há dados de confrontos diretos (H2H) para exibir em {mapa_nome_tab}.")
    except UnicodeDecodeError:
        st.error("Erro de codificação ao ler o arquivo. Tente salvar seu CSV com codificação UTF-8.")
    except pd.errors.EmptyDataError:
        st.error("Erro: O arquivo CSV carregado está vazio ou não contém dados.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        st.exception(e)
        st.error("Verifique se o arquivo CSV está no formato esperado, se os nomes das colunas correspondem aos definidos no dicionário 'rename' da função 'processar_dados', e se os dados de placar estão corretos (ex: '13-7'). Certifique-se também que as colunas de placar e pistol existem e estão corretamente preenchidas.")
else:
    st.info("Por favor, carregue um arquivo CSV para começar a análise.")
