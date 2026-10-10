import io
import os
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

LARGURA, ALTURA = 1280, 720
FPS = 10
SILENCIO_ENTRE_FALAS = 0.6
SILENCIO_FINAL = 1.0

FONTES_NEGRITO = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]
FONTES_NORMAL = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/Library/Fonts/Arial.ttf",
]


@lru_cache(maxsize=4000)
def _audio_tts(texto, lang, tld, lento):
    from gtts import gTTS

    ultimo_erro = None
    for _ in range(3):
        try:
            buf = io.BytesIO()
            gTTS(text=texto, lang=lang, tld=tld, slow=lento).write_to_fp(buf)
            dados = buf.getvalue()
            if dados:
                return dados
        except Exception as e:
            ultimo_erro = e
            time.sleep(1)
    raise RuntimeError(f"Não consegui gerar o áudio de '{texto}': {ultimo_erro}")


def _fonte(tamanho, negrito=True):
    from PIL import ImageFont

    for caminho in FONTES_NEGRITO if negrito else FONTES_NORMAL:
        if os.path.exists(caminho):
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default(size=tamanho)


def _quebrar_linhas(draw, texto, fonte, largura_max):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = f"{atual} {palavra}".strip()
        if draw.textlength(teste, font=fonte) <= largura_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas or [""]


def _slide(caminho, titulo, posicao, total, en, pt):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (LARGURA, ALTURA), (11, 14, 20))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, LARGURA, 8], fill=(99, 102, 241))

    d.text((60, 36), titulo, font=_fonte(30, False), fill=(148, 163, 184))
    contador = f"{posicao} / {total}"
    fonte_cont = _fonte(30, False)
    d.text((LARGURA - 60 - d.textlength(contador, font=fonte_cont), 36), contador, font=fonte_cont, fill=(148, 163, 184))

    fonte_en = _fonte(66)
    fonte_pt = _fonte(54)
    linhas_en = _quebrar_linhas(d, en, fonte_en, LARGURA - 160)
    linhas_pt = _quebrar_linhas(d, pt, fonte_pt, LARGURA - 160) if pt else []
    alt_en, alt_pt = 84, 70
    altura_total = len(linhas_en) * alt_en + (40 + len(linhas_pt) * alt_pt if linhas_pt else 0)
    y = (ALTURA - altura_total) // 2 + 20
    for linha in linhas_en:
        d.text((LARGURA / 2, y), linha, font=fonte_en, fill=(241, 245, 249), anchor="mt")
        y += alt_en
    y += 40
    for linha in linhas_pt:
        d.text((LARGURA / 2, y), linha, font=fonte_pt, fill=(110, 231, 183), anchor="mt")
        y += alt_pt

    largura_barra = int((LARGURA - 120) * posicao / total)
    d.rectangle([60, ALTURA - 40, LARGURA - 60, ALTURA - 32], fill=(30, 41, 59))
    d.rectangle([60, ALTURA - 40, 60 + largura_barra, ALTURA - 32], fill=(16, 185, 129))
    img.save(caminho)


def _segmento(ffmpeg, pasta, nome, png, pecas, saida):
    cmd = [ffmpeg, "-y", "-loop", "1", "-framerate", str(FPS), "-i", png]
    filtros = []
    for i, (tipo, valor) in enumerate(pecas, start=1):
        if tipo == "arquivo":
            cmd += ["-i", valor]
        else:
            cmd += ["-f", "lavfi", "-t", str(valor), "-i", "anullsrc=r=24000:cl=mono"]
        filtros.append(f"[{i}:a]aformat=sample_rates=24000:channel_layouts=mono[a{i}]")
    entradas = "".join(f"[a{i}]" for i in range(1, len(pecas) + 1))
    filtro = ";".join(filtros) + f";{entradas}concat=n={len(pecas)}:v=0:a=1[a]"
    cmd += [
        "-filter_complex", filtro, "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-c:a", "aac", "-b:a", "96k", "-ar", "44100", "-ac", "2",
        "-shortest", saida,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou em {nome}: {r.stderr[-400:]}")


def gerar_video_bloco(dados, repetir_2x, titulo, progresso=None):
    import imageio_ffmpeg

    def avisar(fracao, msg):
        if progresso:
            progresso(min(max(fracao, 0.0), 1.0), msg)

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    total = len(dados)
    pasta = tempfile.mkdtemp(prefix="duocido_")
    try:
        pedidos = []
        for item in dados:
            if repetir_2x:
                pedidos.append((item["en"], "en", "com", True))
            pedidos.append((item["en"], "en", "com", False))
            pedidos.append((item["pt"], "pt", "com.br", False))

        avisar(0.0, "Gerando as vozes...")
        with ThreadPoolExecutor(max_workers=4) as pool:
            for i, _ in enumerate(pool.map(lambda p: _audio_tts(*p), pedidos), start=1):
                avisar(0.5 * i / len(pedidos), f"Gerando as vozes ({i}/{len(pedidos)})...")

        def montar(indice):
            item = dados[indice]
            base = os.path.join(pasta, f"f{indice:04d}")
            arquivos = {}
            for chave, pedido in {
                "en_lento": (item["en"], "en", "com", True),
                "en": (item["en"], "en", "com", False),
                "pt": (item["pt"], "pt", "com.br", False),
            }.items():
                if chave == "en_lento" and not repetir_2x:
                    continue
                caminho = f"{base}_{chave}.mp3"
                with open(caminho, "wb") as f:
                    f.write(_audio_tts(*pedido))
                arquivos[chave] = caminho

            _slide(f"{base}_a.png", titulo, indice + 1, total, item["en"], "")
            _slide(f"{base}_b.png", titulo, indice + 1, total, item["en"], item["pt"])

            pecas_en = []
            if repetir_2x:
                pecas_en += [("arquivo", arquivos["en_lento"]), ("silencio", SILENCIO_ENTRE_FALAS)]
            pecas_en += [("arquivo", arquivos["en"]), ("silencio", SILENCIO_ENTRE_FALAS)]
            pecas_pt = [("arquivo", arquivos["pt"]), ("silencio", SILENCIO_FINAL)]

            seg_a, seg_b = f"{base}_a.mp4", f"{base}_b.mp4"
            _segmento(ffmpeg, pasta, f"{indice}a", f"{base}_a.png", pecas_en, seg_a)
            _segmento(ffmpeg, pasta, f"{indice}b", f"{base}_b.png", pecas_pt, seg_b)
            return [seg_a, seg_b]

        segmentos = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            for i, segs in enumerate(pool.map(montar, range(total)), start=1):
                segmentos += segs
                avisar(0.5 + 0.45 * i / total, f"Montando o vídeo ({i}/{total})...")

        avisar(0.96, "Juntando tudo...")
        lista = os.path.join(pasta, "lista.txt")
        with open(lista, "w", encoding="utf-8") as f:
            for seg in segmentos:
                f.write("file '" + seg.replace("\\", "/") + "'\n")
        final = os.path.join(pasta, "final.mp4")
        r = subprocess.run(
            [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", "-movflags", "+faststart", final],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"ffmpeg falhou ao juntar: {r.stderr[-400:]}")
        with open(final, "rb") as f:
            conteudo = f.read()
        avisar(1.0, "Pronto!")
        return conteudo
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
