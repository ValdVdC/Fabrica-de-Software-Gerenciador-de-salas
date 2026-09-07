#!/usr/bin/env python3
"""
Script de povoamento (seed) idempotente do banco de dados do SIGAAS.
Gera dados sinteticos consistentes para desenvolvimento e testes.
"""

import sys
from datetime import time
from pathlib import Path

# Garante acesso aos modulos em backend
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Campus, Usuario, Equipamento, Sala, SalaEquipamento,
    Curso, Disciplina, Turma, Matricula, Horario, LogAlocacao,
    PerfilUsuario, TipoSala, Turno, TipoEventoLog
)

SENHA_HASH_PADRAO = "$2b$12$e8Y6lqD3EwVqV3V5dI4yO.uA9N3X2B1C4D5E6F7G8H9I0J1K2L3M4"


def seed_database(session: Session) -> dict[str, int]:
    """Popula o banco de forma idempotente e retorna a contagem de registros."""
    # 1. Campi
    c1 = session.scalar(select(Campus).where(Campus.nome == "Campus Central"))
    if not c1:
        c1 = Campus(nome="Campus Central", cidade="Cidade Universitaria", endereco="Av. Principal, 1000")
        session.add(c1)
    c2 = session.scalar(select(Campus).where(Campus.nome == "Campus Zona Norte"))
    if not c2:
        c2 = Campus(nome="Campus Zona Norte", cidade="Cidade Universitaria", endereco="Rua das Palmeiras, 500")
        session.add(c2)
    session.flush()

    # 2. Usuarios
    users_data = [
        ("Admin Central", "admin@sigaas.edu", PerfilUsuario.ADMIN, c1.id),
        ("Coord. Computacao", "coord.cc@sigaas.edu", PerfilUsuario.COORDENADOR, c1.id),
        ("Prof. Alan Turing", "alan.turing@sigaas.edu", PerfilUsuario.PROFESSOR, c1.id),
        ("Prof. Ada Lovelace", "ada.lovelace@sigaas.edu", PerfilUsuario.PROFESSOR, c1.id),
        ("Aluno Joao Silva", "joao.silva@sigaas.edu", PerfilUsuario.ALUNO, c1.id),
        ("Aluna Maria Souza", "maria.souza@sigaas.edu", PerfilUsuario.ALUNO, c1.id),
        ("Secretaria Academica", "secretaria@sigaas.edu", PerfilUsuario.SECRETARIA, c1.id),
    ]
    usuarios = {}
    for nome, email, perfil, campus_id in users_data:
        u = session.scalar(select(Usuario).where(Usuario.email == email))
        if not u:
            u = Usuario(campus_id=campus_id, nome=nome, email=email, senha_hash=SENHA_HASH_PADRAO, perfil=perfil)
            session.add(u)
            session.flush()
        usuarios[email] = u

    # 3. Equipamentos
    equips_data = ["Projetor 4K", "Ar-Condicionado 24k BTUs", "Computadores Dell i7"]
    equipamentos = {}
    for nome in equips_data:
        eq = session.scalar(select(Equipamento).where(Equipamento.nome == nome))
        if not eq:
            eq = Equipamento(nome=nome, descricao=f"Equipamento {nome}")
            session.add(eq)
            session.flush()
        equipamentos[nome] = eq

    # 4. Salas
    salas_data = [
        (c1.id, "A", "101", TipoSala.REGULAR, 50, ["matutino", "noturno"]),
        (c1.id, "B", "201", TipoSala.LABORATORIO, 35, ["matutino", "vespertino", "noturno"]),
        (c1.id, "AUD", "01", TipoSala.AUDITORIO, 120, ["noturno"]),
        (c2.id, "ZN-A", "101", TipoSala.REGULAR, 40, ["matutino", "noturno"]),
    ]
    salas = []
    for cid, bloco, num, tipo, cap, turnos in salas_data:
        s = session.scalar(select(Sala).where(Sala.campus_id == cid, Sala.bloco == bloco, Sala.numero == num))
        if not s:
            s = Sala(campus_id=cid, bloco=bloco, numero=num, tipo=tipo, capacidade=cap, turnos_disponiveis=turnos)
            session.add(s)
            session.flush()
            session.add(SalaEquipamento(sala_id=s.id, equipamento_id=equipamentos["Projetor 4K"].id, quantidade=1))
        salas.append(s)

    # 5. Cursos e Disciplinas
    curso = session.scalar(select(Curso).where(Curso.campus_id == c1.id, Curso.codigo == "CC"))
    if not curso:
        curso = Curso(campus_id=c1.id, nome="Ciencia da Computacao", codigo="CC")
        session.add(curso)
        session.flush()

    disc = session.scalar(select(Disciplina).where(Disciplina.curso_id == curso.id, Disciplina.codigo == "CC-101"))
    if not disc:
        disc = Disciplina(curso_id=curso.id, nome="Algoritmos e Programacao", codigo="CC-101", carga_horaria=60)
        session.add(disc)
        session.flush()

    # 6. Turma e Matriculas
    prof = usuarios["alan.turing@sigaas.edu"]
    turma = session.scalar(select(Turma).where(Turma.disciplina_id == disc.id, Turma.periodo_letivo == "2026.1"))
    if not turma:
        turma = Turma(
            disciplina_id=disc.id, professor_id=prof.id, periodo_letivo="2026.1",
            num_matriculados=2, turno_preferido=Turno.MATUTINO
        )
        session.add(turma)
        session.flush()

    for email_aluno in ["joao.silva@sigaas.edu", "maria.souza@sigaas.edu"]:
        aluno = usuarios[email_aluno]
        mat = session.scalar(select(Matricula).where(Matricula.aluno_id == aluno.id, Matricula.turma_id == turma.id))
        if not mat:
            session.add(Matricula(aluno_id=aluno.id, turma_id=turma.id))

    # 7. Horario e Log
    s101 = salas[0]
    horario = session.scalar(select(Horario).where(Horario.turma_id == turma.id, Horario.sala_id == s101.id))
    if not horario:
        horario = Horario(
            campus_id=c1.id, turma_id=turma.id, sala_id=s101.id,
            dia_semana=0, hora_inicio=time(8, 0), hora_fim=time(10, 0)
        )
        session.add(horario)
        session.flush()
        session.add(LogAlocacao(
            horario_id=horario.id, tipo_evento=TipoEventoLog.CRIACAO,
            usuario_responsavel=prof.id, detalhes="Alocacao de seed"
        ))

    session.commit()
    return {
        "campus": session.query(Campus).count(),
        "usuario": session.query(Usuario).count(),
        "equipamento": session.query(Equipamento).count(),
        "sala": session.query(Sala).count(),
        "curso": session.query(Curso).count(),
        "disciplina": session.query(Disciplina).count(),
        "turma": session.query(Turma).count(),
        "horario": session.query(Horario).count(),
    }


def main():
    print("Iniciando povoamento do banco de dados...")
    with SessionLocal() as session:
        counts = seed_database(session)
    print("Povoamento concluido com sucesso:")
    for k, v in counts.items():
        print(f"  - {k}: {v} registros")


if __name__ == "__main__":
    main()
