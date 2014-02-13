#! /usr/bin/python2
# -*- coding: utf-8 -*-
#
# dac_parser.py
# Copyright (c) 2014, Centro Acadêmico da Computação da Unicamp
# All rights reserved.
#
# Módulo para adquirir informações sobre oferecimento de disciplinas na Unicamp.

import mechanize
import urllib
import re
import sys

################################################################################
# Constantes
################################################################################

### URLs
MAIN_URL = 'http://www.daconline.unicamp.br/altmatr/menupublico.do'
REQUEST_URL = 'http://www.daconline.unicamp.br/altmatr/conspub_matriculadospordisciplinaturma.do?org.apache.struts.taglib.html.TOKEN=%s&txtDisciplina=%s&txtTurma=%s&cboSubG=%s&cboSubP=%s&cboAno=%s&btnAcao=Continuar'

### Regex patterns
TOKEN_PATTERN = 'var token = "((?P<token>[0-9a-f]{32,32}))";'
DISCIPLINE_PATTERN = 'Disciplina:</span>&nbsp;&nbsp;(?P<disciplina>[A-Za-z][A-Za-z ][0-9]{3}) (?P<turma>[A-Za-z0-9]) &nbsp;&nbsp; -&nbsp;&nbsp; (?P<materia>.+)</td>'
PROFESSOR_PATTERN = 'Docente:</span>&nbsp;&nbsp;(?P<professor>.+)</td>'
RA_PATTERN = '<td height="18" bgcolor="white" align="center" class="corpo" width="80">([0-9]+)</td>'
NAME_PATTERN = '<td height="18" bgcolor="white" width="270" align="left" class="corpo">&nbsp;&nbsp;&nbsp;&nbsp;(.+)</td>'

################################################################################
# Funções
################################################################################

def get_students(info):
    """
    Busca lista de alunos e informações de turmas de uma determinada disciplina.

    Recebe como parâmetro um dicionário da seguinte forma:

    info = {
        'course': 'MC868',   # Código da disciplina
        'classes': 'A',   # or 'AB', 'XYWZ'
        'year': '2013',   # Ano do oferecimento
        'semester': '2',
        'type': 'undergrad'   # or 'grad'
    }

    Retorna uma lista com a seguinte tupla para cada turma:
        (
            'MC868',   # Código da disciplina
            'A',   # Identificador da turma
            'Linguagens Formais e Autômatos',   # Nome da disciplina
            'Arnaldo Vieira Moura',   # Nome do professor responsável
            [ lista de tuplas (ra, nome) para cada aluno matriculado ]
        )
    """

    # Recebe as informações da disciplina
    course = info["course"]
    classes = info["classes"]
    year = info["year"]
    if info["type"] == "undergrad":
        undergrad = info["semester"]
        grad = "0"
    elif info["type"] == "grad":
        grad = "2" + info["semester"]
        undergrad = "0"
    else:
        sys.stderr.write('dac_parser: Tipo %s Inválido.\n' % (info['type']))
        return None

    # Abre a página de consultas da DAC
    mech = mechanize.Browser()
    f = mech.open(MAIN_URL)
    site = f.read()

    # Procura pelo token da DAC
    token_pattern = re.compile(TOKEN_PATTERN)
    matches = re.search(token_pattern, site)
    if matches == None:
        sys.stderr.write("dac_parser: Não foi possível acessar o site da DAC.\n")
        sys.exit(1)
    token = matches.group("token")

    # Inicializa lista de turmas
    result = []

    # Percorre a lista com as turmas pegando os dados de seus alunos
    for cls in classes:
        # URL para onde são enviados os requerimentos
        url = REQUEST_URL % (token, course, cls,undergrad, grad, year)

        # Abre a página que contém as informações dos alunos
        f = mech.open(url)
        site = f.read()

        # Obtem informações através de regex
        # Nome do professor
        matches = re.search(PROFESSOR_PATTERN, site)
        if matches == None:
            # Turma inválida (não há docente responsável)
            sys.stderr.write("dac_parser: Turma %s Inválida.\n" % (course+cls))
            continue
        prof = matches.group("professor").strip()

        # Nome da disciplina
        matches = re.search(DISCIPLINE_PATTERN, site)
        if matches == None:
            # Turma inválida (não encontrou nome da disciplina)
            sys.stderr.write("dac_parser: Turma %s Inválida.\n" % (course+cls))
            continue
        disc = matches.group("disciplina").strip()
        class_id = matches.group("turma").strip()
        disc_name = matches.group("materia").strip()

        # Lista de matrículados
        ra_list = re.findall(RA_PATTERN, site)
        names = re.findall(NAME_PATTERN, site)

        # Turma vazia, descarta-a
        if len(names) == 0:
            sys.stderr.write("dac_parser: Turma %s Inválida.\n" % (course+cls))
            continue

        # Erro de parsing
        if len(names) != len(ra_list):
            sys.stderr.write("dac_parser: Problema lendo alunos da Turma %s.\n" % (course+cls))
            continue

        # Gera dicionário onde chave é letra da turma e itens uma lista de
        # (ra,nome) de cada aluno matriculado na turma
        students = []
        for i in range(len(ra_list)):
            students.append( (ra_list[i], (names[i]).strip()) )

        result.append( (disc, class_id, disc_name, prof, students) )

    return result
