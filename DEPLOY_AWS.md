# Deploy Privado Na AWS EC2

Este guia é opcional. Para uso local, rode apenas `streamlit run app.py`.

## Premissas

- Ubuntu 22.04 LTS ou superior.
- Python 3.11.
- Security Group com SSH restrito ao seu IP.
- Porta pública preferencialmente atrás de proxy HTTPS. Evite expor Streamlit
  puro na internet quando houver dados privados.

## Instalação Manual

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git

git clone https://github.com/kleberAbreu/finance-cvm-dashboard.git
cd finance-cvm-dashboard

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para dados reais, gere os Parquets localmente no servidor:

```bash
python run_pipeline.py --inicio 2018 --fim 2025
```

## Autenticação Opcional

O app não exige login por padrão. Em deploy privado, habilite:

```bash
export CVM_DASHBOARD_AUTH=1
```

Crie `auth_config.yaml` somente no servidor, nunca no Git:

```yaml
credentials:
  usernames:
    seu_usuario:
      email: seu-email@example.com
      name: Seu Nome
      password: "$2b$12$HASH_BCRYPT_GERADO_LOCALMENTE"
cookie:
  name: cvm_dashboard_auth
  key: "CHAVE_ALEATORIA_LONGA"
  expiry_days: 7
```

Gere hash e chave no servidor:

```bash
python - <<'PY'
import bcrypt
import getpass
import secrets

password = getpass.getpass("Senha: ")
print("password hash:", bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode())
print("cookie key:", secrets.token_hex(32))
PY
```

## Rodar

```bash
source .venv/bin/activate
CVM_DASHBOARD_AUTH=1 streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Para produção, prefira configurar um serviço `systemd` e um proxy HTTPS
como Nginx ou Caddy.

## Segurança

- Não use senhas padrão.
- Não versione `auth_config.yaml`, `.env`, `secrets.toml` ou credenciais cloud.
- Restrinja SSH ao seu IP.
- Mantenha bases completas e backups fora do Git.
- Atualize dependências periodicamente.
