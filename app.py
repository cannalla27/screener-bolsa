"""
Screener de bolsa por índices (estilo TradingView / Investing.com)
Datos: escáner de TradingView (scanner.tradingview.com) — el mismo que alimenta su screener.
Despliegue: GitHub + Streamlit Community Cloud.
"""
import json
import re
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Screener por índices", page_icon="📈", layout="wide")

# ══════════════════════════════════════════════════════════════════════════════
# 1. UNIVERSOS
# ══════════════════════════════════════════════════════════════════════════════
# Código = "SYML:" + símbolo del índice en TradingView con ";" en vez de ":".
# Si hay varios candidatos se prueban en orden hasta que uno devuelve valores.
INDICES = {
    "🇺🇸 S&P 500": ["SYML:SP;SPX"],
    "🇺🇸 Nasdaq 100": ["SYML:NASDAQ;NDX"],
    "🇺🇸 Dow Jones 30": ["SYML:DJ;DJI"],
    "🇺🇸 S&P 100": ["SYML:SP;OEX", "SYML:CBOE;OEX"],
    "🇺🇸 S&P MidCap 400": ["SYML:SP;MID"],
    "🇺🇸 S&P SmallCap 600": ["SYML:SP;SML"],
    "🇺🇸 Russell 1000": ["SYML:TVC;RUI", "SYML:CBOEFTSE;RUI", "SYML:RUSSELL;RUI"],
    "🇺🇸 Russell 2000": ["SYML:TVC;RUT", "SYML:CBOEFTSE;RUT", "SYML:RUSSELL;RUT"],
    "🇺🇸 Nasdaq Composite": ["SYML:NASDAQ;IXIC"],
    "🇪🇸 IBEX 35": ["SYML:BME;IBC"],
    "🇩🇪 DAX 40": ["SYML:XETR;DAX"],
    "🇩🇪 MDAX": ["SYML:XETR;MDAX"],
    "🇩🇪 TecDAX": ["SYML:XETR;TECDAX", "SYML:XETR;TDXP"],
    "🇫🇷 CAC 40": ["SYML:EURONEXT;PX1"],
    "🇬🇧 FTSE 100": ["SYML:FTSE;UKX", "SYML:TVC;UKX"],
    "🇬🇧 FTSE 250": ["SYML:FTSE;MCX"],
    "🇪🇺 Euro Stoxx 50": ["SYML:TVC;SX5E", "SYML:STOXX;SX5E", "SYML:EUREX;SX5E"],
    "🇪🇺 STOXX Europe 600": ["SYML:TVC;SXXP", "SYML:STOXX;SXXP"],
    "🇮🇹 FTSE MIB": ["SYML:MIL;FTSEMIB", "SYML:TVC;FTMIB"],
    "🇳🇱 AEX": ["SYML:EURONEXT;AEX"],
    "🇧🇪 BEL 20": ["SYML:EURONEXT;BEL20"],
    "🇵🇹 PSI": ["SYML:EURONEXT;PSI20", "SYML:EURONEXT;PSI"],
    "🇨🇭 SMI": ["SYML:SIX;SMI"],
    "🇸🇪 OMX Stockholm 30": ["SYML:OMXSTO;OMXS30"],
    "🇩🇰 OMX Copenhagen 25": ["SYML:OMXCOP;OMXC25"],
    "🇫🇮 OMX Helsinki 25": ["SYML:OMXHEX;OMXH25"],
    "🇳🇴 OBX": ["SYML:OSL;OBX"],
    "🇵🇱 WIG20": ["SYML:GPW;WIG20"],
    "🇯🇵 Nikkei 225": ["SYML:TVC;NI225", "SYML:TSE;NI225"],
    "🇭🇰 Hang Seng": ["SYML:HSI;HSI"],
    "🇨🇳 CSI 300": ["SYML:SSE;000300", "SYML:SZSE;399300"],
    "🇮🇳 Nifty 50": ["SYML:NSE;NIFTY"],
    "🇮🇳 Sensex": ["SYML:BSE;SENSEX"],
    "🇰🇷 KOSPI 200": ["SYML:KRX;KOSPI200", "SYML:KRX;KOSPI"],
    "🇦🇺 S&P/ASX 200": ["SYML:ASX;XJO"],
    "🇨🇦 S&P/TSX Composite": ["SYML:TSX;TSX"],
    "🇨🇦 S&P/TSX 60": ["SYML:TSX;TX60"],
    "🇧🇷 Ibovespa": ["SYML:BMFBOVESPA;IBOV"],
    "🇲🇽 S&P/BMV IPC": ["SYML:BMV;ME"],
}

MERCADOS = {
    "🇺🇸 Estados Unidos": "america", "🇪🇸 España": "spain", "🇩🇪 Alemania": "germany",
    "🇫🇷 Francia": "france", "🇬🇧 Reino Unido": "uk", "🇮🇹 Italia": "italy",
    "🇳🇱 Países Bajos": "netherlands", "🇨🇭 Suiza": "switzerland", "🇵🇹 Portugal": "portugal",
    "🇧🇪 Bélgica": "belgium", "🇸🇪 Suecia": "sweden", "🇯🇵 Japón": "japan",
    "🇭🇰 Hong Kong": "hongkong", "🇨🇳 China": "china", "🇮🇳 India": "india",
    "🇰🇷 Corea del Sur": "korea", "🇦🇺 Australia": "australia", "🇨🇦 Canadá": "canada",
    "🇧🇷 Brasil": "brazil", "🇲🇽 México": "mexico", "🇦🇷 Argentina": "argentina",
    "🇨🇱 Chile": "chile", "🇨🇴 Colombia": "colombia",
}

