import os
import json
import time
import psutil
import requests
import statistics
from datetime import datetime

class LLMBenchmark:
    def __init__(self, models, runs=2):
        self.models = models
        self.runs = runs
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = os.path.join("benchmarks", "results", self.timestamp)
        os.makedirs(self.results_dir, exist_ok=True)
        
        self.test_cases = [
            {
                "category": "Factualidade Simples",
                "prompt": "Qual a capital do Japao?",
                "expected": "Toquio"
            },
            {
                "category": "Raciocinio Curto",
                "prompt": "Se eu tenho 3 macas e ganho mais 2, mas como 1, com quantas macas eu fico? Responda apenas o numero.",
                "expected": "4"
            },
            {
                "category": "Resumo",
                "prompt": "Resuma em uma frase: A inteligencia artificial e um campo da ciencia da computacao que se concentra na criacao de maquinas que podem realizar tarefas que normalmente exigem inteligencia humana.",
                "expected": None
            },
            {
                "category": "Instrucao",
                "prompt": "Liste 3 cores primarias, uma por linha, sem numeracao.",
                "expected": None
            },
            {
                "category": "Portugues Natural",
                "prompt": "Escreva uma saudacao amigavel para um assistente de voz.",
                "expected": None
            },
            {
                "category": "Resistencia a Alucinacao",
                "prompt": "Quem foi o presidente do Brasil em 1492?",
                "expected": "Nenhum (Brasil nao era um pais/descoberto)"
            },
            {
                "category": "Conversacional Real",
                "prompt": "Oi, tudo bem? O que voce pode fazer para me ajudar hoje?",
                "expected": None
            },
            {
                "category": "Respostas Longas",
                "prompt": "Explique detalhadamente como funciona o ciclo da agua para uma crianca.",
                "expected": None
            },
            {
                "category": "Contexto Multi-turn",
                "messages": [
                    {"role": "user", "content": "Meu nome e Rudy e eu adoro tecnologia."},
                    {"role": "assistant", "content": "Ola Rudy! E um prazer saber que voce gosta de tecnologia. Como posso ajudar?"},
                    {"role": "user", "content": "Qual e o meu nome e do que eu gosto?"}
                ],
                "expected": "Rudy, Tecnologia"
            }
        ]

    def get_ram_usage(self):
        """Retorna o uso de RAM do sistema em MB."""
        return psutil.virtual_memory().used / (1024 * 1024)

    def run_benchmark(self):
        print(f"--- Iniciando Benchmark LLM Expandido ({self.timestamp}) ---")
        print(f"Modelos: {', '.join(self.models)}")
        print(f"Execucoes por teste: {self.runs}")
        
        all_results = {}

        for model in self.models:
            print(f"\n[Modelo: {model}]")
            model_results = []
            
            for run in range(self.runs):
                print(f"  Execucao {run+1}/{self.runs}...")
                run_data = {
                    "run": run + 1,
                    "timestamp": datetime.now().isoformat(),
                    "tests": []
                }
                
                for case in self.test_cases:
                    category = case["category"]
                    print(f"    Testando: {category}...", end="", flush=True)
                    
                    start_ram = self.get_ram_usage()
                    start_time = time.time()
                    
                    try:
                        # Prepara o payload para Chat ou Generate
                        if "messages" in case:
                            payload = {
                                "model": model,
                                "messages": case["messages"],
                                "stream": False,
                                "options": {"temperature": 0.0, "num_ctx": 2048}
                            }
                            endpoint = "chat"
                        else:
                            payload = {
                                "model": model,
                                "prompt": case["prompt"],
                                "stream": False,
                                "options": {"temperature": 0.0, "num_ctx": 2048}
                            }
                            endpoint = "generate"

                        response = requests.post(
                            f"http://localhost:11434/api/{endpoint}",
                            json=payload,
                            timeout=90 # Aumentado para modelos maiores
                        )
                        response.raise_for_status()
                        res_json = response.json()
                        
                        end_time = time.time()
                        end_ram = self.get_ram_usage()
                        
                        # Extrai a resposta textual independente do endpoint
                        res_text = ""
                        if endpoint == "chat":
                            res_text = res_json.get("message", {}).get("content", "")
                        else:
                            res_text = res_json.get("response", "")

                        total_duration = res_json.get("total_duration", 0) / 1e9
                        load_duration = res_json.get("load_duration", 0) / 1e9
                        
                        tokens_count = res_json.get("eval_count", 0)
                        eval_duration = res_json.get("eval_duration", 1) / 1e9
                        tokens_per_sec = tokens_count / eval_duration
                        
                        test_result = {
                            "category": category,
                            "prompt": case.get("prompt") or case.get("messages")[-1]["content"],
                            "response": res_text.strip(),
                            "metrics": {
                                "duration_total_s": round(total_duration, 3),
                                "load_duration_s": round(load_duration, 3),
                                "tokens_count": tokens_count,
                                "tokens_per_sec": round(tokens_per_sec, 2),
                                "ram_peak_mb": round(max(start_ram, end_ram), 2),
                                "response_length": len(res_text)
                            }
                        }
                        run_data["tests"].append(test_result)
                        print(" OK")
                        
                    except Exception as e:
                        print(f" ERRO: {e}")
                        run_data["tests"].append({
                            "category": category,
                            "error": str(e)
                        })
                
                model_results.append(run_data)
            
            # Salvar JSON bruto do modelo
            model_file = os.path.join(self.results_dir, f"{model.replace(':', '_')}.json")
            with open(model_file, "w", encoding="utf-8") as f:
                json.dump(model_results, f, indent=2, ensure_ascii=False)
            
            # Calcular Estatisticas
            stats = self.calculate_stats(model_results)
            all_results[model] = stats
            
        # Salvar Resumo Consolidado
        summary_file = os.path.join(self.results_dir, "summary_stats.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
            
        print(f"\n--- Benchmark concluido! Resultados em: {self.results_dir} ---")
        return all_results

    def calculate_stats(self, model_results):
        metrics_pool = {
            "duration_total_s": [],
            "tokens_per_sec": [],
            "ram_peak_mb": []
        }
        
        for run in model_results:
            for test in run["tests"]:
                if "metrics" in test:
                    for key in metrics_pool:
                        metrics_pool[key].append(test["metrics"][key])
        
        stats = {}
        for key, values in metrics_pool.items():
            if values:
                stats[key] = {
                    "min": round(min(values), 3),
                    "max": round(max(values), 3),
                    "mean": round(statistics.mean(values), 3),
                    "stdev": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0
                }
        return stats

if __name__ == "__main__":
    # Modelos para o benchmark expandido
    models_to_test = [
        "qwen2.5:0.5b", 
        "qwen2.5:1.5b", 
        "llama3.2:1b", 
        "gemma3:4b"
    ]
    
    benchmark = LLMBenchmark(models=models_to_test, runs=2)
    benchmark.run_benchmark()
