Variables	Outputs
snapshot_cluster
anthropic:claude-haiku-4-5-20251001
33.33% passing (1/3 cases)

prompt.md: ---
nome: Triagem de pods Kubernetes
descricao: An...
$ kubectl get pods -n sentinel-prod
NAME                            READY   STATUS             RESTARTS       AGE
sentinel-api-7d9c8b6f4-2xk9p    1/1     Running            0              6d
sentinel-api-7d9c8b6f4-h4m2t    0/1     CrashLoopBackOff   
...
2 PASS
# Triagem de Pods — sentinel-prod

**Resumo:** 4 pods avaliados, 1 problemático.

---

**`sentinel-prod/sentinel-api-7d9c8b6f4-h4m2t`** — `CrashLoopBackOff` · restarts: `14`

- **Causa provável:** Vazamento de memória ou consumo anômalo durante carre
...
Tokens: 2.578 (1.951+627)
Latency: 8.8s
Tokens/Sec: 71
Cost: $0.0051


$ kubectl get pods -n sentinel-prod
NAME                            READY   STATUS             RESTARTS   AGE
sentinel-api-7d9c8b6f4-2xk9p    1/1     Running            0          6d
sentinel-api-7d9c8b6f4-zzp10    0/1     ImagePullBackOff   0       
...
1 FAIL 2 PASS
(0.67)
Invalid regex pattern: Invalid regular expression: /(?i)ImagePullBackOff|manifest unknown|ErrImagePull/: Invalid group
# Triagem de Pods — sentinel-prod

**Resumo:** 4 pods avaliados, 2 problemáticos.

---

**`sentinel-prod/sentinel-api-7d9c8b6f4-zzp10`** — `ImagePullBackOff` · restarts: `0`

- **Causa provável:** A imagem `registry.aegis.io/sentinel-api:2.9.2` não e
...
Tokens: 2.767 (1.900+867)
Latency: 9.7s
Tokens/Sec: 89
Cost: $0.0062


$ kubectl get pods -n sentinel-prod
NAME                            READY   STATUS    RESTARTS     AGE
sentinel-api-7d9c8b6f4-2xk9p    1/1     Running   0            6d
sentinel-api-7d9c8b6f4-h4m2t    1/1     Running   0            6d
sentinel-worker
...
1 FAIL 1 PASS
(0.50)
Invalid regex pattern: Invalid regular expression: /(?i)saudável|nenhum pod|no pod|cluster saud/: Invalid group
✅ **Cluster saudável.** 4 pods avaliados, nenhum em estado problemático.

**Evidência de saúde:**
- Todos os 4 pods em `Running` com `Ready 1/1` (ou equivalente).
- Logs da API (pod mais crítico por natureza) mostram operação normal: health checks pa
...
Tokens: 2.002 (1.787+215)
Latency: 3.3s
Tokens/Sec: 66
Cost: $0.0029


Curadoria — devops/triagem-de-pods          
                                    
Modelo avaliado: claude-haiku-4-5-20251001
Resultado geral: 33 % aprovados (1/3 casos)                                                                                           
                                                                                                                              
---                                                                                                                                   
O que passou                                                                                                                          
                                                                                                                              
Entrada 1 — OOMKilled (2/2 asserts): o modelo identificou corretamente o pod sentinel-api-7d9c8b6f4-h4m2t, diagnosticou OOMKilled como
causa, citou o heap próximo ao limite (498 Mi / 512 Mi) e sugeriu aumentar o memory limit ou reduzir o cache. Saída bem estruturada, 
latência 8,8 s, custo $0,0051.                                                                                                        
                               
---                                                                                                                                   
O que falhou
                                                                                                                              
Entrada 2 — ImagePullBackOff + Pending (1 FAIL, 2 PASS):                                                                              
- Os dois icontains passaram (versão 2.9.2 e Insufficient presentes na saída).
- O assert type: regex com (?i)ImagePullBackOff|manifest unknown|ErrImagePull falhou com erro de configuração: Invalid group — o flag
inline (?i) não é suportado pelo engine de regex JavaScript que o promptfoo usa. A saída do modelo estava correta; o problema é do   
teste.                                                                                                                                
                                                                                                                              
Entrada 3 — Cluster saudável (1 FAIL, 1 PASS):                                                                                        
- O assert javascript passou: a saída não continha nenhuma das palavras-chave de erro.                                                
- O assert type: regex com (?i)saudável|nenhum pod|no pod|cluster saud falhou pelo mesmo motivo — (?i) inválido no engine JS. A saída 
do modelo continha "Cluster saudável" e estava correta.                                                                               
                                                                                                                              
---                                                                                                                                   
Causa raiz das falhas                                                                                                                 
                                                                                                                              
100 % dos FAILs são de configuração dos asserts, não de comportamento do modelo. O promptfoo usa JavaScript para avaliar type: regex; 
o flag inline (?i) é sintaxe PCRE/Python e gera Invalid group no JS. O modelo respondeu corretamente em todos os três casos.          
                                                                                                                              
---                                    
Ajuste necessário nos testes                                                                                                          
                                    
Substituir os dois type: regex com (?i) por type: javascript usando a sintaxe nativa JS:                                              
                                                                                                                              
# Entrada 2                                                                                                                           
- type: javascript
value: "/(ImagePullBackOff|manifest unknown|ErrImagePull)/i.test(output)"                                                           
                                                                                                                              
# Entrada 3                                                                                                                           
- type: javascript                                                                                                                    
value: "/(saudável|nenhum pod|no pod|cluster saud)/i.test(output)"       
