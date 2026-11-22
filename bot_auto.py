"""
Bot que PROCURA ofertas na Shopee e posta no canal do Telegram.
Versão para rodar no GitHub Actions: cada execução faz UMA rodada e termina.

Comandos:
  ofertas -> só mostra o que achou (não posta)
  teste   -> posta uma oferta agora (ignora horário e sorteio)
  uma     -> rodada normal (respeita horário e sorteio)
"""
import html
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone

import requests

from shopee_api import ErroShopee, buscar_ofertas

APP_ID = os.getenv("SHOPEE_APP_ID", "").strip()
SECRET = os.getenv("SHOPEE_APP_SECRET", "").strip()
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CANAL = os.getenv("CANAL", "").strip()

PALAVRAS = [p.strip() for p in os.getenv("PALAVRAS", "fone bluetooth").split(",") if p.strip()]
DESCONTO_MIN = int(os.getenv("DESCONTO_MIN", "30"))
VENDAS_MIN = int(os.getenv("VENDAS_MIN", "100"))
AVALIACAO_MIN = float(os.getenv("AVALIACAO_MIN", "4.5"))
ORDENAR = int(os.getenv("ORDENAR", "2"))

HORA_INICIO = int(os.getenv("HORA_INICIO", "8"))
HORA_FIM = int(os.getenv("HORA_FIM", "22"))
PROBABILIDADE = float(os.getenv("PROBABILIDADE", "0.5"))  # chance de postar a cada rodada

ARQ_POSTADOS = "postados.json"
API_TG = f"https://api.telegram.org/bot{TOKEN}"
FUSO_BR = timezone(timedelta(hours=-3))  # horário de Brasília/Bahia


def carregar_postados():
    if not os.path.exists(ARQ_POSTADOS):
        return []
    try:
        with open(ARQ_POSTADOS, encoding="utf-8") as f:
            return json.load(f)
    except ValueError:
        return []


def salvar_postados(lista):
    with open(ARQ_POSTADOS, "w", encoding="utf-8") as f:
        json.dump(lista[-2000:], f)


def preco(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def montar_mensagem(o):
    linhas = [f"🔥 <b>{html.escape(o['titulo'])}</b>", ""]
    if o["preco_de"] and o["desconto"]:
        linhas.append(f"De <s>{preco(o['preco_de'])}</s>")
        linhas.append(f"💰 Por <b>{preco(o['preco_por'])}</b> ({o['desconto']}% OFF)")
    else:
        linhas.append(f"💰 <b>{preco(o['preco_por'])}</b>")
    if o["vendas"]:
        linhas.append(f"⭐ {o['avaliacao']:.1f} | 🛍️ {o['vendas']} vendidos")
    linhas += ["", f'🛒 <a href="{html.escape(o["link"])}">Compre aqui</a>', "", "<i>Link de afiliado.</i>"]
    return "\n".join(linhas)


def enviar(o):
    texto = montar_mensagem(o)
    if o["imagem"]:
        r = requests.post(
            f"{API_TG}/sendPhoto",
            data={"chat_id": CANAL, "photo": o["imagem"], "caption": texto, "parse_mode": "HTML"},
            timeout=60,
        )
        if r.ok:
            return True
        print(f"  (imagem falhou: {r.status_code}, enviando só texto)")
    r = requests.post(
        f"{API_TG}/sendMessage",
        data={"chat_id": CANAL, "text": texto, "parse_mode": "HTML"},
        timeout=60,
    )
    if not r.ok:
        print(f"  Erro no Telegram: {r.status_code} {r.text[:300]}")
    return r.ok


def passa_nos_filtros(o):
    return (
        o["link"]
        and o["preco_por"] > 0
        and o["desconto"] >= DESCONTO_MIN
        and o["vendas"] >= VENDAS_MIN
        and o["avaliacao"] >= AVALIACAO_MIN
    )


def achar_oferta(postados, mostrar=False):
    palavras = PALAVRAS[:]
    random.shuffle(palavras)
    for palavra in palavras:
        try:
            ofertas = buscar_ofertas(APP_ID, SECRET, palavra, ordenar=ORDENAR)
        except ErroShopee as e:
            print(f"Erro ao buscar '{palavra}': {e}")
            continue
        boas = [o for o in ofertas if passa_nos_filtros(o)]
        novas = [o for o in boas if o["id"] not in postados]
        print(f"'{palavra}': {len(ofertas)} achados, {len(boas)} passaram nos filtros, {len(novas)} novos")
        if mostrar:
            for o in boas[:5]:
                print(f"   - {o['titulo'][:60]} | {preco(o['preco_por'])} | {o['desconto']}% OFF | {o['vendas']} vendas")
        if novas:
            return random.choice(novas[:10])
    return None


def uma_rodada(forcar=False):
    """Retorna True se tudo certo, False se deu erro."""
    agora = datetime.now(FUSO_BR)
    if not forcar:
        if not (HORA_INICIO <= agora.hour < HORA_FIM):
            print(f"Fora do horário ({agora:%H:%M}). Nada a fazer.")
            return True
        if random.random() > PROBABILIDADE:
            print("Sorteio: pulando esta rodada.")
            return True
    postados = carregar_postados()
    o = achar_oferta(postados)
    if not o:
        print("Nada novo pra postar agora.")
        return not forcar
    if enviar(o):
        postados.append(o["id"])
        salvar_postados(postados)
        print(f"Postado: {o['titulo'][:60]}")
        return True
    return False


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else "uma"
    if not (APP_ID and SECRET):
        sys.exit("Faltam os segredos SHOPEE_APP_ID e SHOPEE_APP_SECRET no GitHub.")
    if comando == "ofertas":
        achar_oferta([], mostrar=True)
        sys.exit(0)
    if not (TOKEN and CANAL):
        sys.exit("Faltam os segredos TELEGRAM_TOKEN e CANAL no GitHub.")
    ok = uma_rodada(forcar=(comando == "teste"))
    sys.exit(0 if ok else 1)
