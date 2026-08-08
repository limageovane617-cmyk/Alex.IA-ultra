# ============================================================
# 🎬 ALEX IA ULTRA — MOTOR WAN
# Motor de vídeo baseado na família Wan
# Criada por Geovani
# ============================================================

from typing import Optional, Dict, Any


NOME_MOTOR = "Wan"


class WanMotor:
    """
    Adaptador do motor Wan para a Alex IA Ultra.

    A função deste arquivo é manter toda a integração
    do Wan separada do restante da Ultra.
    """

    nome = NOME_MOTOR

    def __init__(self):
        self.disponivel = True

    def info(self) -> Dict[str, Any]:
        """Retorna informações sobre o motor."""
        return {
            "nome": self.nome,
            "tipo": "image-to-video",
            "status": "disponível para integração",
        }

    def preparar_prompt(
        self,
        prompt: str,
        camera: Optional[str] = None,
        proporcao: str = "9:16",
        duracao: int = 8,
    ) -> str:
        """
        Prepara o prompt cinematográfico que será enviado
        ao motor de vídeo.
        """

        partes = [
            prompt.strip(),
            f"Proporção: {proporcao}",
            f"Duração: {duracao} segundos",
        ]

        if camera:
            partes.append(f"Câmera cinematográfica: {camera}")

        return "\n".join(partes)

    def gerar(
        self,
        prompt: str,
        imagem: Optional[str] = None,
        camera: Optional[str] = None,
        proporcao: str = "9:16",
        duracao: int = 8,
    ) -> Dict[str, Any]:
        """
        Prepara uma solicitação de geração.

        A conexão real com o servidor Wan será feita pelo
        gerenciador de motores, permitindo trocar de motor
        quando necessário.
        """

        if not prompt or not prompt.strip():
            return {
                "sucesso": False,
                "motor": self.nome,
                "erro": "O prompt de vídeo está vazio.",
            }

        prompt_final = self.preparar_prompt(
            prompt=prompt,
            camera=camera,
            proporcao=proporcao,
            duracao=duracao,
        )

        return {
            "sucesso": True,
            "motor": self.nome,
            "prompt": prompt_final,
            "imagem": imagem,
            "proporcao": proporcao,
            "duracao": duracao,
            "status": "pronto_para_gerar",
        }


def obter_motor() -> WanMotor:
    """Retorna uma instância do motor Wan."""
    return WanMotor()


def testar_motor() -> bool:
    """Teste simples para verificar se o módulo está funcionando."""

    motor = obter_motor()

    resultado = motor.gerar(
        prompt="Um robô futurista caminhando em uma cidade à noite.",
        camera="Sony FX6",
        proporcao="9:16",
        duracao=8,
    )

    return resultado.get("sucesso", False)


if __name__ == "__main__":
    print("🎬 Motor Wan — Alex IA Ultra")
    print("Status:", "OK" if testar_motor() else "ERRO")