SECTORES = {
    "Commercial Services": "Servicios comerciales", "Communications": "Comunicaciones",
    "Consumer Durables": "Consumo duradero", "Consumer Non-Durables": "Consumo no duradero",
    "Consumer Services": "Servicios al consumidor", "Distribution Services": "Distribución",
    "Electronic Technology": "Tecnología electrónica", "Energy Minerals": "Energía",
    "Finance": "Finanzas", "Health Services": "Servicios de salud",
    "Health Technology": "Tecnología sanitaria", "Industrial Services": "Servicios industriales",
    "Miscellaneous": "Varios", "Non-Energy Minerals": "Minerales no energéticos",
    "Process Industries": "Industrias de proceso", "Producer Manufacturing": "Manufactura",
    "Retail Trade": "Comercio minorista", "Technology Services": "Servicios tecnológicos",
    "Transportation": "Transporte", "Utilities": "Suministros públicos",
}

TIMEFRAMES = {"1 día": "", "1 min": "1", "5 min": "5", "15 min": "15", "30 min": "30",
              "1 hora": "60", "2 horas": "120", "4 horas": "240", "1 semana": "1W", "1 mes": "1M"}

# ══════════════════════════════════════════════════════════════════════════════
# 2. CAMPOS  — campo: (etiqueta, tipo)   tipo: price | pct | big | num | text
# ══════════════════════════════════════════════════════════════════════════════
CAMPOS = {
    # identidad
    "name": ("Ticker", "text"), "description": ("Nombre", "text"), "logoid": ("", "text"),
    "exchange": ("Bolsa", "text"), "country": ("País", "text"), "currency": ("Divisa", "text"),
    "sector": ("Sector", "text"), "industry": ("Industria", "text"), "update_mode": ("Modo", "text"),
    # precio / volumen
    "close": ("Precio", "price"), "open": ("Apertura", "price"), "high": ("Máx.", "price"),
    "low": ("Mín.", "price"), "change": ("Var. %", "pct"), "change_abs": ("Var.", "price"),
    "gap": ("Gap %", "pct"), "volume": ("Volumen", "big"), "Value.Traded": ("Efectivo neg.", "big"),
    "relative_volume_10d_calc": ("Vol. relativo", "num"),
    "average_volume_10d_calc": ("Vol. medio 10d", "big"),
    "average_volume_30d_calc": ("Vol. medio 30d", "big"),
    "market_cap_basic": ("Capitalización", "big"),
    "float_shares_outstanding": ("Free float (acc.)", "big"),
    # pre / post mercado
    "premarket_close": ("Pre: precio", "price"), "premarket_change": ("Pre: var. %", "pct"),
    "premarket_volume": ("Pre: volumen", "big"), "postmarket_close": ("Post: precio", "price"),
    "postmarket_change": ("Post: var. %", "pct"), "postmarket_volume": ("Post: volumen", "big"),
    # rendimiento
    "Perf.W": ("1 sem %", "pct"), "Perf.1M": ("1 mes %", "pct"), "Perf.3M": ("3 meses %", "pct"),
    "Perf.6M": ("6 meses %", "pct"), "Perf.YTD": ("YTD %", "pct"), "Perf.Y": ("1 año %", "pct"),
    "Perf.5Y": ("5 años %", "pct"), "Perf.All": ("Histórico %", "pct"),
    "Volatility.D": ("Volat. día %", "num"), "Volatility.W": ("Volat. sem %", "num"),
    "Volatility.M": ("Volat. mes %", "num"), "beta_1_year": ("Beta 1a", "num"),
    "price_52_week_high": ("Máx. 52s", "price"), "price_52_week_low": ("Mín. 52s", "price"),
    "High.All": ("Máx. histórico", "price"), "Low.All": ("Mín. histórico", "price"),
    # valoración
    "price_earnings_ttm": ("PER", "num"), "price_earnings_growth_ttm": ("PEG", "num"),
    "price_book_fq": ("P/VC", "num"), "price_sales_current": ("P/Ventas", "num"),
    "price_free_cash_flow_ttm": ("P/FCF", "num"), "enterprise_value_ebitda_ttm": ("EV/EBITDA", "num"),
    "enterprise_value_fq": ("Valor empresa", "big"),
    "earnings_per_share_diluted_ttm": ("BPA (TTM)", "num"),
    "earnings_per_share_diluted_yoy_growth_ttm": ("BPA crec. % a/a", "pct"),
    # dividendos
    "dividends_yield_current": ("Rent. div. %", "num"),
    "dividend_payout_ratio_ttm": ("Payout %", "num"),
    "dps_common_stock_prim_issue_fy": ("Div./acción", "num"),
    # rentabilidad
    "gross_margin_ttm": ("Margen bruto %", "num"), "operating_margin_ttm": ("Margen oper. %", "num"),
    "net_margin_ttm": ("Margen neto %", "num"), "return_on_equity_fq": ("ROE %", "num"),
    "return_on_assets_fq": ("ROA %", "num"), "return_on_invested_capital_fq": ("ROIC %", "num"),
    # cuenta de resultados
    "total_revenue_ttm": ("Ingresos", "big"), "total_revenue_yoy_growth_ttm": ("Ingresos crec. % a/a", "pct"),
    "gross_profit_ttm": ("Beneficio bruto", "big"), "oper_income_ttm": ("Rdo. operativo", "big"),
    "net_income_ttm": ("Beneficio neto", "big"), "ebitda_ttm": ("EBITDA", "big"),
    "free_cash_flow_ttm": ("Flujo caja libre", "big"),
    # balance
    "total_assets_fq": ("Activos", "big"), "total_debt_fq": ("Deuda total", "big"),
    "net_debt_fq": ("Deuda neta", "big"), "cash_n_short_term_invest_fq": ("Caja e inv. c/p", "big"),
    "debt_to_equity_fq": ("Deuda/Patrimonio", "num"), "current_ratio_fq": ("Ratio corriente", "num"),
    "quick_ratio_fq": ("Prueba ácida", "num"), "number_of_employees": ("Empleados", "big"),
    # técnicos (admiten temporalidad)
    "Recommend.All": ("Rating técnico", "num"), "Recommend.MA": ("Rating medias", "num"),
    "Recommend.Other": ("Rating osciladores", "num"), "RSI": ("RSI 14", "num"),
    "MACD.macd": ("MACD", "num"), "MACD.signal": ("MACD señal", "num"),
    "SMA20": ("SMA 20", "price"), "SMA50": ("SMA 50", "price"), "SMA200": ("SMA 200", "price"),
    "EMA20": ("EMA 20", "price"), "EMA50": ("EMA 50", "price"), "EMA200": ("EMA 200", "price"),
    "ADX": ("ADX", "num"), "Stoch.K": ("Estoc. %K", "num"), "Stoch.D": ("Estoc. %D", "num"),
    "CCI20": ("CCI 20", "num"), "ATR": ("ATR 14", "num"), "Mom": ("Momentum", "num"),
    "W.R": ("Williams %R", "num"), "BB.upper": ("Bollinger sup.", "price"),
    "BB.lower": ("Bollinger inf.", "price"),
    # analistas / eventos
    "recommendation_mark": ("Nota analistas", "num"), "price_target_average": ("Precio objetivo", "price"),
    "earnings_release_next_date": ("Próx. resultados", "text"),
    # derivados (se calculan aquí)
    "rating_tec": ("Señal técnica", "text"), "rating_ana": ("Consenso analistas", "text"),
    "potencial": ("Potencial %", "pct"), "dist_max52": ("Dist. máx 52s %", "pct"),
    "dist_min52": ("Dist. mín 52s %", "pct"), "vs_sma200": ("vs SMA200 %", "pct"),
    "retraso": ("Datos", "text"),
}
DERIVADOS = {"rating_tec", "rating_ana", "potencial", "dist_max52", "dist_min52", "vs_sma200", "retraso"}
TECNICOS = {"Recommend.All", "Recommend.MA", "Recommend.Other", "RSI", "MACD.macd", "MACD.signal",
            "SMA20", "SMA50", "SMA200", "EMA20", "EMA50", "EMA200", "ADX", "Stoch.K", "Stoch.D",
            "CCI20", "ATR", "Mom", "W.R", "BB.upper", "BB.lower"}
