class PromptBuilder:
    """
    Pure text composition for system prompts.
    Does not hold state. Unaware of pipelines or routing.
    """
    @staticmethod
    def build_system_prompt(persona: dict, base_prompt: str = "") -> str:
        """
        Composes the final system prompt purely declaratively.
        Takes the base architectural prompt and appends persona traits.
        No procedural logic or IFs per persona.
        """
        prompt_parts = []
        
        if base_prompt:
            prompt_parts.append(base_prompt)
            prompt_parts.append("\n--- DIRETRIZES DE PERSONA ---")
            
        traits = persona.get("system_traits", [])
        if traits:
            prompt_parts.extend(traits)
            
        style = persona.get("response_style", {})
        if style:
            if "verbosity" in style:
                prompt_parts.append(f"Nível de verbosidade: {style['verbosity']}.")
            if "format" in style:
                prompt_parts.append(f"Formato esperado: {style['format']}.")
                
        tuning = persona.get("tuning", {})
        if tuning:
            prompt_parts.append("\n--- TUNING COMPORTAMENTAL ---")
            if "verbosity_bias" in tuning:
                prompt_parts.append(f"Tendência de Verbosidade: {tuning['verbosity_bias']}.")
            if "factuality_bias" in tuning:
                prompt_parts.append(f"Tendência de Factualidade: {tuning['factuality_bias']}.")
            if "chunking_style" in tuning:
                prompt_parts.append(f"Estilo de Frase/Chunk: {tuning['chunking_style']}.")
            if "creativity_bias" in tuning:
                prompt_parts.append(f"Tendência Criativa: {tuning['creativity_bias']}.")

        return "\n".join(prompt_parts)
