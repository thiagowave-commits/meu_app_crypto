import streamlit as st
import requests
import numpy as np
from datetime import datetime
import asyncio
from telegram import Bot

# Configuração do app
st.set_page_config(page_title="TAO Explode App", layout="wide")

# Config: Telegram
TELEGRAM_TOKEN = 'SEU_BOT_TOKEN_AQUI'  # Substitua!
CHAT_ID = 'SEU_CHAT_ID_AQUI'           # Substitua!
bot = Bot(token=TELEGRAM_TOKEN)

# Criptos explosivas
CRYPTOS = {
    'TAO': {'id': 'bittensor', 'mu': 2.5, 'vol': 1.5},
    'FET': {'id': 'fetch-ai', 'mu': 2.2, 'vol': 1.3},
    'RNDR': {'id': 'render', 'mu': 2.4, 'vol': 1.4},
    'NEAR': {'id': 'near-protocol', 'mu': 2.0, 'vol': 1.2},
    'QUBIC': {'id': 'qubic-network', 'mu': 2.8, 'vol': 1.6}
}

COINGECKO_API = 'https://api.coingecko.com/api/v3/simple/price?ids={}&vs_currencies=usd'

def fetch_prices():
    ids = ','.join([c['id'] for c in CRYPTOS.values()])
    response = requests.get(COINGECKO_API.format(ids))
    if response.status_code == 200:
        data = response.json()
        return {crypto: data[info['id']]['usd'] for crypto, info in CRYPTOS.items()}
    return {k: 300 for k in CRYPTOS}

def monte_carlo_projection(price, days=3, mu=2.5, sigma=1.5, num_sims=50000):
    dt = days / 365
    sims = np.zeros(num_sims)
    for i in range(num_sims):
        shocks = np.random.normal(mu * dt, sigma * np.sqrt(dt))
        sims[i] = price * np.exp(shocks)
    median_ret = np.median(sims / price) - 1
    p95_ret = np.percentile(sims / price - 1, 95)
    prob_explode = np.mean(sims > price * 1.15)
    return median_ret, p95_ret, prob_explode

def get_hype_score(crypto):
    hype_map = {'TAO': 0.65, 'FET': 0.72, 'RNDR': 0.68, 'NEAR': 0.60, 'QUBIC': 0.75}
    return hype_map.get(crypto, 0.5)

async def send_telegram_alert(crypto, signal, details):
    message = f"🚨 ALERTA {signal} para {crypto}!\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M WITA')}\n{details}\nRisco Alto! DYOR."
    await bot.send_message(chat_id=CHAT_ID, text=message)

# Interface Streamlit
st.title("🚀 TAO Explode App")
crypto = st.selectbox("Escolha a moeda:", list(CRYPTOS.keys()))
prices = fetch_prices()
price = prices.get(crypto, 300)
mu = CRYPTOS[crypto]['mu']
vol = CRYPTOS[crypto]['vol']
ret, p95, prob = monte_carlo_projection(price, mu=mu, sigma=vol)
hype = get_hype_score(crypto)

# Exibição
st.metric("💰 Preço atual", f"${price:.2f}")
st.metric("📊 Projeção mediana (3 dias)", f"+{ret*100:.1f}%")
st.metric("🔥 Projeção 95%ile", f"+{p95*100:.1f}%")
st.metric("💥 Probabilidade de explosão", f"{prob*100:.0f}%")
st.metric("📈 Hype Score", f"{hype*100:.0f}%")

# Botão de alerta
if st.button("🚨 Enviar alerta Telegram"):
    if prob > 0.6 and hype > 0.6 and ret > 0.15:
        signal = "COMPRAR AGORA"
        details = f"Preço: US${price:.2f}\nProjeção: +{ret*100:.1f}% (mediana), +{p95*100:.1f}% (95%ile)\nProb pump: {prob*100:.0f}% | Hype: {hype*100:.0f}%"
    elif ret < -0.10:
        signal = "VENDER"
        details = f"Preço: US${price:.2f}\nProjeção: {ret*100:.1f}% | Venda para evitar perda."
    else:
        signal = "NEUTRO"
        details = f"Sem sinal forte. Projeção: {ret*100:.1f}% | Hype: {hype*100:.0f}%"
    asyncio.run(send_telegram_alert(crypto, signal, details))
    st.success(f"Alerta enviado: {signal}")

