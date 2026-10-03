# 🚀 Guia de Deploy — Dashboard CVM no AWS EC2

> **Tempo estimado:** 30–40 minutos
> **Custo estimado:** ~$8–15/mês (instância t3.micro)
> **Pré-requisito:** Conta AWS ativa com acesso ao Console

---

## PARTE 1 — Criar o Servidor EC2

### Passo 1 — Acessar o Console EC2

1. Entre em [https://console.aws.amazon.com](https://console.aws.amazon.com) e faça login
2. No campo de busca no topo, digite **EC2** e clique no serviço
3. Confirme a região no canto superior direito. Escolha **South America (São Paulo) — sa-east-1** para menor latência
4. Clique no botão laranja **"Launch instance"**

---

### Passo 2 — Configurar a Instância

**Name and tags**
- Name: `cvm-dashboard`

**Application and OS Images (AMI)**
- Clique em **"Ubuntu"**
- Selecione **Ubuntu Server 22.04 LTS (HVM)** — versão gratuita no Free Tier
- Architecture: **64-bit (x86)**

**Instance type**
- Selecione **t3.micro** (~$8/mês) ou **t2.micro** (elegível ao Free Tier se sua conta tiver menos de 12 meses)

**Key pair (login)**
> Você vai precisar dessa chave para se conectar ao servidor via SSH.

- Clique em **"Create new key pair"**
- Key pair name: `cvm-dashboard-key`
- Key pair type: **RSA**
- Private key file format: **.pem** (Mac/Linux) ou **.ppk** (Windows com PuTTY)
- Clique **"Create key pair"** — o arquivo será baixado automaticamente. **Guarde-o bem, não é possível recuperar!**

**Network settings** — clique em **"Edit"**
- VPC: deixe o padrão
- Subnet: deixe o padrão
- Auto-assign public IP: **Enable**

Em **Firewall (security groups)**:
- Selecione **"Create security group"**
- Security group name: `cvm-dashboard-sg`

Adicione as seguintes regras de entrada clicando em "Add security group rule":

| Type       | Protocol | Port | Source    | Descrição          |
|------------|----------|------|-----------|--------------------|
| SSH        | TCP      | 22   | My IP     | Acesso SSH (você)  |
| Custom TCP | TCP      | 8501 | 0.0.0.0/0 | Dashboard Streamlit|

**Configure storage**
- 20 GiB, gp3 (suficiente para o projeto)

**Summary** — clique em **"Launch instance"**

Aguarde ~1 minuto até o status mudar para **"Running"**.

---

### Passo 3 — Obter o IP Público

1. No painel EC2, clique em **"Instances"** no menu lateral
2. Clique na instância `cvm-dashboard`
3. Copie o **"Public IPv4 address"** (ex: `3.95.12.48`)
   - Guarde esse IP — você vai usar para acessar o dashboard

> ⚠️ O IP muda toda vez que a instância for reiniciada. Para um IP fixo, aloque um **Elastic IP** (gratuito enquanto associado a uma instância rodando).

---

## PARTE 2 — Conectar ao Servidor

### Passo 4 — Conectar via SSH

**No Mac ou Linux**, abra o Terminal:

```bash
# Ajusta as permissões da chave (obrigatório)
chmod 400 ~/Downloads/cvm-dashboard-key.pem

# Conecta ao servidor (substitua SEU_IP pelo IP copiado)
ssh -i ~/Downloads/cvm-dashboard-key.pem ubuntu@SEU_IP
```

**No Windows**, use o [Windows Terminal](https://apps.microsoft.com/detail/9N0DX20HK701) ou instale o [Git Bash](https://gitforwindows.org/) e rode o mesmo comando acima.

Quando aparecer a pergunta `Are you sure you want to continue connecting?`, digite `yes` e Enter.

Você verá o prompt do servidor: `ubuntu@ip-xxx-xxx-xxx-xxx:~$` — isso significa que funcionou! ✅

---

## PARTE 3 — Enviar os Arquivos do Projeto

### Passo 5 — Enviar a pasta do projeto para o servidor

**Abra um novo terminal** (deixe o SSH aberto no outro) e rode:

```bash
# Substitua:
# - ~/Documents/project-finance-cvm  →  pelo caminho real da pasta no seu Mac
# - SEU_IP  →  pelo IP público da instância

scp -i ~/Downloads/cvm-dashboard-key.pem -r \
  ~/Documents/project-finance-cvm \
  ubuntu@SEU_IP:/home/ubuntu/cvm-dashboard
```

> O upload pode levar alguns minutos dependendo da sua conexão (o projeto tem ~12 MB).

---

## PARTE 4 — Configurar e Rodar o App

### Passo 6 — Rodar o script de setup automático

No terminal SSH (o que está conectado ao servidor):

```bash
cd /home/ubuntu/cvm-dashboard
bash deploy_setup.sh
```

O script vai:
- Atualizar o sistema
- Instalar Python 3 e pip
- Criar um ambiente virtual
- Instalar todas as dependências do `requirements.txt`
- Configurar o app para iniciar automaticamente como um serviço do sistema

Ao final, você verá seu IP e a URL de acesso.

---

### Passo 7 — Acessar o Dashboard

Abra o navegador e acesse:

```
http://SEU_IP:8501
```

Você verá a **tela de login**. Configure seu próprio usuário em
`auth_config.yaml`, a partir de `auth_config.example.yaml`, antes de iniciar o
serviço. O repositório não fornece credenciais padrão; siga a seção abaixo para
gerar um hash de senha e uma chave de cookie próprios.

---

## PARTE 5 — Personalizar Usuários e Senha

### Passo 8 — Criar usuários e senhas personalizados

No servidor, gere o hash da sua nova senha:

```bash
cd /home/ubuntu/cvm-dashboard
source venv/bin/activate

# A senha é solicitada sem eco e não fica no histórico do terminal
python3 -c "import bcrypt,getpass; print(bcrypt.hashpw(getpass.getpass('Senha: ').encode(), bcrypt.gensalt()).decode())"
```

Copie o hash gerado (começa com `$2b$12$...`).

Edite o arquivo de configuração de usuários:

```bash
nano auth_config.yaml
```

- Substitua o valor de `password:` pelo novo hash
- Altere o `email:` e `name:` conforme desejado
- **Troque também o `key:`** por uma string aleatória:

```bash
# Gera uma chave secreta aleatória
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Salve com `Ctrl+O`, Enter, `Ctrl+X`.

Reinicie o app para aplicar as mudanças:

```bash
sudo systemctl restart cvm-dashboard
```

---

## PARTE 6 — Comandos Úteis no Servidor

```bash
# Ver se o app está rodando
sudo systemctl status cvm-dashboard

# Ver logs em tempo real (útil para debugar erros)
sudo journalctl -u cvm-dashboard -f

# Reiniciar o app
sudo systemctl restart cvm-dashboard

# Parar o app
sudo systemctl stop cvm-dashboard

# Iniciar o app
sudo systemctl start cvm-dashboard

# Atualizar os arquivos do projeto (rodado localmente, no seu Mac)
scp -i ~/Downloads/cvm-dashboard-key.pem -r \
  ~/Documents/project-finance-cvm \
  ubuntu@SEU_IP:/home/ubuntu/cvm-dashboard
```

---

## PARTE 7 — Dicas Opcionais

### IP Fixo (Elastic IP) — recomendado

Por padrão, o IP da instância muda quando ela é reiniciada. Para ter um IP permanente:

1. No Console AWS, vá em **EC2 → Elastic IPs**
2. Clique em **"Allocate Elastic IP address"** → **Allocate**
3. Selecione o IP criado, clique em **Actions → Associate Elastic IP address**
4. Selecione sua instância `cvm-dashboard` → **Associate**

O IP alocado agora é fixo. Use-o para acessar o dashboard. **É gratuito enquanto associado a uma instância em execução.**

### Economizar dinheiro fora do horário de uso

Se não precisar do dashboard 24h, você pode parar a instância quando não usar:

1. No Console EC2, selecione a instância
2. **Instance State → Stop instance**
3. Para usar novamente: **Instance State → Start instance**

> Com IP Elastic, o IP não muda mesmo parando e iniciando.

### Aumentar segurança da porta SSH

Edite o Security Group e mude a regra de SSH de `0.0.0.0/0` para **"My IP"** — assim só você consegue acessar via SSH.

---

## Resumo dos Arquivos Criados

| Arquivo | Função |
|---|---|
| `app.py` | App principal com tela de login integrada |
| `auth_config.yaml` | Usuários, senhas (hashed) e configuração de cookie |
| `requirements.txt` | Dependências Python (inclui streamlit-authenticator) |
| `deploy_setup.sh` | Script automático de instalação no servidor |
| `cvm-dashboard.service` | Serviço systemd para rodar o app em background |

---

*Guia gerado para o projeto Dashboard CVM — março/2026*
