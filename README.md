# Clinic Management API

Backend de um sistema SaaS para gestão de clínicas, desenvolvido com Django REST Framework.

O sistema foi projetado com arquitetura multi-tenant, garantindo isolamento total de dados entre clínicas, além de segurança reforçada para informações sensíveis (LGPD).

## 🚀 Principais funcionalidades

- Autenticação JWT (login seguro)
- Arquitetura multi-clínica (multi-tenant)
- Gestão de pacientes
- Agendamento de consultas
- Prontuário médico digital
- Controle financeiro básico
- Sistema de auditoria (CREATE / UPDATE / DELETE)
- Criptografia de dados sensíveis (CPF, documentos)
- Controle de permissões por perfil (admin / profissional)

## 🔐 Segurança

- Dados sensíveis criptografados em banco
- Auditoria completa de ações dos usuários
- Isolamento de dados por clínica
- Autenticação via JWT
- Proteções contra acesso não autorizado

## 🛠️ Tecnologias

- Python 3.11
- Django 5+
- Django REST Framework
- PostgreSQL
- Simple JWT
- Docker
- CORS Headers

## 🧱 Arquitetura

- Estrutura modular por apps
- Base model compartilhada
- Signals e services para auditoria
- API REST separada do frontend

## 📌 Objetivo

Projeto desenvolvido para portfólio e demonstração de arquitetura backend escalável para sistemas de saúde e SaaS.