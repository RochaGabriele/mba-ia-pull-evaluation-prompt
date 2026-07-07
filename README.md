# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Software que faz **pull** de um prompt de baixa qualidade do **LangSmith Prompt Hub**, o **refatora** com técnicas avançadas de Prompt Engineering, faz **push** da versão otimizada de volta ao Hub (público) e **avalia** a qualidade com 5 métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision), buscando **≥ 0.8 em todas**.

- **Tarefa:** converter relatos de bugs em **User Stories** acionáveis.
- **Prompt base (v1):** `leonanluppi/bug_to_user_story_v1`
- **Prompt otimizado (v2):** `{seu_username}/bug_to_user_story_v2`

---

## Técnicas Aplicadas (Fase 2)

O prompt inicial (v1) era propositalmente ruim: instruções vagas, `{bug_report}` duplicado no system e user prompt, **sem persona**, **sem exemplos** e **sem formato de saída definido**. Para otimizá-lo ([`prompts/bug_to_user_story_v2.yml`](prompts/bug_to_user_story_v2.yml)) apliquei **quatro** técnicas:

### 1. Role Prompting (definição de persona)
**Por quê:** dar ao modelo um papel especializado calibra vocabulário, foco e critério de qualidade — essencial para produzir documentação ágil no padrão esperado.
**Como apliquei:** o system prompt começa com *"Você é um **Product Manager sênior**, especialista em metodologias ágeis (Scrum) e engenharia de requisitos..."*

### 2. Few-shot Learning (obrigatório)
**Por quê:** exemplos de entrada→saída são a forma mais eficaz de ensinar **formato** e **profundidade**. Como as métricas comparam a resposta com uma referência, alinhar o formato ao ground truth eleva diretamente F1, Clarity e Precision.
**Como apliquei:** incluí **3 exemplos** cobrindo os níveis de complexidade do dataset — simples (botão do carrinho), médio (webhook, com "Contexto Técnico") e complexo (checkout com múltiplas falhas, estrutura expandida com cabeçalhos `=== ... ===`).

### 3. Chain of Thought (CoT)
**Por quê:** derivar persona, ação, benefício e critérios a partir de um bug exige raciocínio, especialmente em bugs médios/complexos.
**Como apliquei:** instruí um raciocínio passo a passo **interno** (Persona → Ação → Benefício → Critérios → Complexidade) com a diretriz de **não exibir** esse raciocínio, retornando apenas a User Story final (mantendo a resposta limpa e a Clareza alta).

### 4. Skeleton of Thought (estrutura fixa da resposta)
**Por quê:** um esqueleto previsível garante consistência e cobertura, favorecendo Clarity e Recall (F1).
**Como apliquei:** defini a ordem obrigatória da saída (User Story → Critérios de Aceitação em Gherkin → Contexto Técnico → estrutura expandida para casos complexos), com **profundidade adaptável à complexidade** do bug.

> **Edge cases e regras explícitas:** proibição de inventar dados (usar placeholders `[...]` quando faltar informação), persona específica (nunca "usuário" genérico), preservação de comportamentos esperados (validações, notificações, logs) e resposta sem preâmbulos. System prompt (persona/regras/few-shot) e User prompt (`{bug_report}`) separados adequadamente.

---

## Resultados Finais

### Tabela comparativa — v1 (ruim) vs v2 (otimizado)

| Métrica | v1 (baseline) | v2 (otimizado) | Meta |
|--------------|:-------------:|:--------------:|:----:|
| Helpfulness  | <!-- V1_HELP --> | <!-- V2_HELP --> | ≥ 0.8 |
| Correctness  | <!-- V1_CORR --> | <!-- V2_CORR --> | ≥ 0.8 |
| F1-Score     | <!-- V1_F1 -->   | <!-- V2_F1 -->   | ≥ 0.8 |
| Clarity      | <!-- V1_CLA -->  | <!-- V2_CLA -->  | ≥ 0.8 |
| Precision    | <!-- V1_PRE -->  | <!-- V2_PRE -->  | ≥ 0.8 |
| **Status**   | ❌ REPROVADO | <!-- V2_STATUS --> | — |

_(Números preenchidos após rodar `python src/evaluate.py`.)_

### Evidências no LangSmith
- **Dashboard público:** <!-- LANGSMITH_DASHBOARD_URL -->
- **Prompt v2 publicado:** <!-- LANGSMITH_PROMPT_URL -->
- **Dataset de avaliação:** 15 exemplos (5 simples, 7 médios, 3 complexos)
- **Screenshots:** ver pasta `screenshots/` (notas ≥ 0.8 e tracing de ao menos 3 exemplos)

---

## Como Executar

### Pré-requisitos
- **Python 3.12** (o `requirements.txt` fixa versões sem wheel para o Python 3.14)
- Conta no **LangSmith** com **API Key** — https://smith.langchain.com (Settings → API Keys)
- **API Key** de um provedor de LLM (OpenAI ou Google Gemini — veja `.env.example`)

### 1. Ambiente virtual e dependências
```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variáveis de ambiente
```bash
cp .env.example .env
```
Preencha no `.env`: `LANGSMITH_API_KEY`, `USERNAME_LANGSMITH_HUB` (seu handle do Hub) e as credenciais/modelos do provedor escolhido (`LLM_PROVIDER`, `LLM_MODEL`, `EVAL_MODEL`).

### 3. Pull do prompt inicial
```bash
python src/pull_prompts.py
```
Salva `leonanluppi/bug_to_user_story_v1` em `prompts/bug_to_user_story_v1.yml`.

### 4. Push do prompt otimizado (público)
```bash
python src/push_prompts.py
```
Publica `{seu_username}/bug_to_user_story_v2` no Hub, público, com metadados.

### 5. Avaliação
```bash
python src/evaluate.py
```
Cria o dataset no LangSmith, roda o v2 contra os 15 exemplos e calcula as 5 métricas.

### 6. Testes de validação
```bash
pytest tests/test_prompts.py -v
```

---

## Estrutura do projeto

```
├── .env.example
├── requirements.txt
├── README.md
├── prompts/
│   ├── bug_to_user_story_v1.yml   # baseline (pull do Hub)
│   └── bug_to_user_story_v2.yml   # otimizado (entregável)
├── datasets/
│   └── bug_to_user_story.jsonl    # 15 bugs (não alterar)
├── src/
│   ├── pull_prompts.py            # implementado
│   ├── push_prompts.py            # implementado
│   ├── evaluate.py                # pronto (não alterar)
│   ├── metrics.py                 # pronto (não alterar)
│   └── utils.py                   # pronto (não alterar)
└── tests/
    └── test_prompts.py            # 6 testes implementados
```
