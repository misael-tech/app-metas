"""Cálculos de metas e vendas (única fonte dos cálculos)."""
import calendar
from datetime import date
from decimal import Decimal

from django.db.models import Count, Q, Sum

from .models import MESES, MetaEmpresa, Venda, Vendedor

ZERO = Decimal("0")
# REGRA DA META: campo usado para comparar com a meta.
# Para usar o valor à vista, troque por "valor_a_vista".
CAMPO_META = "valor_bruto"
NOMES_MES = dict(MESES)
TXT = {"batida": "BATIDA", "proxima": "PRÓXIMA", "nao": "NÃO BATIDA", "sem": "SEM META"}


def limites(ano, mes):
    return date(ano, mes, 1), date(ano, mes, calendar.monthrange(ano, mes)[1])


def percentual(vendido, meta):
    return (vendido / meta * 100) if meta else ZERO


def linha(meta, vendido):
    vendido = vendido or ZERO
    p = percentual(vendido, meta)
    st = "sem" if not meta else "batida" if p >= 100 else "proxima" if p >= 80 else "nao"
    return {"meta": meta, "vendido": vendido, "falta": max(meta - vendido, ZERO), "pct": p,
            "pct_bar": int(min(p, 100)), "status": st, "status_txt": TXT[st]}


def stats_vendedor(v, ini, fim):
    """Desempenho do vendedor entre ini e fim (meta mensal do mês de ini)."""
    metas = {(m.ano, m.mes): m for m in v.metas.all()}
    vendas = v.vendas.filter(data__range=(ini, fim))
    tot = vendas.aggregate(b=Sum("valor_bruto"), a=Sum("valor_a_vista"), n=Count("id"))
    mm = metas.get((ini.year, ini.month))
    meta_m = mm.valor_meta_mensal if mm else ZERO
    meta_d = mm.valor_meta_diaria if mm else ZERO
    dias = []
    for d in vendas.values("data").annotate(t=Sum(CAMPO_META)).order_by("data"):
        m = metas.get((d["data"].year, d["data"].month))
        dias.append({"data": d["data"], **linha(m.valor_meta_diaria if m else ZERO, d["t"])})
    vendido = sum((d["vendido"] for d in dias), ZERO)
    batidos = sum(1 for d in dias if d["status"] == "batida")
    r = linha(meta_m, vendido)
    r.update(vendedor=v, meta_mensal=meta_m, meta_diaria=meta_d, bruto=tot["b"] or ZERO,
             avista=tot["a"] or ZERO, qtd=tot["n"], dias=dias, dias_trabalhados=len(dias),
             batidos=batidos, nao_batidos=len(dias) - batidos,
             taxa=percentual(Decimal(batidos), Decimal(len(dias))),
             media=(vendido / len(dias)) if dias else ZERO)
    return r


def resumo_empresa(ano, mes):
    ini, fim = limites(ano, mes)
    me = MetaEmpresa.objects.filter(ano=ano, mes=mes).first()
    vendas = Venda.objects.filter(data__range=(ini, fim))
    r = linha(me.valor_meta if me else ZERO, vendas.aggregate(t=Sum(CAMPO_META))["t"])
    r["avista"] = vendas.aggregate(t=Sum("valor_a_vista"))["t"] or ZERO
    return r


def vendedores_do_periodo(ini, fim):
    return Vendedor.objects.filter(
        Q(vendas__data__range=(ini, fim)) | Q(metas__ano=ini.year, metas__mes=ini.month)).distinct()


def desempenho_dia(vendedores, dia):
    res = []
    for v in vendedores:
        m = v.metas.filter(ano=dia.year, mes=dia.month).first()
        t = v.vendas.filter(data=dia).aggregate(t=Sum(CAMPO_META))["t"]
        res.append({"vendedor": v, **linha(m.valor_meta_diaria if m else ZERO, t)})
    return res


def evolucao_dias(ano, mes, vendedor_id=None, ate=None):
    ini, fim = limites(ano, mes)
    qs = Venda.objects.filter(data__range=(ini, fim))
    if vendedor_id:
        qs = qs.filter(vendedor_id=vendedor_id)
    por_dia = {d["data"].day: float(d["t"]) for d in qs.values("data").annotate(t=Sum(CAMPO_META))}
    return [str(i) for i in range(1, fim.day + 1)], [por_dia.get(i, 0) for i in range(1, fim.day + 1)]


def historico_vendedor(v):
    res = []
    for m in v.metas.order_by("ano", "mes"):
        ini, fim = limites(m.ano, m.mes)
        t = v.vendas.filter(data__range=(ini, fim)).aggregate(t=Sum(CAMPO_META))["t"] or ZERO
        res.append({"rotulo": f"{m.mes:02d}/{m.ano}", "meta": float(m.valor_meta_mensal), "vendido": float(t)})
    return res


def totais(ini, fim, vendedor_id=None):
    qs = Venda.objects.filter(data__range=(ini, fim))
    if vendedor_id:
        qs = qs.filter(vendedor_id=vendedor_id)
    t = qs.aggregate(b=Sum("valor_bruto"), a=Sum("valor_a_vista"), n=Count("id"))
    return {"bruto": t["b"] or ZERO, "avista": t["a"] or ZERO, "qtd": t["n"]}
