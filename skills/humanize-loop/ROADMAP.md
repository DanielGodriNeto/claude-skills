# humanize-loop: plano de melhoria

Status em 2026-10-14. Rascunho local; não está commitado.

## Resultado da execução (2026-10-14)

| Fase | Status | Resultado |
|---|---|---|
| F1 harness | **feito** | Fica em `~/tools/humanize-calib/`: `scores.csv` (59 textos com nota), `eval.py`, `lmscore.py`, `para.py`, `one.py`. Reproduz a tabela abaixo. |
| F2 previsibilidade | **feito (pt)** | Log-prob média no Qwen3-0.6B-Base: AUC **0,99 em pt** (45 textos) e **0,60 em en** (12). Fast-DetectGPT 0,54, Binoculars 0,50, variância de surpresa invertida. O `predict.py` substitui o `binoculars.py`. Regra pt: documento ≤ −2,50 e nenhum parágrafo > −2,30. Aprova 11/13 bons e rejeita os 2 ruins (ajustada na própria amostra). |
| F3 reescrita guiada | **falhou em en** | A paráfrase com Qwen3-8B piorou tudo: pt7 foi de 27% a 73%, en de 64–83% a 75–92%. Reestruturar só levou en1 de 79% a 64%. O único 20,9% não se repetiu. Humano em inglês dá 0% (Jerome, Paul Graham), então o problema é do texto gerado pelo Claude, não da língua. |
| F4 SlopTotal | **testado, descartado** | Instalado após revisão de segurança (sem `trust_remote_code`, sem `exec`, sem telemetria). Contra o ZeroGPT >10%: AUC pt 0,71 (log-prob 0,99), en 0,75 (log-prob 0,60). Discorda muito do ZeroGPT: deu 86–98 em 6 textos pt que o ZeroGPT marcou 0%, e 15–27 em textos en que o ZeroGPT marcou 64–79%. Não prevê o ZeroGPT e não entra na skill. Ocupa ~9,4 GB (venv + modelos). |
| F5 padrões extras | **pulado** | Entre os textos com 0 flags, nenhuma feature de estilo separa os detectados (AUC 0,27–0,69). Padrões a mais não resolvem o que falta. |

Achados novos:

- O ZeroGPT tem ruído: o mesmo texto deu 79,2% e 86,2%.
- Em inglês ele destaca quase todas as frases de texto escrito pelo Claude, mesmo reescrito.
- Próximo passo para o inglês, se valer a pena: F4, ou testar paráfrase com modelo maior e de outra família (Llama, Mistral).

## Onde estamos (medido)

| Conjunto | Textos com 0 flags | ZeroGPT ≤10% |
|---|---|---|
| Calibração pt-BR (32 textos) | 3 | 3/3 |
| Held-out pt-BR curto | 9 | 8/9 (acadêmico: 27%) |
| Held-out es | 1 | 1/1 |
| Held-out pt-BR longo (1000 palavras) | 1 | 0/1 (14,5%; trechos destacados no começo) |
| Held-out en | 3 | **0/3 (64–83%)** |

Conclusões:

- **O lint mede só o estilo.** Os textos que falharam têm ritmo igual ou "mais humano" que os que passaram. O que o ZeroGPT pega e o lint não vê é a **previsibilidade** do texto (perplexidade).
- **O lint por seção funciona,** mas no mix_ptlong o lint global também pegou o trecho de IA. O ganho dele aparece em documentos maiores que esse.
- **Limites da literatura:**
  - Nenhum detector é confiável contra reescrita (Sadasivan 2303.11156).
  - Os detectores punem texto formal e de quem não é nativo (Liang 2304.02819).
  - Não há benchmark público de robustez em português.

## Ativo novo: corpus rotulado

Temos 47 textos (pt, es, en; IA, humano e humanizado) com nota do ZeroGPT e com as frases que ele destacou. É o primeiro conjunto de treino e teste próprio, e as fases abaixo dependem dele.

## Fases

Ordem recomendada: F1 → F2 → F3 → F4 → F5. Viabilidade é a chance de entregar o ganho esperado. Risco é o de segurança ou dados.

### F1. Harness de calibração reproduzível (pequeno)

