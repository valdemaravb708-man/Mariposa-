import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback, dash_table, ctx, State
import dash_bootstrap_components as dbc
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# ==================== CARREGAR DADOS ====================
file_path = r'C:\Users\user\Documents\Vaga-lumes\dac\Mariposa.xlsx'

def format_currency(value):
    if abs(value) >= 1_000_000:
        return f'€{value/1_000_000:.2f} Mi'
    elif abs(value) >= 1_000:
        return f'€{value/1_000:.0f}K'
    else:
        return f'€{value:,.0f}'

def format_number(value):
    if abs(value) >= 1_000_000:
        return f'{value/1_000_000:.1f}M'
    elif abs(value) >= 1_000:
        return f'{value/1_000:.0f}K'
    else:
        return f'{value:,.0f}'

def load_and_prepare_data(filepath):
    if os.path.exists(filepath):
        try:
            df = pd.read_excel(filepath, sheet_name='Mariposa', header=0)
            print(f"✅ Arquivo carregado: {len(df)} registros")
        except Exception as e:
            print(f"❌ Erro ao ler Excel: {e}")
            df = create_sample_data()
    else:
        print("⚠️ Arquivo não encontrado, gerando dados de exemplo...")
        df = create_sample_data()

    df['Data_Pedido'] = pd.to_datetime(df['Data_Pedido'], errors='coerce')

    numeric_cols = ['Valor_Frete', 'Distancia_KM', 'Peso_KG', 'Volume_M3',
                    'Custo_Combustivel', 'Pedagio', 'Outras_Despesas']

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['Mes_Ano'] = df['Data_Pedido'].dt.strftime('%b/%Y')
    df['Mes_Ano_Sort'] = df['Data_Pedido'].dt.strftime('%Y-%m')

    if 'Lucro_Liquido' not in df.columns:
        df['Lucro_Liquido'] = df['Valor_Frete'] - (
            df.get('Custo_Combustivel', 0) +
            df.get('Pedagio', 0) +
            df.get('Outras_Despesas', 0)
        )

    return df

def create_sample_data():
    np.random.seed(42)
    n = 300

    datas = pd.date_range('2024-01-01', '2024-12-31', periods=n)
    filiais = ['São Paulo - SP', 'Rio de Janeiro - RJ', 'Belo Horizonte - MG',
               'Salvador - BA', 'Curitiba - PR', 'Porto Alegre - RS',
               'Brasília - DF', 'Recife - PE', 'Fortaleza - CE', 'Manaus - AM']
    clientes = ['Distribuidora Alpha', 'Comércio Beta S.A.', 'Varejo Epsilon',
                'Loja Theta', 'Mercado Central Ltda', 'Indústria Zeta',
                'Empresa Iota', 'Farmácia Eta', 'Atacado Delta', 'Supermercados Gama']
    motoristas = ['João Silva', 'Maria Santos', 'Pedro Oliveira', 'Ana Costa',
                  'Carlos Souza', 'Juliana Lima', 'Paulo Mendes', 'Fernanda Rocha',
                  'Ricardo Nunes', 'Patrícia Gomes']
    veiculos = ['Van', 'Caminhão Toco', 'Caminhão Truck', 'Carreta', 'Utilitário']
    cargas = ['Eletrônicos', 'Móveis', 'Alimentos', 'Medicamentos', 'Vestuário', 'Bebidas']
    status_list = ['Entregue', 'Em Trânsito', 'Aguardando Coleta', 'Atrasado', 'Cancelado', 'Devolvido']
    cidades = ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Salvador', 'Curitiba',
               'Porto Alegre', 'Brasília', 'Recife', 'Fortaleza', 'Manaus']

    dados = []
    for i in range(n):
        distancia = np.random.uniform(100, 2000)
        frete = np.random.uniform(800, 8000)
        custo_comb = np.random.uniform(100, 600)
        pedagio = np.random.uniform(50, 400)
        outras = np.random.uniform(20, 200)

        dados.append({
            'ID_Pedido': f'LOG2025{100000+i:06d}',
            'Data_Pedido': datas[i],
            'Filial_Origem': np.random.choice(filiais),
            'Cliente': np.random.choice(clientes),
            'Motorista': np.random.choice(motoristas),
            'Tipo_Veiculo': np.random.choice(veiculos),
            'Tipo_Carga': np.random.choice(cargas),
            'Peso_KG': np.random.uniform(500, 12000),
            'Volume_M3': np.random.uniform(1, 45),
            'Valor_Frete': frete,
            'Distancia_KM': distancia,
            'Status': np.random.choice(status_list, p=[0.3, 0.2, 0.15, 0.12, 0.1, 0.13]),
            'Cidade_Destino': np.random.choice(cidades),
            'Custo_Combustivel': custo_comb,
            'Pedagio': pedagio,
            'Outras_Despesas': outras,
            'Lucro_Liquido': frete - (custo_comb + pedagio + outras)
        })

    return pd.DataFrame(dados)

