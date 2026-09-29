import time

from django.shortcuts import redirect

VALIDADE = 30 * 60  # segundos


class AdminSenhaMiddleware:
    """Exige confirmação de senha (tela /admin-acesso/) para abrir o /admin/."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/") and time.time() - request.session.get("admin_ok", 0) > VALIDADE:
            return redirect("admin_acesso")
        return self.get_response(request)
