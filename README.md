# Zara Access

Add-on para o [NVDA](https://www.nvaccess.org/) que torna o **ZaraRadio** (programa de automação de rádio) totalmente utilizável com leitor de tela. Corrige o foco nas janelas do programa, faz o Tab passar por todos os controles e traz atalhos para as informações que importam durante a operação: faixa no ar, próxima faixa, tempo restante, vinhetas, eventos, players auxiliares, volume, temperatura e umidade.

Funciona com qualquer tradução do ZaraRadio, ou com ele em inglês.

Por L-R Productions.

## Download

Baixe a versão mais recente na aba **[Releases](../../releases)** deste repositório: o arquivo `Zara-Access.nvda-addon`.

Cada Release traz nas notas o hash **SHA-256** do arquivo. Só são oficiais os arquivos publicados ali.

## Instalação

1. Se você tem instalado o add-on antigo "ZaraRadio", desinstale-o antes: os dois cuidam do mesmo programa e só um funciona.
2. Pressione Enter no arquivo `Zara-Access.nvda-addon` e confirme a instalação.
3. Reinicie o NVDA quando ele pedir.

## Requisitos

- Windows 10 ou 11.
- NVDA 2021.1 ou mais novo (testado no NVDA 2026.2).
- ZaraRadio instalado.

## Atalhos

### Janela principal

- **Tab e Shift+Tab**: passam por todos os controles, incluindo a lista de reprodução, os próximos eventos, a árvore de pastas e as caixas de modo de reprodução e de vinhetas.
- **Ctrl+Shift+L**: vai para a lista de reprodução principal.
- **Ctrl+M**: vai para a caixa de modo de reprodução.
- **Ctrl+J**: fala a faixa que está tocando.
- **Ctrl+K**: fala a próxima faixa.
- **Ctrl+Shift+T**: fala o tempo restante da faixa. Pressionado duas vezes, fala também o término da faixa e a duração total da lista.
- **Ctrl+Shift+P**: pausa.
- **Seta esquerda e seta direita**: retrocedem e avançam na faixa.
- **Alt+seta acima e Alt+seta abaixo**: aumentam e diminuem o volume, de qualquer controle da janela principal.
- **Ctrl+Shift+V**: fala as vinhetas da página ativa.
- **Alt+número**: troca a página de vinhetas.
- **F8**: abre a lista dos botões da barra de eventos.
- **F9**: abre a lista das faixas, para marcar com Espaço quais ativar.
- **Ctrl+Shift+X**: fala o estado dos players auxiliares.
- **Ctrl+P**: abre a pré-escuta e leva o foco para ela.
- **Ctrl+C e Ctrl+X na lista de reprodução**: copiam e recortam faixas, com aviso falado.
- **E**: fala a temperatura. Pressionado duas vezes, toca a locução da temperatura.
- **U**: fala a umidade. Pressionado duas vezes, toca a locução da umidade.
- **Tecla Aplicações**: abre o menu de opções nas listas e na árvore de pastas.

Na árvore de pastas, digitar uma letra leva ao próximo item que começa com ela, como em qualquer árvore do Windows.

### Players auxiliares

- **Ctrl+Tab e Ctrl+Shift+Tab**: alternam entre a lista principal, os players auxiliares e a janela Encontrar em pastas.
- **P**: toca. **S**: para. **B**: para depois da faixa atual. **N**: próxima faixa.
- **Ctrl+Shift+P**: pausa.
- **Seta esquerda e seta direita**: retrocedem e avançam na faixa.
- **Ctrl+N, Ctrl+O, Ctrl+S, Ctrl+Shift+S**: novo, abrir, salvar e salvar como.
- **Ctrl+Shift+A**: adiciona faixa.
- **Esc**: volta para a lista principal sem desativar o player.

### Encontrar em pastas

- **Ctrl+C nos resultados**: copia o caminho dos arquivos selecionados, para colar na lista de reprodução ou num player auxiliar.
- **Esc**: fecha a janela.

### Programação de eventos

- O foco entra direto no grupo de periodicidade, e as setas navegam pelas opções sem perder o foco.
- **Espaço em "Outras horas"**: abre a janela de horários.
- No grupo de tipos de eventos, as setas trocam o tipo e o Tab passa pelos campos dele.

## Licença

Veja [LICENSE](LICENSE).
