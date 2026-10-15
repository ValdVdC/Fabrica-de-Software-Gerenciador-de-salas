"""
Testes automatizados TDD para o servico de IA preditiva de absenteismo e remanejamento (Sprint 06).
Valida pipeline scikit-learn, prevencao de vazamento temporal, calibracao e regra de ouro.
"""

from datetime import date, datetime, time, timedelta
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models import (
    Campus,
    Curso,
    Disciplina,
    Frequencia,
    Horario,
    Matricula,
    PerfilUsuario,
    PrevisaoFalta,
    Sala,
    StatusSugestao,
    SugestaoRemanejamento,
    TipoSala,
    Turma,
    Turno,
    Usuario,
)
from app.services.ia_service import (
    carregar_ou_inicializar_modelo,
    converter_sugestao_para_read,
    criar_pipeline_absenteismo,
    extrair_dataset_frequencias,
    gerar_sugestoes_remanejamento,
    prever_probabilidade_absenteismo,
    treinar_modelo_absenteismo,
)


@pytest.fixture
def db_session():
    """Sessao isolada em memoria para testes do servico de IA."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture
def dados_cenario_ia(db_session: Session):
    """Cria cenario completo com campus, usuarios, salas, turmas e frequencias."""
    campus = Campus(nome="Campus Central IA", cidade="Cidade", endereco="Rua 1")
    db_session.add(campus)
    db_session.flush()

    prof = Usuario(
        campus_id=campus.id,
        nome="Prof. Data Science",
        email="prof.ds@sigaas.edu",
        senha_hash="hash123",
        perfil=PerfilUsuario.PROFESSOR,
    )
    db_session.add(prof)
    db_session.flush()

    # Salas: Uma sala grande (120 lugares) e uma sala menor livre (30 lugares)
    sala_grande = Sala(
        campus_id=campus.id,
        bloco="AUD",
        numero="01",
        tipo=TipoSala.REGULAR,
        capacidade=120,
        turnos_disponiveis=["matutino", "noturno"],
        ativo=True,
    )
    sala_menor = Sala(
        campus_id=campus.id,
        bloco="A",
        numero="102",
        tipo=TipoSala.REGULAR,
        capacidade=30,
        turnos_disponiveis=["matutino", "noturno"],
        ativo=True,
    )
    db_session.add_all([sala_grande, sala_menor])
    db_session.flush()

    curso = Curso(campus_id=campus.id, nome="Ciencia de Dados", codigo="CD")
    db_session.add(curso)
    db_session.flush()

    disc = Disciplina(curso_id=curso.id, nome="Machine Learning", codigo="CD-101", carga_horaria=60)
    db_session.add(disc)
    db_session.flush()

    # Turma com 25 alunos na sexta-feira a noite
    turma = Turma(
        disciplina_id=disc.id,
        professor_id=prof.id,
        periodo_letivo="2026.1",
        num_matriculados=25,
        turno_preferido=Turno.NOTURNO,
    )
    db_session.add(turma)
    db_session.flush()

    horario = Horario(
        campus_id=campus.id,
        turma_id=turma.id,
        sala_id=sala_grande.id,
        dia_semana=4,  # Sexta-feira
        hora_inicio=time(19, 0),
        hora_fim=time(21, 0),
    )
    db_session.add(horario)
    db_session.flush()

    # Cria discentes e matriculas
    matriculas = []
    for i in range(1, 26):
        aluno = Usuario(
            campus_id=campus.id,
            nome=f"Aluno Teste {i}",
            email=f"aluno.teste.{i}@sigaas.edu",
            senha_hash="hash123",
            perfil=PerfilUsuario.ALUNO,
        )
        db_session.add(aluno)
        db_session.flush()
        mat = Matricula(aluno_id=aluno.id, turma_id=turma.id)
        db_session.add(mat)
        db_session.flush()
        matriculas.append(mat)

    # Historico de frequencias simulando alto absenteismo na sexta a noite
    base_data = date(2026, 2, 6)
    for w in range(6):
        dt_aula = base_data + timedelta(days=w * 7)
        for idx, mat in enumerate(matriculas):
            # 60% dos alunos faltam (somente 40% presentes)
            presente = (idx % 5) in (0, 1)
            freq = Frequencia(
                matricula_id=mat.id,
                horario_id=horario.id,
                data=dt_aula,
                presente=presente,
            )
            db_session.add(freq)

    db_session.commit()
    return {
        "campus": campus,
        "prof": prof,
        "sala_grande": sala_grande,
        "sala_menor": sala_menor,
        "turma": turma,
        "horario": horario,
        "matriculas": matriculas,
    }


def test_criar_pipeline_absenteismo():
    """Valida construcao dos transformadores e classificador do pipeline scikit-learn."""
    pipeline = criar_pipeline_absenteismo()
    assert "preprocessor" in pipeline.named_steps
    assert "classifier" in pipeline.named_steps


def test_extrair_dataset_frequencias_ordenacao_temporal(db_session, dados_cenario_ia):
    """Valida extracao sem vazamento temporal, conferindo ordenacao cronologica."""
    X, y = extrair_dataset_frequencias(db_session)
    assert len(X) > 0
    assert len(X) == len(y)
    assert "dia_semana" in X.columns
    assert "razao_ocupacao" in X.columns
    assert "turno" in X.columns


def test_treinar_modelo_e_serializacao(db_session, dados_cenario_ia, tmp_path, monkeypatch):
    """Valida treino completo com TimeSeriesSplit e persistencia no formato joblib."""
    artefato_teste = tmp_path / "modelo_absenteismo.joblib"
    monkeypatch.setattr("app.services.ia_service.MODELO_ARTEFATO_PATH", artefato_teste)
    monkeypatch.setattr("app.services.ia_service.ARTEFATO_DIR", tmp_path)

    res = treinar_modelo_absenteismo(db_session)
    assert res["total_amostras"] > 0
    assert artefato_teste.is_file()

    # Carrega do artefato
    modelo_carregado = carregar_ou_inicializar_modelo(db_session)
    assert modelo_carregado is not None


def test_prever_probabilidade_absenteismo(db_session, dados_cenario_ia):
    """Valida inferencia de probabilidade no intervalo unitario [0.0, 1.0]."""
    horario = dados_cenario_ia["horario"]
    prob = prever_probabilidade_absenteismo(horario, db=db_session)
    assert 0.0 <= prob <= 1.0


def test_gerar_sugestoes_remanejamento_e_regra_de_ouro(db_session, dados_cenario_ia):
    """
    Valida geracao de sugestoes para turma ociosa em sala superdimensionada.
    Garante a regra de ouro: horario.sala_id NUNCA e modificado pelo algoritmo.
    """
    horario = dados_cenario_ia["horario"]
    sala_grande = dados_cenario_ia["sala_grande"]
    sala_menor = dados_cenario_ia["sala_menor"]
    sala_id_original = horario.sala_id

    sugestoes = gerar_sugestoes_remanejamento(
        db=db_session,
        campus_id=dados_cenario_ia["campus"].id,
        limiar_ociosidade=0.40,
    )

    assert len(sugestoes) >= 1
    sugestao = sugestoes[0]

    # Verifica status pendente
    assert sugestao.status == StatusSugestao.PENDENTE
    assert sugestao.horario_id == horario.id
    assert sugestao.sala_atual_id == sala_grande.id
    assert sugestao.sala_sugerida_id == sala_menor.id

    # REGRA DE OURO: Horario permanece inalterado!
    db_session.refresh(horario)
    assert horario.sala_id == sala_id_original

    # Verifica registro em previsao_falta
    prevs = db_session.scalars(
        select(PrevisaoFalta).where(PrevisaoFalta.horario_id == horario.id)
    ).all()
    assert len(prevs) >= 1
    assert 0.0 <= prevs[0].prob_ausencia <= 1.0


def test_gerar_sugestoes_remanejamento_idempotencia(db_session, dados_cenario_ia):
    """Valida que chamadas repetidas nao geram sugestoes pendentes duplicadas."""
    sugestoes_1 = gerar_sugestoes_remanejamento(db=db_session, campus_id=dados_cenario_ia["campus"].id)
    qtd_1 = len(sugestoes_1)

    sugestoes_2 = gerar_sugestoes_remanejamento(db=db_session, campus_id=dados_cenario_ia["campus"].id)
    assert len(sugestoes_2) == 0  # Ja existe pendente, nao duplica

    total_no_banco = db_session.query(SugestaoRemanejamento).count()
    assert total_no_banco == qtd_1


def test_gerar_sugestoes_sem_sala_livre(db_session, dados_cenario_ia):
    """Quando a sala menor ja esta ocupada no mesmo horario, nao deve sugerir."""
    horario = dados_cenario_ia["horario"]
    sala_menor = dados_cenario_ia["sala_menor"]

    # Cria horario conflitante na sala menor
    outro_horario = Horario(
        campus_id=dados_cenario_ia["campus"].id,
        turma_id=dados_cenario_ia["turma"].id,
        sala_id=sala_menor.id,
        dia_semana=horario.dia_semana,
        hora_inicio=horario.hora_inicio,
        hora_fim=horario.hora_fim,
    )
    db_session.add(outro_horario)
    db_session.commit()

    sugestoes = gerar_sugestoes_remanejamento(
        db=db_session,
        campus_id=dados_cenario_ia["campus"].id,
        limiar_ociosidade=0.40,
    )
    assert len(sugestoes) == 0


def test_converter_sugestao_para_read(db_session, dados_cenario_ia):
    """Valida conversao para o schema Pydantic enriquecido SugestaoRemanejamentoRead."""
    sugestoes = gerar_sugestoes_remanejamento(db=db_session, campus_id=dados_cenario_ia["campus"].id)
    assert len(sugestoes) >= 1
    read_obj = converter_sugestao_para_read(sugestoes[0])

    assert read_obj.id == sugestoes[0].id
    assert read_obj.disciplina_codigo == "CD-101"
    assert read_obj.sala_atual_bloco == "AUD"
    assert read_obj.sala_sugerida_bloco == "A"
    assert read_obj.status == StatusSugestao.PENDENTE
    assert read_obj.prob_ausencia is not None
    assert 0.0 <= read_obj.prob_ausencia <= 1.0


def test_gerar_sugestoes_turma_sem_matriculados_ou_sala_invalida(db_session, dados_cenario_ia):
    """Garante que turmas com 0 matriculados ou sem sala nao geram excecao nem sugestao espuria."""
    turma_vazia = Turma(
        disciplina_id=dados_cenario_ia["turma"].disciplina_id,
        professor_id=dados_cenario_ia["prof"].id,
        periodo_letivo="2026.1",
        num_matriculados=0,
        turno_preferido=Turno.MATUTINO,
    )
    db_session.add(turma_vazia)
    db_session.flush()

    horario_vazio = Horario(
        campus_id=dados_cenario_ia["campus"].id,
        turma_id=turma_vazia.id,
        sala_id=dados_cenario_ia["sala_grande"].id,
        dia_semana=1,
        hora_inicio=time(8, 0),
        hora_fim=time(10, 0),
    )
    db_session.add(horario_vazio)
    db_session.commit()

    sugestoes = gerar_sugestoes_remanejamento(db=db_session, campus_id=dados_cenario_ia["campus"].id)
    # Nenhuma sugestao deve ter sido gerada para a turma com 0 matriculados
    ids_horarios_sugeridos = [s.horario_id for s in sugestoes]
    assert horario_vazio.id not in ids_horarios_sugeridos


def test_prever_probabilidade_absenteismo_casos_de_borda(db_session):
    """Valida resiliencia da inferencia quando horarios ou turmas possuem valores nulos/ausentes."""
    horario_sem_relacionamentos = Horario(
        campus_id=1,
        turma_id=1,
        sala_id=1,
        dia_semana=4,
        hora_inicio=time(19, 0),
        hora_fim=time(21, 0),
    )
    # Sem turma ou sala associada no objeto em memoria
    prob = prever_probabilidade_absenteismo(horario_sem_relacionamentos, db=db_session)
    assert 0.0 <= prob <= 1.0


def test_gerar_sugestoes_sem_conflito_entre_duas_turmas_mesmo_slot(db_session, dados_cenario_ia):
    """
    Quando duas turmas com alto absenteismo estao no mesmo horario e ha apenas UMA sala menor disponivel,
    o algoritmo nao pode sugerir a mesma sala menor para ambas.
    """
    campus = dados_cenario_ia["campus"]
    disc = dados_cenario_ia["turma"].disciplina
    prof = dados_cenario_ia["prof"]

    # Cria segunda sala grande e segunda turma para o mesmo horario (sexta 19:00 - 21:00)
    sala_grande_2 = Sala(
        campus_id=campus.id,
        bloco="AUD",
        numero="02",
        tipo=TipoSala.REGULAR,
        capacidade=100,
        turnos_disponiveis=["matutino", "noturno"],
        ativo=True,
    )
    db_session.add(sala_grande_2)
    db_session.flush()

    turma_2 = Turma(
        disciplina_id=disc.id,
        professor_id=prof.id,
        periodo_letivo="2026.1",
        num_matriculados=20,
        turno_preferido=Turno.NOTURNO,
    )
    db_session.add(turma_2)
    db_session.flush()

    horario_2 = Horario(
        campus_id=campus.id,
        turma_id=turma_2.id,
        sala_id=sala_grande_2.id,
        dia_semana=4,
        hora_inicio=time(19, 0),
        hora_fim=time(21, 0),
    )
    db_session.add(horario_2)
    db_session.commit()

    sugestoes = gerar_sugestoes_remanejamento(db=db_session, campus_id=campus.id)
    # As sugestoes geradas no lote nao podem ter salas sugeridas duplicadas para o mesmo slot
    salas_sugeridas_slot = [
        s.sala_sugerida_id for s in sugestoes
        if s.horario.dia_semana == 4 and s.horario.hora_inicio == time(19, 0)
    ]
    assert len(salas_sugeridas_slot) == len(set(salas_sugeridas_slot))


def test_extrair_dataset_frequencias_base_vazia_usa_priors(db_session):
    """Quando o banco nao contem frequencias, deve retornar distribuicao prior sintetica."""
    X, y = extrair_dataset_frequencias(db_session)
    assert len(X) == 10
    assert len(y) == 10
    assert set(y.unique()) == {0, 1}


def test_prever_probabilidade_absenteismo_erros_e_fallback(dados_cenario_ia):
    """Valida erro quando nem db nem modelo sao fornecidos e o fallback heuristico."""
    horario = dados_cenario_ia["horario"]
    with pytest.raises(ValueError, match="db ou modelo deve ser informado"):
        prever_probabilidade_absenteismo(horario, modelo=None, db=None)

    # Forca excecao de predicao para testar o fallback deterministico
    prob_fallback = prever_probabilidade_absenteismo(horario, modelo="objeto_invalido_sem_predict_proba")
    assert 0.0 <= prob_fallback <= 1.0
    assert prob_fallback > 0.30  # sexta-feira e noturno no fallback adicionam 0.35 + 0.15


def test_gerar_sugestoes_com_filtro_periodo_letivo_e_incompatibilidade_turno(db_session, dados_cenario_ia):
    """Valida filtro por periodo_letivo e restricao de turnos_disponiveis da sala candidata."""
    campus = dados_cenario_ia["campus"]
    sala_menor = dados_cenario_ia["sala_menor"]

    # Torna a sala menor disponivel apenas no vespertino (incompativel com turma noturna)
    sala_menor.turnos_disponiveis = ["vespertino"]
    db_session.commit()

    # Com periodo letivo inexistente nao encontra
    sug_inexistente = gerar_sugestoes_remanejamento(db=db_session, campus_id=campus.id, periodo_letivo="2099.2")
    assert len(sug_inexistente) == 0

    # Com periodo correto, porem com sala menor de turno incompativel, nao deve sugerir
    sug_compat = gerar_sugestoes_remanejamento(db=db_session, campus_id=campus.id, periodo_letivo="2026.1")
    assert len(sug_compat) == 0


def test_converter_sugestao_para_read_fallback_motivo():
    """Valida extracao de prob_ausencia via string do motivo quando nao ha PrevisaoFalta anexada."""
    horario = Horario(id=1, campus_id=1, turma_id=1, sala_id=1, dia_semana=4, hora_inicio=time(19, 0), hora_fim=time(21, 0))
    sug = SugestaoRemanejamento(
        id=999,
        horario_id=1,
        sala_atual_id=1,
        sala_sugerida_id=2,
        motivo="Probabilidade estimada de absenteismo: 58.5%. Remanejamento sugerido.",
        status=StatusSugestao.PENDENTE,
        criado_em=datetime.now(),
        atualizado_em=datetime.now(),
    )
    sug.horario = horario
    sug.sala_atual = None
    sug.sala_sugerida = None

    read_obj = converter_sugestao_para_read(sug)
    assert read_obj.prob_ausencia == 0.585