CAMPOS_API = [c for c in CAMPOS if c not in DERIVADOS]

BASE = ["logoid", "name", "description"]
VISTAS = {
    "Resumen": ["close", "change", "change_abs", "volume", "relative_volume_10d_calc", "market_cap_basic",
                "price_earnings_ttm", "dividends_yield_current", "sector", "rating_tec", "rating_ana", "retraso"],
    "Rendimiento": ["close", "change", "Perf.W", "Perf.1M", "Perf.3M", "Perf.6M", "Perf.YTD", "Perf.Y",
                    "Perf.5Y", "Perf.All", "dist_max52", "dist_min52", "Volatility.M", "beta_1_year"],
    "Valoración": ["close", "market_cap_basic", "enterprise_value_fq", "price_earnings_ttm",
                   "price_earnings_growth_ttm", "price_book_fq", "price_sales_current",
                   "price_free_cash_flow_ttm", "enterprise_value_ebitda_ttm",
                   "earnings_per_share_diluted_ttm", "earnings_per_share_diluted_yoy_growth_ttm"],
    "Dividendos": ["close", "dividends_yield_current", "dps_common_stock_prim_issue_fy",
                   "dividend_payout_ratio_ttm", "free_cash_flow_ttm", "market_cap_basic"],
    "Rentabilidad": ["gross_margin_ttm", "operating_margin_ttm", "net_margin_ttm", "return_on_equity_fq",
                     "return_on_assets_fq", "return_on_invested_capital_fq"],
    "Resultados": ["total_revenue_ttm", "total_revenue_yoy_growth_ttm", "gross_profit_ttm", "oper_income_ttm",
                   "ebitda_ttm", "net_income_ttm", "free_cash_flow_ttm", "earnings_release_next_date"],
    "Balance": ["total_assets_fq", "cash_n_short_term_invest_fq", "total_debt_fq", "net_debt_fq",
                "debt_to_equity_fq", "current_ratio_fq", "quick_ratio_fq", "number_of_employees"],
    "Técnicos": ["close", "change", "rating_tec", "Recommend.MA", "Recommend.Other", "RSI", "MACD.macd",
                 "MACD.signal", "ADX", "Stoch.K", "Stoch.D", "CCI20", "W.R", "Mom", "ATR", "SMA20", "SMA50",
                 "SMA200", "vs_sma200", "EMA20", "EMA50", "EMA200", "BB.upper", "BB.lower"],
    "Pre/Post": ["close", "change", "gap", "premarket_close", "premarket_change", "premarket_volume",
                 "postmarket_close", "postmarket_change", "postmarket_volume"],
    "Analistas": ["close", "rating_ana", "recommendation_mark", "price_target_average", "potencial",
                  "earnings_release_next_date"],
    "Ficha": ["exchange", "country", "currency", "sector", "industry", "market_cap_basic",
              "float_shares_outstanding", "number_of_employees", "retraso"],
}

