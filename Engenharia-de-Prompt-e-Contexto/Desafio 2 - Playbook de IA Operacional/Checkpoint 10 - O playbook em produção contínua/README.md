# Gate de qualidade — pipeline CI  

O build falha quando qualquer assertion reprovar — determinística ou LLM-judge. A suíte tem duas camadas: asserts de estrutura (icontains, latência, custo) e LLM-as-judge com rubrica 0–2 por critério, corte em 6/8. A folga de 2 pontos na rubrica absorve flutuação não-determinística — um prompt bem escrito passa mesmo com o juiz rigoroso em um critério; um prompt que regride perde mais de 2 pontos e é bloqueado.


# O que falha o build e por quê — alternativas consideradas:                                           

Só asserts determinísticos bloqueiam (rejeitado): verifica estrutura, não qualidade. Um prompt que regride de 8/8 para 4/8 no juiz passaria silenciosamente — os asserts confirmam que a palavra "Diagnóstico" existe, não que o diagnóstico está correto. Ganha-se zero falsos positivos; perde-se a proteção real contra regressão de raciocínio.

Judge como aviso, não bloqueio (rejeitado): avisos são ignorados sistematicamente. Se o judge não pode bloquear, não tem propósito em CI.


# Escopo por PR — alternativas consideradas:                                                                                         

Suite completa em todo PR (rejeitado): com 6 prompts custa ~US$ 0,18 e ~3–4 min por PR; à medida que o catálogo crescer, o custo escala linearmente sem benefício proporcional — prompts que não foram tocados não podem regredir por aquele PR. O push para main já roda tudo como gate final.

Nenhum eval no PR (rejeitado): elimina o feedback rápido no ciclo de desenvolvimento. O desenvolvedor só descobre a regressão após o merge.


# Não-determinismo do juiz — alternativas consideradas:                                                                                 

Retry com maioria (2 de 3 passam): triplica o custo de tokens e pode mascarar uma falha real se dois rodam com sorte. A folga na rubrica é mais honesta: tolera imperfeição pontual, bloqueia mediocridade consistente.

Desabilitar judge em CI (rejeitado): equivale a operar só com Camada 1. O judge existe para detectar exatamente o que icontains não consegue detectar — regressão de raciocínio, não de formato.
