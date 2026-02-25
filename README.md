# Radar BLE - Escaner e Analisador de Beacons

Uma aplicação desktop desenvolvida em Python para rastreamento, visualização e análise de sinais de dispositivos Bluetooth Low Energy (BLE) em tempo real. O sistema oferece uma interface gráfica moderna e ferramentas integradas para plotagem de gráficos de força do sinal (RSSI) e exportação de dados.

## Funcionalidades Principais

* **Monitoramento em Tempo Real:** Escaneamento contínuo de dispositivos BLE próximos, exibindo Endereço MAC, Status, Nome e Potência do Sinal (RSSI).
* **Análise Visual Avançada:** Gráfico de linha dinâmico integrado (via Matplotlib) que plota o histórico de RSSI dos dispositivos selecionados na tabela.
* **Personalização de Gráficos:** Ferramenta dedicada para renomear os títulos do gráfico, eixos X e Y, além de permitir a customização dos nomes das legendas para cada dispositivo rastreado.
* **Exportação de Mídia:** Capacidade de salvar o gráfico gerado em diversos formatos profissionais, como PNG, JPEG, PDF e SVG.
* **Gestão de Dados (CSV):** Possibilidade de exportar todo o histórico de telemetria capturado para arquivos CSV, bem como importar arquivos antigos para visualização e análise offline.
* **Filtros e Organização:** Filtragem dinâmica de dispositivos visíveis com base na potência mínima do sinal (RSSI) e ordenação interativa pelas colunas da tabela.
* **Interface Moderna:** Layout responsivo dividido em painéis ajustáveis, utilizando Themed Tkinter (ttk) para uma melhor usabilidade.

## Pré-requisitos

Para executar esta aplicação, você precisará do Python 3.7 ou superior instalado em sua máquina.

Além das bibliotecas nativas do Python (como `tkinter`, `asyncio`, `threading` e `csv`), o projeto requer a instalação das seguintes dependências:

* `matplotlib` (Para a renderização e personalização dos gráficos)
* Módulo responsável pelo escaneamento BLE (geralmente `bleak`, dependendo da implementação do seu `beacon_scanner.py`).

## Instalação

1. Clone este repositório para a sua máquina local:

```bash
git clone https://github.com/seu-usuario/radar-ble-escaner.git

```

2. Navegue até o diretório do projeto:

```bash
cd radar-ble-escaner

```

3. Instale as dependências necessárias utilizando o pip:

```bash
pip install matplotlib

```

*(Nota: Certifique-se de instalar também a biblioteca utilizada no arquivo `beacon_scanner.py` para a comunicação Bluetooth).*

## Como Utilizar

Execute o arquivo principal para iniciar a aplicação:

```bash
python main_gui.py

```

### Fluxo de Uso Básico

1. **Iniciar o Escaneamento:** Clique em "Iniciar" no painel superior. A aplicação começará a listar os dispositivos BLE detectados na tabela principal.
2. **Filtrar Dispositivos:** Se houver muita poluição de dispositivos, ajuste a "Potência Mínima" no painel de filtros para ocultar sinais fracos.
3. **Visualizar Gráfico:** Selecione um ou mais dispositivos clicando nas linhas correspondentes da tabela. O gráfico inferior começará imediatamente a traçar a curva de RSSI ao longo do tempo.
4. **Personalizar Visualização:** Clique em "Personalizar" no painel inferior para abrir a janela de edição. Insira os títulos desejados e substitua os nomes genéricos por identificações reais (por exemplo, "Sensor Porta Principal").
5. **Salvar e Exportar:** Utilize o botão "Salvar" para gerar uma imagem do gráfico, ou clique em "Exportar CSV" no painel superior para guardar todos os dados brutos da sessão.

## Estrutura do Projeto

* `main_gui.py`: Contém toda a lógica da interface gráfica (Tkinter), integração com o Matplotlib, e o gerenciamento de estados da aplicação.
* `beacon_scanner.py`: Módulo responsável pela lógica assíncrona de comunicação com o hardware Bluetooth e coleta das informações dos beacons.

## Contribuição

Contribuições são bem-vindas. Sinta-se à vontade para abrir uma issue relatando bugs, sugerindo melhorias ou enviando pull requests com novas funcionalidades.

## Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo LICENSE para obter mais detalhes.