# Filtros de rango — grupo: [(etiqueta, campo, multiplicador)]
FILTROS = {
    "📌 Descriptivos": [
        ("Capitalización (miles de M)", "market_cap_basic", 1e9), ("Precio", "close", 1),
        ("Variación %", "change", 1), ("Gap %", "gap", 1), ("Volumen (M)", "volume", 1e6),
        ("Vol. medio 30d (M)", "average_volume_30d_calc", 1e6),
        ("Volumen relativo", "relative_volume_10d_calc", 1),
    ],
    "💶 Valoración": [
        ("PER", "price_earnings_ttm", 1), ("PEG", "price_earnings_growth_ttm", 1),
        ("P/Valor contable", "price_book_fq", 1), ("P/Ventas", "price_sales_current", 1),
        ("P/FCF", "price_free_cash_flow_ttm", 1), ("EV/EBITDA", "enterprise_value_ebitda_ttm", 1),
    ],
    "🪙 Dividendos": [
        ("Rentabilidad por dividendo %", "dividends_yield_current", 1),
        ("Payout %", "dividend_payout_ratio_ttm", 1),
    ],
    "🏭 Rentabilidad y crecimiento": [
        ("Margen bruto %", "gross_margin_ttm", 1), ("Margen operativo %", "operating_margin_ttm", 1),
        ("Margen neto %", "net_margin_ttm", 1), ("ROE %", "return_on_equity_fq", 1),
        ("ROA %", "return_on_assets_fq", 1), ("ROIC %", "return_on_invested_capital_fq", 1),
        ("Crec. ingresos % a/a", "total_revenue_yoy_growth_ttm", 1),
        ("Crec. BPA % a/a", "earnings_per_share_diluted_yoy_growth_ttm", 1),
    ],
    "🏦 Solidez financiera": [
        ("Deuda/Patrimonio", "debt_to_equity_fq", 1), ("Ratio corriente", "current_ratio_fq", 1),
        ("Prueba ácida", "quick_ratio_fq", 1),
    ],
    "📅 Rendimiento": [
        ("1 semana %", "Perf.W", 1), ("1 mes %", "Perf.1M", 1), ("3 meses %", "Perf.3M", 1),
        ("6 meses %", "Perf.6M", 1), ("YTD %", "Perf.YTD", 1), ("1 año %", "Perf.Y", 1),
        ("5 años %", "Perf.5Y", 1), ("Volatilidad mensual %", "Volatility.M", 1),
        ("Beta 1 año", "beta_1_year", 1),
    ],
    "📐 Técnicos": [
        ("RSI (14)", "RSI", 1), ("ADX", "ADX", 1), ("Estocástico %K", "Stoch.K", 1),
        ("CCI (20)", "CCI20", 1), ("Williams %R", "W.R", 1),
    ],
}

# Señales (casillas) — etiqueta: (izquierda, operación, derecha)
SENALES = {
    "Precio > SMA 20": ("close", "greater", "SMA20"), "Precio > SMA 50": ("close", "greater", "SMA50"),
    "Precio > SMA 200": ("close", "greater", "SMA200"), "Precio < SMA 200": ("close", "less", "SMA200"),
    "SMA 50 > SMA 200 (alcista)": ("SMA50", "greater", "SMA200"),
    "SMA 50 < SMA 200 (bajista)": ("SMA50", "less", "SMA200"),
    "MACD > señal": ("MACD.macd", "greater", "MACD.signal"),
    "MACD < señal": ("MACD.macd", "less", "MACD.signal"),
    "Precio > Bollinger superior": ("close", "greater", "BB.upper"),
    "Precio < Bollinger inferior": ("close", "less", "BB.lower"),
    "Nuevo máximo 52 semanas": ("high", "egreater", "price_52_week_high"),
    "Nuevo mínimo 52 semanas": ("low", "eless", "price_52_week_low"),
    "Nuevo máximo histórico": ("high", "egreater", "High.All"),
}

RATING_TEC = {
    "Cualquiera": None, "Compra fuerte": ("Recommend.All", "greater", 0.5),
    "Compra o mejor": ("Recommend.All", "greater", 0.1),
    "Neutral": ("Recommend.All", "in_range", [-0.1, 0.1]),
    "Venta o peor": ("Recommend.All", "less", -0.1), "Venta fuerte": ("Recommend.All", "less", -0.5),
}
RATING_ANA = {
    "Cualquiera": None, "Compra fuerte": ("recommendation_mark", "eless", 1.25),
    "Compra o mejor": ("recommendation_mark", "eless", 1.75),
    "Mantener": ("recommendation_mark", "in_range", [1.75, 2.25]),
    "Venta o peor": ("recommendation_mark", "greater", 2.25),
}

# Preajustes — nombre: (filtros extra, ordenar por, orden)
PRESETS = {
    "— Ninguno —": ([], None, None),
    "🚀 Mayores subidas": ([], "change", "desc"),
    "📉 Mayores caídas": ([], "change", "asc"),
    "🔥 Más negociados": ([], "volume", "desc"),
    "⚡ Volumen inusual (x2)": ([("relative_volume_10d_calc", "greater", 2)], "relative_volume_10d_calc", "desc"),
    "🟢 Sobrevendidos (RSI < 30)": ([("RSI", "less", 30)], "RSI", "asc"),
    "🔴 Sobrecomprados (RSI > 70)": ([("RSI", "greater", 70)], "RSI", "desc"),
    "🏔️ Nuevos máximos 52 sem.": ([("high", "egreater", "price_52_week_high")], "change", "desc"),
    "🕳️ Nuevos mínimos 52 sem.": ([("low", "eless", "price_52_week_low")], "change", "asc"),
    "💰 Alto dividendo (> 4 %)": ([("dividends_yield_current", "greater", 4)], "dividends_yield_current", "desc"),
    "🧮 Value (PER < 15, P/VC < 2)": ([("price_earnings_ttm", "in_range", [0, 15]),
                                       ("price_book_fq", "less", 2)], "price_earnings_ttm", "asc"),
    "🌱 Crecimiento (> 20 % a/a)": ([("total_revenue_yoy_growth_ttm", "greater", 20),
                                     ("earnings_per_share_diluted_yoy_growth_ttm", "greater", 20)],
                                    "total_revenue_yoy_growth_ttm", "desc"),
    "🏆 Calidad (ROE > 20, deuda baja)": ([("return_on_equity_fq", "greater", 20),
                                          ("debt_to_equity_fq", "less", 1)], "return_on_equity_fq", "desc"),
    "✅ Compra fuerte técnica": ([("Recommend.All", "greater", 0.5)], "Recommend.All", "desc"),
    "⭐ Favoritas de analistas": ([("recommendation_mark", "eless", 1.5)], "recommendation_mark", "asc"),
    "📈 Tendencia alcista": ([("close", "greater", "SMA50"), ("SMA50", "greater", "SMA200")], "Perf.3M", "desc"),
    "🌅 Movimientos premarket": ([], "premarket_change", "desc"),
    "🌙 Movimientos postmarket": ([], "postmarket_change", "desc"),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0 Safari/537.36",
    "Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/",
}


# ══════════════════════════════════════════════════════════════════════════════
# 3. DATOS
# ══════════════════════════════════════════════════════════════════════════════
def con_tf(campo, tf):
    """Añade la temporalidad a los campos técnicos (p. ej. RSI|60)."""
    return f"{campo}|{tf}" if tf and isinstance(campo, str) and campo in TECNICOS else campo


