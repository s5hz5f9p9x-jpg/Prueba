#!/usr/bin/env python3
"""
Audio Report Summary
Generates an audio summary of a report using Claude API and gTTS.
Usage: python audio_summary.py [report_file] [--lang es|en] [--output output.mp3]
"""

import sys
import os
import argparse
import anthropic
from gtts import gTTS

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


def read_report(file_path: str) -> str:
    """Read the report content from a text or PDF file."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        if not PDF_SUPPORT:
            raise RuntimeError("PyPDF2 is required for PDF support: pip install PyPDF2")
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() for page in reader.pages)

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def summarize_for_audio(report_text: str, lang: str) -> str:
    """Use Claude to create a concise, audio-friendly summary."""
    client = anthropic.Anthropic()

    lang_instruction = (
        "en español, en un estilo natural y fluido para escucha de audio"
        if lang == "es"
        else "in English, in a natural and fluid style suitable for audio listening"
    )

    system_prompt = (
        "Eres un experto en síntesis de informes para formato de audio. "
        "Tu tarea es generar resúmenes concisos, claros y amenos para escuchar. "
        "Evita listas con viñetas, tablas o formatos visuales. "
        "Usa frases completas y un tono conversacional."
        if lang == "es"
        else
        "You are an expert at summarizing reports for audio format. "
        "Your task is to generate concise, clear, and pleasant summaries to listen to. "
        "Avoid bullet points, tables, or visual formatting. "
        "Use complete sentences and a conversational tone."
    )

    prompt = (
        f"Resume el siguiente informe {lang_instruction}. "
        f"El resumen debe durar aproximadamente 60-90 segundos al escucharlo. "
        f"Cubre los puntos más importantes: resultados clave, logros destacados y perspectivas.\n\n"
        f"INFORME:\n{report_text}"
        if lang == "es"
        else
        f"Summarize the following report {lang_instruction}. "
        f"The summary should take approximately 60-90 seconds to listen to. "
        f"Cover the most important points: key results, highlights, and outlook.\n\n"
        f"REPORT:\n{report_text}"
    )

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        summary = ""
        print("Generando resumen..." if lang == "es" else "Generating summary...")
        for text in stream.text_stream:
            summary += text
            print(text, end="", flush=True)

    print("\n")
    return summary


def text_to_audio(text: str, output_path: str, lang: str) -> None:
    """Convert text to audio using gTTS and save as MP3."""
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Genera un audio resumido de un informe."
    )
    parser.add_argument(
        "report",
        nargs="?",
        default="sample_report.txt",
        help="Ruta al archivo del informe (.txt o .pdf)",
    )
    parser.add_argument(
        "--lang",
        choices=["es", "en"],
        default="es",
        help="Idioma del audio (es=español, en=inglés). Default: es",
    )
    parser.add_argument(
        "--output",
        default="resumen_audio.mp3",
        help="Nombre del archivo de audio de salida. Default: resumen_audio.mp3",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.report):
        print(f"Error: no se encontró el archivo '{args.report}'")
        sys.exit(1)

    print(f"Leyendo informe: {args.report}")
    report_text = read_report(args.report)

    if not report_text.strip():
        print("Error: el archivo de informe está vacío.")
        sys.exit(1)

    print(f"Informe cargado ({len(report_text)} caracteres).\n")

    summary = summarize_for_audio(report_text, args.lang)

    print("Convirtiendo resumen a audio...")
    text_to_audio(summary, args.output, args.lang)

    print(f"Audio generado exitosamente: {args.output}")
    print(
        f"Tip: abre el archivo '{args.output}' con cualquier reproductor de audio."
    )


if __name__ == "__main__":
    main()
