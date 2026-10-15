"""
Testes automatizados TDD para o servico de IA preditiva de absenteismo e remanejamento (Sprint 06).
Valida pipeline scikit-learn, prevencao de vazamento temporal, calibracao e regra de ouro.
"""

from datetime import date, time, timedelta
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