def construir_payload(filtros, tf, orden_campo, orden_dir, limite, excluidos=(), symbolset=None, primarios=False):
    campos = [c for c in CAMPOS_API if c not in excluidos]
    flt = []
    for izq, op, der in filtros:
        if izq in excluidos or (isinstance(der, str) and der in excluidos):
            continue
        flt.append({"left": con_tf(izq, tf), "operation": op,
                    "right": con_tf(der, tf) if isinstance(der, str) and der in CAMPOS else der})
    if primarios:
        flt.append({"left": "type", "operation": "in_range", "right": ["stock", "dr"]})
        if "is_primary" not in excluidos:
            flt.append({"left": "is_primary", "operation": "equal", "right": True})
    payload = {
        "columns": [con_tf(c, tf) for c in campos],
        "filter": flt,
        "options": {"lang": "en"},
        "range": [0, int(limite)],
        "ignore_unknown_fields": False,
    }
    if orden_campo and orden_campo not in excluidos:
        payload["sort"] = {"sortBy": con_tf(orden_campo, tf), "sortOrder": orden_dir}
    if symbolset:
        payload["symbols"] = {"symbolset": [symbolset]}
    return payload


@st.cache_data(ttl=5, show_spinner=False)
def escanear(url, payload_json, sessionid):
    """Llama al escáner. Si un campo ya no existe en la API lo descarta y reintenta."""
    payload = json.loads(payload_json)
    cookies = {"sessionid": sessionid} if sessionid else None
    descartados = []
    for _ in range(30):
        try:
            r = requests.post(url, json=payload, headers=HEADERS, cookies=cookies, timeout=25)
        except requests.RequestException as e:
            return [], 0, payload["columns"], descartados, f"Error de red: {e}"
        try:
            js = r.json()
        except ValueError:
            js = {}
        err = js.get("error") if isinstance(js, dict) else None
        if r.ok and not err:
            return js.get("data") or [], js.get("totalCount", 0), payload["columns"], descartados, None
        texto = str(err or r.text[:300])
        m = re.search(r'[Uu]nknown field:?\s*\\?"?([\w.|]+)', texto)
        malo = m.group(1) if m else None
        en_cols = malo in payload["columns"]
        en_flt = any(f["left"] == malo or (isinstance(f.get("right"), str) and f["right"] == malo)
                     for f in payload["filter"])
        en_sort = payload.get("sort", {}).get("sortBy") == malo
        if not malo or not (en_cols or en_flt or en_sort):
            return [], 0, payload["columns"], descartados, f"HTTP {r.status_code}: {texto}"
        payload["columns"] = [c for c in payload["columns"] if c != malo]
        payload["filter"] = [f for f in payload["filter"]
                             if f["left"] != malo and (isinstance(f.get("right"), list) or f.get("right") != malo)]
        if en_sort:
            payload.pop("sort", None)
        descartados.append(malo)
    return [], 0, payload["columns"], descartados, "Demasiados campos desconocidos."


def a_dataframe(filas, columnas):
    df = pd.DataFrame([f["d"] for f in filas], columns=[c.split("|")[0] for c in columnas])
    df.insert(0, "ticker", [f["s"] for f in filas])
    return enriquecer(df)


def etiqueta_tec(v):
    if pd.isna(v):
        return None
    return ("🟢 Compra fuerte" if v > 0.5 else "🟢 Compra" if v > 0.1 else
            "🔴 Venta fuerte" if v < -0.5 else "🔴 Venta" if v < -0.1 else "⚪ Neutral")


def etiqueta_ana(v):
    if pd.isna(v):
        return None
    return ("🟢 Compra fuerte" if v <= 1.25 else "🟢 Compra" if v <= 1.75 else
            "⚪ Mantener" if v <= 2.25 else "🔴 Venta" if v <= 2.75 else "🔴 Venta fuerte")


def etiqueta_retraso(v):
    if not isinstance(v, str):
        return None
    if v == "streaming":
        return "⚡ Tiempo real"
    m = re.search(r"delayed_streaming_(\d+)", v)
    if m:
        return f"⏱️ {int(m.group(1)) // 60} min"
    return "🌙 Cierre" if "endofday" in v else v


def enriquecer(df):
    def col(c):
        return pd.to_numeric(df[c], errors="coerce") if c in df else pd.Series(float("nan"), index=df.index)

    precio = col("close")
    if "Recommend.All" in df:
        df["rating_tec"] = col("Recommend.All").map(etiqueta_tec)
    if "recommendation_mark" in df:
        df["rating_ana"] = col("recommendation_mark").map(etiqueta_ana)
    if "price_target_average" in df:
        df["potencial"] = (col("price_target_average") / precio - 1) * 100
    if "price_52_week_high" in df:
        df["dist_max52"] = (precio / col("price_52_week_high") - 1) * 100
    if "price_52_week_low" in df:
        df["dist_min52"] = (precio / col("price_52_week_low") - 1) * 100
    if "SMA200" in df:
        df["vs_sma200"] = (precio / col("SMA200") - 1) * 100
    if "update_mode" in df:
        df["retraso"] = df["update_mode"].map(etiqueta_retraso)
    if "earnings_release_next_date" in df:
        df["earnings_release_next_date"] = pd.to_datetime(
            col("earnings_release_next_date"), unit="s", errors="coerce").dt.strftime("%d/%m/%Y")
    if "logoid" in df:
        df["logoid"] = df["logoid"].map(
            lambda x: f"https://s3-symbol-logo.tradingview.com/{x}.svg" if isinstance(x, str) and x else None)
    if "sector" in df:
        df["sector"] = df["sector"].map(lambda s: SECTORES.get(s, s))
    return df


