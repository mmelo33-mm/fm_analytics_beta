"""
Sistema de Licenciamento e Planos do FM Analytics
"""

from datetime import datetime, timedelta
import json

# =======================
# CONFIGURAÇÃO DE PLANOS
# =======================

PLANOS = {
    "FREE": {
        "nome": "FREE",
        "preco_mensal": 99.90,
        "preco_anual": 999.00,  # ~17% desconto
        "limite_partidas": 999999,
        "limite_times": 999999,
        "limite_temporadas": 999999,
        "limite_usuarios": 5,
        "exportar_pdf": True,
        "exportar_excel": True,
        "backup_nuvem": True,
        "multiplos_times": True,
        "graficos_avancados": True,
        "comparar_temporadas": True,
        "api_acesso": True,
        "suporte": "vip",
        "cor": "purple"
    },
    "STARTER": {
        "nome": "Starter",
        "preco_mensal": 19.90,
        "preco_anual": 199.00,  # ~17% desconto
        "limite_partidas": 50,
        "limite_times": 2,
        "limite_temporadas": 2,
        "exportar_pdf": True,
        "exportar_excel": False,
        "backup_nuvem": False,
        "multiplos_times": True,
        "graficos_avancados": True,
        "comparar_temporadas": False,
        "suporte": "email",
        "cor": "blue"
    },
    "PRO": {
        "nome": "Pro",
        "preco_mensal": 39.90,
        "preco_anual": 399.00,  # ~17% desconto
        "limite_partidas": 999999,
        "limite_times": 999999,
        "limite_temporadas": 999999,
        "exportar_pdf": True,
        "exportar_excel": True,
        "backup_nuvem": True,
        "multiplos_times": True,
        "graficos_avancados": True,
        "comparar_temporadas": True,
        "suporte": "prioritario",
        "cor": "green"
    },
    "TEAM": {
        "nome": "Team",
        "preco_mensal": 99.90,
        "preco_anual": 999.00,  # ~17% desconto
        "limite_partidas": 999999,
        "limite_times": 999999,
        "limite_temporadas": 999999,
        "limite_usuarios": 5,
        "exportar_pdf": True,
        "exportar_excel": True,
        "backup_nuvem": True,
        "multiplos_times": True,
        "graficos_avancados": True,
        "comparar_temporadas": True,
        "api_acesso": True,
        "suporte": "vip",
        "cor": "purple"
    }
}


# =======================
# CLASSE DE LICENÇA
# =======================

class Licenca:
    """Gerencia licenças e permissões de usuários"""
    
    def __init__(self, plano="FREE", data_expiracao=None, codigo_ativacao=None):
        self.plano = plano
        self.data_expiracao = data_expiracao
        self.codigo_ativacao = codigo_ativacao
        self.configuracao = PLANOS.get(plano, PLANOS["FREE"])
    
    def esta_ativa(self):
        """Verifica se a licença está ativa"""
        if self.plano == "FREE":
            return True
        
        if self.data_expiracao is None:
            return False
        
        return datetime.now() < self.data_expiracao
    
    def dias_restantes(self):
        """Retorna quantos dias faltam para expirar"""
        if self.plano == "FREE":
            return 999999
        
        if self.data_expiracao is None:
            return 0
        
        delta = self.data_expiracao - datetime.now()
        return max(0, delta.days)
    
    def pode_cadastrar_partida(self, num_partidas_atual):
        """Verifica se pode cadastrar mais partidas"""
        if not self.esta_ativa():
            return False, "Licença expirada! Renove para continuar."
        
        limite = self.configuracao["limite_partidas"]
        
        if num_partidas_atual >= limite:
            return False, f"Limite de {limite} partidas atingido! Faça upgrade."
        
        return True, ""
    
    def pode_exportar_pdf(self):
        """Verifica se pode exportar PDF"""
        return self.esta_ativa() and self.configuracao["exportar_pdf"]
    
    def pode_exportar_excel(self):
        """Verifica se pode exportar Excel"""
        return self.esta_ativa() and self.configuracao["exportar_excel"]
    
    def pode_backup_nuvem(self):
        """Verifica se tem backup em nuvem"""
        return self.esta_ativa() and self.configuracao["backup_nuvem"]
    
    def pode_multiplos_times(self):
        """Verifica se pode ter múltiplos times"""
        return self.esta_ativa() and self.configuracao["multiplos_times"]
    
    def tem_graficos_avancados(self):
        """Verifica se tem acesso a gráficos avançados"""
        return self.esta_ativa() and self.configuracao["graficos_avancados"]
    
    def pode_comparar_temporadas(self):
        """Verifica se pode comparar temporadas"""
        return self.esta_ativa() and self.configuracao["comparar_temporadas"]
    
    def get_badge(self):
        """Retorna badge do plano"""
        badges = {
            "FREE": "🆓",
            "STARTER": "🌟",
            "PRO": "⚡",
            "TEAM": "🏆"
        }
        return badges.get(self.plano, "🆓")
    
    def get_info(self):
        """Retorna informações da licença"""
        return {
            "plano": self.plano,
            "nome": self.configuracao["nome"],
            "ativa": self.esta_ativa(),
            "dias_restantes": self.dias_restantes(),
            "limite_partidas": self.configuracao["limite_partidas"],
            "badge": self.get_badge(),
            "cor": self.configuracao["cor"]
        }


# =======================
# FUNÇÕES DE ATIVAÇÃO
# =======================

