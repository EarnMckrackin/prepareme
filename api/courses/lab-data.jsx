/* ============================================================
   LAB-DATA.JSX — Module A: Fine-Tuning the Model
   All course content as data. The engine renders it generically.
   ============================================================ */

const MODULE_A = {
  id: 'fine-tuning',
  title: 'Fine-Tuning the Model',
  series: 'Advanced RAG & Agentic Systems',
  level: 2,
  moduleLabel: 'A',
  description: 'When does improving the model itself beat improving what you feed it? Learn LoRA, quantization, and the ROI framework to decide.',
  tags: ['fine-tuning', 'lora', 'qlora', 'quantization', 'evaluation', 'llm'],
  stages: [
    // ── STAGE 1 ──────────────────────────────────────────────
    {
      id: 's1-decision',
      title: 'The Decision',
      subtitle: 'Fine-tune or retrieve?',
      icon: '⚖',
      why: 'You built a RAG system. It answers questions, but the answers feel generic — right information, wrong voice. You have two levers: improve what you feed the model (retrieval), or improve the model itself (fine-tuning). Pulling the wrong lever wastes weeks.',
      concepts: [
        {
          id: 'c-two-levers',
          title: 'The Two Levers',
          why: {
            scenario: 'Your legal RAG system retrieves the right contract clauses, but the answers read like a blog post instead of a legal memo. You\'ve already tuned your chunking strategy and reranker. What now?',
            tension: 'Better retrieval can\'t fix how the model writes — only what it reads.'
          },
          what: {
            definition: 'Retrieval improvement',
            body: 'Retrieval is the **input lever** — better chunking, better embeddings, better reranking, better prompts. It controls *what information* reaches the model. When the model has the right information but still produces poor output, retrieval has hit its ceiling.',
          },
          what2: {
            definition: 'Fine-tuning',
            body: 'Fine-tuning is the **model lever** — you change the model\'s weights so it *processes* information differently. It learns your domain\'s style, jargon, reasoning patterns, and output format. The model becomes a specialist instead of a generalist.',
          },
          example: {
            label: 'The spectrum',
            items: [
              { left: 'Retrieval wins', right: 'Model can\'t find the right docs', icon: '🔍' },
              { left: 'Either could work', right: 'Answers are OK but not great', icon: '🤔' },
              { left: 'Fine-tuning wins', right: 'Right docs, wrong output style', icon: '🎯' },
            ]
          },
          drill: {
            type: 'choice',
            question: 'Your RAG system finds the correct medical guidelines but outputs advice in casual language instead of clinical format. Which lever do you pull?',
            options: [
              'Improve retrieval — add more clinical documents to the knowledge base',
              'Fine-tune the model — teach it to write in clinical format',
              'Add a better reranker to surface higher-quality chunks',
              'Increase the context window so the model sees more documents',
            ],
            correct: 1,
            explanation: 'The model already has the right information (retrieval is working). The problem is how it processes and presents that information. Fine-tuning teaches the model the clinical writing style, jargon, and formatting that retrieval alone can\'t provide.'
          }
        },
        {
          id: 'c-when-ft-wins',
          title: 'When Fine-Tuning Wins',
          why: {
            scenario: 'You\'ve optimized retrieval for weeks — better embeddings, hybrid search, a reranker, even a chain-of-thought prompt. The system still sounds like a generic chatbot wearing a lab coat.',
            tension: 'Some problems live inside the model, not in its inputs.'
          },
          what: {
            definition: 'Fine-tuning signals',
            body: 'Fine-tuning is the right call when the gap is in **behavior**, not **knowledge**. Four clear signals: (1) **Style adaptation** — the output needs a specific voice, tone, or register. (2) **Domain jargon** — the model doesn\'t use field-specific terminology naturally. (3) **Consistent formatting** — outputs need a rigid structure the model keeps breaking. (4) **Implicit reasoning** — the domain has unwritten rules a general model doesn\'t know.',
          },
          example: {
            label: 'Real scenarios',
            table: [
              { scenario: 'Customer service bot uses wrong product names', fix: 'Fine-tune', reason: 'The model needs to learn your product taxonomy as instinct' },
              { scenario: 'Bot can\'t find the return policy', fix: 'Retrieval', reason: 'The information isn\'t reaching the model' },
              { scenario: 'Legal summaries miss key clause types', fix: 'Fine-tune', reason: 'The model needs to learn what constitutes a "key clause" in your domain' },
              { scenario: 'Answers reference outdated pricing', fix: 'Retrieval', reason: 'The knowledge base needs current data' },
            ]
          },
          drill: {
            type: 'match',
            question: 'For each scenario, decide: improve Retrieval or Fine-tune the model?',
            pairs: [
              { item: 'The model writes Python but you need it to write Rust', answer: 'Fine-tune', hint: 'Style/language adaptation' },
              { item: 'The system can\'t answer questions about last quarter\'s earnings', answer: 'Retrieval', hint: 'Missing information' },
              { item: 'Outputs are correct but never include confidence scores', answer: 'Fine-tune', hint: 'Formatting behavior' },
              { item: 'The model hallucinates facts about your product', answer: 'Retrieval', hint: 'Grounding in source data' },
            ],
            explanation: 'The pattern: if the problem is *what information* reaches the model → retrieval. If the problem is *how the model uses* that information → fine-tuning. Hallucination is tricky — it can be either, but if retrieval already surfaces correct docs, it\'s a fine-tuning problem.'
          }
        },
        {
          id: 'c-cost-equation',
          title: 'The Cost Equation',
          why: {
            scenario: 'Your manager asks: "Fine-tuning sounds great — how much will it cost and how long?" You need a framework, not a guess.',
            tension: 'Fine-tuning has real costs. Pulling this lever when retrieval would suffice wastes time and money.'
          },
          what: {
            definition: 'Cost components',
            body: 'Fine-tuning costs come in four buckets: (1) **Data preparation** — curating, formatting, and validating training examples (often the most time-consuming). (2) **Compute** — GPU hours for training (minutes to hours for LoRA, days for full fine-tuning). (3) **Evaluation** — you need a rigorous eval set and the discipline to measure before/after. (4) **Maintenance** — the fine-tuned model drifts as your domain changes; you\'ll retrain periodically.',
          },
          example: {
            label: 'Ballpark costs for LoRA fine-tuning Llama 3.1 8B',
            costs: [
              { item: 'Data prep (500 examples)', time: '8–16 hours', cost: 'Your time' },
              { item: 'Training (LoRA, 3 epochs)', time: '30–90 min', cost: '$2–10 cloud GPU' },
              { item: 'Evaluation', time: '2–4 hours', cost: 'Your time + eval set creation' },
              { item: 'Maintenance (quarterly retrain)', time: '4 hours/quarter', cost: '$2–10 + data refresh' },
            ]
          },
          drill: {
            type: 'scenario',
            question: 'Your team has a tight deadline: 2 weeks. The RAG system answers correctly 70% of the time. Retrieval improvements could get you to 80%. Fine-tuning could get you to 90%, but data prep alone takes 10 days. What\'s the right call?',
            options: [
              { label: 'Fine-tune — 90% is worth the stretch', detail: 'Commit the 10 days to data prep and hope training goes smoothly.' },
              { label: 'Retrieval first — ship 80%, fine-tune later', detail: 'Take the faster win now, collect real usage data, and fine-tune with better data next sprint.' },
              { label: 'Do both in parallel', detail: 'Split the team across both efforts.' },
              { label: 'Wait for more time before doing either', detail: 'Push back on the deadline.' },
            ],
            correct: 1,
            explanation: 'With a 2-week window, the 10-day data prep leaves no margin for training issues or iteration. Ship the retrieval improvement (80% in days), then use real user queries as fine-tuning data — you\'ll get better training data AND a shipped product. This is the "smaller promise kept" discipline.'
          }
        },
      ],
    },

    // ── STAGE 2 ──────────────────────────────────────────────
    {
      id: 's2-inside',
      title: 'Inside the Model',
      subtitle: 'What fine-tuning actually changes',
      icon: '🧠',
      why: 'Before you write a single line of training code, you need a mental model of what\'s happening inside the neural network. Not the math — the intuition. This stage gives you the vocabulary to make smart decisions about how to fine-tune.',
      concepts: [
        {
          id: 'c-pretrain-vs-ft',
          title: 'Pre-training vs Fine-tuning',
          why: {
            scenario: 'A colleague asks: "Why can\'t we just train the model on our data from scratch?" You need to explain why that\'s a $10M question with a $10 answer.',
            tension: 'Pre-training and fine-tuning solve fundamentally different problems — confusing them leads to massive waste.'
          },
          what: {
            definition: 'Two phases of learning',
            body: '**Pre-training** teaches the model *language itself* — grammar, facts, reasoning patterns — from trillions of tokens. It costs millions of dollars and takes weeks on hundreds of GPUs. **Fine-tuning** teaches the model *specific behavior* — your domain\'s style, format, and reasoning — from hundreds or thousands of examples. It costs dollars and takes minutes to hours on a single GPU.',
          },
          what2: {
            definition: 'Why fine-tuning works',
            body: 'The pre-trained model already understands language, logic, and a vast knowledge base. Fine-tuning doesn\'t replace that — it *redirects* it. Like teaching a fluent English speaker legal terminology: you\'re not teaching them English, just the specialized vocabulary and conventions on top of what they already know.',
          },
          drill: {
            type: 'choice',
            question: 'A startup wants to build an AI that writes in their brand voice. They have 1,000 examples of on-brand writing. What\'s the most cost-effective approach?',
            options: [
              'Pre-train a new model from scratch on their 1,000 examples',
              'Fine-tune an existing pre-trained model on their 1,000 examples',
              'Use prompt engineering only — no training needed',
              'Wait until they have 1 million examples, then pre-train',
            ],
            correct: 1,
            explanation: 'Fine-tuning an existing model leverages trillions of tokens of pre-training (language understanding) and adds the brand voice with just 1,000 examples. Pre-training from scratch on 1,000 examples would produce gibberish — far too little data to learn language. Prompt engineering alone may work for simple cases but can\'t reliably maintain a consistent brand voice across varied outputs.'
          }
        },
        {
          id: 'c-weights',
          title: 'Weights & Parameters',
          why: {
            scenario: 'Someone says "fine-tuning adjusts the model\'s weights." What does that actually mean? If you can\'t explain it simply, you can\'t reason about what kind of fine-tuning you need.',
            tension: 'You need enough understanding to make architecture decisions, not enough to write the optimizer.'
          },
          what: {
            definition: 'Weight matrices',
            body: 'A language model is a stack of **weight matrices** — giant grids of numbers. Each matrix encodes patterns the model learned during pre-training. When text enters the model, it\'s multiplied through these matrices, which transform it step by step from raw tokens into meaningful output. **Fine-tuning updates these numbers** so the transformations favor your domain\'s patterns.',
          },
          example: {
            label: 'Model sizes in perspective',
            items: [
              { left: 'Llama 3.1 8B', right: '8 billion parameters — fits on a gaming GPU', icon: '💻' },
              { left: 'Llama 3.1 70B', right: '70 billion parameters — needs a multi-GPU server', icon: '🖥' },
              { left: 'GPT-4 class', right: '~1.8 trillion parameters (estimated) — data center scale', icon: '🏢' },
            ]
          },
          drill: {
            type: 'choice',
            question: 'An 8B parameter model stores its knowledge as:',
            options: [
              'A database of 8 billion facts it can look up',
              '8 billion numbers in weight matrices that transform input text into output',
              '8 billion training examples it memorized',
              '8 billion rules for grammar and logic',
            ],
            correct: 1,
            explanation: 'Parameters are numbers in weight matrices — not facts, not examples, not rules. The model encodes patterns as mathematical transformations. This is why fine-tuning works: you\'re adjusting these numbers to favor new patterns, not adding a database of new facts.'
          }
        },
      ],
    },

    // ── STAGE 3 ──────────────────────────────────────────────
    {
      id: 's3-lora',
      title: 'LoRA',
      subtitle: 'The breakthrough that makes fine-tuning practical',
      icon: '⚡',
      why: 'Full fine-tuning updates every parameter in the model — for an 8B model, that means storing gradients for 8 billion numbers. You need 60+ GB of VRAM just for training. LoRA makes fine-tuning possible on a single consumer GPU by updating less than 1% of parameters.',
      concepts: [
        {
          id: 'c-memory-problem',
          title: 'The Memory Problem',
          why: {
            scenario: 'You try to fine-tune Llama 3.1 8B on your fancy new GPU with 24GB VRAM. The training script immediately crashes with "CUDA out of memory." Why?',
            tension: 'Full fine-tuning requires 3-4x the model\'s size in memory — most hardware can\'t handle it.'
          },
          what: {
            definition: 'Why full fine-tuning is expensive',
            body: 'During training, you need memory for: (1) **The model weights** — 8B params × 4 bytes = ~32 GB for float32. (2) **Gradients** — same size as weights, ~32 GB. (3) **Optimizer states** — Adam stores 2 extra copies, ~64 GB. Total: **~128 GB** for an 8B model in float32. Even in half-precision (float16), you need ~60 GB. Your 24GB GPU never stood a chance.',
          },
          drill: {
            type: 'choice',
            question: 'You have a 24GB GPU. What\'s the largest model you could FULLY fine-tune in float16? (Assume you need ~4x the model size for training)',
            options: [
              '~70B parameters',
              '~8B parameters',
              '~3B parameters',
              '~1.5B parameters',
            ],
            correct: 2,
            explanation: '24GB ÷ 4 (training overhead) = ~6 GB for the model itself in float16. At 2 bytes per parameter in float16, that\'s ~3B parameters. This is why LoRA was such a breakthrough — it sidesteps this entire constraint.'
          }
        },
        {
          id: 'c-lora-how',
          title: 'How LoRA Works',
          why: {
            scenario: 'Researchers at Microsoft discovered something surprising: when you fine-tune a large model, the actual changes to the weight matrices are *low-rank* — most of the information in the update can be compressed into much smaller matrices.',
            tension: 'If the meaningful changes are small, why update the entire model?'
          },
          what: {
            definition: 'Low-Rank Adaptation',
            body: 'Instead of updating a weight matrix **W** (which might be 4096 × 4096 = 16M numbers), LoRA freezes W and adds two small matrices: **B** (4096 × r) and **A** (r × 4096), where r (the rank) is tiny — often 8 to 64. The adapted weight becomes **W + BA**. Those two small matrices hold only r × 4096 × 2 numbers instead of 4096 × 4096. With rank 16: that\'s 131K parameters instead of 16M — **a 99.2% reduction**.',
          },
          what2: {
            definition: 'Why it works',
            body: 'During fine-tuning, the changes to weight matrices tend to be "low-rank" — they mostly move along a small number of directions rather than changing randomly across all dimensions. LoRA captures these important directions with the small adapter matrices, achieving 95–99% of full fine-tuning quality with under 1% of the trainable parameters.',
          },
          example: {
            label: 'LoRA configuration in code',
            code: true,
            codeContent: [
              { text: 'from', cls: 'kw' }, { text: ' peft ', cls: 'var' }, { text: 'import', cls: 'kw' }, { text: ' LoraConfig, get_peft_model\n\n', cls: 'var' },
              { text: 'config = ', cls: 'var' }, { text: 'LoraConfig', cls: 'cls' }, { text: '(\n', cls: 'op' },
              { text: '    r', cls: 'param' }, { text: '=', cls: 'op' }, { text: '16', cls: 'num' }, { text: ',              ', cls: '' }, { text: '# Rank: dimensions to adapt', cls: 'cm' }, { text: '\n', cls: '' },
              { text: '    lora_alpha', cls: 'param' }, { text: '=', cls: 'op' }, { text: '32', cls: 'num' }, { text: ',       ', cls: '' }, { text: '# Scaling factor (usually 2× rank)', cls: 'cm' }, { text: '\n', cls: '' },
              { text: '    target_modules', cls: 'param' }, { text: '=', cls: 'op' }, { text: '[\n', cls: 'op' },
              { text: '        ', cls: '' }, { text: '"q_proj"', cls: 'str' }, { text: ', ', cls: 'op' }, { text: '"v_proj"', cls: 'str' }, { text: ',  ', cls: '' }, { text: '# Attention layers to adapt', cls: 'cm' }, { text: '\n', cls: '' },
              { text: '        ', cls: '' }, { text: '"k_proj"', cls: 'str' }, { text: ', ', cls: 'op' }, { text: '"o_proj"', cls: 'str' }, { text: '\n', cls: '' },
              { text: '    ]\n', cls: 'op' },
              { text: ')\n', cls: 'op' },
              { text: 'model = ', cls: 'var' }, { text: 'get_peft_model', cls: 'fn' }, { text: '(base_model, config)', cls: 'var' },
            ]
          },
          drill: {
            type: 'choice',
            question: 'LoRA adds small adapter matrices B and A with rank r=16 to a weight matrix of size 4096×4096. How many trainable parameters does this add?',
            options: [
              '16,777,216 (the full matrix)',
              '131,072 (4096 × 16 × 2)',
              '65,536 (4096 × 16)',
              '16 (just the rank)',
            ],
            correct: 1,
            explanation: 'B is 4096 × 16 = 65,536 parameters. A is 16 × 4096 = 65,536 parameters. Total: 131,072. Compared to the 16.7M parameters in the full matrix, that\'s less than 1% — yet captures the meaningful fine-tuning changes.'
          }
        },
        {
          id: 'c-qlora',
          title: 'QLoRA: Quantize + Adapt',
          why: {
            scenario: 'LoRA reduces trainable parameters, but you still need to load the full base model into memory for the forward pass. An 8B model in float16 is still 16GB. Can we compress the base model too?',
            tension: 'LoRA solved the training cost. QLoRA solves the memory floor.'
          },
          what: {
            definition: 'Quantization',
            body: '**Quantization** reduces the precision of model weights — from 16-bit floats (2 bytes each) to 8-bit or 4-bit integers (1 or 0.5 bytes each). An 8B model drops from **16 GB** (float16) to **8 GB** (8-bit) or **4 GB** (4-bit). The tradeoff: slight quality loss from reduced precision.',
          },
          what2: {
            definition: 'QLoRA = quantized base + full-precision adapters',
            body: 'QLoRA loads the frozen base model in **4-bit** (saving massive memory) but keeps the LoRA adapter matrices in **full precision** (float16 or bfloat16). The adapters are tiny, so their memory cost is negligible. Result: fine-tune a 70B model on a single 48GB GPU, or an 8B model on a laptop with 8GB VRAM.',
          },
          example: {
            label: 'Memory comparison',
            items: [
              { left: 'Full fine-tune (float32)', right: '~128 GB for 8B model', icon: '🔴' },
              { left: 'Full fine-tune (float16)', right: '~60 GB for 8B model', icon: '🟠' },
              { left: 'LoRA (float16 base)', right: '~18 GB for 8B model', icon: '🟡' },
              { left: 'QLoRA (4-bit base)', right: '~6 GB for 8B model', icon: '🟢' },
            ]
          },
          drill: {
            type: 'choice',
            question: 'You have a 24GB GPU and want to fine-tune Llama 3.1 70B. Which approach makes this possible?',
            options: [
              'Full fine-tuning in float16',
              'LoRA with the base model in float16',
              'QLoRA with the base model in 4-bit',
              'None — 70B is impossible on 24GB',
            ],
            correct: 2,
            explanation: '70B × 0.5 bytes (4-bit) = ~35 GB — still too large for 24GB in one GPU. But with model parallelism tricks (offloading layers to CPU RAM), QLoRA can make 70B fine-tuning work on a 24GB GPU with 64GB+ system RAM. For a clean single-GPU fit, you\'d need 48GB. The key insight: QLoRA makes models accessible at scales that were previously data-center-only.'
          }
        },
      ],
    },

    // ── STAGE 4 ──────────────────────────────────────────────
    {
      id: 's4-data',
      title: 'Data & Training',
      subtitle: 'Preparing examples and running the loop',
      icon: '📊',
      why: 'The model is only as good as what you teach it. This stage covers the two most common failure modes: bad training data and misconfigured training runs. Get these right and the model improves reliably. Get them wrong and you\'ve wasted a week.',
      concepts: [
        {
          id: 'c-data-format',
          title: 'Instruction Format',
          why: {
            scenario: 'You dump 500 customer service transcripts into the training pipeline. The fine-tuned model starts outputting both sides of the conversation — customer AND agent — in every response. What went wrong?',
            tension: 'The format of your training data teaches the model what role to play.'
          },
          what: {
            definition: 'The instruction-response format',
            body: 'Training examples must match how the model will be used in production. The standard format has three parts: (1) **System prompt** — the role and constraints (same as production). (2) **User message** — a real question or request. (3) **Assistant response** — the *ideal* answer you want the model to learn. Every example must be complete, consistent, and match the production interface exactly.',
          },
          example: {
            label: 'Good vs bad training example',
            comparison: {
              bad: {
                label: 'Bad — wrong format',
                content: 'Customer: How do I return this?\nAgent: You can initiate a return within 30 days by visiting...\nCustomer: Thanks!\nAgent: Happy to help!'
              },
              good: {
                label: 'Good — instruction format',
                content: '{"system": "You are a support agent for Acme. Be concise and cite policy.",\n "user": "How do I return this?",\n "assistant": "You can return any item within 30 days. Visit acme.com/returns or bring it to any store with your receipt. — Returns Policy §3.1"}'
              }
            }
          },
          drill: {
            type: 'choice',
            question: 'After fine-tuning, your model sometimes outputs "User:" at the start of its responses. What\'s the most likely cause?',
            options: [
              'The learning rate was too high',
              'Training examples included conversation turns without clear role separation',
              'The model was quantized too aggressively',
              'The rank (r) in LoRA was too low',
            ],
            correct: 1,
            explanation: 'When the model outputs "User:" it\'s confused about role boundaries — it learned from examples where conversation turns weren\'t clearly separated into system/user/assistant roles. The fix is clean instruction formatting with explicit role markers.'
          }
        },
        {
          id: 'c-training-loop',
          title: 'The Training Loop',
          why: {
            scenario: 'Your training loss drops steadily for 3 epochs, then starts climbing on epoch 4. Your eval score peaks at epoch 2 and gets worse after. Is this a bug or a feature?',
            tension: 'Loss curves tell you exactly what\'s happening — if you know how to read them.'
          },
          what: {
            definition: 'Key hyperparameters',
            body: 'Three hyperparameters matter most: (1) **Learning rate** — how big each update step is. Too high: the model oscillates and never converges. Too low: training takes forever or gets stuck. Start with 2e-4 for LoRA. (2) **Epochs** — how many times you cycle through all training data. 2-5 epochs is typical; more risks overfitting. (3) **Batch size** — how many examples per update step. Larger = more stable but uses more memory.',
          },
          what2: {
            definition: 'Reading loss curves',
            body: '**Training loss going down** = the model is learning from your data. **Eval loss going down** = the model is generalizing. **Eval loss going UP while training loss goes down** = overfitting — the model is memorizing training examples instead of learning patterns. Stop training at the epoch where eval loss is lowest.',
          },
          drill: {
            type: 'scenario',
            question: 'You fine-tuned for 5 epochs. Training loss: [2.1, 1.4, 0.8, 0.3, 0.1]. Eval loss: [2.0, 1.5, 1.3, 1.6, 2.0]. Which epoch\'s checkpoint should you deploy?',
            options: [
              { label: 'Epoch 5 — lowest training loss', detail: 'The model learned the most from the training data.' },
              { label: 'Epoch 3 — lowest eval loss', detail: 'Best generalization performance on held-out data.' },
              { label: 'Epoch 1 — play it safe', detail: 'Minimal training to avoid overfitting.' },
              { label: 'Average all 5 checkpoints together', detail: 'Combine the learning from all epochs.' },
            ],
            correct: 1,
            explanation: 'Always deploy the checkpoint with the lowest EVAL loss — that\'s where the model generalizes best to new inputs. By epoch 3, training loss is still dropping (0.8) but eval loss has bottomed out (1.3). Epochs 4–5 show classic overfitting: the model memorizes training data (loss → 0.1) while getting worse on new data (eval loss → 2.0).'
          }
        },
        {
          id: 'c-data-quality',
          title: 'Quality Over Quantity',
          why: {
            scenario: 'Team A fine-tunes with 5,000 hastily generated examples. Team B fine-tunes with 300 hand-curated examples. Team B wins on every eval metric. Why?',
            tension: 'More data is not always better. In fine-tuning, data quality is the single largest factor in outcome.'
          },
          what: {
            definition: 'What makes training data good',
            body: 'Good training data has four properties: (1) **Representative** — examples match the real distribution of queries in production. (2) **Correct** — every assistant response is the *ideal* response you\'d want. (3) **Diverse** — covers the full range of topics, edge cases, and difficulty levels. (4) **Consistent** — all examples follow the same style, format, and quality bar. Five hundred excellent examples consistently outperform thousands of mediocre ones.',
          },
          drill: {
            type: 'match',
            question: 'Classify each data quality issue:',
            pairs: [
              { item: 'All 500 examples are about the same 3 topics', answer: 'Lacks diversity', hint: 'Production queries will span many topics' },
              { item: 'Some responses use bullet points, others use paragraphs, randomly', answer: 'Lacks consistency', hint: 'The model will randomly switch formats' },
              { item: 'Training questions are simple but production queries are complex', answer: 'Not representative', hint: 'Distribution mismatch' },
              { item: '20% of responses contain factual errors', answer: 'Not correct', hint: 'The model will learn the errors' },
            ],
            explanation: 'Each quality issue creates a different failure mode in the fine-tuned model. Lack of diversity causes the model to struggle with unseen topics. Inconsistency causes random output format. Non-representative data creates a distribution shift. Incorrect data teaches the model to confidently state falsehoods.'
          }
        },
      ],
    },

    // ── STAGE 5 ──────────────────────────────────────────────
    {
      id: 's5-eval',
      title: 'Evaluation & ROI',
      subtitle: 'Prove it worked — then decide if it was worth it',
      icon: '📈',
      why: 'You\'ve fine-tuned the model. It feels better. But "feels better" doesn\'t survive a budget review. This stage teaches you to measure the improvement rigorously and calculate whether fine-tuning was the right investment.',
      concepts: [
        {
          id: 'c-eval-design',
          title: 'Designing Your Eval',
          why: {
            scenario: 'You show the fine-tuned model to your team. Everyone says "it\'s better!" Your tech lead asks: "Better by how much? On what?" Silence.',
            tension: 'Without a rigorous eval, you can\'t prove improvement, compare approaches, or justify the investment.'
          },
          what: {
            definition: 'The eval framework',
            body: 'A good eval needs three things: (1) **A held-out test set** — examples the model never saw during training, representing real production queries. 50–100 examples is enough for directional signal. (2) **Clear metrics** — what does "better" mean? Accuracy? Style match? Format compliance? Pick 2–3 metrics you can score objectively. (3) **A baseline** — the same test set run through the *un-fine-tuned* model, so you can measure the delta.',
          },
          what2: {
            definition: 'Metrics that matter',
            body: '**Task accuracy** — does the answer contain the correct information? (human-graded or LLM-as-judge). **Style compliance** — does it match the required format, tone, and terminology? (rubric-scored). **Regression check** — did fine-tuning break general capabilities? Test on generic benchmarks to ensure the model didn\'t "forget" how to reason.',
          },
          drill: {
            type: 'scenario',
            question: 'You\'re designing an eval for a fine-tuned legal Q&A model. Which eval set design is strongest?',
            options: [
              { label: '50 questions from the training data', detail: 'Questions the model was trained on, to verify it learned them.' },
              { label: '50 novel questions written by lawyers, covering 10 legal topics', detail: 'New questions the model never saw, spanning the domain.' },
              { label: '200 auto-generated questions from GPT-4', detail: 'Large volume, machine-generated, covering many topics.' },
              { label: '10 extremely difficult edge cases', detail: 'The hardest questions to stress-test the model.' },
            ],
            correct: 1,
            explanation: '50 novel questions written by domain experts is the gold standard. Training data tests memorization, not generalization. Auto-generated questions may not reflect real usage patterns. 10 edge cases is too small and skews toward difficulty rather than representing real distribution. Expert-written, diverse, held-out questions give you the most reliable signal.'
          }
        },
        {
          id: 'c-roi',
          title: 'The ROI Verdict',
          why: {
            scenario: 'Your fine-tuned model scores 85% on your eval vs. the baseline\'s 72%. That\'s a 13-point improvement. Is it worth it? Depends on what those 13 points cost and what they\'re worth.',
            tension: 'The question isn\'t "did fine-tuning help?" — it\'s "was fine-tuning the best use of your team\'s time and budget?"'
          },
          what: {
            definition: 'Cost per improvement point',
            body: 'Calculate: **Total cost** (data prep hours × rate + compute + eval time) ÷ **Improvement points** (fine-tuned score − baseline score). Compare this to the cost of achieving the same improvement through retrieval optimization. If retrieval could get you from 72% to 80% in 2 days, and fine-tuning gets you from 72% to 85% in 2 weeks, the first 8 points were cheaper via retrieval. Fine-tuning\'s value is the *incremental* improvement beyond what retrieval could achieve.',
          },
          what2: {
            definition: 'The decision matrix',
            body: 'Fine-tuning is worth it when: **The quality gap matters** — in medical, legal, or financial domains, 72% → 85% could be the difference between useful and dangerous. **Retrieval has plateaued** — you\'ve already optimized chunking, embeddings, and reranking. **The domain is stable** — retraining won\'t be needed monthly. **You have good data** — or can get it without excessive cost.',
          },
          drill: {
            type: 'scenario',
            question: 'Two teams report their fine-tuning results:\n\nTeam A: Baseline 60% → Fine-tuned 88%. Cost: $5,000 and 3 weeks.\nTeam B: Baseline 82% → Fine-tuned 87%. Cost: $5,000 and 3 weeks.\n\nWhich team made the better investment?',
            options: [
              { label: 'Team A — bigger absolute improvement (28 points)', detail: 'Going from 60% to 88% is transformative.' },
              { label: 'Team B — they were already good and got better', detail: 'Incremental improvement from a strong baseline.' },
              { label: 'Both good — same cost, both improved', detail: 'Any improvement justifies the spend.' },
              { label: 'Need more context — what was retrieval-only capable of?', detail: 'The ROI depends on what retrieval could have achieved.' },
            ],
            correct: 3,
            explanation: 'The missing variable is: could retrieval have gotten Team A from 60% to 80% for $500 in 2 days? If so, fine-tuning\'s *incremental* value is 80% → 88% for $5,000 — much less impressive. Team B might have already exhausted retrieval gains, making fine-tuning the only lever left. ROI always requires the counterfactual: what was the cheaper alternative capable of?'
          }
        },
      ],
    },
  ],
};