- **O quê:**
  - `calib/` local, fora do repo público. A Wikipédia é CC BY-SA, a licença do Essay-BR não foi verificada e há nomes fictícios.
  - `scores.csv` + `eval.py`: mede a precisão de "0 flags ⇒ ≤10%" e a AUC de cada feature, com leave-one-out.
  - Roteiro do browser para colar em lote no ZeroGPT (o JS já existe nesta sessão).
- **Gate:** `eval.py` reproduz os números da tabela acima.
- **Viabilidade:** 95%. **Risco:** 5%. **Esforço:** 1 sessão curta.

### F2. Sinal local de previsibilidade (maior ganho esperado)

- **O quê:**
  - Reaproveitar o `aidetect-venv` e o Qwen3 que já estão instalados.
  - Implementar dois sinais:
    - Fast-DetectGPT (2310.05130), com curvatura de probabilidade condicional usando um modelo só;
    - variância de surpresa no estilo DivEye (2509.18880), só a ideia, porque a licença do código não é clara.
  - Pontuar também por seção.
  - Testar Qwen3-1.7B/4B se o 0.6B não separar.
- **Calibração:** treinar o limiar no corpus da F1 para prever "ZeroGPT >10%". Principal alvo: os 3 textos em inglês e o pt7.
- **Gate:** em leave-one-out, nenhum texto aprovado (0 flags + sinal OK) acima de 10%, rejeitando no máximo 30% dos textos bons.
- **Viabilidade:** 55–65%. O Binoculars 0.6B já falhou no Claude, então pode ser preciso modelo maior (CPU lento: ~1 min por página com 4B, estimativa).
- **Risco:** 10% (download de pesos do Hugging Face oficial).

### F3. Reescrita guiada por detector

- **O quê:**
  - Para cada parágrafo marcado, gerar 2–3 versões e ficar com a de menor sinal da F2 que mantenha o sentido.
  - Base: Cheng 2506.07001 (reescrita guiada derrubou o TPR@1%FPR em 64–99%) e DIPPER 2303.13408.
  - Adicionar o auto-teste Raidar (2401.12970): pedir uma reescrita ao modelo e medir quanto mudou; texto de IA muda menos.
- **Gate:** os 3 textos em inglês do held-out abaixo de 10% no ZeroGPT sem mudar fatos (checagem de sentido manual).
- **Viabilidade:** 60% (depende da F2). **Risco:** 5%. **Custo:** mais tokens por rodada (cerca de 2–3× na fase de reescrita).

### F4. SlopTotal como backend local opcional (avaliar antes)

- **O quê:**
  - SlopTotal: MIT, ativo, CPU com 4–8 GB, diz suportar PT e ES, AUC própria de 0,942, pega ~metade do texto humanizado.
  - Instalar num venv isolado e rodar no corpus da F1.
- **Antes de instalar:** gate de segurança (ler dependências e scripts, procurar chamadas de rede, conferir a licença de cada peso). Pede sua aprovação.
- **Gate:** supera a F2 no corpus. Senão, descartar.
- **Viabilidade:** 50%: projeto de 7 meses, benchmark feito pelo próprio autor, sem números para Claude.
- **Risco:** 25% (dependência de terceiros e download de modelos).

### F5. Lint: padrões extras (barato, ganho baixo)

- **O quê:**
  - Padrões do Wikipedia "Signs of AI writing" por língua: regra de três, "não só X, mas Y", "serve como" no lugar de "é", fecho de "importância", atribuição vaga.
  - MTLD (diversidade lexical) em stdlib.
  - Lista de frases versionada por língua (o vocabulário muda com o tempo: Kobak 2406.07016).
- **Gate:** a AUC no corpus sobe sem quebrar a precisão de 0 flags.
- **Viabilidade:** 90%. **Ganho:** heurísticas sozinhas ficam em AUC 0,52–0,84 (dados do SlopTotal). **Risco:** 0%.

## Fora do escopo

- **Bypass de detector comercial pago** (Turnitin, GPTZero): sem acesso legítimo para calibrar.
- **Chamar a API do ZeroGPT direto:** é produto pago, então segue pela UI e só com opt-in.
- **Garantia de 0%:** a literatura mostra que não existe.

## Riscos abertos

- Se o ZeroGPT trocar de modelo, toda a calibração precisa ser refeita.
- O corpus é pequeno (47 textos), o que dá intervalos de confiança largos.
- Os textos humanizados foram escritos por modelos Claude e não cobrem GPT nem Gemini.
