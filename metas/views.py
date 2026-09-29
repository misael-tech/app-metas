import time
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import services as s
from .forms import VendaForm, VendedorForm
from .models import MESES, MetaEmpresa, MetaMensal, Venda, Vendedor


def _int(v, padrao=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return padrao


def _data(v):
    try:
        return datetime.strptime(v, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _periodo(request):
    h = date.today()
    mes = min(max(_int(request.GET.get("mes"), h.month), 1), 12)
    return _int(request.GET.get("ano"), h.year), mes


def _ctx(ano, mes, **kw):
    h = date.today()
    return dict(ano=ano, mes=mes, meses=MESES, anos=range(h.year - 3, h.year + 2),
                mes_nome=s.NOMES_MES[mes], **kw)


@login_required
def dashboard(request):
    ano, mes = _periodo(request)
    modo_hoje = request.GET.get("modo") == "hoje"
    vid = _int(request.GET.get("vendedor"))
    ativos = Vendedor.objects.filter(ativo=True)
    vendedores = ativos.filter(pk=vid) if vid else ativos
    ini, fim = s.limites(ano, mes)
    ctx = _ctx(ano, mes, modo_hoje=modo_hoje, vid=vid, lista_vendedores=ativos,
               hoje=date.today(), diario=s.desempenho_dia(vendedores, date.today()))
    if not modo_hoje:
        stats = [s.stats_vendedor(v, ini, fim) for v in vendedores]
        dias, valores = s.evolucao_dias(ano, mes, vid)
        ctx.update(empresa=s.resumo_empresa(ano, mes), stats=stats, chart={
            "nomes": [x["vendedor"].nome for x in stats],
            "metas": [float(x["meta_mensal"]) for x in stats],
            "vendidos": [float(x["vendido"]) for x in stats],
            "pcts": [round(float(x["pct"]), 2) for x in stats],
            "dias": dias, "valores": valores})
    return render(request, "dashboard.html", ctx)


# ---------- Vendedores ----------
@login_required
def vendedores(request):
    h = date.today()
    ini, fim = s.limites(h.year, h.month)
    stats = [s.stats_vendedor(v, ini, fim) for v in Vendedor.objects.all()]
    return render(request, "vendedores.html", {"stats": stats})


@login_required
def vendedor_form(request, pk=None):
    v = get_object_or_404(Vendedor, pk=pk) if pk else None
    h = date.today()
    meta = v.metas.filter(ano=h.year, mes=h.month).first() if v else None
    inicial = {"meta_mensal": meta.valor_meta_mensal, "meta_diaria": meta.valor_meta_diaria} if meta else {}
    form = VendedorForm(request.POST or None, instance=v, initial=inicial)
    if request.method == "POST" and form.is_valid():
        v = form.save()
        mm, md = form.cleaned_data["meta_mensal"], form.cleaned_data["meta_diaria"]
        if mm is not None or md is not None:
            MetaMensal.objects.update_or_create(
                vendedor=v, ano=h.year, mes=h.month,
                defaults={"valor_meta_mensal": mm or 0, "valor_meta_diaria": md or 0})
        messages.success(request, "Vendedor salvo.")
        return redirect("vendedores")
    return render(request, "form.html", {"form": form, "titulo": "Editar vendedor" if pk else "Novo vendedor",
                                         "voltar": "vendedores"})


@login_required
@require_POST
def vendedor_toggle(request, pk):
    v = get_object_or_404(Vendedor, pk=pk)
    v.ativo = not v.ativo
    v.save(update_fields=["ativo"])
    return redirect("vendedores")


@login_required
def vendedor_detalhe(request, pk):
    v = get_object_or_404(Vendedor, pk=pk)
    ano, mes = _periodo(request)
    ini, fim = s.limites(ano, mes)
    st = s.stats_vendedor(v, ini, fim)
    dias, valores = s.evolucao_dias(ano, mes, v.pk)
    hist = s.historico_vendedor(v)
    chart = {"dias": dias, "valores": valores, "meta_diaria": float(st["meta_diaria"]),
             "hist_rotulos": [x["rotulo"] for x in hist],
             "hist_metas": [x["meta"] for x in hist], "hist_vendidos": [x["vendido"] for x in hist]}
    return render(request, "vendedor_detalhe.html", _ctx(ano, mes, v=v, st=st, chart=chart))


# ---------- Lançamentos ----------
@login_required
def lancamentos(request):
    q = request.GET.get("q", "").strip()
    data = _data(request.GET.get("data"))
    vid = _int(request.GET.get("vendedor"))
    qs = Venda.objects.select_related("vendedor")
    if q:
        qs = qs.filter(Q(observacao__icontains=q) | Q(vendedor__nome__icontains=q))
    if data:
        qs = qs.filter(data=data)
    if vid:
        qs = qs.filter(vendedor_id=vid)
    tot = qs.aggregate(b=Sum("valor_bruto"), a=Sum("valor_a_vista"))
    return render(request, "lancamentos.html", {
        "vendas": qs[:500], "q": q, "data": request.GET.get("data", ""), "vid": vid,
        "lista_vendedores": Vendedor.objects.all(), "tot": tot})


@login_required
def venda_form(request, pk=None):
    venda = get_object_or_404(Venda, pk=pk) if pk else None
    form = VendaForm(request.POST or None, instance=venda)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Venda salva.")
        return redirect("lancamentos")
    return render(request, "form.html", {"form": form, "titulo": "Editar venda" if pk else "Nova venda",
                                         "voltar": "lancamentos"})


@login_required
@require_POST
def venda_excluir(request, pk):
    get_object_or_404(Venda, pk=pk).delete()
    messages.success(request, "Venda excluída.")
    return redirect("lancamentos")


# ---------- Metas ----------
def _dec(txt):
    txt = (txt or "").strip().replace(",", ".")
    if not txt:
        return None
    try:
        d = Decimal(txt)
    except InvalidOperation:
        return None
    return d if d >= 0 else None


@login_required
def metas(request):
    if request.method == "POST":
        ano, mes = _int(request.POST.get("ano")), _int(request.POST.get("mes"))
        for v in Vendedor.objects.filter(ativo=True):
            mm, md = _dec(request.POST.get(f"mensal_{v.pk}")), _dec(request.POST.get(f"diaria_{v.pk}"))
            if mm is not None or md is not None:
                MetaMensal.objects.update_or_create(
                    vendedor=v, ano=ano, mes=mes,
                    defaults={"valor_meta_mensal": mm or 0, "valor_meta_diaria": md or 0})
        emp = _dec(request.POST.get("empresa"))
        if emp is not None:
            MetaEmpresa.objects.update_or_create(ano=ano, mes=mes, defaults={"valor_meta": emp})
        messages.success(request, "Metas salvas. Os demais meses permanecem no histórico.")
        return redirect(f"/metas/?ano={ano}&mes={mes}")
    ano, mes = _periodo(request)
    existentes = {m.vendedor_id: m for m in MetaMensal.objects.filter(ano=ano, mes=mes)}
    linhas = [{"v": v, "mensal": str(existentes[v.pk].valor_meta_mensal) if v.pk in existentes else "",
               "diaria": str(existentes[v.pk].valor_meta_diaria) if v.pk in existentes else ""}
              for v in Vendedor.objects.filter(ativo=True)]
    me = MetaEmpresa.objects.filter(ano=ano, mes=mes).first()
    return render(request, "metas.html", _ctx(ano, mes, linhas=linhas,
                                              empresa=str(me.valor_meta) if me else ""))


# ---------- Histórico ----------
@login_required
def historico(request):
    meses = set()
    for d in Venda.objects.dates("data", "month"):
        meses.add((d.year, d.month))
    meses |= set(MetaMensal.objects.values_list("ano", "mes"))
    meses |= set(MetaEmpresa.objects.values_list("ano", "mes"))
    meses = sorted(meses, reverse=True)
    sel = (_int(request.GET.get("ano")), _int(request.GET.get("mes")))
    if sel not in meses:
        sel = meses[0] if meses else None
    ctx = {"lista": [(a, m, f"{s.NOMES_MES[m]} {a}") for a, m in meses], "sel": sel}
    if sel:
        ano, mes = sel
        ini, fim = s.limites(ano, mes)
        ctx.update(titulo=f"{s.NOMES_MES[mes]} {ano}", empresa=s.resumo_empresa(ano, mes),
                   stats=[s.stats_vendedor(v, ini, fim) for v in s.vendedores_do_periodo(ini, fim)],
                   vendas=Venda.objects.filter(data__range=(ini, fim)).select_related("vendedor"))
    return render(request, "historico.html", ctx)


# ---------- Relatórios ----------
@login_required
def relatorios(request):
    ano, mes = _periodo(request)
    vid = _int(request.GET.get("vendedor"))
    di, df = _data(request.GET.get("data_ini")), _data(request.GET.get("data_fim"))
    ini, fim = (di, df) if di and df and di <= df else s.limites(ano, mes)
    vends = s.vendedores_do_periodo(ini, fim)
    if vid:
        vends = vends.filter(pk=vid)
    stats = [s.stats_vendedor(v, ini, fim) for v in vends]
    soma = lambda k: sum((x[k] for x in stats), Decimal("0"))
    resumo = {"bruto": soma("bruto"), "avista": soma("avista"), "qtd": sum(x["qtd"] for x in stats),
              "meta": soma("meta_mensal"), "vendido": soma("vendido"),
              "batidos": sum(x["batidos"] for x in stats), "nao_batidos": sum(x["nao_batidos"] for x in stats)}
    resumo["pct"] = s.percentual(resumo["vendido"], resumo["meta"])
    comp = None
    a2, m2 = _int(request.GET.get("ano2")), _int(request.GET.get("mes2"))
    if a2 and m2 and 1 <= m2 <= 12:
        i2, f2 = s.limites(a2, m2)
        a, b = s.totais(ini, fim, vid), s.totais(i2, f2, vid)
        comp = {"rotulo": f"{s.NOMES_MES[m2]} {a2}", "a": a, "b": b,
                "dif": {k: a[k] - b[k] for k in a},
                "var": s.percentual(a["bruto"] - b["bruto"], b["bruto"])}
    return render(request, "relatorios.html", _ctx(
        ano, mes, stats=stats, resumo=resumo, ini=ini, fim=fim, vid=vid, comp=comp,
        lista_vendedores=Vendedor.objects.all(), a2=a2, m2=m2,
        data_ini=request.GET.get("data_ini", ""), data_fim=request.GET.get("data_fim", "")))


# ---------- Acesso ao Admin (pede a senha) ----------
@login_required
def admin_acesso(request):
    erro = ""
    if request.method == "POST":
        if request.user.is_staff and request.user.check_password(request.POST.get("senha", "")):
            request.session["admin_ok"] = time.time()
            return redirect("/admin/")
        erro = "Senha incorreta ou usuário sem permissão de administrador."
    else:
        request.session.pop("admin_ok", None)
    return render(request, "admin_acesso.html", {"erro": erro})