def config_columnas(cols):
    cfg = {}
    for c in cols:
        etq, tipo = CAMPOS.get(c, (c, "text"))
        if c == "logoid":
            cfg[c] = st.column_config.ImageColumn("", width="small")
        elif tipo == "price":
            cfg[c] = st.column_config.NumberColumn(etq, format="%.2f")
        elif tipo == "pct":
            cfg[c] = st.column_config.NumberColumn(etq, format="%.2f%%")
        elif tipo == "big":
            cfg[c] = st.column_config.NumberColumn(etq, format="compact")
        elif tipo == "num":
            cfg[c] = st.column_config.NumberColumn(etq, format="%.2f")
        else:
            cfg[c] = st.column_config.TextColumn(etq)
    return cfg


def color_signo(v):
    if pd.isna(v) or v == 0:
        return ""
    return "color:#26a69a;font-weight:600" if v > 0 else "color:#ef5350;font-weight:600"


def compacto(v, sufijo=""):
    if v is None or pd.isna(v):
        return "—"
    for lim, s in ((1e12, " B"), (1e9, " mil M"), (1e6, " M"), (1e3, " k")):
        if abs(v) >= lim:
            return f"{v / lim:,.2f}{s}{sufijo}"
    return f"{v:,.2f}{sufijo}"


def widget_tv(ticker, tf, alto=520):
    intervalo = {"": "D", "1W": "W", "1M": "M"}.get(tf, tf)
    components.html(f"""
    <div id="tvchart" style="height:{alto}px"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
      new TradingView.widget({{container_id:"tvchart", symbol:"{ticker}", interval:"{intervalo}",
        width:"100%", height:{alto}, theme:"dark", style:"1", locale:"es", timezone:"Europe/Madrid",
        allow_symbol_change:true, hide_side_toolbar:false, withdateranges:true,
        studies:["RSI@tv-basicstudies","MASimple@tv-basicstudies"]}});
    </script>""", height=alto + 10)


# ══════════════════════════════════════════════════════════════════════════════
# 4. BARRA LATERAL
# ══════════════════════════════════════════════════════════════════════════════
ss = st.session_state
ss.setdefault("malos", [])
ss.setdefault("codigo_ok", {})


def limpiar_filtros():
    for k in list(ss.keys()):
        if k.startswith(("min_", "max_")):
            ss[k] = None
        elif k.startswith("sen_"):
            ss[k] = False
    ss["sectores"] = []
    ss["rt"] = ss["ra"] = "Cualquiera"
    ss["preset"] = "— Ninguno —"


with st.sidebar:
    st.title("📈 Screener")
    modo = st.radio("Universo", ["Índice", "Mercado", "Código"], horizontal=True,
                    help="Índice: componentes de un índice. Mercado: todas las acciones de un país. "
                         "Código: cualquier índice de TradingView (p. ej. SYML:SP;SPX).")
    if modo == "Índice":
        indice = st.selectbox("Índice", list(INDICES))
        candidatos, universo = INDICES[indice], indice
    elif modo == "Mercado":
        pais = st.selectbox("País", list(MERCADOS))
        candidatos, universo = [None], pais
    else:
        cod = st.text_input("Código del índice", "SYML:SP;SPX",
                            help="Símbolo del índice en TradingView cambiando ':' por ';' y con el prefijo SYML:")
        candidatos, universo = [cod.strip()], cod.strip()

    preset = st.selectbox("Preajuste", list(PRESETS), key="preset")
    c1, c2 = st.columns([3, 2])
    ordenables = [c for c in CAMPOS_API if CAMPOS[c][1] != "text"]
    orden_campo = c1.selectbox("Ordenar por", ordenables, index=ordenables.index("market_cap_basic"),
                               format_func=lambda c: CAMPOS[c][0])
    orden_dir = c2.selectbox("Orden", ["desc", "asc"], format_func=lambda d: "Mayor→menor" if d == "desc" else "Menor→mayor")
    limite = st.slider("Máx. resultados", 50, 3000, 600, 50) if modo == "Mercado" else 3000

    st.divider()
    cab1, cab2 = st.columns([3, 2])
    cab1.subheader("Filtros")
    cab2.button("Limpiar", on_click=limpiar_filtros, use_container_width=True)

    filtros = []
    for grupo, items in FILTROS.items():
        with st.expander(grupo):
            if grupo.startswith("📌"):
                secs = st.multiselect("Sector", list(SECTORES), format_func=SECTORES.get, key="sectores")
                if secs:
                    filtros.append(("sector", "in_range", secs))
            if grupo.startswith("📐"):
                tf_nombre = st.selectbox("Temporalidad de indicadores", list(TIMEFRAMES))
                rt = st.selectbox("Rating técnico", list(RATING_TEC), key="rt")
                if RATING_TEC[rt]:
                    filtros.append(RATING_TEC[rt])
            for etq, campo, mult in items:
                st.caption(etq)
                a, b = st.columns(2)
                vmin = a.number_input("mín", value=None, key=f"min_{campo}", placeholder="mín", label_visibility="collapsed")
                vmax = b.number_input("máx", value=None, key=f"max_{campo}", placeholder="máx", label_visibility="collapsed")
                if vmin is not None and vmax is not None:
                    filtros.append((campo, "in_range", [vmin * mult, vmax * mult]))
                elif vmin is not None:
                    filtros.append((campo, "egreater", vmin * mult))
                elif vmax is not None:
                    filtros.append((campo, "eless", vmax * mult))
    tf = TIMEFRAMES[tf_nombre]

    with st.expander("🚦 Señales"):
        for etq, regla in SENALES.items():
            if st.checkbox(etq, key=f"sen_{etq}"):
                filtros.append(regla)
    with st.expander("🎯 Analistas"):
        ra = st.selectbox("Consenso", list(RATING_ANA), key="ra")
        if RATING_ANA[ra]:
            filtros.append(RATING_ANA[ra])

    st.divider()
    with st.expander("⚙️ Datos y actualización", expanded=False):
        auto = st.toggle("Actualización automática", value=False)
        cada = st.select_slider("Cada (segundos)", [10, 15, 30, 60, 120, 300], value=30)
        try:
            sid_secreto = st.secrets.get("TV_SESSIONID", "")
        except Exception:
            sid_secreto = ""
        sid_manual = st.text_input("sessionid de TradingView (opcional)", type="password",
                                   help="Cookie 'sessionid' de tu cuenta de TradingView. Con ella el escáner "
                                        "devuelve datos en tiempo real en las bolsas que tu cuenta tenga activas. "
                                        "Mejor guardarla en Secrets como TV_SESSIONID.")
        sessionid = sid_manual or sid_secreto
        st.caption("🔐 Sesión activa" if sessionid else "Sin sesión: la mayoría de bolsas llegan con 15 min de retraso.")

