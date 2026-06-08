# ==============================================================================
# SISTEMA CONTÁBIL SIMPLIFICADO
# ==============================================================================

# 1. Cadastro de Contas (Plano de Contas simplificado)
plano_de_contas = {
    # Contas Patrimoniais
    "1.01": "Ativo Circulante - Caixa/Banco",
    "1.02": "Ativo Não Circulante - Imobilizado",
    "2.01": "Passivo Circulante - Fornecedores",
    "2.02": "Patrimônio Líquido - Capital Social",
    "2.03": "Patrimônio Líquido - Lucros/Prejuízos Acumulados",
    
    # Contas de Resultado
    "4.01": "Receita Bruta de Vendas",
    "4.02": "Deduções de Vendas",
    "5.01": "Despesas Administrativas",
    "5.02": "Outras Receitas",
    "6.01": "Impostos sobre o Lucro",
    "7.01": "ARE (Apuração do Resultado do Exercício)"
}

# 2. Banco de Dados temporário (Lista de Lançamentos)
# Estrutura: [Data, Conta Débito, Conta Crédito, Valor, Histórico]
livro_diario = [
    ["01/06/2026", "1.01", "2.02", 50000.00, "Constituição de Capital Social"],
    ["02/06/2026", "1.01", "4.01", 15000.00, "Venda de Serviços à Vista"],
    ["03/06/2026", "5.01", "1.01",  2000.00, "Pagamento de Aluguel"],
    ["04/06/2026", "6.01", "1.01",   500.00, "Provisão/Pgto de Impostos"]
]

def novo_lancamento(data, conta_debito, conta_credito, valor, historico):
    """Função para adicionar novos lançamentos no Diário"""
    if conta_debito not in plano_de_contas or conta_credito not in plano_de_contas:
        print("❌ Erro: Uma ou ambas as contas não existem no Plano de Contas.")
        return
    
    livro_diario.append([data, conta_debito, conta_credito, valor, historico])
    print("✅ Lançamento realizado com sucesso!")

def gerar_relatorios():
    """Calcula os saldos e separa entre DRE e Balanço"""
    # Dicionário para armazenar o saldo final de cada conta
    saldos = {codigo: 0.0 for codigo in plano_de_contas}
    
    # Processa as Partidas Dobradas (Débito e Crédito)
    for lancamento in livro_diario:
        _, c_deb, c_cred, valor, _ = lancamento
        
        # Regra Contábil Simplificada:
        # Contas que começam com 1, 5, 6 (Ativo e Despesas) -> Aumentam no Débito, diminuem no Crédito
        # Contas que começam com 2, 4 (Passivo, PL e Receitas) -> Aumentam no Crédito, diminuem no Débito
        
        # Aplicando Débito
        if c_deb.startswith(('1', '5', '6')):
            saldos[c_deb] += valor
        else:
            saldos[c_deb] -= valor
            
        # Aplicando Crédito
        if c_cred.startswith(('2', '4')):
            saldos[c_cred] += valor
        else:
            saldos[c_cred] -= valor

    # --- GERANDO A DRE ---
    print("\n========================================")
    print("      DRE - DEMONSTRAÇÃO DE RESULTADO   ")
    print("========================================")
    
    receitas = saldos.get("4.01", 0) - saldos.get("4.02", 0)
    despesas = saldos.get("5.01", 0) - saldos.get("5.02", 0)
    impostos = saldos.get("6.01", 0)
    
    lucro_liquido = receitas - despesas - impostos
    
    print(f"Receita Líquida:      R$ {receitas:,.2f}")
    print(f"Despesas:             R$ {despesas:,.2f}")
    print(f"Impostos sobre Lucro: R$ {impostos:,.2f}")
    print("----------------------------------------")
    print(f"LUCRO LÍQUIDO (ARE):  R$ {lucro_liquido:,.2f}")
    
    # Transfere o lucro da DRE para o Lucro Acumulado do Balanço (Simulação da conta 7)
    saldos["2.03"] += lucro_liquido

    # --- GERANDO O BALANÇO PATRIMONIAL ---
    print("\n========================================")
    print("         BALANÇO PATRIMONIAL            ")
    print("========================================")
    print(" ATIVO (Aplicações)")
    total_ativo = 0
    for cod, nome in plano_de_contas.items():
        if cod.startswith('1'):
            print(f"  {cod} - {nome}: R$ {saldos[cod]:,.2f}")
            total_ativo += saldos[cod]
            
    print(f" TOTAL DO ATIVO: R$ {total_ativo:,.2f}")
    print("----------------------------------------")
    print(" PASSIVO E PL (Origens)")
    total_passivo_pl = 0
    for cod, nome in plano_de_contas.items():
        if cod.startswith('2'):
            print(f"  {cod} - {nome}: R$ {saldos[cod]:,.2f}")
            total_passivo_pl += saldos[cod]
            
    print(f" TOTAL DO PASSIVO + PL: R$ {total_passivo_pl:,.2f}")
    print("========================================")
    
    # Validação da Equação Patrimonial: Ativo deve ser igual a Passivo + PL
    if round(total_ativo, 2) == round(total_passivo_pl, 2):
        print("💪 Balanço Fechado com Sucesso! (A = P + PL)")
    else:
        print("⚠️ Alerta: O Balanço não fechou! Verifique os lançamentos.")

# --- TESTANDO O SISTEMA ---
# 1. Executa com os dados iniciais
gerar_relatorios()

# 2. Fazendo um novo lançamento de venda para testar
print("\n--- Inserindo nova receita de R$ 5.000,00 ---")
novo_lancamento("05/06/2026", "1.01", "4.01", 5000.00, "Venda de serviços em dinheiro")

# 3. Gera os relatórios atualizados
gerar_relatorios()
