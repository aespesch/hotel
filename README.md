# Sistema de Confirmação de Presença para Festas 🎉

Um sistema web completo para gerenciar confirmações de presença e pagamentos para eventos, desenvolvido com Python e Streamlit.

## Visão Geral

Este sistema permite que convidados confirmem sua presença em eventos, informem quantos acompanhantes levarão, e realizem o pagamento via PIX de forma automatizada. Foi desenvolvido pensando na praticidade tanto para organizadores quanto para convidados.

## Funcionalidades Principais

- **Verificação de Convidados**: Sistema valida se a pessoa está na lista de convidados. A validação é feita comparando o nome digitado pelo usuário com o campo full_name do arquivo participants.csv. A comparação é feita de modo que maiúsculas, minúsculas, acentos e espaços em branco não façam diferença. Ou seja: " jose da  silva" e "José    da   Silva" são iguais.
- **Formulário Dinâmico**: Coleta informações sobre acompanhantes por faixa etária
- **Cálculo Automático**: Calcula o valor total baseado nas configurações de preço
- **Pagamento PIX**: Gera QR Code para pagamento instantâneo
- **Registro de Confirmações**: Salva todas as confirmações para controle do organizador no arquivo ./data/confirations.csv com os seguintes campos: confirmation_id,timestamp,participant_name,participant_id,participant_email,guests_under_5,guests_5_to_12,guests_above_12,total_amount,payment_status
- **Painel Administrativo**: Visualização de estatísticas e confirmações (opcional)

## Tecnologias Utilizadas

- **Python 3.12.7**: Linguagem principal
- **Streamlit**: Framework para criar a interface web
- **Pandas**: Manipulação de dados e CSV
- **QRCode**: Geração de códigos QR para pagamento
- **Python-dotenv**: Gerenciamento seguro de variáveis de ambiente

## Estrutura do Projeto

```
party-registration-system/
│
├── app.py                    # Aplicação principal
├── config.py                 # Configurações centralizadas
├── requirements.txt          # Dependências do projeto
├── .gitignore               # Arquivos ignorados pelo Git
├── README.md                # Este arquivo
│
├── data/                    # Dados do sistema
│   ├── participants.csv     # Lista de convidados
│   └── confirmations/       # Pasta para salvar confirmações
│
└── utils/                   # Utilitários (futuras expansões)
    └── __init__.py
```


## Instalação e Configuração Local

### Pré-requisitos

- Python 3.12 ou superior instalado
- Git instalado
- Conta no GitHub
- Conta no Streamlit Cloud

### Passo a Passo

1. **Clone o repositório**
   ```bash
   git clone https://github.com/aespesch/party-registration-system.git
   cd party-registration-system
   ```

2. **Crie um ambiente virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # No Windows:
   venv\Scripts\activate
   
   # No Mac/Linux:
   source venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**
   
   Crie um arquivo `.env` na raiz do projeto:
   ```
   PIX_KEY=sua_chave_pix_real@email.com
   PIX_MERCHANT_NAME=Seu Nome
   PIX_CITY=Sua Cidade
   ADMIN_PASSWORD=senha_segura_aqui
   ```

5. **Prepare os dados dos convidados**
   
   Edite o arquivo `data/participants.csv` com os dados reais dos seus convidados.

6. **Execute localmente**
   ```bash
   streamlit run app.py
   ```

## Deploy no Streamlit Cloud

1. **Faça commit e push do seu código**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Configure no Streamlit Cloud**
   - Acesse [share.streamlit.io](https://share.streamlit.io)
   - Clique em "New app"
   - Selecione seu repositório
   - Branch: main
   - Main file path: app.py

3. **Configure os Secrets**
   
   No Streamlit Cloud, vá em Settings > Secrets e adicione:
   ```toml
   PIX_KEY = "sua_chave_pix_real@email.com"
   PIX_MERCHANT_NAME = "Seu Nome"
   PIX_CITY = "Sua Cidade"
   ADMIN_PASSWORD = "senha_segura_aqui"
   ```

## Configuração e Personalização

### Modificando Preços

Edite o arquivo `config.py`:
```python
PRICING = {
    "under_5": 0,      # Gratuito para menores de 5
    "5_to_12": 25,     # Meia entrada para 5-12 anos
    "above_12": 50     # Inteira para maiores de 12
}
```

### Personalizando Mensagens

No arquivo `config.py`, modifique o dicionário `MESSAGES` para alterar os textos exibidos aos usuários.

### Alterando Informações do Evento

Modifique as variáveis no início do `config.py`:
```python
EVENT_NAME = "Nome do Seu Evento"
EVENT_DATE = "Data do Evento"
EVENT_LOCATION = "Local do Evento"
```

## Segurança

- **Nunca commite** o arquivo `.env` com suas chaves reais
- Use senhas fortes para o painel administrativo
- Mantenha o arquivo `participants.csv` atualizado
- Faça backup regular do arquivo de confirmações

## Próximos Passos e Melhorias

- [ ] Integração com API de pagamento para validação automática
- [ ] Envio de e-mail de confirmação
- [ ] Exportação de relatórios em PDF
- [ ] Sistema de autenticação mais robusto
- [ ] Integração com Google Sheets
- [ ] Dashboard administrativo mais completo

## Solução de Problemas

### Erro ao carregar participantes
- Verifique se o arquivo `data/participants.csv` existe
- Confirme que o CSV tem todas as colunas necessárias
- Verifique a codificação do arquivo (deve ser UTF-8)

### QR Code não funciona
- Certifique-se de usar uma chave PIX válida
- Para produção, implemente a geração correta do payload PIX

### Aplicação não inicia
- Confirme que todas as dependências foram instaladas
- Verifique se está usando Python 3.12 ou superior

## Contribuindo

Sinta-se à vontade para abrir issues ou enviar pull requests com melhorias!

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Contato

Para dúvidas ou sugestões sobre o sistema, entre em contato através do e-mail configurado no sistema.

---

Desenvolvido com ❤️ usando Python e Streamlit