extra, p_campo, p_dir = PRESETS[preset]
filtros = filtros + list(extra)
if p_campo:
    orden_campo, orden_dir = p_campo, p_dir


# ══════════════════════════════════════════════════════════════════════════════
# 5. CUERPO
# ══════════════════════════════════════════════════════════════════════════════
def cargar():
    """Devuelve (df, total, error). Prueba los códigos candidatos del índice."""
    if modo == "Mercado":
        url = f"https://scanner.tradingview.com/{MERCADOS[pais]}/scan"
        pruebas = [None]
    else:
        url = "https://scanner.tradingview.com/global/scan"
        ok = ss["codigo_ok"].get(universo)
        pruebas = [ok] if ok else candidatos
    error = None
    for codigo in pruebas:
        # 1) sin filtros de usuario comprobamos que el código existe; 2) consulta real
        payload = construir_payload(filtros, tf, orden_campo, orden_dir, limite, ss["malos"],
                                    symbolset=codigo, primarios=(modo == "Mercado"))
        filas, total, cols, malos, error = escanear(url, json.dumps(payload, sort_keys=True), sessionid)
        for m in malos:
            base = m.split("|")[0]
            if base not in ss["malos"]:
                ss["malos"].append(base)
        if error:
            continue
        if filas or modo == "Mercado" or len(pruebas) == 1:
            if codigo:
                ss["codigo_ok"][universo] = codigo
            return a_dataframe(filas, cols), total, None
        # sin filas: ¿código inválido o filtros demasiado estrictos?
        vacio = construir_payload([], tf, None, "desc", 1, ss["malos"], symbolset=codigo)
        f0, _, _, _, e0 = escanear(url, json.dumps(vacio, sort_keys=True), sessionid)
        if f0 and not e0:
            ss["codigo_ok"][universo] = codigo
            return a_dataframe(filas, cols), total, None
    return pd.DataFrame(), 0, error or "El índice no devolvió componentes con ninguno de los códigos conocidos."


