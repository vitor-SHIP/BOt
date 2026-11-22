"""Conexão com a API de afiliados da Shopee (Brasil)."""
import hashlib
import json
import time

import requests

ENDPOINT = "https://open-api.affiliate.shopee.com.br/graphql"


class ErroShopee(Exception):
    pass


def _chamar(query, app_id, secret):
    """Envia uma consulta GraphQL assinada. A assinatura é
    SHA256(app_id + timestamp + corpo_da_requisição + secret)."""
    payload = json.dumps({"query": query}, ensure_ascii=False, separators=(",", ":"))
    timestamp = str(int(time.time()))
    assinatura = hashlib.sha256(
        (app_id + timestamp + payload + secret).encode("utf-8")
    ).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={assinatura}",
    }
    r = requests.post(ENDPOINT, headers=headers, data=payload.encode("utf-8"), timeout=30)
    try:
        dados = r.json()
    except ValueError:
        raise ErroShopee(f"Resposta inesperada ({r.status_code}): {r.text[:300]}")
    if dados.get("errors"):
        raise ErroShopee(f"A Shopee recusou o pedido: {json.dumps(dados['errors'], ensure_ascii=False)[:500]}")
    if not r.ok:
        raise ErroShopee(f"Erro HTTP {r.status_code}: {r.text[:300]}")
    return dados.get("data", {})


def _numero(valor, padrao=0.0):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def buscar_ofertas(app_id, secret, palavra, limite=30, ordenar=2, pagina=1):
    """Busca produtos por palavra-chave.
    ordenar: 1 = relevância, 2 = mais vendidos, 3 = maior preço,
             4 = menor preço, 5 = maior comissão."""
    query = (
        "{ productOfferV2("
        f"keyword: {json.dumps(palavra, ensure_ascii=False)}, "
        f"sortType: {int(ordenar)}, page: {int(pagina)}, limit: {int(limite)}"
        ") { nodes { itemId shopId productName imageUrl priceMin priceMax "
        "priceDiscountRate commissionRate sales ratingStar offerLink productLink shopName } } }"
    )
    dados = _chamar(query, app_id, secret)
    nos = (dados.get("productOfferV2") or {}).get("nodes") or []
    ofertas = []
    for n in nos:
        por = _numero(n.get("priceMin"))
        desconto = int(_numero(n.get("priceDiscountRate")))
        de = round(por / (1 - desconto / 100), 2) if 0 < desconto < 100 and por else 0
        ofertas.append(
            {
                "id": str(n.get("itemId")),
                "titulo": n.get("productName") or "",
                "preco_por": por,
                "preco_de": de,
                "desconto": desconto,
                "vendas": int(_numero(n.get("sales"))),
                "avaliacao": _numero(n.get("ratingStar")),
                "link": n.get("offerLink") or n.get("productLink") or "",
                "imagem": n.get("imageUrl") or "",
                "loja": n.get("shopName") or "",
            }
        )
    return ofertas