# Carregar dados
df = load_and_prepare_data(file_path)

filiais = sorted(df['Filial_Origem'].dropna().unique())
clientes = sorted(df['Cliente'].dropna().unique())
status_list_unique = sorted(df['Status'].dropna().unique())
cliente_filial_map = df.groupby('Cliente')['Filial_Origem'].apply(lambda x: sorted(x.unique())).to_dict()

# ==================== TEMA ====================
THEME = {
    'bg': '#0f172a',
    'card': '#111827',
    'sidebar': '#0a0f1a',
    'sidebar_collapsed': '#0d1117',
    'text': '#f1f5f9',
    'muted': '#94a3b8',
    'primary': '#3b82f6',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#8b5cf6',
    'border': 'rgba(255,255,255,0.06)',
}

# ==================== APP ====================
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])
app.title = "Mariposa Logistics"

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
        <style>
            :root {
                --sidebar-width: 320px;
                --sidebar-collapsed-width: 64px;
                --transition-speed: 0.4s;
            }

            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            }

            body {
                background-color: #0f172a;
                margin: 0;
                overflow-x: hidden;
            }

            .sidebar-container {
                position: fixed;
                top: 0;
                left: 0;
                bottom: 0;
                z-index: 1000;
                transition: all var(--transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
            }

            .sidebar-container.open {
                width: var(--sidebar-width);
            }

            .sidebar-container.closed {
                width: var(--sidebar-collapsed-width);
            }

            .sidebar-content {
                height: 100%;
                overflow-y: auto;
                overflow-x: hidden;
                background: linear-gradient(180deg, #0a0f1a 0%, #0d1117 50%, #0f172a 100%);
                border-right: 1px solid rgba(255,255,255,0.06);
                border-radius: 0 16px 16px 0;  /* cantos direitos arredondados */
                transition: all var(--transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
            }

            /* ===== DatePicker: confinado à sidebar ===== */
            .DateRangePicker_picker {
                position: absolute !important;
                left: 0 !important;
                top: 100% !important;
                transform: none !important;
                z-index: 9999 !important;
                box-shadow: 0 12px 30px rgba(0,0,0,0.5) !important;
                border-radius: 12px !important;
                background-color: #111827 !important;
                border: 1px solid rgba(255,255,255,0.08) !important;
            }
            .DayPicker {
                width: 300px !important;
                min-width: unset !important;
            }
            .DayPicker_transitionContainer {
                width: 300px !important;
            }
            .CalendarMonthGrid {
                width: 300px !important;
            }
            .CalendarMonth {
                padding: 0 8px !important;
                width: 300px !important;
            }
            .CalendarMonth_table {
                font-size: 0.78rem !important;
                width: 100% !important;
            }
            .CalendarDay {
                font-size: 0.78rem !important;
                width: 36px !important;
                height: 36px !important;
            }
            .DayPickerNavigation_button {
                padding: 4px 10px !important;
            }
            .CalendarMonth_caption {
                font-size: 0.82rem !important;
                padding-bottom: 44px !important;
            }

            .sidebar-content::-webkit-scrollbar { width: 3px; }
            .sidebar-content::-webkit-scrollbar-track { background: transparent; }
            .sidebar-content::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

            .sidebar-toggle {
                width: 40px;
                height: 40px;
                border-radius: 10px;
                background-color: #111827;
                border: 1px solid rgba(59,130,246,0.3);
                color: #94a3b8;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                z-index: 1001;
            }

            .sidebar-toggle:hover {
                background-color: #3b82f6;
                color: white;
                border-color: #3b82f6;
                box-shadow: 0 0 20px rgba(59,130,246,0.3);
                transform: scale(1.05);
            }

            /* efeito de clique no botão */
            .sidebar-toggle:active {
                transform: scale(0.95);
                transition: transform 0.1s ease;
            }

            .sidebar-toggle i {
                transition: transform 0.4s ease;
                font-size: 1.2rem;
            }

            .sidebar-separator {
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
                margin: 8px 16px;
            }

            .sidebar-expanded-content {
                display: block;
                opacity: 1;
                transition: opacity 0.3s ease 0.1s;
            }

            .sidebar-expanded-content.hidden {
                display: none;
                opacity: 0;
            }

            .sidebar-logo-text-block {
                display: block;
                transition: opacity 0.3s ease;
            }

            .sidebar-logo-text-block.hidden {
                display: none;
            }

            .main-content {
                transition: all var(--transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
                min-height: 100vh;
                padding: 26px;
            }

            .main-content.expanded {
                margin-left: var(--sidebar-width);
                width: calc(100% - var(--sidebar-width));
            }

            .main-content.collapsed {
                margin-left: var(--sidebar-collapsed-width);
                width: calc(100% - var(--sidebar-collapsed-width));
            }

            .Select-control {
                background-color: #111827 !important;
                border-color: rgba(255,255,255,0.1) !important;
                border-radius: 8px !important;
                transition: all 0.2s ease;
            }
            .Select-control:hover { border-color: rgba(59,130,246,0.3) !important; }

            /* resposta visual ao focar/ativar filtros */
            .Select-control:focus-within,
            .Select-control:active {
                border-color: #3b82f6 !important;
                box-shadow: 0 0 10px rgba(59,130,246,0.3) !important;
            }

            .Select-value-label { color: #f1f5f9 !important; }
            .Select-menu-outer { background-color: #111827 !important; border-color: rgba(255,255,255,0.1) !important; }
            .Select-option { background-color: #111827 !important; color: #94a3b8 !important; }
            .Select-option:hover { background-color: rgba(255,255,255,0.05) !important; }
            .DateInput_input {
                background-color: #111827 !important;
                color: #f1f5f9 !important;
                transition: border-color 0.2s ease, box-shadow 0.2s ease;
            }
            .DateInput_input:focus {
                border-color: #3b82f6 !important;
                box-shadow: 0 0 8px rgba(59,130,246,0.3) !important;
            }
            .DateRangePickerInput {
                background-color: #111827 !important;
                border-color: rgba(255,255,255,0.1) !important;
                border-radius: 8px !important;
            }

            ::-webkit-scrollbar { width: 5px; }
            ::-webkit-scrollbar-track { background: #0f172a; }
            ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
            ::-webkit-scrollbar-thumb:hover { background: #475569; }

            .kpi-card { transition: all 0.3s ease; }
            .kpi-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 12px 30px rgba(0,0,0,0.4) !important;
            }

            @keyframes pulse-glow {
                0%, 100% { box-shadow: 0 0 5px rgba(59,130,246,0.2); }
                50% { box-shadow: 0 0 15px rgba(59,130,246,0.4); }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ==================== COMPONENTES ====================

def create_kpi_card(title, value_id, icon, color, subtitle_id=None):
    return html.Div([
        html.Div([
            html.Div([
                html.I(className=f"bi {icon}", style={'fontSize': '1.2rem', 'color': color, 'opacity': '0.7'}),
            ], style={'marginBottom': '12px'}),
            html.P(title, style={
                'color': THEME['muted'], 'fontSize': '0.72rem', 'fontWeight': '500',
                'marginBottom': '4px', 'letterSpacing': '0.5px', 'textTransform': 'uppercase'
            }),
            html.H3(id=value_id, style={
                'color': THEME['text'], 'fontWeight': '700', 'fontSize': '1.9rem',
                'marginBottom': '4px', 'lineHeight': '1.2'
            }),
            html.P(id=subtitle_id, style={
                'color': THEME['muted'], 'fontSize': '0.68rem', 'fontWeight': '400', 'marginBottom': '0'
            }) if subtitle_id else None
        ], style={'padding': '20px'})
    ], style={
        'backgroundColor': THEME['card'],
        'border': f'1px solid {THEME["border"]}',
        'borderRadius': '14px',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.25)',
        'height': '100%'
    }, className='kpi-card')

def create_chart_card(title, chart_id, height='380px', subtitle=None):
    return html.Div([
        html.Div([
            html.H6(title, style={
                'color': THEME['text'], 'fontWeight': '600', 'fontSize': '0.82rem', 'marginBottom': '2px'
            }),
            html.P(subtitle, style={
                'color': THEME['muted'], 'fontSize': '0.68rem', 'marginBottom': '0'
            }) if subtitle else None
        ], style={'padding': '16px 20px', 'borderBottom': f'1px solid {THEME["border"]}'}),
        html.Div([
            dcc.Loading(
                dcc.Graph(id=chart_id, config={'displayModeBar': False, 'responsive': True}, style={'height': height}),
                type='circle', color=THEME['primary']
            )
        ], style={'padding': '10px'})
    ], style={
        'backgroundColor': THEME['card'],
        'border': f'1px solid {THEME["border"]}',
        'borderRadius': '14px',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.25)',
        'height': '100%'
    })

# ==================== SIDEBAR ====================
sidebar = html.Div([
    html.Div([
        html.Div([
            # ===== TOPO: Logo + Toggle =====
            html.Div([
                html.Div([
                    html.I(className="bi bi-send-fill", style={
                        'fontSize': '1.8rem',
                        'color': THEME['primary'],
                        'filter': 'drop-shadow(0 0 8px rgba(59,130,246,0.5))'
                    }),
                ], style={'textAlign': 'center', 'marginBottom': '5px'}),

                html.Div([
                    html.Span("MARIPOSA", style={
                        'color': THEME['text'], 'fontWeight': '800', 'fontSize': '1.1rem',
                    }),
                    html.Br(),
                    html.Span("LOGISTICS", style={
                        'color': THEME['muted'], 'fontSize': '0.6rem', 'letterSpacing': '3px'
                    })
                ], id='sidebar-logo-text', style={'textAlign': 'center'}),

                html.Button(
                    html.I(className="bi bi-list", id='toggle-icon'),
                    id='sidebar-toggle-btn',
                    className='sidebar-toggle',
                    n_clicks=0,
                    style={'margin': '8px auto 0', 'display': 'block'}
                )
            ], style={'padding': '16px 12px', 'borderBottom': '1px solid rgba(255,255,255,0.04)'}),

            # ===== FILTROS =====
            html.Div([
                html.Div(className='sidebar-separator'),

                # Período (com apenas um mês visível para caber na sidebar)
                html.Div([
                    html.Label([
                        html.I(className="bi bi-calendar3", style={'color': THEME['primary'], 'marginRight': '6px', 'fontSize': '0.8rem'}),
                        "Período"
                    ], style={
                        'color': THEME['text'], 'fontSize': '0.72rem', 'fontWeight': '600', 'marginBottom': '8px',
                        'display': 'flex', 'alignItems': 'center'
                    }),
                    dcc.DatePickerRange(
                        id='date-filter',
                        start_date=df['Data_Pedido'].min(),
                        end_date=df['Data_Pedido'].max(),
                        display_format='DD/MM/YYYY',
                        number_of_months_shown=1,   # ← ALTERAÇÃO: apenas um mês
                        className="mb-3"
                    )
                ], style={'padding': '0 4px'}),

                # Filial
                html.Div([
                    html.Label([
                        html.I(className="bi bi-building", style={'color': THEME['primary'], 'marginRight': '6px', 'fontSize': '0.8rem'}),
                        "Filial"
                    ], style={
                        'color': THEME['text'], 'fontSize': '0.72rem', 'fontWeight': '600', 'marginBottom': '8px',
                        'display': 'flex', 'alignItems': 'center'
                    }),
                    dcc.Dropdown(
                        id='filial-filter',
                        options=[{'label': f, 'value': f} for f in filiais],
                        multi=True,
                        placeholder="Todas...",
                        className="mb-3",
                        style={'color': '#111'}
                    )
                ], style={'padding': '0 4px'}),

                # Cliente
                html.Div([
                    html.Label([
                        html.I(className="bi bi-people", style={'color': THEME['primary'], 'marginRight': '6px', 'fontSize': '0.8rem'}),
                        "Cliente"
                    ], style={
                        'color': THEME['text'], 'fontSize': '0.72rem', 'fontWeight': '600', 'marginBottom': '8px',
                        'display': 'flex', 'alignItems': 'center'
                    }),
                    dcc.Dropdown(
                        id='cliente-filter',
                        options=[{'label': c, 'value': c} for c in clientes],
                        multi=True,
                        placeholder="Todos...",
                        className="mb-3",
                        style={'color': '#111'}
                    )
                ], style={'padding': '0 4px'}),

                # Status
                html.Div([
                    html.Label([
                        html.I(className="bi bi-bar-chart-line", style={'color': THEME['primary'], 'marginRight': '6px', 'fontSize': '0.8rem'}),
                        "Status"
                    ], style={
                        'color': THEME['text'], 'fontSize': '0.72rem', 'fontWeight': '600', 'marginBottom': '8px',
                        'display': 'flex', 'alignItems': 'center'
                    }),
                    dcc.Dropdown(
                        id='status-filter',
                        options=[{'label': s, 'value': s} for s in status_list_unique],
                        multi=True,
                        placeholder="Todos...",
                        className="mb-3",
                        style={'color': '#111'}
                    )
                ], style={'padding': '0 4px'}),

                html.Div(className='sidebar-separator', style={'marginTop': '8px'}),

                html.Button(
                    [html.I(className="bi bi-arrow-counterclockwise", style={'marginRight': '6px'}), "Limpar Filtros"],
                    id='clear-filters-btn',
                    n_clicks=0,
                    style={
                        'width': '100%', 'padding': '8px 12px', 'marginTop': '8px',
                        'backgroundColor': 'rgba(239,68,68,0.15)', 'color': '#ef4444',
                        'border': '1px solid rgba(239,68,68,0.3)', 'borderRadius': '8px',
                        'cursor': 'pointer', 'fontSize': '0.72rem', 'fontWeight': '600',
                        'transition': 'all 0.2s ease'
                    }
                ),
            ], id='sidebar-filters', style={'padding': '12px 8px'}),

        ], className='sidebar-content'),
    ], id='sidebar-container', className='sidebar-container open'),
], style={'position': 'relative'})

# ==================== LAYOUT PRINCIPAL ====================
app.layout = html.Div([
    dcc.Store(id='sidebar-state', data={'open': True}),
    sidebar,
    html.Div([
        # Header
        html.Div([
            html.Div([
                html.H4("Dashboard de Logística", style={
                    'color': THEME['text'], 'fontWeight': '700', 'marginBottom': '2px', 'fontSize': '1.3rem'
                }),
                html.P("Mariposa Logistics · Visão Geral Operacional", style={
                    'color': THEME['muted'], 'fontSize': '0.75rem', 'marginBottom': '0'
                })
            ]),
            html.Div(id='last-update', style={
                'color': THEME['muted'], 'fontSize': '0.7rem',
                'backgroundColor': THEME['card'],
                'padding': '6px 14px', 'borderRadius': '8px',
                'border': f'1px solid {THEME["border"]}'
            })
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '24px'}),

        # KPI Cards
        dbc.Row([
            dbc.Col(create_kpi_card("Total Fretes", "kpi-total-fretes", "bi-truck", THEME['primary'], "kpi-sub-fretes"), md=3),
            dbc.Col(create_kpi_card("Receita Total", "kpi-receita", "bi-currency-euro", THEME['success'], "kpi-sub-receita"), md=3),
            dbc.Col(create_kpi_card("Lucro Líquido", "kpi-lucro", "bi-graph-up-arrow", THEME['info'], "kpi-sub-lucro"), md=3),
            dbc.Col(create_kpi_card("Dist. Média KM", "kpi-distancia", "bi-geo-alt", THEME['warning'], "kpi-sub-distancia"), md=3),
        ], className="mb-4 g-3"),

        # Gráficos linha 1
        dbc.Row([
            dbc.Col(create_chart_card("Receita por Período", "chart-receita-periodo", subtitle="Evolução mensal"), md=8),
            dbc.Col(create_chart_card("Status das Entregas", "chart-status", subtitle="Distribuição atual"), md=4),
        ], className="mb-4 g-3"),

        # Gráficos linha 2
        dbc.Row([
            dbc.Col(create_chart_card("Top Clientes por Receita", "chart-top-clientes", subtitle="Ranking por valor"), md=6),
            dbc.Col(create_chart_card("Receita por Filial", "chart-filial", subtitle="Performance por unidade"), md=6),
        ], className="mb-4 g-3"),

        # Gráficos linha 3
        dbc.Row([
            dbc.Col(create_chart_card("Tipo de Veículo", "chart-veiculo", subtitle="Distribuição da frota"), md=4),
            dbc.Col(create_chart_card("Tipo de Carga", "chart-carga", subtitle="Composição por categoria"), md=4),
            dbc.Col(create_chart_card("Lucro por Motorista", "chart-motorista", subtitle="Top 10 motoristas"), md=4),
        ], className="mb-4 g-3"),

        # Tabela
        html.Div([
            html.Div([
                html.H6("Detalhamento dos Pedidos", style={
                    'color': THEME['text'], 'fontWeight': '600', 'fontSize': '0.82rem', 'marginBottom': '0'
                }),
            ], style={'padding': '16px 20px', 'borderBottom': f'1px solid {THEME["border"]}'}),
            html.Div([
                dcc.Loading(
                    html.Div(id='tabela-pedidos'),
                    type='circle', color=THEME['primary']
                )
            ], style={'padding': '12px'})
        ], style={
            'backgroundColor': THEME['card'],
            'border': f'1px solid {THEME["border"]}',
            'borderRadius': '14px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.25)',
            'marginBottom': '24px'
        }),

    ], id='main-content', className='main-content expanded',
       style={'backgroundColor': THEME['bg']}),

], style={'backgroundColor': THEME['bg']})


# ==================== CALLBACKS ====================

@app.callback(
    Output('sidebar-state', 'data'),
    Input('sidebar-toggle-btn', 'n_clicks'),
    State('sidebar-state', 'data'),
    prevent_initial_call=True
)
def toggle_sidebar_state(n_clicks, state):
    if n_clicks:
        return {'open': not state['open']}
    return state


@app.callback(
    Output('sidebar-container', 'className'),
    Output('main-content', 'className'),
    Output('sidebar-filters', 'style'),
    Output('sidebar-logo-text', 'style'),
    Input('sidebar-state', 'data')
)
def update_sidebar_ui(state):
    if state['open']:
        sidebar_class = 'sidebar-container open'
        main_class = 'main-content expanded'
        filters_style = {'padding': '12px 8px', 'display': 'block'}
        logo_text_style = {'textAlign': 'center', 'display': 'block'}
    else:
        sidebar_class = 'sidebar-container closed'
        main_class = 'main-content collapsed'
        filters_style = {'display': 'none'}
        logo_text_style = {'display': 'none'}
    return sidebar_class, main_class, filters_style, logo_text_style


@app.callback(
    Output('filial-filter', 'value'),
    Output('cliente-filter', 'value'),
    Output('status-filter', 'value'),
    Input('clear-filters-btn', 'n_clicks'),
    prevent_initial_call=True
)
def clear_filters(n):
    return None, None, None


@app.callback(
    Output('cliente-filter', 'options'),
    Input('filial-filter', 'value')
)
def update_cliente_options(filiais_sel):
    if not filiais_sel:
        clientes_disp = sorted(df['Cliente'].dropna().unique())
    else:
        clientes_disp = sorted(
            df[df['Filial_Origem'].isin(filiais_sel)]['Cliente'].dropna().unique()
        )
    return [{'label': c, 'value': c} for c in clientes_disp]


@app.callback(
    Output('kpi-total-fretes', 'children'),
    Output('kpi-sub-fretes', 'children'),
    Output('kpi-receita', 'children'),
    Output('kpi-sub-receita', 'children'),
    Output('kpi-lucro', 'children'),
    Output('kpi-sub-lucro', 'children'),
    Output('kpi-distancia', 'children'),
    Output('kpi-sub-distancia', 'children'),
    Output('chart-receita-periodo', 'figure'),
    Output('chart-status', 'figure'),
    Output('chart-top-clientes', 'figure'),
    Output('chart-filial', 'figure'),
    Output('chart-veiculo', 'figure'),
    Output('chart-carga', 'figure'),
    Output('chart-motorista', 'figure'),
    Output('tabela-pedidos', 'children'),
    Output('last-update', 'children'),
    Input('date-filter', 'start_date'),
    Input('date-filter', 'end_date'),
    Input('filial-filter', 'value'),
    Input('cliente-filter', 'value'),
    Input('status-filter', 'value'),
)
def update_dashboard(start_date, end_date, filiais_sel, clientes_sel, status_sel):
    dff = df.copy()

    if start_date:
        dff = dff[dff['Data_Pedido'] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff['Data_Pedido'] <= pd.to_datetime(end_date)]

    if filiais_sel:
        dff = dff[dff['Filial_Origem'].isin(filiais_sel)]

    if clientes_sel:
        dff = dff[dff['Cliente'].isin(clientes_sel)]

    if status_sel:
        dff = dff[dff['Status'].isin(status_sel)]

    if dff.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color=THEME['muted'],
            annotations=[{'text': 'Sem dados para os filtros selecionados',
                          'x': 0.5, 'y': 0.5, 'xref': 'paper', 'yref': 'paper',
                          'showarrow': False, 'font': {'color': THEME['muted']}}]
        )
        return (
            "0", "registros", "€0", "-", "€0", "-", "0 km", "-",
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
            html.P("Sem dados.", style={'color': THEME['muted'], 'padding': '12px'}),
            f"Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )

    # ===== KPIs =====
    total_fretes = len(dff)
    receita_total = dff['Valor_Frete'].sum()
    lucro_total = dff['Lucro_Liquido'].sum()
    dist_media = dff['Distancia_KM'].mean()

    entregues = len(dff[dff['Status'] == 'Entregue'])
    pct_entregue = (entregues / total_fretes * 100) if total_fretes > 0 else 0
    margem = (lucro_total / receita_total * 100) if receita_total > 0 else 0

    kpi_fretes = format_number(total_fretes)
    kpi_sub_fretes = f"{entregues} entregues ({pct_entregue:.0f}%)"
    kpi_receita = format_currency(receita_total)
    kpi_sub_receita = f"Frete médio: {format_currency(receita_total/total_fretes)}"
    kpi_lucro = format_currency(lucro_total)
    kpi_sub_lucro = f"Margem: {margem:.1f}%"
    kpi_distancia = f"{dist_media:,.0f} km"
    kpi_sub_distancia = f"Total: {format_number(dff['Distancia_KM'].sum())} km"

    layout_base = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=THEME['muted'], family='Inter', size=11),
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
        xaxis=dict(gridcolor='rgba(255,255,255,0.04)', zerolinecolor='rgba(255,255,255,0.04)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.04)', zerolinecolor='rgba(255,255,255,0.04)'),
        hovermode='closest'  # destaque suave ao passar o mouse
    )

    # ===== Receita por período (gráfico de linha suavizada) =====
    df_mes = dff.groupby('Mes_Ano_Sort').agg(
        Receita=('Valor_Frete', 'sum'),
        Mes_Ano=('Mes_Ano', 'first')
    ).reset_index().sort_values('Mes_Ano_Sort')

    fig_periodo = go.Figure()
    fig_periodo.add_trace(go.Scatter(
        x=df_mes['Mes_Ano'], y=df_mes['Receita'],
        mode='lines+markers',
        line=dict(color=THEME['primary'], width=2.5, shape='spline', smoothing=1.3),
        marker=dict(size=6, color=THEME['primary']),
        fill='tozeroy',
        fillcolor='rgba(59,130,246,0.08)',
        hovertemplate='%{x}<br>Receita: €%{y:,.0f}<extra></extra>',
        hoverlabel=dict(
            bgcolor=THEME['primary'],
            font=dict(color='white', size=12, family='Inter')
        )
    ))
    fig_periodo.update_layout(**layout_base)
    fig_periodo.update_xaxes(tickfont_size=10)

    # ===== Status =====
    df_status = dff['Status'].value_counts().reset_index()
    df_status.columns = ['Status', 'Count']
    status_colors = {
        'Entregue': THEME['success'], 'Em Trânsito': THEME['primary'],
        'Aguardando Coleta': THEME['warning'], 'Atrasado': THEME['danger'],
        'Cancelado': '#64748b', 'Devolvido': THEME['info']
    }
    colors_list = [status_colors.get(s, THEME['muted']) for s in df_status['Status']]

    fig_status = go.Figure(go.Pie(
        labels=df_status['Status'], values=df_status['Count'],
        hole=0.55,
        marker=dict(colors=colors_list, line=dict(color='rgba(0,0,0,0)', width=0)),
        textfont=dict(size=10),
        hovertemplate='%{label}<br>%{value} pedidos (%{percent})<extra></extra>'
    ))
    fig_status.update_layout(**{**layout_base, 'showlegend': True,
        'legend': dict(font=dict(size=9, color=THEME['muted']), bgcolor='rgba(0,0,0,0)')})

    # ===== Top Clientes =====
    df_cli = dff.groupby('Cliente')['Valor_Frete'].sum().nlargest(10).reset_index()
    df_cli = df_cli.sort_values('Valor_Frete')

    fig_clientes = go.Figure(go.Bar(
        x=df_cli['Valor_Frete'], y=df_cli['Cliente'],
        orientation='h',
        marker=dict(
            color=df_cli['Valor_Frete'],
            colorscale=[[0, 'rgba(59,130,246,0.3)'], [1, THEME['primary']]],
            line=dict(width=0)
        ),
        hovertemplate='%{y}<br>€%{x:,.0f}<extra></extra>'
    ))
    fig_clientes.update_layout(**layout_base)
    fig_clientes.update_xaxes(tickfont_size=9)
    fig_clientes.update_yaxes(tickfont_size=9)

    # ===== Receita por Filial =====
    df_fil = dff.groupby('Filial_Origem')['Valor_Frete'].sum().reset_index().sort_values('Valor_Frete', ascending=False)

    fig_filial = go.Figure(go.Bar(
        x=df_fil['Filial_Origem'], y=df_fil['Valor_Frete'],
        marker=dict(
            color=df_fil['Valor_Frete'],
            colorscale=[[0, 'rgba(16,185,129,0.3)'], [1, THEME['success']]],
            line=dict(width=0)
        ),
        hovertemplate='%{x}<br>€%{y:,.0f}<extra></extra>'
    ))
    fig_filial.update_layout(**layout_base)
    fig_filial.update_xaxes(tickfont_size=8, tickangle=-30)

    # ===== Tipo de Veículo =====
    df_veic = dff['Tipo_Veiculo'].value_counts().reset_index()
    df_veic.columns = ['Veiculo', 'Count']

    fig_veiculo = go.Figure(go.Pie(
        labels=df_veic['Veiculo'], values=df_veic['Count'],
        hole=0.5,
        marker=dict(colors=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
                    line=dict(color='rgba(0,0,0,0)', width=0)),
        textfont=dict(size=9),
        hovertemplate='%{label}<br>%{value} (%{percent})<extra></extra>'
    ))
    fig_veiculo.update_layout(**{**layout_base, 'showlegend': True,
        'legend': dict(font=dict(size=9, color=THEME['muted']), bgcolor='rgba(0,0,0,0)')})

    # ===== Tipo de Carga =====
    df_carga = dff['Tipo_Carga'].value_counts().reset_index()
    df_carga.columns = ['Carga', 'Count']

    fig_carga = go.Figure(go.Bar(
        x=df_carga['Carga'], y=df_carga['Count'],
        marker=dict(color=THEME['info'], opacity=0.85, line=dict(width=0)),
        hovertemplate='%{x}<br>%{y} pedidos<extra></extra>'
    ))
    fig_carga.update_layout(**layout_base)
    fig_carga.update_xaxes(tickfont_size=9, tickangle=-20)

    # ===== Lucro por Motorista =====
    df_mot = dff.groupby('Motorista')['Lucro_Liquido'].sum().nlargest(10).reset_index().sort_values('Lucro_Liquido')

    fig_motorista = go.Figure(go.Bar(
        x=df_mot['Lucro_Liquido'], y=df_mot['Motorista'],
        orientation='h',
        marker=dict(
            color=df_mot['Lucro_Liquido'],
            colorscale=[[0, 'rgba(245,158,11,0.3)'], [1, THEME['warning']]],
            line=dict(width=0)
        ),
        hovertemplate='%{y}<br>€%{x:,.0f}<extra></extra>'
    ))
    fig_motorista.update_layout(**layout_base)
    fig_motorista.update_xaxes(tickfont_size=9)
    fig_motorista.update_yaxes(tickfont_size=9)

    # ===== Tabela =====
    cols_tabela = ['ID_Pedido', 'Data_Pedido', 'Filial_Origem', 'Cliente',
                   'Status', 'Valor_Frete', 'Distancia_KM', 'Motorista']
    cols_disp = [c for c in cols_tabela if c in dff.columns]
    df_tab = dff[cols_disp].head(100).copy()
    if 'Data_Pedido' in df_tab.columns:
        df_tab['Data_Pedido'] = df_tab['Data_Pedido'].dt.strftime('%d/%m/%Y')
    if 'Valor_Frete' in df_tab.columns:
        df_tab['Valor_Frete'] = df_tab['Valor_Frete'].apply(lambda x: f'€{x:,.0f}')
    if 'Distancia_KM' in df_tab.columns:
        df_tab['Distancia_KM'] = df_tab['Distancia_KM'].apply(lambda x: f'{x:,.0f} km')

    tabela = dash_table.DataTable(
        data=df_tab.to_dict('records'),
        columns=[{'name': c.replace('_', ' '), 'id': c} for c in df_tab.columns],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={
            'backgroundColor': THEME['card'], 'color': THEME['muted'],
            'border': f'1px solid {THEME["border"]}', 'padding': '10px 14px',
            'fontSize': '0.75rem', 'fontFamily': 'Inter',
            'textAlign': 'left', 'whiteSpace': 'normal'
        },
        style_header={
            'backgroundColor': '#1e293b', 'color': THEME['text'],
            'fontWeight': '600', 'fontSize': '0.72rem',
            'border': f'1px solid {THEME["border"]}',
            'textTransform': 'uppercase', 'letterSpacing': '0.5px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgba(255,255,255,0.02)'},
            {'if': {'filter_query': '{Status} = "Entregue"', 'column_id': 'Status'},
             'color': THEME['success'], 'fontWeight': '600'},
            {'if': {'filter_query': '{Status} = "Atrasado"', 'column_id': 'Status'},
             'color': THEME['danger'], 'fontWeight': '600'},
            {'if': {'filter_query': '{Status} = "Em Trânsito"', 'column_id': 'Status'},
             'color': THEME['primary'], 'fontWeight': '600'},
            {'if': {'filter_query': '{Status} = "Cancelado"', 'column_id': 'Status'},
             'color': '#64748b', 'fontWeight': '600'},
        ]
    )

    last_update = f"Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')} · {total_fretes} registros"

    return (
        kpi_fretes, kpi_sub_fretes,
        kpi_receita, kpi_sub_receita,
        kpi_lucro, kpi_sub_lucro,
        kpi_distancia, kpi_sub_distancia,
        fig_periodo, fig_status, fig_clientes, fig_filial,
        fig_veiculo, fig_carga, fig_motorista,
        tabela, last_update
    )


if __name__ == '__main__':
    app.run(debug=True, port=8050)