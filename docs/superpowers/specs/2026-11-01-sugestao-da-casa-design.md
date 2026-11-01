# Sugestão da Casa: design

Data: 2026-11-01
Status: rascunho para aprovação
Nome do projeto: Sugestão da Casa (provisório)

## 1. Intenção e o porquê

Projeto de portfólio do Mateus.

**A dor.** A pessoa está com fome e sabe mais ou menos o que quer ("algo quentinho, não muito pesado, barato"), mas os apps de delivery só filtram por categoria, preço e tempo de entrega. Não existe filtro para "reconfortante", "leve", "pra comer vendo série" ou "sem lactose, mas que não seja salada triste". Ela rola a tela, rola e não decide.

**A solução.** Um agente que traduz essa vontade vaga em uma decisão. A pessoa escreve do jeito dela. O agente entende as restrições duras (orçamento, tempo, alergias e restrições alimentares) e as subjetivas (sensação, peso, ocasião), consulta um cardápio fictício por meio de ferramentas (tool calling) e devolve **uma escolha confiante**, com duas alternativas e uma explicação humana do porquê.

**O que o recrutador precisa sentir** (palavras do Mateus):
- que ele resolveu uma dor real de uma pessoa e pode agregar valor à empresa;
- que o visual é extremamente bonito e de bom gosto, e que ele capricha;
- que nunca viu uma solução assim, e que o Mateus é único e memorável.

## 2. Objetivos

1. O recrutador abre um link público e usa o agente na hora, como um usuário comum, sem cadastro, instalação ou vídeo.
2. Em poucos segundos, a partir de uma frase vaga, o agente entrega uma sugestão principal e duas alternativas, todas respeitando as restrições duras.
3. Cada sugestão vem com uma explicação curta e humana ligando o prato ao que a pessoa descreveu.
4. A pessoa vê o que o agente entendeu (etiquetas como "quentinho", "leve", "até R$ 40", "sem lactose") e pode refinar ("mais barato", "algo menos gorduroso"), e a sugestão muda.
5. "Quero esse" leva a um carrinho e uma confirmação simulados, fechando o fluxo.
6. O visual segue a direção A3 · Cozinha aberta (seção 6).

## 3. Fora do escopo (não objetivos)

- Pedido em grupo, em que várias pessoas opinam e o agente acha a média. Fica como "próximos passos" no README.
- Pagamento real, contas de usuário, login, histórico de pedidos.
- Restaurantes e cardápios reais, ou integração com apps de delivery.
- Entrada por voz (pode ser um próximo passo).

## 4. Antiobjetivos (fracasso mesmo que funcione)

Palavras do Mateus: seria vergonhoso se o site **travasse**, fosse **muito lento**, fosse **difícil de entender** ou tivesse **animações bugadas**. Isso vira regra:

- **Nunca travar:** qualquer falha do modelo (timeout, cota esgotada, resposta malformada, ferramenta com erro) cai em um caminho elegante. A tela nunca fica quebrada, vazia ou com erro técnico.
- **Rápido:** retorno visual imediato ao enviar (estado de "pensando" animado, em menos de 100 ms). A sugestão final deve chegar em poucos segundos no site público. Meta de referência: até ~5 s no caso típico.
- **Entendível sem explicação:** a primeira tela deixa óbvio o que fazer, com um exemplo clicável de frase.
- **Animações sem engasgo:** suaves, sem pulos de layout, e respeitando `prefers-reduced-motion`.
- Também é fracasso se o agente sugerir algo que **viola uma restrição dura** (por exemplo, prato com lactose para quem pediu sem lactose, ou acima do orçamento).
- Também é fracasso se parecer um template genérico de IA.

## 5. Restrições

- **Custo zero.** Nada pago. Modelos locais no desenvolvimento.
- **IA no desenvolvimento:** Ollama, com um modelo aberto que suporte tool calling (Qwen 3 ou Llama 3.x).
- **IA no site público:** a cota gratuita de um provedor com tool calling (candidatos: Groq, Cloudflare Workers AI, Google Gemini). *Decisão do Claude:* o requisito é custo zero, não modelo aberto, então um modelo fechado com cota grátis (como o Gemini) também vale. Escolher pelo que tiver tool calling mais confiável e menor latência, depois de confirmar as condições atuais da cota grátis, sem cartão de crédito, durante o plano.
- **O código não depende do provedor:** uma camada única de "cliente de LLM", e trocar Ollama pela API é configuração (variáveis de ambiente), não reescrita.
- **Modo demonstração (rede de segurança):** se a API falhar ou a cota acabar, o app cai em sugestões pré-calculadas para as frases mais comuns e de exemplo, e avisa com elegância que está em modo demonstração.
- **Stack decidida:** FastAPI (backend e agente), Postgres via Supabase (cardápio), Next.js (frontend).
- **Hospedagem grátis:** frontend na Vercel; banco no plano gratuito do Supabase; FastAPI em um host com plano gratuito (Render ou similar, a definir no plano). Atenção: planos gratuitos que "dormem" podem gerar lentidão na primeira requisição, e isso conflita com o antiobjetivo "lento". O plano deve tratar isso.
- **Regras do fluxo do Mateus:** toda tabela com RLS; mudanças de schema via migration; TDD na lógica de negócio (filtros, restrições, ranking); GSAP para animações, com reduced motion; skill impeccable para o frontend; testes e build rodando antes de dizer que terminou; screenshots em desktop e mobile.