// ── LIBRARY: additional courses for the dashboard ────────────
const LIBRARY_COURSES = [
  MODULE_A,
  {
    id: 'agentic-rag',
    title: 'Agentic RAG',
    series: 'Advanced RAG & Agentic Systems',
    level: 2, moduleLabel: 'B',
    description: 'Build multi-step reasoning systems where the LLM plans retrieval, uses tools, and corrects itself.',
    tags: ['agents', 'tool-use', 'planning', 'langchain', 'multi-hop'],
    stages: [], locked: true,
  },
  {
    id: 'multimodal-rag',
    title: 'Multimodal RAG',
    series: 'Advanced RAG & Agentic Systems',
    level: 2, moduleLabel: 'C',
    description: 'Handle documents beyond text — images, tables, PDFs — with dual embeddings and vision models.',
    tags: ['multimodal', 'vision', 'pdf', 'clip', 'tables'],
    stages: [], locked: true,
  },
  {
    id: 'production-deploy',
    title: 'Production Deployment',
    series: 'Advanced RAG & Agentic Systems',
    level: 2, moduleLabel: 'D',
    description: 'Deploy safely: local serving, rate limiting, prompt injection defense, audit logging, A/B testing.',
    tags: ['production', 'vllm', 'safety', 'monitoring', 'deployment'],
    stages: [], locked: true,
  },
];

const SUGGESTED_NEXT = [
  {
    title: 'Agentic RAG — Multi-Step Reasoning',
    reason: 'Fine-tuning teaches the model to process better. Agentic RAG teaches it to plan what to retrieve. Together, they\'re the full stack.',
    prereq: 'fine-tuning',
    level: 2, moduleLabel: 'B',
  },
  {
    title: 'Production Deployment & Safety',
    reason: 'You\'ve improved the model — now deploy it safely with rate limiting, audit logging, and prompt injection defense.',
    prereq: 'fine-tuning',
    level: 2, moduleLabel: 'D',
  },
];

window.MODULE_A = MODULE_A;
window.LIBRARY_COURSES = LIBRARY_COURSES;
window.SUGGESTED_NEXT = SUGGESTED_NEXT;