@st.fragment(run_every=cada if auto else None)
def cuerpo():
    with st.spinner("Cargando datos…"):
        df, total, error = cargar()

    izq, der = st.columns([5, 2])
    izq.subheader(universo)
    der.caption(f"Actualizado {datetime.now().strftime('%H:%M:%S')} (hora del servidor)"
                + (f" · auto {cada}s" if auto else ""))
    if der.button("🔄 Actualizar", use_container_width=True):
        escanear.clear()
        st.rerun(scope="fragment")

    if error:
        st.error(error)
        st.info("Prueba el modo **Mercado** o introduce el código del índice en el modo **Código**.")
        return
    if df.empty:
        st.warning("Ningún valor cumple los filtros. Relaja alguno o pulsa **Limpiar**.")
        return

    # ── amplitud del mercado ────────────────────────────────────────────────
    ch = pd.to_numeric(df.get("change"), errors="coerce")
    m = st.columns(6)
    m[0].metric("Valores", f"{len(df)}", f"de {total}" if total > len(df) else None, delta_color="off")
    m[1].metric("Suben", int((ch > 0).sum()))
    m[2].metric("Bajan", int((ch < 0).sum()))
    m[3].metric("Var. media", f"{ch.mean():.2f} %")
    if "market_cap_basic" in df:
        cap = pd.to_numeric(df["market_cap_basic"], errors="coerce")
        pond = (ch * cap).sum() / cap[ch.notna()].sum() if cap[ch.notna()].sum() else float("nan")
        m[4].metric("Var. ponderada", f"{pond:.2f} %")
    if "price_earnings_ttm" in df:
        m[5].metric("PER mediano", f"{pd.to_numeric(df['price_earnings_ttm'], errors='coerce').median():.1f}")
    if "retraso" in df:
        modos = df["retraso"].value_counts()
        st.caption("Frescura de los datos: " + " · ".join(f"{k} ({v})" for k, v in modos.items()))

    t_tabla, t_mapa, t_graf = st.tabs(["📋 Tabla", "🗺️ Mapa de calor", "📊 Gráficos"])

    # ── tabla ───────────────────────────────────────────────────────────────
    with t_tabla:
        a, b = st.columns([2, 5])
        buscar = a.text_input("Buscar", placeholder="Ticker o nombre…", label_visibility="collapsed")
        vista = b.radio("Vista", list(VISTAS) + ["Personalizada"], horizontal=True, label_visibility="collapsed")
        if vista == "Personalizada":
            disponibles = [c for c in CAMPOS if c in df.columns and c not in BASE]
            cols_vista = st.multiselect("Columnas", disponibles, default=[c for c in VISTAS["Resumen"] if c in disponibles],
                                        format_func=lambda c: CAMPOS[c][0])
        else:
            cols_vista = VISTAS[vista]
        cols = [c for c in BASE + cols_vista if c in df.columns]

        dv = df
        if buscar:
            q = buscar.lower()
            dv = df[df["name"].astype(str).str.lower().str.contains(q, regex=False)
                    | df["description"].astype(str).str.lower().str.contains(q, regex=False)]
        dv = dv.reset_index(drop=True)
        tabla = dv[cols]
        pct = [c for c in cols if CAMPOS[c][1] == "pct" or c == "change_abs"]
        estilo = tabla.style.map(color_signo, subset=pct) if pct else tabla

        ev = st.dataframe(estilo, column_config=config_columnas(cols), hide_index=True,
                          use_container_width=True, height=560, on_select="rerun",
                          selection_mode="single-row", key="tabla")
        d1, d2 = st.columns([1, 4])
        d1.download_button("⬇️ CSV completo", df.drop(columns=["logoid"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
                           f"screener_{datetime.now():%Y%m%d_%H%M}.csv", "text/csv", use_container_width=True)
        d2.caption("Selecciona una fila para ver su gráfico y ficha. Haz clic en una cabecera para reordenar.")

        sel = ev.selection.rows if ev and ev.selection else []
        if sel and sel[0] < len(dv):
            r = dv.iloc[sel[0]]
            st.divider()
            st.subheader(f"{r.get('description', '')} · {r['ticker']}")
            k = st.columns(6)
            var = r.get("change")
            k[0].metric("Precio", f"{compacto(r.get('close'))} {r.get('currency') or ''}",
                        None if var is None or pd.isna(var) else f"{var:.2f} %")
            k[1].metric("Capitalización", compacto(r.get("market_cap_basic")))
            k[2].metric("PER", compacto(r.get("price_earnings_ttm")))
            k[3].metric("Dividendo", compacto(r.get("dividends_yield_current"), " %"))
            k[4].metric("Técnico", (r.get("rating_tec") or "—"))
            k[5].metric("Analistas", (r.get("rating_ana") or "—"))
            widget_tv(r["ticker"], tf)
            with st.expander("Todos los datos del valor"):
                ficha = pd.DataFrame(
                    [(CAMPOS[c][0] or c, compacto(r[c]) if isinstance(r[c], (int, float)) else r[c])
                     for c in df.columns if c in CAMPOS and c not in ("logoid",)],
                    columns=["Dato", "Valor"])
                st.dataframe(ficha.astype(str), hide_index=True, use_container_width=True)

    # ── mapa de calor ───────────────────────────────────────────────────────
    with t_mapa:
        a, b = st.columns(2)
        colorear = a.selectbox("Color", ["change", "Perf.W", "Perf.1M", "Perf.3M", "Perf.YTD", "Perf.Y"],
                               format_func=lambda c: CAMPOS[c][0])
        tam = b.selectbox("Tamaño", ["market_cap_basic", "volume", "Value.Traded"], format_func=lambda c: CAMPOS[c][0])
        if {colorear, tam, "sector"} <= set(df.columns):
            dm = df[["name", "description", "sector", colorear, tam]].copy()
            dm[tam] = pd.to_numeric(dm[tam], errors="coerce")
            dm[colorear] = pd.to_numeric(dm[colorear], errors="coerce")
            dm = dm[(dm[tam] > 0) & dm[colorear].notna()].fillna({"sector": "Otros"})
            if len(dm):
                rango = max(1.0, float(dm[colorear].abs().quantile(0.9)))
                fig = px.treemap(dm, path=[px.Constant(universo), "sector", "name"], values=tam, color=colorear,
                                 color_continuous_scale=["#f23645", "#801922", "#2a2e39", "#056636", "#089950"],
                                 range_color=[-rango, rango], hover_data={"description": True, colorear: ":.2f"})
                fig.update_traces(texttemplate="<b>%{label}</b><br>%{color:.2f}%", marker_line_width=1)
                fig.update_layout(height=680, margin=dict(t=10, l=0, r=0, b=0), coloraxis_colorbar_title="%")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos suficientes para el mapa.")
        else:
            st.info("La API no devolvió los campos necesarios para el mapa.")

    # ── gráficos ────────────────────────────────────────────────────────────
    with t_graf:
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Variación media por sector**")
            if "sector" in df:
                s = df.assign(change=ch).groupby("sector")["change"].mean().sort_values().reset_index()
                fig = px.bar(s, x="change", y="sector", orientation="h", color="change",
                             color_continuous_scale=["#f23645", "#2a2e39", "#089950"], color_continuous_midpoint=0)
                fig.update_layout(height=480, showlegend=False, coloraxis_showscale=False,
                                  margin=dict(t=10, l=0, r=0, b=0), xaxis_title="%", yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.markdown("**Dispersión**")
            nums = [c for c in CAMPOS if c in df.columns and CAMPOS[c][1] != "text"]
            x1, x2 = st.columns(2)
            ex = x1.selectbox("Eje X", nums, index=nums.index("price_earnings_ttm") if "price_earnings_ttm" in nums else 0,
                              format_func=lambda c: CAMPOS[c][0])
            ey = x2.selectbox("Eje Y", nums, index=nums.index("Perf.Y") if "Perf.Y" in nums else 0,
                              format_func=lambda c: CAMPOS[c][0])
            ds = df[["name", "description", ex, ey] + (["sector"] if "sector" in df else [])].copy()
            ds = ds.loc[:, ~ds.columns.duplicated()]
            ds[ex] = pd.to_numeric(ds[ex], errors="coerce")
            ds[ey] = pd.to_numeric(ds[ey], errors="coerce")
            ds = ds.dropna(subset=[ex, ey])
            fig = px.scatter(ds, x=ex, y=ey, color="sector" if "sector" in ds else None, hover_name="name",
                             hover_data=["description"], labels={ex: CAMPOS[ex][0], ey: CAMPOS[ey][0]})
            fig.update_layout(height=440, margin=dict(t=10, l=0, r=0, b=0), legend=dict(font=dict(size=9)))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Top 10 del día**")
        s1, s2 = st.columns(2)
        top = df.assign(change=ch).dropna(subset=["change"])
        mini = ["name", "description", "close", "change"]
        s1.dataframe(top.nlargest(10, "change")[mini].style.map(color_signo, subset=["change"]),
                     column_config=config_columnas(mini), hide_index=True, use_container_width=True)
        s2.dataframe(top.nsmallest(10, "change")[mini].style.map(color_signo, subset=["change"]),
                     column_config=config_columnas(mini), hide_index=True, use_container_width=True)

    if ss["malos"]:
        with st.expander("ℹ️ Campos no disponibles en la API"):
            st.caption("TradingView cambia nombres de campos de vez en cuando; estos se han omitido automáticamente: "
                       + ", ".join(sorted(set(ss["malos"]))))


cuerpo()
st.caption("Datos del escáner de TradingView (endpoint no oficial). Uso personal e informativo; no es asesoramiento financiero.")