def gerar_codigo_ativacao(plano, duracao_dias=30):
    """Gera código de ativação único"""
    import hashlib
    import secrets
    
    timestamp = datetime.now().isoformat()
    random = secrets.token_hex(8)
    
    codigo = f"{plano}-{random}"
    hash_code = hashlib.sha256(codigo.encode()).hexdigest()[:12].upper()
    
    return f"{plano[:3]}{hash_code}"


def ativar_licenca(codigo_ativacao):
    """Ativa licença com código fornecido"""
    # Aqui você validaria o código no banco de dados
    # Por enquanto, exemplo básico:
    
    prefixo = codigo_ativacao[:3]
    plano_map = {
        "STA": "STARTER",
        "PRO": "PRO",
        "TEA": "TEAM"
    }
    
    plano = plano_map.get(prefixo, "FREE")
    data_expiracao = datetime.now() + timedelta(days=30)
    
    return Licenca(plano, data_expiracao, codigo_ativacao)


def verificar_promocao(codigo_promocao):
    """Verifica se código promocional é válido"""
    promocoes = {
        "PRIMEIRA7": {"desconto": 0, "dias_gratis": 7, "plano": "PRO"},
        "BLACKFRIDAY": {"desconto": 30, "dias_gratis": 0, "plano": None},
        "ANUAL50": {"desconto": 50, "dias_gratis": 0, "plano": None},
        "EARLYBIRD": {"desconto": 50, "dias_gratis": 30, "plano": "PRO"}
    }
    
    return promocoes.get(codigo_promocao.upper())


# =======================
# COMPARAÇÃO DE PLANOS
# =======================

def comparar_planos():
    """Retorna tabela comparativa de planos"""
    recursos = [
        ("Partidas cadastradas", "limite_partidas"),
        ("Times diferentes", "limite_times"),
        ("Exportar PDF", "exportar_pdf"),
        ("Exportar Excel", "exportar_excel"),
        ("Backup em nuvem", "backup_nuvem"),
        ("Gráficos avançados", "graficos_avancados"),
        ("Comparar temporadas", "comparar_temporadas"),
        ("Suporte", "suporte")
    ]
    
    comparacao = []
    
    for recurso_nome, recurso_chave in recursos:
        linha = {"recurso": recurso_nome}
        
        for plano_id, plano_config in PLANOS.items():
            valor = plano_config.get(recurso_chave, False)
            
            if isinstance(valor, bool):
                linha[plano_id] = "✅" if valor else "❌"
            elif isinstance(valor, int) and valor > 999:
                linha[plano_id] = "Ilimitado"
            else:
                linha[plano_id] = str(valor)
        
        comparacao.append(linha)
    
    return comparacao


# =======================
# MENSAGENS DE UPGRADE
# =======================

def get_mensagem_upgrade(motivo="limite_partidas"):
    """Retorna mensagem personalizada de upgrade"""
    mensagens = {
        "limite_partidas": {
            "titulo": "🚫 Limite de partidas atingido!",
            "texto": "Você atingiu o limite do plano gratuito. Faça upgrade para continuar analisando suas partidas!",
            "cta": "Ver Planos",
            "oferta": "🎁 30% OFF no primeiro mês com o cupom PRIMEIRA30"
        },
        "exportar_pdf": {
            "titulo": "🔒 Recurso Premium",
            "texto": "Exportar relatórios em PDF é exclusivo para assinantes. Upgrade agora e tenha acesso a essa e outras funcionalidades!",
            "cta": "Fazer Upgrade",
            "oferta": "✨ Teste 7 dias grátis do plano PRO"
        },
        "multiplos_times": {
            "titulo": "🔒 Recurso STARTER+",
            "texto": "Gerenciar múltiplos times é exclusivo para planos pagos. Faça upgrade e acompanhe todos os seus times!",
            "cta": "Ver Planos",
            "oferta": "🎯 Plano STARTER por apenas R$ 19,90/mês"
        },
        "backup_nuvem": {
            "titulo": "🔒 Recurso PRO",
            "texto": "Backup automático na nuvem é exclusivo do plano PRO. Nunca perca seus dados!",
            "cta": "Fazer Upgrade PRO",
            "oferta": "☁️ Seus dados seguros e acessíveis de qualquer lugar"
        }
    }
    
    return mensagens.get(motivo, mensagens["limite_partidas"])


# =======================
# EXEMPLO DE USO
# =======================

if __name__ == "__main__":
    # Criar licença FREE
    licenca_free = Licenca("FREE")
    print(f"Plano: {licenca_free.plano}")
    print(f"Pode cadastrar? {licenca_free.pode_cadastrar_partida(3)}")
    print(f"Pode exportar PDF? {licenca_free.pode_exportar_pdf()}")
    print(f"Badge: {licenca_free.get_badge()}")
    print()
    
    # Criar licença PRO
    data_exp = datetime.now() + timedelta(days=30)
    licenca_pro = Licenca("PRO", data_exp)
    print(f"Plano: {licenca_pro.plano}")
    print(f"Dias restantes: {licenca_pro.dias_restantes()}")
    print(f"Pode exportar PDF? {licenca_pro.pode_exportar_pdf()}")
    print(f"Info: {licenca_pro.get_info()}")
    print()
    
    # Gerar código de ativação
    codigo = gerar_codigo_ativacao("PRO", 30)
    print(f"Código gerado: {codigo}")
    print()
    
    # Comparar planos
    print("Comparação de planos:")
    for item in comparar_planos()[:3]:
        print(item)
