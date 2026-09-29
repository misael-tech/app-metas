# Controle de Metas e Vendas Diárias (Django)

## Instalação (Linux)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations metas
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse http://127.0.0.1:8000/

## Dados de teste (opcional)

```bash
python manage.py seed   # 5 vendedores, metas ago/set 2026 e vendas; cria admin / admin123
```

## Regras

- Meta calculada sobre o **valor bruto**. Para mudar: `CAMPO_META` em `metas/services.py`.
- Metas são gravadas por vendedor/mês/ano (histórico preservado).