## 6. Decisões de experiência e visual (tomadas pelo Mateus)

**Direção visual: A3 · Cozinha aberta** (escolhida entre as propostas mostradas).
- Linha "cardápio editorial": fundo de papel creme, fonte serifada elegante nos títulos (no mockup, Fraunces) e sans legível no texto (no mockup, Inter).
- Cores da comida para abrir o apetite: páprica e tomate (vermelho-alaranjado) como cor principal, açafrão como destaque, manjericão (verde) para etiquetas positivas como "sem lactose".
- Topo da tela de resultado em bloco quente (gradiente páprica para tomate) com o prato sugerido em destaque e a frase de decisão ("Hoje pede um caldo verde.").
- Cartão branco sobreposto com nome, preço, explicação curta, etiquetas (restrições, tempo) e botão "Quero esse".
- Abaixo: "Ou, se preferir", com duas alternativas compactas mostrando o que as diferencia ("mais salgadinho", "um toque de picância").
- Etiquetas discretas com o que o agente entendeu da frase.

**Fluxo:**
1. Tela inicial com convite para escrever a vontade, mais um ou dois exemplos clicáveis.
2. Estado "pensando" imediato e animado.
3. Resultado: decisão, duas alternativas e etiquetas do que foi entendido.
4. Refinamento em linguagem natural ("mais barato"), que atualiza o resultado.
5. "Quero esse" leva ao carrinho simulado e à confirmação.

**O agente decide por você.** A sugestão principal é apresentada com confiança, e não como uma lista de resultados de busca.

## 7. Agente e dados (direção)

- O agente usa ferramentas para consultar o cardápio (por exemplo: buscar pratos por restrições, obter detalhes de um prato). **As restrições duras são aplicadas por código determinístico**, nunca só confiando no modelo: o modelo interpreta a frase em critérios estruturados, a busca filtra no banco e uma validação final garante que nada que viole restrição dura chegue à tela.
- **Restrições duras x preferências** (*decisão do Claude*):
  - Duras (nunca violadas): alergias e restrições alimentares (sem lactose, sem glúten, vegetariano, vegano etc.); ingrediente excluído explicitamente ("sem cebola"); orçamento com valor ("até R$ 40", comparado com o preço do prato mais a taxa de entrega); tempo com valor ("em 30 min").
  - Preferências (influenciam o ranking, não eliminam): termos vagos como "barato", "rápido", "não muito picante", "leve".
- **Quando nada passa nas restrições duras** (decidido pelo Mateus): o agente é honesto e oferece uma saída concreta, por exemplo: "Com tudo isso junto não achei nada, mas se subir para R$ 22 tem um bowl de grão-de-bico perfeito." Ele só sugere afrouxar orçamento ou tempo, nunca alergias, dietas ou ingredientes excluídos, e sempre diz claramente o que mudaria. Nunca afrouxa nada sozinho. Se passarem só um ou dois pratos, mostra só esses. Isso pede um estado de tela próprio, com o mesmo capricho visual, e testes específicos.
- **Refinamento acumula contexto** (*decisão do Claude*): "mais barato" depois de "quentinho, sem lactose" mantém as restrições anteriores e é relativo à sugestão atual. As etiquetas do que foi entendido podem ser removidas com um clique, além do refinamento por texto. A API recebe o estado atual dos critérios a cada pedido (o frontend guarda a sessão, sem login).
- Atributos subjetivos (quentinho/fresco, leve/pesado, reconfortante, picância etc.) ficam registrados nos pratos do cardápio fictício para o agente poder casar a vontade com o prato.
- Cardápio fictício e realista: vários restaurantes e categorias, pratos com preço, tempo de entrega, ingredientes, alergênicos/restrições e atributos subjetivos. Precisa ter variedade suficiente para frases bem diferentes darem respostas diferentes e críveis.
- Fotos: no app final, fotos reais de comida de banco gratuito com licença livre (como Unsplash), no lugar das ilustrações do mockup.

## 8. Prazo

Nenhum prazo informado. *Decisão do Claude:* ir direto para a versão caprichada, mas organizar o plano em etapas que deixem o projeto publicável cedo (deploy feito nas primeiras etapas, não só no fim), para não descobrir problemas de hospedagem ou latência tarde demais.

## 9. Decisões que ficam com quem construir

Ficam a cargo de quem construir, respeitando tudo acima:
- Modelo exato no Ollama e provedor/modelo exato da cota gratuita (após verificar condições atuais).
- Schema do banco, formato das ferramentas do agente e o prompt.
- Tamanho e conteúdo do cardápio fictício.
- Lógica de ranking entre os pratos que passam nos filtros.
- Como montar e quando acionar o modo demonstração.
- Detalhes finos de tipografia, espaçamento, ícones e animações dentro da direção A3.
- Host do FastAPI e a estratégia contra a lentidão de "acordar" o servidor gratuito.

## 10. Próximos passos para o README

- Pedido em grupo (várias pessoas, uma decisão).
- Entrada por voz.
- Avaliação sistemática do agente (dataset de frases e métricas de acerto das restrições).
