#!/usr/bin/env python3
"""
Script de povoamento (seed) idempotente do banco de dados do SIGAAS.
Gera dados sinteticos consistentes para desenvolvimento, testes e modelos de IA.
"""

import sys
import random
from datetime import date, time, timedelta
from pathlib import Path

# Garante acesso aos modulos em backend (compativel com host e container Docker)
root_dir = Path(__file__).resolve().parent.parent
for candidate in [root_dir / "backend", Path("/app")]:
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Campus, Usuario, Equipamento, Sala, SalaEquipamento,
    Curso, Disciplina, Turma, Matricula, Horario, LogAlocacao,
    Frequencia, PerfilUsuario, TipoSala, Turno, TipoEventoLog
)
from app.core.security import get_password_hash  # noqa: E402


def seed_database(session: Session) -> dict[str, int]:
    """Popula o banco de forma idempotente e retorna a contagem de registros."""
    senha_hash_padrao = get_password_hash("sigaas123")

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

    # 2. Usuarios Base
    users_data = [
        ("Admin Central", "admin@sigaas.edu", PerfilUsuario.ADMIN, c1.id),
        ("Coord. Computacao", "coord.cc@sigaas.edu", PerfilUsuario.COORDENADOR, c1.id),
        ("Prof. Alan Turing", "alan.turing@sigaas.edu", PerfilUsuario.PROFESSOR, c1.id),
        ("Professor Padrao", "professor@sigaas.edu", PerfilUsuario.PROFESSOR, c1.id),
        ("Prof. Ada Lovelace", "ada.lovelace@sigaas.edu", PerfilUsuario.PROFESSOR, c1.id),
        ("Aluno Joao Silva", "joao.silva@sigaas.edu", PerfilUsuario.ALUNO, c1.id),
        ("Aluno Padrao", "aluno@sigaas.edu", PerfilUsuario.ALUNO, c1.id),
        ("Aluna Maria Souza", "maria.souza@sigaas.edu", PerfilUsuario.ALUNO, c1.id),
        ("Secretaria Academica", "secretaria@sigaas.edu", PerfilUsuario.SECRETARIA, c1.id),
    ]
    usuarios = {}
    for nome, email, perfil, campus_id in users_data:
        u = session.scalar(select(Usuario).where(Usuario.email == email))
        if not u:
            u = Usuario(campus_id=campus_id, nome=nome, email=email, senha_hash=senha_hash_padrao, perfil=perfil)
            session.add(u)
            session.flush()
        usuarios[email] = u

    # Usuarios discentes adicionais para compor turmas realistas
    alunos = [usuarios["joao.silva@sigaas.edu"], usuarios["maria.souza@sigaas.edu"], usuarios["aluno@sigaas.edu"]]
    for i in range(1, 31):
        email_aluno = f"aluno{i:02d}@sigaas.edu"
        u = session.scalar(select(Usuario).where(Usuario.email == email_aluno))
        if not u:
            u = Usuario(
                campus_id=c1.id,
                nome=f"Aluno Sintetico {i:02d}",
                email=email_aluno,
                senha_hash=senha_hash_padrao,
                perfil=PerfilUsuario.ALUNO
            )
            session.add(u)
            session.flush()
        if u not in alunos:
            alunos.append(u)

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
        (c1.id, "A", "101", TipoSala.REGULAR, 50, ["matutino", "vespertino", "noturno"]),
        (c1.id, "A", "102", TipoSala.REGULAR, 25, ["matutino", "vespertino", "noturno"]),
        (c1.id, "B", "201", TipoSala.LABORATORIO, 35, ["matutino", "vespertino", "noturno"]),
        (c1.id, "B", "202", TipoSala.REGULAR, 30, ["matutino", "vespertino", "noturno"]),
        (c1.id, "AUD", "01", TipoSala.AUDITORIO, 120, ["vespertino", "noturno"]),
        (c2.id, "ZN-A", "101", TipoSala.REGULAR, 40, ["matutino", "noturno"]),
    ]
    salas = {}
    for cid, bloco, num, tipo, cap, turnos in salas_data:
        key = f"{cid}_{bloco}_{num}"
        s = session.scalar(select(Sala).where(Sala.campus_id == cid, Sala.bloco == bloco, Sala.numero == num))
        if not s:
            s = Sala(campus_id=cid, bloco=bloco, numero=num, tipo=tipo, capacidade=cap, turnos_disponiveis=turnos)
            session.add(s)
            session.flush()
            session.add(SalaEquipamento(sala_id=s.id, equipamento_id=equipamentos["Projetor 4K"].id, quantidade=1))
        salas[key] = s

    # 5. Cursos e Disciplinas
    curso = session.scalar(select(Curso).where(Curso.campus_id == c1.id, Curso.codigo == "CC"))
    if not curso:
        curso = Curso(campus_id=c1.id, nome="Ciencia da Computacao", codigo="CC")
        session.add(curso)
        session.flush()

    disciplinas_data = [
        ("CC-101", "Algoritmos e Programacao", 60),
        ("CC-102", "Engenharia de Software", 60),
        ("CC-201", "Banco de Dados", 60),
    ]
    disciplinas = {}
    for cod, nome, ch in disciplinas_data:
        disc = session.scalar(select(Disciplina).where(Disciplina.curso_id == curso.id, Disciplina.codigo == cod))
        if not disc:
            disc = Disciplina(curso_id=curso.id, nome=nome, codigo=cod, carga_horaria=ch)
            session.add(disc)
            session.flush()
        disciplinas[cod] = disc

    # 6. Turmas e Matriculas
    prof = usuarios["alan.turing@sigaas.edu"]
    prof_ada = usuarios["ada.lovelace@sigaas.edu"]

    turmas_config = [
        ("CC-101", "2026.1", Turno.MATUTINO, prof.id, 20),
        ("CC-102", "2026.1", Turno.NOTURNO, prof_ada.id, 30),
        ("CC-201", "2026.1", Turno.VESPERTINO, prof.id, 25),
    ]
    turmas = {}
    matriculas_por_turma = {}
    for cod_disc, periodo, turno, prof_id, num_m in turmas_config:
        disc_obj = disciplinas[cod_disc]
        t = session.scalar(
            select(Turma).where(Turma.disciplina_id == disc_obj.id, Turma.periodo_letivo == periodo)
        )
        if not t:
            t = Turma(
                disciplina_id=disc_obj.id,
                professor_id=prof_id,
                periodo_letivo=periodo,
                num_matriculados=num_m,
                turno_preferido=turno
            )
            session.add(t)
            session.flush()
        else:
            t.num_matriculados = num_m
        turmas[cod_disc] = t

        mats = []
        for aluno in alunos[:num_m]:
            mat = session.scalar(
                select(Matricula).where(Matricula.aluno_id == aluno.id, Matricula.turma_id == t.id)
            )
            if not mat:
                mat = Matricula(aluno_id=aluno.id, turma_id=t.id)
                session.add(mat)
                session.flush()
            mats.append(mat)
        matriculas_por_turma[t.id] = mats

    # 7. Horarios e Logs
    s_a101 = salas[f"{c1.id}_A_101"]
    s_aud01 = salas[f"{c1.id}_AUD_01"]
    s_b201 = salas[f"{c1.id}_B_201"]

    horarios_config = [
        (turmas["CC-101"].id, s_a101.id, 0, time(8, 0), time(10, 0), prof.id),
        (turmas["CC-102"].id, s_aud01.id, 4, time(19, 0), time(21, 0), prof_ada.id),
        (turmas["CC-201"].id, s_b201.id, 2, time(14, 0), time(16, 0), prof.id),
    ]
    horarios = []
    for turma_id, sala_id, dia, h_ini, h_fim, resp_id in horarios_config:
        h = session.scalar(select(Horario).where(Horario.turma_id == turma_id, Horario.sala_id == sala_id))
        if not h:
            h = Horario(
                campus_id=c1.id,
                turma_id=turma_id,
                sala_id=sala_id,
                dia_semana=dia,
                hora_inicio=h_ini,
                hora_fim=h_fim
            )
            session.add(h)
            session.flush()
            session.add(LogAlocacao(
                horario_id=h.id,
                tipo_evento=TipoEventoLog.CRIACAO,
                usuario_responsavel=resp_id,
                detalhes="Alocacao de seed"
            ))
        horarios.append(h)

    # 8. Frequencias Sinteticas Realistas (Semanas Anteriores)
    # Gera 8 semanas de historico em dias uteis.
    # Sexta-feira e turno noturno apresentam absenteismo acentuado.
    data_base_segunda = date(2026, 2, 9)
    existing_freqs = set(
        session.execute(
            select(Frequencia.matricula_id, Frequencia.horario_id, Frequencia.data)
        ).all()
    )
    for h in horarios:
        mats = matriculas_por_turma.get(h.turma_id, [])
        dia_offset = h.dia_semana  # 0=Segunda, 2=Quarta, 4=Sexta
        for sem in range(8):
            dt_aula = data_base_segunda + timedelta(days=(sem * 7) + dia_offset)
            for mat in mats:
                if (mat.id, h.id, dt_aula) not in existing_freqs:
                    # Determinismo com seed reproduzivel
                    rng = random.Random(mat.id * 1000 + sem * 10 + dia_offset)
                    # Probabilidade base de presenca
                    prob_presenca = 0.88
                    if h.dia_semana == 4:
                        # Sexta-feira: queda acentuada de presenca
                        prob_presenca -= 0.35
                    if h.hora_inicio.hour >= 18:
                        # Turno noturno: queda adicional
                        prob_presenca -= 0.12
                    if len(mats) >= 30:
                        # Turma grande: menor engajamento
                        prob_presenca -= 0.06

                    esta_presente = rng.random() < max(0.15, prob_presenca)
                    session.add(Frequencia(
                        matricula_id=mat.id,
                        horario_id=h.id,
                        data=dt_aula,
                        presente=esta_presente
                    ))
                    existing_freqs.add((mat.id, h.id, dt_aula))

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
        "frequencia": session.query(Frequencia).count(),
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
