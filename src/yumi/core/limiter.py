from slowapi import Limiter
from slowapi.util import get_remote_address

# Instância global do rate limiter.
# Usa o IP do cliente como chave para contar as requisições.
# Importado em:
#   - main.py        → registra no app (middleware)
#   - auth_routes.py → aplica o decorator nas rotas
limiter = Limiter(key_func=get_remote_address)
