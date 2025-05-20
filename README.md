# 📊 Analisador de Partidas de Valorant

Bem-vindo ao Analisador de Partidas de Valorant! Esta é uma aplicação desenvolvida com Streamlit que permite gerar um dashboard interativo e detalhado sobre o desempenho do seu time, utilizando as suas próprias anotações de partidas.

Com este dashboard, você poderá extrair insights valiosos para otimizar os treinos, identificar pontos fortes, áreas de melhoria e tomar decisões mais estratégicas sobre mapas, lados e composições.

## ✨ Funcionalidades do Dashboard

O dashboard gerado oferece uma visão completa do desempenho do seu time, incluindo:

* **Visão Geral Global**:
    * Win Rate de Lados (CT e TR) baseados em vitórias nos *halves* da partida.
    * Win Rate de Rounds Pistol (CT e TR) do seu time.
* **Ranking de Mapas**:
    * Classificação dos mapas com base no Win Rate de partidas do seu time.
    * Identificação da melhor composição utilizada pelo seu time em cada mapa (baseado no Win Rate de partidas da composição).
* **Análise Detalhada por Mapa**:
    * Win Rate geral de partidas no mapa específico.
    * Win Rate de Lados (CT e TR) no mapa.
    * Win Rate de Pistols (CT e TR) no mapa.
    * Identificação da melhor composição do seu time para aquele mapa específico (baseado no Win Rate de partidas da composição).
    * Estatísticas de confronto direto entre as composições do seu time e as composições adversárias, mostrando o resultado da partida.
* **Exportação para PDF**:
    * Gere um relatório completo em formato PDF com todas as informações e gráficos do dashboard para análise offline ou compartilhamento.

## 🚀 Como Usar

Siga os passos abaixo para gerar e analisar o dashboard do seu time:

1.  **Obtenha a Planilha Modelo**:
    * No diretório deste projeto, você encontrará uma planilha modelo chamada `modelo_dados_partidas.xlsx` (ou similar, verifique o nome no projeto).
    * Esta planilha contém as colunas necessárias e exemplos de como preenchê-las.

2.  **Preencha com os Dados das Partidas**:
    * Abra a planilha modelo e insira os dados das partidas do seu time. É crucial que os dados sejam preenchidos corretamente, seguindo o formato dos exemplos.
    * **Colunas Principais e Formato Esperado**:
        * `Data do jogo`: Data da partida (ex: `AAAA-MM-DD` ou `DD/MM/AAAA`).
        * `Hora do jogo`: Hora da partida (ex: `HH:MM`).
        * `Time adversario`: Nome do time adversário.
        * `Mapa jogado`: Nome do mapa (ex: `Ascent`, `Bind`, `Haven`).
        * `Placar final do jogo`: Placar final da partida no formato `NOSSO_TIME-ADVERSARIO` (ex: `13-7`).
        * `Placar lado CT`: Placar do *half* em que seu time jogou de CT, no formato `NOSSO_TIME_CT-ADV_TR` (ex: `8-4`).
        * `Placar lado TR`: Placar do *half* em que seu time jogou de TR, no formato `NOSSO_TIME_TR-ADV_CT` (ex: `5-3`).
        * `Pistol CT`: Resultado do round pistol quando seu time estava de CT (`win` ou `lose`).
        * `Pistol TR`: Resultado do round pistol quando seu time estava de TR (`win` ou `lose`).
        * `Composicao`: Composição de agentes do seu time, separados por vírgula (ex: `Sova,Jett,Killjoy,Omen,Sage`).
        * `Composicao adversaria`: Composição de agentes do time adversário, separados por vírgula.

3.  **Exporte para CSV**:
    * Após preencher todos os dados, exporte a planilha para o formato **CSV (delimitado por vírgula)**. Geralmente, essa opção está disponível em "Salvar Como" ou "Exportar" no seu software de planilhas (Excel, Google Sheets, LibreOffice Calc).

4.  **Carregue o Arquivo no Aplicativo**:
    * Abra o aplicativo Analisador de Partidas de Valorant.
    * Clique no botão "Carregue seu arquivo CSV".
    * Selecione o arquivo `.csv` que você acabou de exportar.

5.  **Explore o Dashboard**:
    * Pronto! O dashboard será gerado automaticamente com base nos seus dados.
    * Navegue pelas abas "🌎 Geral" e pelas abas específicas de cada mapa (`🗺️ NomeDoMapa`) para visualizar as análises.
    * Utilize o botão "📄 Exportar Relatório para PDF" para salvar uma cópia offline dos dados.

## 🎯 Benefícios e Insights para o Seu Time

Este dashboard foi projetado para ajudar seu time a:

* 🔎 **Visualizar o desempenho**: Acompanhe de forma clara como seu time está se saindo nos treinos e partidas oficiais.
* 💡 **Gerar Insights Estratégicos**: Descubra padrões, pontos fortes e fracos que podem não ser óbvios.
* 🗺️ **Nortear os Treinos**: Utilize os dados para focar os treinos nas áreas que mais precisam de atenção:
    * Qual mapa apresenta o menor/maior Win Rate?
    * Seu time performa melhor de CT ou TR em mapas específicos?
    * Como está a conversão dos rounds pistol? Existe um lado pistol mais problemático?
    * Quais composições do seu time têm tido mais sucesso?
    * Contra quais tipos de composições adversárias seu time tem mais dificuldade?

## 🛠️ Para Desenvolvedores / Rodando Localmente (Opcional)

Se você deseja rodar este aplicativo localmente ou contribuir para o desenvolvimento:

1.  **Pré-requisitos**:
    * Python 3.7 ou superior.
    * pip (gerenciador de pacotes Python).

2.  **Clone o Repositório**:
    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
    cd seu-repositorio
    ```

3.  **Crie um Ambiente Virtual (Recomendado)**:
    ```bash
    python -m venv venv
    # No Windows
    venv\Scripts\activate
    # No macOS/Linux
    source venv/bin/activate
    ```

4.  **Instale as Dependências**:
    Crie um arquivo `requirements.txt` com o seguinte conteúdo:
    ```txt
    streamlit
    pandas
    reportlab
    # plotly (se for usar para gráficos interativos no futuro)
    ```
    E então instale:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Execute o Aplicativo Streamlit**:
    (Supondo que o nome do seu script principal seja `app.py` ou o nome do arquivo que você forneceu)
    ```bash
    streamlit run nome_do_seu_script.py
    ```
    O aplicativo deverá abrir automaticamente no seu navegador padrão.

---

Esperamos que esta ferramenta seja muito útil para o desenvolvimento e sucesso do seu time! Boa análise e bons treinos! 🎮
