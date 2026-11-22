# Bot de ofertas Shopee -> Telegram, rodando no GitHub (sem instalar nada)

## 1. Criar o repositório
1. Crie uma conta gratuita em github.com.
2. Clique em "New repository" (botão verde / sinal de +).
3. Nome: `bot-shopee`. Marque **Private** (privado). Clique em "Create repository".

## 2. Enviar os arquivos
1. Na página do repositório, clique em "uploading an existing file".
2. Arraste estes 4 arquivos: `bot_auto.py`, `shopee_api.py`, `requirements.txt`, `postados.json`.
   Clique em "Commit changes".
3. Clique em "Add file" > "Create new file".
   No campo do nome, digite exatamente: `.github/workflows/bot.yml`
   (ao digitar as barras, o GitHub cria as pastas sozinho).
4. Abra o arquivo `bot.yml` desta pasta, copie TODO o conteúdo, cole na caixa grande e
   clique em "Commit changes".

## 3. Cadastrar os segredos (suas chaves)
No repositório: Settings > Secrets and variables > Actions > "New repository secret".
Crie 4 segredos (o nome tem que ser exatamente igual):
- `SHOPEE_APP_ID`
- `SHOPEE_APP_SECRET`
- `TELEGRAM_TOKEN`  (token do @BotFather)
- `CANAL`  (ex: @seucanal)

## 4. Testar
1. Clique na aba "Actions". Se aparecer um aviso, clique para habilitar os workflows.
2. Clique em "Bot de ofertas Shopee" > "Run workflow" > escolha `ofertas` > "Run workflow".
3. Espere 1 minuto, abra a execução e veja o texto do "Rodar o bot":
   ele mostra as ofertas que achou. Se der erro, copie a mensagem e me mande.
4. Rode de novo escolhendo `teste`: uma oferta deve aparecer no seu canal.

## 5. Pronto
Depois disso ele roda sozinho, 2 vezes por hora, entre 8h e 22h (horário de Brasília),
e sorteia se posta ou não (PROBABILIDADE 0.5 = média de 1 post por hora).

## Ajustes
Edite o `bot.yml` pelo próprio site (ícone de lápis). Dá pra mudar PALAVRAS (seu nicho),
os filtros de desconto/vendas/avaliação e a PROBABILIDADE (mais perto de 1 = posta mais).

## Observações
- O plano gratuito do GitHub tem um limite de minutos por mês para repositórios
  privados. Cada rodada leva cerca de 1 minuto. Confira o limite atual no site do GitHub.
- Os horários não são exatos: o GitHub pode atrasar algumas execuções.
- Nunca coloque suas chaves dentro dos arquivos. Só nos "Secrets".
