# Diretrizes e Regras de Fidelidade para Entregas Acadêmicas

Este arquivo define os requisitos obrigatórios e invioláveis para a confecção de relatórios técnicos, apresentações, especificações e PDFs no projeto SIGAAS.

---

## 1. Fidelidade a Metadados Institucionais (Zero Tolerância a Alucinações)
- **Proibição Absoluta:** Jamais invente, presuma ou interpole nomes de instituições de ensino, faculdades, universidades, centros universitários, cidades ou estados.
- **Identificação Oficial Mandatória:**
  - **Disciplina:** Fábrica de Software & Tópicos Avançados em Computação
  - **Curso:** Curso de Bacharelado em Ciência da Computação
  - **Turma:** 8MB - CC (Semestre 2026/2)
  - **Equipe:** Grupo 31 — SIGAAS
  - **Repositório GitHub:** `https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas`
- **Tabela de Integrantes Mandatória (4 Colunas Obrigatórias):**
  1. `Ewerton Thyago Tavares da Silva` | `01573977` | `Scrum Master (Líder)` | `Facilitação ágil, gestão de entregas, governança de branches e submissão no Teams`
  2. `Wesclei Batista Da Cruz Júnior` | `01606772` | `Product Owner` | `Levantamento de requisitos, regras de negócio e validação dos critérios de aceite`
  3. `Osvaldo Vasconcelos de Carvalho` | `01614171` | `Dev Backend / Sistemas` | `Arquitetura de API, integração FFI C/OpenMP (ctypes), endpoints e migrations`
  4. `Gabriel Porfírio dos Santos` | `01591399` | `Dev Frontend` | `Interface SPA Angular 20, componentes, estados reativos e interceptors`
  5. `Flávio Vecch de Brito Farias` | `01600988` | `DBA & Documentação` | `Modelagem relacional PostgreSQL, scripts de seed, integridade e documentação técnica`

---

## 2. Padrões de Diagramação e Geração de PDF (ABNT)
- **Capa Institucional:** A capa deve conter no topo exclusivamente:
  ```text
  FÁBRICA DE SOFTWARE & TÓPICOS AVANÇADOS EM COMPUTAÇÃO
  CURSO DE BACHARELADO EM CIÊNCIA DA COMPUTAÇÃO — TURMA 8MB - CC
  ```
  Não deve conter cabeçalho de universidade ou cidade na base, salvo se explicitamente determinado pelo usuário.
- **Tipografia:** Times New Roman (corpo e títulos) e Consolas (código e logs monoespaçados).
- **Cores:** `#1f4e79` (azul institucional primário), `#cbd5e1` (bordas) e `#f8fafc` (fundo alternado).
- **Cabeçalhos e Rodapés:**
  - Cabeçalho superior corrido: `Grupo 31 - SIGAAS: Sistema Integrado de Gestão Acadêmica e Alocação de Salas com IA | Fábrica de Software - Sprint XX`.
  - Rodapé com numeração paginada dinâmica: `Página X de Y`.
- **Figuras e Legendas:**
  - Títulos de subseções de figuras e introduções devem permanecer na mesma página que a imagem (`KeepTogether` ou quebra explícita de página).
  - Todas as capturas devem preservar aspect ratio e estar dimensionadas para a mancha de texto.
